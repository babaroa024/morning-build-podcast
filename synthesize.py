#!/usr/bin/env python3
"""台本(.md) を日本語女性音声の MP3 に変換する。

- Edge TTS (ja-JP-NanamiNeural) を使用。APIキー不要・無料。
- 「―――」の行を境にセクション分割し、その間に無音を挿入して「間」を作る。
- 読み上げ対象外のメタ情報（ディレクション表・尺の表・出典）は自動で除去する。

使い方:  python3 scripts/synthesize.py episodes/2026-09-15.md build/2026-09-15.mp3
"""
import asyncio
import os
import re
import subprocess
import sys
import tempfile

VOICE = os.environ.get("TTS_VOICE", "ja-JP-NanamiNeural")
RATE = os.environ.get("TTS_RATE", "-5%")          # 標準よりわずかに遅め
PITCH = os.environ.get("TTS_PITCH", "+0Hz")
PAUSE_SEC = float(os.environ.get("TTS_PAUSE_SEC", "1.6"))   # セクション間の無音
MAX_CHARS = 1800                                   # 1リクエストあたりの上限

# 読み上げから除外する見出しブロック（この見出しから次の "## " まで捨てる）
SKIP_HEADINGS = ("音声合成ディレクション", "構成と尺の目安", "出典", "本人向けメモ")


def extract_speech(markdown: str) -> list[str]:
    """Markdown 台本から、読み上げるテキストをセクションのリストとして取り出す。"""
    lines = markdown.splitlines()
    kept, skipping = [], False

    for line in lines:
        if line.startswith("#"):
            heading = line.lstrip("#").strip()
            skipping = any(k in heading for k in SKIP_HEADINGS)
            # 本文の見出し自体は読み上げない（章題は音声に不要）
            continue
        if skipping:
            continue
        kept.append(line)

    body = "\n".join(kept)

    body = re.sub(r"^\s*\|.*\|\s*$", "", body, flags=re.M)   # 表を削除
    body = re.sub(r"^\s*-{3,}\s*$", "", body, flags=re.M)    # 水平線を削除
    body = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", body)     # リンクはテキストだけ残す
    body = re.sub(r"[*_`>]", "", body)                       # 装飾記号を削除

    sections = [s.strip() for s in re.split(r"^\s*―――\s*$", body, flags=re.M)]
    return [s for s in sections if s]


def chunk(text: str, limit: int = MAX_CHARS) -> list[str]:
    """段落単位で、上限文字数に収まるように束ねる。"""
    out, buf = [], ""
    for para in [p.strip() for p in text.split("\n\n") if p.strip()]:
        if len(buf) + len(para) + 2 > limit and buf:
            out.append(buf)
            buf = para
        else:
            buf = f"{buf}\n\n{para}" if buf else para
    if buf:
        out.append(buf)
    return out


async def synth_one(text: str, path: str) -> None:
    import edge_tts
    for attempt in range(1, 4):
        try:
            await edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH).save(path)
            if os.path.getsize(path) > 1024:
                return
            raise RuntimeError("出力が小さすぎます")
        except Exception as exc:                      # noqa: BLE001
            if attempt == 3:
                raise
            print(f"  再試行 {attempt}/3: {exc}", file=sys.stderr)
            await asyncio.sleep(3 * attempt)


async def main() -> None:
    src, dst = sys.argv[1], sys.argv[2]
    sections = extract_speech(open(src, encoding="utf-8").read())
    total = sum(len(s) for s in sections)
    print(f"セクション数: {len(sections)} / 読み上げ文字数: {total:,}")
    if total < 500:
        sys.exit("読み上げるテキストが見つかりません。台本の形式を確認してください。")

    with tempfile.TemporaryDirectory() as tmp:
        silence = os.path.join(tmp, "pause.mp3")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i",
             f"anullsrc=r=24000:cl=mono:d={PAUSE_SEC}", "-q:a", "9", silence],
            check=True, capture_output=True,
        )

        parts: list[str] = []
        for si, section in enumerate(sections):
            for ci, piece in enumerate(chunk(section)):
                out = os.path.join(tmp, f"{si:03d}_{ci:03d}.mp3")
                print(f"  合成中 {si + 1}/{len(sections)}-{ci + 1} ({len(piece)}字)")
                await synth_one(piece, out)
                parts.append(out)
            if si < len(sections) - 1:
                parts.append(silence)

        listing = os.path.join(tmp, "list.txt")
        with open(listing, "w", encoding="utf-8") as fh:
            for p in parts:
                fh.write(f"file '{p}'\n")

        os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listing,
             "-c:a", "libmp3lame", "-b:a", "64k", "-ar", "24000", "-ac", "1", dst],
            check=True, capture_output=True,
        )

    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", dst],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    print(f"完成: {dst} / {os.path.getsize(dst) / 1e6:.1f} MB / {float(dur) / 60:.1f} 分")


if __name__ == "__main__":
    asyncio.run(main())
