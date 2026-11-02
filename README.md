# Sandbox Arena

面向 Agent Sandbox 的真实 workload benchmark。

Sandbox Arena 不把“API 返回速度”当成最终答案，而是记录一个任务从创建环境到完成有用工作的完整过程：执行时间、成功率、尾延迟、重试和成本。

当前仓库是第一版框架，目标是：

- 用统一的 workload 描述不同测试任务；
- 用 provider adapter 接入不同 Sandbox；
- 输出可审查、可复现的 JSON 结果；
- 允许用户通过 GitHub PR 提交结果；
- 为后续网页展示保留稳定的数据 schema。

## 快速开始

需要 Python 3.10+，不需要额外依赖。

```bash
cd SandboxArena
python -m arena list-workloads
python -m arena run --provider mock --workload python-smoke --repetitions 3 --output /tmp/arena-result.json
python -m arena validate /tmp/arena-result.json
```

`mock` provider 只在本机执行，用来验证 workload、计时、结果格式和 PR 流程。它不是 Sandbox 性能数据，结果中的 provenance 会标记为 `self-run`，provider 标记为 `mock-local`。

## 目录结构

```text
arena/                         CLI、schema 校验和 provider 接口
  providers/                   各 Sandbox 的 adapter
workloads/                     版本化 workload 定义
schemas/                       网页和校验器共用的 JSON Schema
data/results/                  已审核的 benchmark 结果
tests/                         无网络、无账号的本地测试
.github/                       PR 模板和结果校验 workflow
```

## 提交测试结果

结果文件是一条完整的 benchmark observation，建议命名为：

```text
data/results/<provider>-<workload>-<date>-<short-id>.json
```

提交前运行：

```bash
python -m arena run \
  --provider mock \
  --workload python-smoke \
  --repetitions 10 \
  --region local \
  --output data/results/mock-local-python-smoke-20261102-example.json

python -m arena validate data/results/mock-local-python-smoke-20261102-example.json
```

真实 provider 的 adapter 还没有在这个初始版本中实现。接入时请参考 `arena/providers/base.py`，不要在结果文件中提交 API key、token、完整环境变量或私有仓库内容。

## 数据可信度

结果中的 `provenance.source` 用来区分证据来源：

- `self-run`：使用本仓库脚本运行并上传原始结果；
- `community-run`：社区运行，待审核；
- `vendor-reported`：厂商提交或确认；
- `official-claim`：来自官方宣传，不是独立实测。

网页应始终展示这个字段，不要把不同来源混成一个排行榜。

## 设计原则

1. workload、provider、结果 schema 分离，避免把某一家 SDK 的概念写死。
2. 所有结果保留测试条件和时间，避免脱离上下文比较。
3. 先公开原始 observation，再计算 p50、p95、成功率和成本等聚合指标。
4. 不能复现的结果可以展示，但必须明确标注证据等级。

## Deploy to GitHub Pages

网页是纯静态 HTML/CSS/JS，发布目录是 `web/`。每次 push 到 `main` 或 `master` 时，`.github/workflows/deploy-pages.yml` 会先把 `data/results/*.json` 汇总成 `web/data/results.json`，再部署到 GitHub Pages。

首次启用时，在 GitHub 仓库中打开：

```text
Settings → Pages → Build and deployment → Source → GitHub Actions
```

如果仓库叫 `SandboxArena`，默认地址会是：

```text
https://<username>.github.io/SandboxArena/
```

本地预览网页：

```bash
python scripts/build_site_data.py
python -m http.server 4173 --directory web
```

然后打开 `http://localhost:4173/`。网页不会执行 benchmark，也不会读取 API key；它只展示已经提交并审核的结果文件。

