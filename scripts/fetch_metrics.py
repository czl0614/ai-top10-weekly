# -*- coding: utf-8 -*-
"""抓取候选池的公开下载量（无 key）

数据源：
  npm  -> https://api.npmjs.org/downloads/point/last-week/<pkg>   周下载量
  PyPI -> https://pypistats.org/api/packages/<pkg>/recent         月下载量

统一换算成「周安装量」：PyPI 月下载 / 4.345。
输出 data/metrics.json，失败项会带 error 字段，不影响其他条目。
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
WEEKS_PER_MONTH = 4.345


def fetch(url, timeout=25, retries=3):
    last = ""
    for attempt in range(retries):
        req = urllib.request.Request(
            url, headers={"User-Agent": UA, "Accept": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8", "ignore")), None
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")[:160]
            last = f"HTTP {e.code}: {body}"
            if e.code in (400, 401, 403, 404):
                return None, last          # 不重试，这类错误重试也没用
        except Exception as e:
            last = f"{type(e).__name__}: {str(e)[:120]}"
        if attempt < retries - 1:
            time.sleep(1.5 * (attempt + 1))
    return None, last


def npm_weekly(pkg):
    d, err = fetch(f"https://api.npmjs.org/downloads/point/last-week/{pkg}")
    if not d:
        return None, None, err
    n = d.get("downloads")
    if not isinstance(n, int):
        return None, None, f"unexpected payload: {str(d)[:120]}"
    return n, float(n), None


def pypi_weekly(pkg):
    d, err = fetch(f"https://pypistats.org/api/packages/{pkg}/recent")
    if not d:
        return None, None, err
    n = (d.get("data") or {}).get("last_month")
    if not isinstance(n, int):
        return None, None, f"unexpected payload: {str(d)[:120]}"
    return n, n / WEEKS_PER_MONTH, None


def main():
    with open(os.path.join(ROOT, "data", "candidates.json"), "r", encoding="utf-8") as f:
        pool = json.load(f)["candidates"]

    out = []
    for c in pool:
        row = {
            "id": c["id"],
            "name": c["name"],
            "cn": c["cn"],
            "tag": c.get("tag", ""),
            "source": None,
            "raw": None,
            "raw_period": None,
            "weekly": None,
            "error": None,
        }
        if c.get("npm"):
            raw, weekly, err = npm_weekly(c["npm"])
            row.update(source=f"npm:{c['npm']}", raw=raw,
                       raw_period="last-week", weekly=weekly, error=err)
        elif c.get("pypi"):
            raw, weekly, err = pypi_weekly(c["pypi"])
            row.update(source=f"pypi:{c['pypi']}", raw=raw,
                       raw_period="last-month", weekly=weekly, error=err)
        else:
            row["error"] = "candidates.json 里既没有 npm 也没有 pypi"

        ok = row["weekly"] is not None
        print(f"  {'OK ' if ok else 'ERR'} {row['id']:16s} "
              f"{(str(row['raw']) if ok else row['error'])[:70]}")
        out.append(row)

    payload = {
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "weeks_per_month": WEEKS_PER_MONTH,
        "metrics": out,
    }
    dst = os.path.join(ROOT, "data", "metrics.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    ok_n = sum(1 for r in out if r["weekly"] is not None)
    print(f"\n抓取完成：{ok_n}/{len(out)} 成功 -> {dst}")
    # 部分失败不阻断流程，由 rank.py 按下限判断是否还能出榜
    return 0


if __name__ == "__main__":
    sys.exit(main())
