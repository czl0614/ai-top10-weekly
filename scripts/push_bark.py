# -*- coding: utf-8 -*-
"""Bark 推送（CI 版）

两种模式：
  正常  从 data/ai_top10.json 生成十行榜单 + 海报图
  告警  设置 BARK_ALERT 环境变量时，只推一条纯文本失败通知
        （工作流里用 if: failure() 触发，避免某周静默失败）
"""
import os
import sys
import json
import urllib.request
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def send(payload):
    print("图片地址:", payload.get("image", "(无)"))
    print("跳转地址:", payload.get("url", "(无)"))
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


def main():
    key = os.environ.get("BARK_KEY", "").strip()
    if not key:
        print("ERROR: 缺少 BARK_KEY 环境变量 / Secret")
        return 2

    group = os.environ.get("BARK_GROUP", "AI周报")

    # --- 告警模式：不读榜单数据，只发一条失败提示 ---
    alert = os.environ.get("BARK_ALERT", "").strip()
    if alert:
        return send({
            "device_key": key,
            "title": alert,
            "body": "本周海报没有生成，去仓库 Actions 页面看日志。",
            "group": group,
            "level": "timeSensitive",
        })

    # --- 正常模式 ---
    with open(os.path.join(ROOT, "data", "ai_top10.json"), "r", encoding="utf-8") as f:
        data = json.load(f)

    lines = [f"{i:02d} {it['name']} · {it['metric']}"
             for i, it in enumerate(data["items"][:10], 1)]
    body = "\n".join(lines) + "\n\n展开通知看海报 · 点击看大图"

    payload = {
        "device_key": key,
        "title": "AI 应用周榜 TOP10",
        "body": body,
        "group": group,
    }

    image_url = os.environ.get("POSTER_URL", "").strip()
    if image_url:
        # Bark 里两个参数分工不同：
        #   image -> 通知卡片里显示哪张图
        #   url   -> 点这条通知后跳到哪个地址
        # 默认让 url 指向海报原图（点开就是大图），要跳别的页面用 SITE_URL 覆盖。
        payload["image"] = image_url
        payload["url"] = os.environ.get("SITE_URL", "").strip() or image_url

    return send(payload)


if __name__ == "__main__":
    sys.exit(main())
