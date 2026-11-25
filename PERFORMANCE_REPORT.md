# PERFORMANCE_REPORT.md — P033 TextProof, T011 性能报告

- 任务：T011 验收 4（PROJECT_BOOK.md §8.3 运行时门槛）
- 基线：master `b0885dd`，分支 `t011-full-regression`
- 测量时间：2026-11-25 约 10:00–10:03 GMT
- 脚本：`scripts/benchmark_perf.py`（新增，T011 所有）
- 结论：**P95 3.817s ≤ 5s，PASS**

> **FIX-R1 重新测量（2026-11-25 19:59–20:01 GMT，终审 R1 P1-03）：
> 在最终冻结代码（commit `93d1b7c`，当前 HEAD `16a3ef5`，`src/` /
> `scripts/` / `tests/fixtures` 与冻结版零差异）上重测 30 次，
> P95 4.458s ≤ 5s，PASS。详见文末新增的“FIX-R1 重新测量”一节。
> 下面的 T011 一节是 T013 核心修改之前的历史测量，数字原样保留，
> 不得与新一轮混为一谈。**

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

---

# FIX-R1 重新测量（终审 R1 P1-03，2026-11-25）

- 任务：FIX-R1-03——终审 R1 指出 T011 的 3.817s 报告来自 T013 核心
  算法修改之前，须在最终冻结代码上重新测量 §8.3 门槛
  （1920×1080、30 次运行、P95 ≤ 5s）
- 测量时间：2026-11-25 19:59:39–20:01:23 GMT（UTC）
- 分支：`fix-r1`，HEAD `16a3ef5`；冻结 commit `93d1b7c`
- 测试前验证：`git diff 93d1b7c HEAD -- src/ scripts/ tests/fixtures`
  输出为空——冻结版与当前 HEAD 在 `src/`、`scripts/`、
  `tests/fixtures` 上零差异（其余差异仅 README / review /
  release 文件）。未提交任何东西，未切换分支。
- 结论：**P95 4.458s ≤ 5s，PASS（余量 0.542s）**

## FIX-R1-1. 结果

| 指标 | 秒 |
|---|---:|
| P50 | 2.812 |
| **P95** | **4.458** |
| 均值 | 2.934 |
| 最小 | 1.804 |
| 最大 | 4.585 |
| 门槛（§8.3） | ≤ 5.0（P95） |
| 余量 | 0.542 |

- 测量次数：30 次（另有 3 次预热，不计入统计；默认参数，
  未改 `--runs` / `--warmup`，未调阈值）
- 单次测量内容：与 T011 相同——完整产品检查路径（T002 图片加载 +
  T003 RapidOCR CPU-only + T004 比较 + §5 报告生成），经
  `textproof.api.routes.run_check`（与 API、CLI 同一入口）
- 百分位方法：numpy `percentile(..., method="linear")`（线性插值）
- 原始测量数据：`task_handoffs/FIX-R1/perf/perf_measurements.jsonl`
  （30 行，每行含 run 序号、秒数、verdict、图片 SHA-256）；
  摘要 JSON：`task_handoffs/FIX-R1/perf/perf_summary.json`；
  完整 stdout：`task_handoffs/FIX-R1/perf/perf_stdout.log`；
  退出码：0（见 `task_handoffs/FIX-R1/perf/perf_exit_code.txt`）
- 逐次秒数（run:秒）：1:2.712、2:2.673、3:2.837、4:2.394、5:1.804、
  6:2.282、7:2.203、8:2.782、9:1.922、10:2.082、11:2.419、12:2.879、
  13:2.498、14:2.934、15:2.765、16:2.233、17:3.182、18:4.585、
  19:4.420、20:4.488、21:4.202、22:3.001、23:2.711、24:3.407、
  25:3.575、26:2.998、27:2.896、28:3.505、29:2.815、30:2.809

预热 3 次耗时：4.114s、2.388s、2.698s（第 1 次含模型加载；
不计入统计，见 `task_handoffs/FIX-R1/perf/perf_stdout.log`）。

## FIX-R1-2. 判读 verdict：30 次均为 MISMATCH（与 T011 相同，如实记录）

本次 30 次测量的 verdict 全部为 MISMATCH，**不是** MATCH。
脚本 docstring 称“期望文本即所绘文本，故 verdict 为 MATCH”，
这一说法与两轮实测均不符（T011 30 次亦全为 MISMATCH，
见上文 §4）。单独一次独立 `run_check` 核实，原因与 T011 完全相同：

- OCR 把两处中文词间空格漏读（“限时优惠 全场5折”→“限时优惠全场5折”、
  “新品上市 会员专享”→“新品上市会员专享”，2 条 `MISSING_CHARACTER`，
  E001 / E002）；
- OCR 把第 3 行的“减”读成“減”（1 条 `SUBSTITUTION`，E003）。

