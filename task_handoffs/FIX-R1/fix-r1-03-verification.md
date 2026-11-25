# FIX-R1-03 验证报告 — §8.3 性能门槛在最终冻结代码上重新测量

- 任务：FIX-R1-03（终审 R1 P1-03：T011 的 3.817s 报告来自 T013 核心算法修改之前，须在最终版本上重测）
- 执行时间：2026-11-25 19:59:39–20:01:23 GMT（UTC），测量本身约 104 秒
- 执行者：FIX-R1-03 子任务执行员
- 分支：`fix-r1`，HEAD `16a3ef5c1b5162f9dff6dfd63c85f10ae703ecbd`
- **结论：P95 4.458s ≤ 5s，门槛 PASS（余量 0.542s）；30 次 verdict 全部为 MISMATCH（见 §5，如实记录，与 T011 相同）**

## 1. 测试前状态

### 1.1 git diff（冻结版 vs 当前 HEAD）

命令：

```bash
git diff 93d1b7c HEAD -- src/ scripts/ tests/fixtures
```

**输出为空**——冻结 commit `93d1b7c` 与当前 HEAD `16a3ef5` 在 `src/`、`scripts/`、`tests/fixtures` 上零差异。`git diff --stat 93d1b7c HEAD` 的全部 22 个文件差异都在 README / review / release / task_handoffs 范围（`T014_MAINCHAT_VERDICT.md`、`release/RELEASE_MANIFEST.json`、`release/SHA256SUMS.txt`、`release/source.zip`、`review/REVIEW_INDEX.md`、`review/REVIEW_PACK_T014R3.md`、`task_handoffs/T014/...` 等），无一涉及产品代码、脚本或 fixture。测试期间未提交任何东西，未切换分支。

测试前 `git status --short` 仅有未追踪文件（`FINAL_REVIEW_R1_MESSAGE.md`、`P033_FINAL_REVIEW_R1.md`、`task_handoffs/T001/`、`tests/e2e/evidence/`、`tmp/`），无已修改的已追踪文件。

### 1.2 字典文件

测量前检查：

```bash
.venv/bin/python scripts/setup_dictionary.py --check
# 输出：missing: dictionaries/ppocrv6_dict.txt
#       Run without --check to rebuild it from the local model file.
```

字典缺失，按 T014 的做法本地重建：

```bash
.venv/bin/python scripts/setup_dictionary.py
# rebuilt dictionary: dictionaries/ppocrv6_dict.txt
#   source: models/PP-OCRv6_rec_small.onnx (embedded character metadata)
#   sha256: b5f2bfe2bdd9448429e3e82b51c789775d9b42f2403d082b00662eb77e401c5d
#   lines:  18708
```

重建后 SHA-256 `b5f2bfe2bdd9448429e3e82b51c789775d9b42f2403d082b00662eb77e401c5d`、18,708 行，与 T014 记录完全一致。重建位置：`assets/ocr/dictionaries/ppocrv6_dict.txt`。

### 1.3 环境

| 项目 | 值 |
|---|---|
| CPU | AMD EPYC 9D25 126-Core Processor（本 VM 可见 4 个逻辑核） |
| OS | Linux 7.0.0-44-generic（#1 SMP PREEMPT_DYNAMIC Fri Nov 6 01:23:31 UTC 2026），x86_64 |
| Python | 3.12.3（`~/workspace/p033-textproof/.venv/bin/python`） |
| RapidOCR | 3.10.0 |
| onnxruntime | 1.32.0（可用 providers：Azure、CPU；实际使用仅 `CPUExecutionProvider`） |
| Pillow | 11.3.0 |
| FastAPI | 0.165.0 |
| uvicorn | 0.54.0 |
| pydantic | 2.14.4 |
| numpy | 2.5.5 |

模型文件 SHA-256（脚本实测，与 T011 / S0 一致）：

| 文件 | 字节 | SHA-256 |
|---|---:|---|
| `PP-OCRv6_det_small.onnx` | 9,929,594 | `090f04abcd9d9a7498bc4ebf677e4cb9bdce1fe4197ddb7e529f1ef44e1ff94f` |
| `PP-OCRv6_rec_small.onnx` | 21,234,383 | `6f327246b50388f3c176ae304bd95767ea6dc0c9ae92153ef8cbe210b3c14884` |
| `ch_ppocr_mobile_v2.0_cls_mobile.onnx` | 585,532 | `e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c` |

环境与 T011 测量时完全相同（同一 VM、同一 CPU 型号与核数、同一 Python 与依赖版本）。

