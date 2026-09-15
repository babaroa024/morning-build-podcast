#!/usr/bin/env python3
"""episodes/*.json から Spotify 取り込み用のポッドキャスト RSS を生成する。

各エピソードの音声は GitHub Releases に置き、その公開URLを enclosure に入れる。
出力: feed/index.xml（GitHub Pages で公開される）
"""
import glob
import html
import json
import os
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))
CFG = json.load(open("show.json", encoding="utf-8"))
BASE = f"https://github.com/{CFG['repo']}/releases/download"
PAGES = CFG["pages_url"].rstrip("/")
MAX_ITEMS = int(CFG.get("max_items", 60))


def esc(text: str) -> str:
    return html.escape(text or "", quote=False)


def rfc2822(dt: datetime) -> str:
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return (f"{days[dt.weekday()]}, {dt.day:02d} {months[dt.month - 1]} {dt.year} "
            f"{dt:%H:%M:%S} +0900")


def load_episodes() -> list[dict]:
    eps = []
    for path in glob.glob("episodes/*.json"):
        with open(path, encoding="utf-8") as fh:
            ep = json.load(fh)
        if ep.get("audio_bytes"):          # 音声が出来ているものだけ配信
            eps.append(ep)
    eps.sort(key=lambda e: e["date"], reverse=True)
    return eps[:MAX_ITEMS]


def item_xml(ep: dict) -> str:
    date = ep["date"]                                    # YYYY-MM-DD
    pub = datetime.strptime(date, "%Y-%m-%d").replace(hour=4, tzinfo=JST)
    url = f"{BASE}/ep-{date}/{date}.mp3"
    secs = int(ep.get("duration_sec", 0))
    return f"""    <item>
      <title>{esc(ep['title'])}</title>
      <description><![CDATA[{ep.get('description', '')}]]></description>
      <itunes:summary><![CDATA[{ep.get('description', '')}]]></itunes:summary>
      <pubDate>{rfc2822(pub)}</pubDate>
      <guid isPermaLink="false">morning-build-{date}</guid>
      <link>{PAGES}/</link>
      <enclosure url="{url}" length="{ep['audio_bytes']}" type="audio/mpeg"/>
      <itunes:duration>{secs // 3600:02d}:{secs % 3600 // 60:02d}:{secs % 60:02d}</itunes:duration>
      <itunes:episodeType>full</itunes:episodeType>
      <itunes:explicit>false</itunes:explicit>
    </item>"""


def main() -> None:
    eps = load_episodes()
    now = datetime.now(JST)
    items = "\n".join(item_xml(e) for e in eps)

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>{esc(CFG['title'])}</title>
    <link>{PAGES}/</link>
    <language>ja</language>
    <copyright>{esc(CFG['author'])}</copyright>
    <description><![CDATA[{CFG['description']}]]></description>
    <itunes:summary><![CDATA[{CFG['description']}]]></itunes:summary>
    <itunes:author>{esc(CFG['author'])}</itunes:author>
    <itunes:owner>
      <itunes:name>{esc(CFG['author'])}</itunes:name>
      <itunes:email>{esc(CFG['email'])}</itunes:email>
    </itunes:owner>
    <itunes:image href="{PAGES}/cover.png"/>
    <itunes:category text="{esc(CFG['category'])}">
      <itunes:category text="{esc(CFG['subcategory'])}"/>
    </itunes:category>
    <itunes:explicit>false</itunes:explicit>
    <itunes:type>episodic</itunes:type>
    <lastBuildDate>{rfc2822(now)}</lastBuildDate>
{items}
  </channel>
</rss>
"""
    os.makedirs("feed", exist_ok=True)
    with open("feed/index.xml", "w", encoding="utf-8") as fh:
        fh.write(feed)
    print(f"RSS生成完了: {len(eps)} エピソード -> feed/index.xml")


if __name__ == "__main__":
    main()
