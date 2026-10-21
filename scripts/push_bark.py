# -*- coding: utf-8 -*-
"""Bark 推送（CI 版）：从 data/ai_top10.json 生成十行榜单并推送"""
import os
import sys
import json
import urllib.request
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    key = os.environ.get("BARK_KEY", "").strip()
    if not key:
        print("ERROR: 缺少 BARK_KEY 环境变量 / Secret")
        return 2

    with open(os.path.join(ROOT, "data", "ai_top10.json"), "r", encoding="utf-8") as f:
        data = json.load(f)

    lines = []
    for i, it in enumerate(data["items"][:10], 1):
        lines.append(f"{i:02d} {it['name']} · {it['metric']}")
    body = "\n".join(lines) + "\n\n展开通知看海报 · 点击查看完整榜单"

    payload = {
        "device_key": key,
        "title": "AI 应用周榜 TOP10",
        "body": body,
        "group": os.environ.get("BARK_GROUP", "AI周报"),
    }

    image_url = os.environ.get("POSTER_URL", "").strip()
    if image_url:
        payload["image"] = image_url
        payload["url"] = os.environ.get("SITE_URL", "").strip() or image_url

    req = urllib.request.Request(
        "https://api.day.app/push",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            txt = r.read().decode("utf-8", "ignore")
            print("Bark:", r.status, txt[:300])
            return 0 if r.status == 200 else 1
    except urllib.error.HTTPError as e:
        print("HTTP_ERROR", e.code, e.read().decode("utf-8", "ignore")[:300])
    except Exception as e:
        print("ERROR", type(e).__name__, str(e)[:300])
    return 1


if __name__ == "__main__":
    sys.exit(main())