## 2. 测量命令（完整）

```bash
cd ~/workspace/p033-textproof
mkdir -p task_handoffs/FIX-R1/perf tests/fixtures/performance tmp
export TMPDIR=$PWD/tmp   # /tmp 是 512M tmpfs，须指到持久磁盘
.venv/bin/python scripts/benchmark_perf.py \
  --out task_handoffs/FIX-R1/perf/perf_measurements.jsonl \
  --summary task_handoffs/FIX-R1/perf/perf_summary.json \
  --image-out tests/fixtures/performance/perf_1920x1080.png
```

参数说明：未传 `--runs` / `--warmup`，即默认 `--runs 30 --warmup 3`；未改任何阈值。一次运行 = 生产全链路（图片加载 + RapidOCR CPU-only + 比较 + §5 报告），经 `textproof.api.routes.run_check`。stdout 同时 tee 到 `task_handoffs/FIX-R1/perf/perf_stdout.log`。

**退出码：0**（记录于 `task_handoffs/FIX-R1/perf/perf_exit_code.txt`；脚本在 P95 ≤ 5.0s 时返回 0，超标返回 1）。

## 3. 测量结果

来自 `task_handoffs/FIX-R1/perf/perf_summary.json`（`seconds` 一节，numpy 线性插值百分位）：

| 指标 | 秒 |
|---|---:|
| P50 | 2.8115884950000236（报告取 2.812） |
| **P95** | **4.457670171749851（报告取 4.458）** |
| 均值 | 2.9338241943999797（报告取 2.934） |
| 最小 | 1.8038439540000581（报告取 1.804） |
| 最大 | 4.585492044000148（报告取 4.585） |
| 门槛（§8.3） | ≤ 5.0（P95） |
| 余量 | 0.542 |

**门槛判定：P95 4.458s ≤ 5s，PASS。**

逐次秒数（`task_handoffs/FIX-R1/perf/perf_measurements.jsonl`，30 行）：

| run | 秒 | run | 秒 | run | 秒 |
|---:|---:|---:|---:|---:|---:|
| 1 | 2.712 | 11 | 2.419 | 21 | 4.202 |
| 2 | 2.673 | 12 | 2.879 | 22 | 3.001 |
| 3 | 2.837 | 13 | 2.498 | 23 | 2.711 |
| 4 | 2.394 | 14 | 2.934 | 24 | 3.407 |
| 5 | 1.804 | 15 | 2.765 | 25 | 3.575 |
| 6 | 2.282 | 16 | 2.233 | 26 | 2.998 |
| 7 | 2.203 | 17 | 3.182 | 27 | 2.896 |
| 8 | 2.782 | 18 | 4.585 | 28 | 3.505 |
| 9 | 1.922 | 19 | 4.420 | 29 | 2.815 |
| 10 | 2.082 | 20 | 4.488 | 30 | 2.809 |

预热 3 次（不计入统计）：4.114s、2.388s、2.698s。

## 4. 基准图片与 S0 manifest

- 基准图：`tests/fixtures/performance/perf_1920x1080.png`（新路径；T011 的旧文件 `task_handoffs/T011/perf_image_1920x1080.png` 未覆盖）
- 尺寸 1920×1080，PNG，58,171 字节
- SHA-256：`2bd4573f286c4d3c14a0f93351264511fff7f85919f4e9fbc858a3693c5f8f03`——**与 T011 的图片 SHA 完全相同**（同一固定种子 20261125、同一文字、同一字体，确定性复现）；30 次测量的每行记录的 `image_sha256` 均为该值
- 内容：4 行混合海报文案——`限时优惠 全场5折` / `新品上市 会员专享` / `新客立减20元` / `SALE 50% OFF ￥28.80`，64 px Noto Sans SC，白底黑字
- S0 manifest：`tests/fixtures/s0/manifest.json` 跑前跑后 SHA 均为 `cc9a0ea9ed75fda800882c226665fa61cfc8d7213682655d52358cf5c128f959`，`diff` 为空，**未改动**

## 5. Verdict 统计——30 次全部为 MISMATCH（重要发现，如实记录）

| verdict | 次数 |
|---|---:|
| MISMATCH | 30 |
| MATCH | 0 |

**本次 30 次测量（含 3 次预热）的 verdict 全部为 MISMATCH，不是 MATCH。** 任务书中“30 次 verdict 全为 MATCH（脚本设计如此）”的预期与实测不符：脚本 docstring 称“期望文本即所绘文本，故 verdict 为 MATCH”，但两轮实测（T011 与本次）均为 30× MISMATCH。根目录 `PERFORMANCE_REPORT.md` §4 在 T011 时已诚实记录过同一现象，本次复现并再次核实。

