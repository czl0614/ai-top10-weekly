# -*- coding: utf-8 -*-
"""按周安装量排序，产出海报数据 data/ai_top10.json"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOP_N = 10
MIN_N = 5


def fmt(n):
    """13153561 -> 1315万；45040 -> 4.5万；3237 -> 3,237"""
    n = int(round(n))
    if n >= 1e8:
        return f"{n / 1e8:.1f}亿"
    if n >= 1e5:
        return f"{n / 1e4:.0f}万"
    if n >= 1e4:
        s = f"{n / 1e4:.1f}万"
        return s.replace(".0万", "万")
    return f"{n:,}"


def main():
    mp = os.path.join(ROOT, "data", "metrics.json")
    if not os.path.exists(mp):
        print("ERROR: 缺少 data/metrics.json，先跑 fetch_metrics.py")
        return 2

    with open(mp, "r", encoding="utf-8") as f:
        payload = json.load(f)

    rows = [r for r in payload["metrics"] if r.get("weekly") is not None]
    dropped = [r for r in payload["metrics"] if r.get("weekly") is None]
    if dropped:
        print("本周抓取失败（已排除）：")
        for r in dropped:
            print(f"  - {r['id']}: {r['error']}")

    if len(rows) < MIN_N:
        print(f"ERROR: 只有 {len(rows)} 项拿到数据，少于下限 {MIN_N}，不生成海报")
        return 1
    if len(rows) < TOP_N:
        print(f"WARN: 只有 {len(rows)} 项拿到数据，榜单将少于 {TOP_N} 行")

    rows.sort(key=lambda r: r["weekly"], reverse=True)
    top = rows[:TOP_N]

    bj = datetime.now(timezone.utc) + timedelta(hours=8)
    data = {
        "title_main": "AI 编程工具",
        "title_accent": "周安装量 TOP 10",
        "subtitle": f"按 npm / PyPI 公开周下载量排序 · 数据截至 {bj.strftime('%Y.%m.%d')}",
        "footer": "数据来源 npm registry · PyPI stats ｜ 每周一自动更新",
        "generated_at": payload["fetched_at"],
        "items": [
            {
                "name": r["name"],
                "cn": r["cn"],
                "metric": fmt(r["weekly"]),
                "tag": r["tag"],
                "raw_weekly": int(round(r["weekly"])),
                "source": r["source"],
            }
            for r in top
        ],
    }

    dst = os.path.join(ROOT, "data", "ai_top10.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n本周 TOP {len(top)}：")
    for i, it in enumerate(data["items"], 1):
        print(f"  {i:02d}  {it['name']:22s} {it['metric']:>8s}/周   "
              f"{it['raw_weekly']:>12,}  [{it['tag']}]")
    print(f"\n已写入 {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
