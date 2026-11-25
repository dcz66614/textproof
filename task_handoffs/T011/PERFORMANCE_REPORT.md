# PERFORMANCE_REPORT.md — P033 TextProof, T011 性能报告

- 任务：T011 验收 4（PROJECT_BOOK.md §8.3 运行时门槛）
- 基线：master `b0885dd`，分支 `t011-full-regression`
- 测量时间：2026-11-25 约 10:00–10:03 GMT
- 脚本：`scripts/benchmark_perf.py`（新增，T011 所有）
- 结论：**P95 3.817s ≤ 5s，PASS**

## 1. 结果

| 指标 | 秒 |
|---|---:|
| P50 | 2.906 |
| **P95** | **3.817** |
| 均值 | 2.926 |
| 最小 | 2.085 |
| 最大 | 3.825 |
| 门槛（§8.3） | ≤ 5.0（P95） |
| 余量 | 1.183 |

- 测量次数：30 次（另有 3 次预热，不计入统计）
- 单次测量内容：完整产品检查路径——T002 图片加载 + T003 RapidOCR
  （CPU-only）+ T004 比较 + §5 报告生成，经 `textproof.api.routes.run_check`
  （与 API、CLI 同一入口）
- 百分位方法：numpy `percentile(..., method="linear")`（线性插值），
  见脚本 `percentile_sorted`
- 原始测量数据：`task_handoffs/T011/perf_measurements.jsonl`（30 行，
  每行含 run 序号、秒数、verdict、图片 SHA-256）；摘要：
  `task_handoffs/T011/perf_summary.json`
- 退出码：0（P95 ≤ 5s；脚本在 P95 超标时返回 1，本次未触发）

预热 3 次耗时：5.496s、3.178s、4.308s（第 1 次含模型加载；
不计入统计，见 `task_handoffs/T011/perf_stdout.log`）。

## 2. 基准图片（非 S0 fixture）

S0 冻结 fixture 为 1200×480，§8.3 运行时门槛要求 1920×1080 合成图，
故本任务新生成一张基准图；**S0 manifest 未改动**。

- 文件：`task_handoffs/T011/perf_image_1920x1080.png`
- 尺寸：1920×1080，PNG，58,171 字节
- SHA-256：`2bd4573f286c4d3c14a0f93351264511fff7f85919f4e9fbc858a3693c5f8f03`
- 生成：`scripts/benchmark_perf.py`（`render_perf_image`），种子 20261125
- 字体：与 S0 fixture 相同的捆绑 Noto Sans SC（Regular / wght 400，
  64 px，SHA-256 已校验，见 `scripts/generate_fixtures.py::load_font`）
- 内容：4 行混合海报文案，白底黑字，居中排布：
  `限时优惠 全场5折` / `新品上市 会员专享` / `新客立减20元` /
  `SALE 50% OFF ￥28.80`
- 期望文本：上述 4 行以 `\n` 连接

## 3. 环境

| 项目 | 值 |
|---|---|
| CPU | AMD EPYC 9D25 126-Core Processor（本 VM 可见 4 个逻辑核） |
| OS | Ubuntu 24.04.5 LTS，内核 Linux 7.0.0-44-generic |
| Python | 3.12.3 |
| RapidOCR | 3.10.0 |
| onnxruntime | 1.32.0（CPU-only 包；可用 providers 含 Azure 与 CPU，实际使用仅 `CPUExecutionProvider`） |
| Pillow | 11.3.0 |
| FastAPI | 0.165.0 |
| uvicorn | 0.54.0 |
| pydantic | 2.14.4 |
| numpy | 2.5.5 |

模型文件（SHA-256 与 T006 / S0 运行的 model route 完全一致）：

| 文件 | 字节 | SHA-256 |
|---|---:|---|
| `PP-OCRv6_det_small.onnx` | 9,929,594 | `090f04abcd9d9a7498bc4ebf677e4cb9bdce1fe4197ddb7e529f1ef44e1ff94f` |
| `PP-OCRv6_rec_small.onnx` | 21,234,383 | `6f327246b50388f3c176ae304bd95767ea6dc0c9ae92153ef8cbe210b3c14884` |
| `ch_ppocr_mobile_v2.0_cls_mobile.onnx` | 585,532 | `e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c` |
| 字典 `ppocrv6_dict.txt`（18,708 行） | — | `b5f2bfe2bdd9448429e3e82b51c789775d9b42f2403d082b00662eb77e401c5d` |

（字典 SHA 引自 S0 运行的 model route 输出；三个 ONNX 文件的 SHA
由本脚本实测文件哈希得到，与 S0 输出一致。）

## 4. 性能图判读为 MISMATCH 的说明（诚实记录）

30 次测量的 verdict 均为 MISMATCH，不是 MATCH。原因（已单独核实，
一次独立 `run_check`）：

- OCR 把两处中文词间空格漏读（“限时优惠 全场5折”→“限时优惠全场5折”
  等，2 条 `MISSING_CHARACTER`）；
- OCR 把第 3 行的“减”读成“減”（1 条 `SUBSTITUTION`）。

这是该合成图上的 OCR 读法差异（多行 1920×1080 排版与单行 S0
fixture 不同；S0 300 样本的 CER 仍为 0.0008）。它不影响计时有效性：
每次测量都完整跑了 OCR + 比较 + 报告生成全路径；门槛只约束运行时间，
不约束该图的判读结果。本任务未因此改图、未挑数据、未改阈值——
数字与 verdict 均如实记录。

## 5. 测量条件与 caveat

- 测量期间 VM 上另有进程并行占用 CPU：`formal-exp-v7/pool/verify_pool_v7.py`
  （8 workers，约 09:35 起）与 SpiderQuant P5R 的 paper/serve 进程
  （约 09:54 起）。本测量值含该争用；P95 3.817s 仍低于门槛 1.183s。
  在空闲机器上复测预计只会更快，不会更慢——但本次报告的数字以实测
  为准，不做“空闲推断”。
- 单次测量方差较大（2.085–3.825s），主因是共享 CPU 的争用；P95
  仍在门槛内。
- S0 300 张 1200×480 fixture 的 live 计时（同一天同台机器，
  `s0_metrics.json`）：P50 2.232s、P95 2.978s、max 3.523s，
  与 1920×1080 的测量量级一致。

## 6. 复现

```bash
python scripts/benchmark_perf.py \
  --out task_handoffs/T011/perf_measurements.jsonl \
  --summary task_handoffs/T011/perf_summary.json \
  --image-out task_handoffs/T011/perf_image_1920x1080.png
```

退出码 0 当且仅当 P95 ≤ 5s。图片由固定种子与固定文字生成，
SHA-256 应与 §2 一致。