单独一次独立 `run_check`（`PYTHONPATH=src`，同一图片与期望文本）确认原因，3 条 error：

- E001 `MISSING_CHARACTER`：期望 `限时优惠 全场5折`，识别为 `限时优惠全场5折`（漏读词间空格）
- E002 `MISSING_CHARACTER`：期望 `新品上市 会员专享`，识别为 `新品上市会员专享`（漏读词间空格）
- E003 `SUBSTITUTION`：期望 `新客立减20元`，识别为 `新客立減20元`（简体“减”读成繁体“減”）

`error_count: 3`，verdict MISMATCH。影响评估：

- **计时有效性不受影响**——每次测量都完整跑了 OCR + 比较 + §5 报告生成全路径；§8.3 门槛只约束运行时间，不约束该图的判读结果。
- **未采取任何凑数手段**——未改图、未挑数据、未改阈值、未改脚本；数字与 verdict 均如实记录。
- 遗留问题（本任务未擅自改动，留给 FIX-R1 协调员决定）：脚本 docstring 的“MATCH”说法与实测不符；是否修正 docstring 或基准图期望文本，需另行定夺。

## 6. 输出文件清单与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `task_handoffs/FIX-R1/perf/perf_measurements.jsonl`（30 行） | `18ccb2d406c02da400b8e637e29560cc76d74d3126e9883c363098ce42b4f235` |
| `task_handoffs/FIX-R1/perf/perf_summary.json` | `ca7bacbebf67fde3a590dd59494578ecb30afcf6597dce74dd4434ddb04ffc5d` |
| `task_handoffs/FIX-R1/perf/perf_stdout.log` | `3c630fb8a328194362588b9f48cd2cb48f83a15bfbaece7bda036da937e94bf1` |
| `task_handoffs/FIX-R1/perf/perf_exit_code.txt`（内容 `0`） | — |
| `tests/fixtures/performance/perf_1920x1080.png`（58,171 字节） | `2bd4573f286c4d3c14a0f93351264511fff7f85919f4e9fbc858a3693c5f8f03` |
| `PERFORMANCE_REPORT.md`（已更新：新增 FIX-R1 一节，T011 历史数字原样保留） | — |
| 本验证报告 `task_handoffs/FIX-R1/fix-r1-03-verification.md` | — |

T011 历史文件（`task_handoffs/T011/perf_measurements.jsonl`、`perf_summary.json`、`perf_image_1920x1080.png`、`perf_stdout.log` 等）**未覆盖、未改动**。

## 7. 新旧测量对照表

| 轮次 | 代码基线 | 测量时间（GMT） | P50 | **P95** | 均值 | 最小 | 最大 | verdict | 门槛 |
|---|---|---|---|---:|---:|---:|---:|---:|---|---|---|
| T011（历史） | T013 核心修改**之前** | 2026-11-25 ~10:00 | 2.906 | **3.817** | 2.926 | 2.085 | 3.825 | 30× MISMATCH | PASS |
| **FIX-R1（本次）** | **最终冻结 `93d1b7c` / HEAD `16a3ef5`** | **2026-11-25 19:59** | **2.812** | **4.458** | **2.934** | **1.804** | **4.585** | **30× MISMATCH** | **PASS** |

本次 P95 比 T011 高 0.641s（4.458 vs 3.817），余量从 1.183s 收窄到 0.542s。单次方差大（1.804–4.585s），后半段 run 18–21 连续 4 次 > 4.2s，主因应为共享 CPU 争用（同 T011 §5 的 caveat）；未做“空闲推断”，报告数字以实测为准。门槛仍通过，但余量收窄值得注意——若后续核心代码再变重或机器更忙，P95 有逼近 5s 的风险。

## 8. 复现命令

```bash
cd ~/workspace/p033-textproof
export TMPDIR=$PWD/tmp
.venv/bin/python scripts/benchmark_perf.py \
  --out task_handoffs/FIX-R1/perf/perf_measurements.jsonl \
  --summary task_handoffs/FIX-R1/perf/perf_summary.json \
  --image-out tests/fixtures/performance/perf_1920x1080.png
# 默认 --runs 30 --warmup 3；退出码 0 当且仅当 P95 ≤ 5s
# 字典缺失时先跑 .venv/bin/python scripts/setup_dictionary.py 重建
# （SHA 应为 b5f2bfe2…401c5d，18,708 行）
```