共 3 条 error，`error_count: 3`，verdict MISMATCH。它不影响计时有效性：
每次测量都完整跑了 OCR + 比较 + 报告生成全路径；§8.3 门槛只约束
运行时间，不约束该图的判读结果。本任务未因此改图、未挑数据、
未改阈值——数字与 verdict 均如实记录。是否修脚本 docstring /
基准图期望文本，留给 FIX-R1 协调员决定，本任务不擅自改动。

## FIX-R1-3. 基准图片与 S0 manifest

- 文件：`tests/fixtures/performance/perf_1920x1080.png`（新路径，
  与 T011 的 `task_handoffs/T011/` 旧文件分开存放，旧文件未覆盖）
- 尺寸：1920×1080，PNG，58,171 字节
- SHA-256：`2bd4573f286c4d3c14a0f93351264511fff7f85919f4e9fbc858a3693c5f8f03`
  ——与 T011 的图片 SHA **完全相同**（同一固定种子、同一文字、
  同一字体生成，确定性复现）
- S0 manifest：`tests/fixtures/s0/manifest.json` 跑前跑后 SHA 均为
  `cc9a0ea9ed75fda800882c226665fa61cfc8d7213682655d52358cf5c128f959`，
  未改动

## FIX-R1-4. 环境（与 T011 相同）

| 项目 | 值 |
|---|---|
| CPU | AMD EPYC 9D25 126-Core Processor（本 VM 可见 4 个逻辑核） |
| OS | Linux 7.0.0-44-generic（#1 SMP PREEMPT_DYNAMIC Fri Nov 6 01:23:31 UTC 2026），x86_64 |
| Python | 3.12.3 |
| RapidOCR | 3.10.0 |
| onnxruntime | 1.32.0（CPU-only；可用 providers 含 Azure 与 CPU，实际使用仅 `CPUExecutionProvider`） |
| Pillow | 11.3.0 |
| FastAPI | 0.165.0 |
| uvicorn | 0.54.0 |
| pydantic | 2.14.4 |
| numpy | 2.5.5 |

模型文件 SHA-256 与 T011 / S0 完全一致（见
`task_handoffs/FIX-R1/perf/perf_summary.json` 的 environment 一节）：
`PP-OCRv6_det_small.onnx` `090f04ab…f1ef44e1ff94f`、
`PP-OCRv6_rec_small.onnx` `6f327246…c14884`、
`ch_ppocr_mobile_v2.0_cls_mobile.onnx` `e47acedf…6215c`。

字典：测量前 `scripts/setup_dictionary.py --check` 报缺失
（`dictionaries/ppocrv6_dict.txt` 不存在），按 T014 的做法本地重建；
重建后 SHA-256
`b5f2bfe2bdd9448429e3e82b51c789775d9b42f2403d082b00662eb77e401c5d`，
18,708 行，与 T014 记录一致。

## FIX-R1-5. 新旧测量对照

| 轮次 | 代码基线 | 测量时间（GMT） | P50 | **P95** | 均值 | 最小 | 最大 | verdict | 门槛 |
|---|---|---|---|---:|---:|---:|---:|---:|---|---|---|
| T011（历史） | T013 核心修改**之前** | 2026-11-25 ~10:00 | 2.906 | **3.817** | 2.926 | 2.085 | 3.825 | 30× MISMATCH | PASS |
| **FIX-R1（本次）** | **最终冻结 `93d1b7c` / HEAD `16a3ef5`** | **2026-11-25 19:59** | **2.812** | **4.458** | **2.934** | **1.804** | **4.585** | **30× MISMATCH** | **PASS** |

本次 P95 比 T011 高 0.641s（4.458 vs 3.817），余量从 1.183s 收窄到
0.542s。单次方差大（1.804–4.585s），后半段（run 18–21）连续 4 次
> 4.2s，主因应为共享 CPU 争用（同 T011 §5 的 caveat）；未做“空闲
推断”，报告数字以实测为准。门槛仍通过，但余量收窄值得注意——
若后续核心代码再变重或机器更忙，P95 有逼近 5s 的风险。

## FIX-R1-6. 复现

```bash
export TMPDIR=$PWD/tmp   # /tmp 是 512M tmpfs，须指到持久磁盘
.venv/bin/python scripts/benchmark_perf.py \
  --out task_handoffs/FIX-R1/perf/perf_measurements.jsonl \
  --summary task_handoffs/FIX-R1/perf/perf_summary.json \
  --image-out tests/fixtures/performance/perf_1920x1080.png
```

默认 `--runs 30 --warmup 3`，退出码 0 当且仅当 P95 ≤ 5s。
字典缺失时先跑 `.venv/bin/python scripts/setup_dictionary.py` 重建
（SHA 应为 `b5f2bfe2…401c5d`，18,708 行）。
