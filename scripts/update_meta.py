#!/usr/bin/env python3
import json, os, re, sys
meta, date, byts, secs, script = sys.argv[1:6]
data = json.load(open(meta, encoding="utf-8")) if os.path.exists(meta) else {}
text = open(script, encoding="utf-8").read()
heads = [h.strip() for h in re.findall(r"^##\s*【\d+】(.+)$", text, re.M)]
data.setdefault("title", text.splitlines()[0].lstrip("# ").strip())
data.setdefault("description", "本日の内容：" + " ／ ".join(heads) if heads else data["title"])
data.update({"date": date, "audio_bytes": int(byts), "duration_sec": int(secs)})
json.dump(data, open(meta, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("メタ情報を更新しました:", meta)
