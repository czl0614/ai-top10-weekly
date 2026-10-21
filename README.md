# AI 应用周榜 TOP10

每周一自动生成「AI 生产力应用热度 TOP 10」海报，并通过 Bark 推送到手机。
跑在 GitHub Actions 上，**不需要本地电脑开机**。

## 它是怎么跑的

```
每周一 09:00（北京时间）
        ↓
读取 data/ai_top10.json 的榜单数据
        ↓
Pillow 合成海报（底图 assets/bg.jpg）
        ↓
提交 poster_latest.png 回仓库
        ↓
通过 jsdelivr 取图，Bark 推送带图通知
```

> 图床为什么不用 `raw.githubusercontent.com`：这个域名在国内网络下经常连不通，
> Bark 服务端拉不到图，通知就只剩文字。所以改用 jsdelivr，并按 commit SHA 取图
> （SHA 不可变，不会命中旧缓存）；jsdelivr 自检失败时自动回退到 ghfast 镜像。

## 部署步骤

### 1. 建仓库

新建一个仓库，把这个目录的内容推上去。默认分支必须是 `main`（工作流里的图片链接写死了 `main`）。

### 2. 配置 Secret

仓库 → Settings → Secrets and variables → Actions → New repository secret

| 名称 | 值 | 必填 |
|---|---|---|
| `BARK_KEY` | Bark App 里的推送 key | ✅ |

可选：Settings → Variables 里加 `BARK_GROUP`，默认分组「AI周报」。

### 3. 启用 Actions

仓库 → Actions 标签页 → 如果提示需要启用，点「I understand my workflows, go ahead and enable them」。

### 4. 手动跑一次验证

Actions → 「AI 应用周榜 TOP10」→ Run workflow。
跑完检查两件事：
- 手机收到推送
- 仓库里出现了 `poster_latest.png`

之后每周一自动运行，无需干预。

## 更新榜单数据

编辑 `data/ai_top10.json`：

```json
{
  "title_main": "AI 生产力应用",
  "title_accent": "热度 TOP 10",
  "subtitle": "按实际使用规模排序 · 数据截至 2026.10.22",
  "footer": "数据来源 易观分析 / JetBrains AI Pulse / 厂商披露",
  "items": [
    {
      "name": "GitHub Copilot",
      "cn": "装机量最大的编程助手",
      "metric": "470万付费",
      "tag": "编程"
    }
  ]
}
```

- `items` 必须正好 10 项，按热度降序
- `tag` 建议只用「编程 / 办公 / 创作」，太长会挤到数字
- `metric` 控制在 6 个字符以内，否则会盖住标签

改完提交，下周自动用新数据。

## 关于安全

**Secrets 不会泄露。** GitHub Actions 的 Secrets 加密存储，日志里自动打码成 `***`，写入后连你自己也读不回来。

需要注意的几点：

1. **不要把 key 写进任何文件**，包括临时调试。一旦提交进 Git 历史，删掉也还在。
2. **不要用 `pull_request_target` 触发**，那个触发器会让外部 PR 读到 Secrets。本项目只用 `schedule` 和 `workflow_dispatch`。
3. **仓库公开与否**：代码里没有敏感信息，但 `poster_latest.png` 需要被 Bark 以公开 URL 访问，所以仓库需要是公开的。如果你要私有仓库，得换成图床上传方案（改 `weekly.yml` 的最后一步）。

## 已知限制

- **GitHub 定时任务会延迟**：高峰期可能晚 5-30 分钟，这是平台的调度策略，不是配置问题。
- **jsdelivr 有速率限制**：单文件 20MB 以内、单 IP 高频访问会被限流。本项目一周一次，远低于阈值。
- **60 天无活动会禁用定时任务**：本项目每周提交海报，仓库持续活跃，不会触发这个限制。
- **海报底图**：`assets/bg.jpg` 请确认你有使用权。仓库公开意味着这张图也会被公开访问。
- **数据不会自动更新**：`data/ai_top10.json` 是静态的，每周推的是同一批数据（只有副标题日期自动刷新）。
  要换榜单就改这个文件，或者另写一个抓取脚本替换「生成海报」这一步。

## 文件说明

```
.github/workflows/weekly.yml   定时任务定义
scripts/generate.py            海报生成（Pillow）
scripts/push_bark.py           Bark 推送
data/ai_top10.json             榜单数据（每周改这里）
assets/bg.jpg                  海报底图
poster_latest.png              自动生成，每周覆盖
```
