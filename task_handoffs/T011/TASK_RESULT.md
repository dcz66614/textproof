# TASK_RESULT.md — P033 TextProof T011 全量回归、300 样本指标与性能报告

- 分支：`t011-full-regression`（基于 master `b0885dd`，T010 已合入）
- Worktree：`~/workspace/p033-textproof-t011`
- 运行时间：2026-11-25 09:42–10:05 GMT
- 结论：**6 项验收全部 PASS；无真实失败转入 T013**（除 S0 裁决已路由的
  已知缺陷 F-01）

## 逐项验收对照

### 验收 1 — 单元 / 集成 / API / CLI / UI / privacy / offline 全量测试通过

- 命令：`python -m pytest -q`（worktree 根目录）
- 结果：**438 passed, 2 warnings in 287.31s**，退出码 **0**
- 分目录：unit 155、integration 105、privacy 83、oracle 43、e2e 31
  （真实浏览器）、s0 12、offline 9；收集数 438 = 通过数 438，0 失败
- 2 条警告均为 `DecompressionBombWarning`，来自
  `test_pixels_over_40m_rejected` 构造 40,008,000 像素图片的被测行为，
  测试通过
- 结论：**PASS**

### 验收 2 — 300 样本数量和 SHA 与 S0 manifest 一致

- 命令：`python scripts/verify_s0.py --manifest tests/fixtures/s0/manifest.json --force-live`
- 结果：项 [0] manifest 完整性 **PASS**（300 PNG SHA-256 全部匹配）；
  300 条 live 记录写出（`s0/live_ocr_results.jsonl`）
- 结论：**PASS**

### 验收 3 — 召回率、分类型召回率、clean FPR、OCR CER 分开报告

- 来源：`s0/s0_metrics.json`（300 张 live OCR）；报告正本
  `METRICS_REPORT.json`（四项各自独立成项，未合并）
- 召回率：**100.00%**（201/201；门槛 ≥95%）
- 分类型召回率：substitution 100%（70/70）、omission 100%（71/71，
  含 TP-S0-ZH-003 的双字符注入）、numeric_change 100%（60/60）；
  门槛每类 ≥90%
- clean FPR：**0.00%**（0/100；门槛 ≤8%）；非 MATCH 率亦为 0/100
- OCR CER：**0.0008**（S=1、D=1、I=0、N=2496；仅记录，不替代召回率）
- 另：schema 合法率 100%（300/300）；IoU min 0.829、mean 0.938、
  <0.80 计 0；blind min 0.835
- 结论：**PASS**

### 验收 4 — 预热后 1920×1080 图片 30 次测量 P95 ≤5 秒；报告环境版本

- 命令：`python scripts/benchmark_perf.py --out task_handoffs/T011/perf_measurements.jsonl --summary task_handoffs/T011/perf_summary.json --image-out task_handoffs/T011/perf_image_1920x1080.png`
- 结果：**P95 3.817s**（P50 2.906s，均值 2.926s，最小 2.085s，
  最大 3.825s；3 次预热不计入），退出码 **0**
- 基准图：新生成 1920×1080 合成图（种子 20261125，SHA-256
  `2bd4573f…5f8f03`）；S0 manifest 未改动
- 环境：AMD EPYC 9D25（VM 可见 4 核）、Ubuntu 24.04.5 LTS、
  Python 3.12.3、RapidOCR 3.10.0、onnxruntime 1.32.0（CPU-only）、
  Pillow 11.3.0；模型 PP-OCRv6 det/rec + PP-OCRv4 cls（SHA 与 S0
  运行一致）
- 结论：**PASS**（详见 `PERFORMANCE_REPORT.md`）

### 验收 5 — API、UI、CLI 同一输入输出 JSON 语义一致

- 命令：`python tests/consistency_check.py --manifest tests/fixtures/s0/manifest.json --out task_handoffs/T011/consistency_report.json`
- 方法：真实 uvicorn 服务（API）+ 真实 `textproof check` 子进程
  （CLI）+ 真实 headless Chrome + CDP 点击（UI），解析后逐字段比对
- 输入：`TP-S0-ZH-002`（MISMATCH）、`TP-CLN-001`（MATCH）
- 结果：**两案三路 JSON 完全相同**，退出码 **0**
- 结论：**PASS**

### 验收 6 — S0 独立 Oracle parity 仍为 100%

- 命令：`python scripts/verify_s0.py --manifest tests/fixtures/s0/manifest.json --force-live`
  及独立 `python scripts/parity_check.py --manifest tests/fixtures/s0/manifest.json`
- 结果：**S0 VERDICT: PASS**（退出码 0）；固定记录 parity **300/300**
  （100.0%）；四固定样本生产 + Oracle 全部 PASS
- 边缘电池（诊断，不属冻结门禁）：13/26，与 T006 完全相同
- 结论：**PASS**

## 退出码汇总

| 命令 | 退出码 |
|---|---:|
| `python -m pytest -q` | 0 |
| `python scripts/verify_s0.py --manifest tests/fixtures/s0/manifest.json --force-live` | 0 |
| `python scripts/parity_check.py --manifest tests/fixtures/s0/manifest.json` | 0 |
| `python scripts/benchmark_perf.py` | 0 |
| `python scripts/consistency_check.py` | 0 |

（另见 `exit_codes.txt`；各命令 stdout/stderr 见同目录 `*_stdout.log` /
`*_stderr.log`。）

## 交付文件

根目录（报告正本）：`FULL_TEST_REPORT.md`、`METRICS_REPORT.json`、
`PERFORMANCE_REPORT.md`

新增脚本（T011 所有）：`scripts/benchmark_perf.py`、
`scripts/consistency_check.py`

交接包 `task_handoffs/T011/`：本文件、三个报告的副本、
`changed_files.txt`、`exit_codes.txt`、全部原始日志与退出码、
`s0/`（`s0_metrics.json`、`parity_report.json`、
`live_ocr_results.jsonl`、`schema_validation.log`）、
`parity_report.json`（独立 parity 运行）、
`consistency_report.json`、`perf_measurements.jsonl`、
`perf_summary.json`、`perf_image_1920x1080.png`、
`test_collect.log`、`e2e_evidence/`（pytest e2e 运行的截图与网络日志）。

## 未改动项

相对 `b0885dd` 无任何已跟踪文件被修改：fixture、manifest、分母、
S0 阈值、核心契约、测试预期、产品代码均未动；依赖未升级、未新增。
（`git status` 只有新增文件；见 `changed_files.txt`。）

## 发现的问题（诚实记录）

1. **边缘电池 13/26（诊断）**：与 T006 完全相同，含已知真实缺陷
   F-01（`align_lines` 浮点比较）。不属冻结门禁范围，不影响 PASS；
   已按 S0 裁决路由 T013 P1 必修。本任务未修产品代码、未改测试预期。
2. **性能图 live 判读 MISMATCH**：1920×1080 性能图上 OCR 漏读中文
   词间空格（2 处）并把“减”读成“減”（1 处）。计时不受影响（每次
   测量均跑完完整路径）；S0 300 样本 CER 仍为 0.0008。未改图、未挑
   数据，见 `PERFORMANCE_REPORT.md` §4。
3. **测量期 CPU 争用**：S0 live 与性能测量期间 VM 上另有
   `verify_pool_v7.py`（8 workers）与 SpiderQuant P5R 进程在跑；
   P95 3.817s 仍有 1.18s 余量。见 `PERFORMANCE_REPORT.md` §5。
4. **无真实失败**：全量回归 0 失败、S0 全部项 PASS、parity 无回退；
   除已知的 F-01 外无内容转入 T013。
