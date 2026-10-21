# AI 应用周榜 TOP10

每周一自动生成「AI 编程工具 · 周安装量 TOP 10」海报，通过 Bark 推送到手机。
跑在 GitHub Actions 上，**不需要本地电脑开机，也不需要任何 API key**。

## 它是怎么跑的

```
每周一 09:00（北京时间）
        ↓
抓 npm registry 的周下载量 + PyPI stats 的月下载量（公开接口，无鉴权）
        ↓
统一换算成「周安装量」，降序取前 10
        ↓
Pillow 合成海报（底图 assets/bg.jpg）
        ↓
提交 poster_latest.png + 数据快照回仓库
        ↓
通过 jsdelivr 取图，Bark 推送带图通知
```

全链路只用 `urllib` 和 `pillow`，没有任何密钥。

> **图床为什么不用 `raw.githubusercontent.com`**：这个域名在国内网络下经常连不通，
> Bark 服务端拉不到图，通知就只剩文字。改用 jsdelivr，并按 commit SHA 取图
> （SHA 不可变，不会命中旧缓存）；jsdelivr 自检失败时自动回退到 ghfast 镜像。

## 榜单口径

排名**只看一个指标**：周安装量。

| 来源 | 原始口径 | 换算 |
|---|---|---|
| npm | `last-week` 下载量 | 直接使用 |
| PyPI | `last_month` 下载量 | ÷ 4.345 |

**为什么口径要收窄到「周安装量」**：付费用户数、月访问量、ARR 这些来自分析机构报告，
没有可自动抓取的公开接口。要让榜单每周自动变化且可验证，只能用它。
代价是闭源 IDE（Cursor、Windsurf）没有公开下载数据，进不了榜。

## 部署步骤

### 1. 建仓库

新建仓库推上去，默认分支必须是 `main`。

### 2. 配置 Secret

Settings → Secrets and variables → Actions → New repository secret

| 名称 | 值 | 必填 |
|---|---|---|
| `BARK_KEY` | Bark App 里的推送 key | ✅ |

可选：Settings → Variables 里加 `BARK_GROUP`，默认分组「AI周报」。

### 3. 启用 Actions

Actions 标签页 → 如提示需要启用，点「I understand my workflows, go ahead and enable them」。

### 4. 手动跑一次验证

Actions → 「AI 应用周榜 TOP10」→ Run workflow。
检查三件事：手机收到带图推送、仓库出现 `poster_latest.png`、`data/ai_top10.json` 已更新。

之后每周一自动运行，无需干预。

## 怎么改候选池

编辑 `data/candidates.json`，加一行即可：

```json
{
  "id": "my-tool",
  "name": "My Tool",
  "cn": "一句话中文说明",
  "tag": "开源",
  "npm": "my-tool-cli"
}
```

- `npm` 和 `pypi` 二选一，至少有一个，否则拿不到下载量
- `tag` 只放 2 个字（「开源 / 商业」），太长会挤到数字列
- `cn` 建议 8-14 个字，超过会换行撞到下一行

候选池目前 15 个，前 10 入榜。池子越大榜单越稳——某个包抓取失败时还有余量。

## 关于安全

**这个项目没有任何模型 API key，所以不存在 key 泄露问题。**

仓库里唯一的 Secret 是 `BARK_KEY`，它只能往你手机推通知，泄露了最多被推垃圾消息，烧不到钱。

仍需要注意：

1. **不要用 `pull_request_target` 触发**，那个触发器会让外部 PR 读到 Secrets。本项目只用 `schedule` 和 `workflow_dispatch`。
2. **公开仓库的 Actions 日志是公开的**。本项目日志里只有下载量数字，没有敏感信息。
3. **海报底图** `assets/bg.jpg` 会随仓库公开，确认你有使用权。

## 已知限制

- **GitHub 定时任务会延迟**：高峰期可能晚 5-30 分钟，这是平台调度策略，不是配置问题。
- **60 天无活动会禁用定时任务**：本项目每周提交，仓库持续活跃，不会触发。
- **npm 下载量含 CI 流量**：自动化流水线也会 `npm install`，所以数字高于真实人数。这是 npm 生态的通病，用同一口径横向比较仍然有效。
- **VS Code Marketplace 未接入**：Cline、Roo Code 这类 IDE 插件的真实装机量在那里，但该接口 TLS 握手在本机网络下不稳定，暂未纳入。
- **单源失败不影响整体**：`fetch_metrics.py` 每个包重试 3 次，仍失败则排除该项；拿到数据的少于 5 项时整个任务失败，不会推一张残缺海报。

## 文件说明

```
.github/workflows/weekly.yml   定时任务定义
scripts/fetch_metrics.py       抓 npm / PyPI 下载量 -> data/metrics.json
scripts/rank.py                排序取前 10 -> data/ai_top10.json
scripts/generate.py            海报生成（Pillow）
scripts/push_bark.py           Bark 推送
data/candidates.json           候选池（要加应用改这里）
data/metrics.json              每周抓取的原始数据快照
data/ai_top10.json             本周榜单（自动生成）
assets/bg.jpg                  海报底图
poster_latest.png              自动生成，每周覆盖
```
