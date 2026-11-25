# FULL_TEST_REPORT.md — P033 TextProof, T011 全量回归

- 任务：T011（IMPLEMENTATION_PLAN.md §T011）
- 基线：master `b0885dd`（T010 已合入），分支 `t011-full-regression`
- 运行时间：2026-11-25 09:42–09:46 GMT（pytest）；09:48–09:59 GMT（S0 live）；
  约 10:00–10:03 GMT（性能）；约 10:03–10:04 GMT（一致性）
- 运行环境：本 VM，`~/workspace/p033-textproof/.venv/bin/python`（Python 3.12.3；
  该 venv 由 T001 建立、lock 冻结；测试通过根 `conftest.py` 对本 worktree 的
  `src/` 运行，未改依赖、未装新包）
- 结论：**全量测试 438 通过、0 失败；S0 VERDICT: PASS；Oracle parity 300/300**

## 1. 全量测试 `python -m pytest -q`

- 命令：`python -m pytest -q`（worktree 根目录）
- 结果：**438 passed, 2 warnings in 287.31s (0:04:47)**，退出码 **0**
- 原始日志：`task_handoffs/T011/test_stdout.log`、`test_stderr.log`
  （stderr 为空；stdout 共 15 行：进度点 + 2 条警告 + 总结行）
- 收集数核对：`pytest --collect-only -q` 亦为 438 个测试，与通过数一致
  （`task_handoffs/T011/test_collect.log`）

### 按目录统计（收集数 = 通过数，0 失败）

| 目录 | 测试数 | 内容 |
|---|---:|---|
| `tests/unit` | 155 | 核心比较、归一化、图片加载、fixture |
| `tests/integration` | 105 | API、CLI、OCR 适配器 |
| `tests/e2e` | 31 | 真实浏览器 UI（headless Chrome + CDP） |
| `tests/privacy` | 83 | 无外联、无持久化、回环与 fail-closed、ORT 遥测关闭 |
| `tests/offline` | 9 | 离线命名空间 / 静态检查 / strace |
| `tests/oracle` | 43 | Oracle 独立性与对照比较 |
| `tests/s0` | 12 | S0 门禁测试 |
| 合计 | **438** | |

### 警告（2 条，非失败）

两条均为 `Pillow DecompressionBombWarning`，来自
`tests/unit/test_image_loader.py::test_pixels_over_40m_rejected` 构造
40,008,000 像素图片以验证“超限拒绝”——警告本身就是被测行为的一部分，
测试通过。无其他警告。

### 覆盖的验收项

验收 1（单元 / 集成 / API / CLI / UI / privacy / offline 全量测试通过）：
**PASS**。e2e 真实浏览器测试与 privacy/offline 较慢测试均包含在本次
`pytest -q` 全量运行内，无跳过、无 xfail、无失败。

## 2. S0 门禁 `python scripts/verify_s0.py --manifest tests/fixtures/s0/manifest.json --force-live`

- 结果：**S0 VERDICT: PASS**，退出码 **0**，stderr 为空
- 原始输出：`task_handoffs/T011/s0_stdout.log`；证据：
  `task_handoffs/T011/s0/`（`s0_metrics.json`、`parity_report.json`、
  `live_ocr_results.jsonl` 300 条、`schema_validation.log`）

| S0 项 | 结果 |
|---|---|
| [0] manifest 完整性（300 PNG SHA-256） | PASS |
| [1] Oracle 独立性（只引 stdlib） | PASS |
| [3] 四个固定样本（生产 + Oracle） | 全部 PASS，各 1 条错误，verdict MISMATCH |
| [2] 固定记录 parity | **300/300** |
| [4] 召回率 | **100.00%**（201/201；分类型 100/100/100），门槛 ≥95% / 每类 ≥90% |
| [5] clean FPR | **0.00%**（0/100），门槛 ≤8% |
| [6] schema 合法率 | **100.0%**（300/300）；CER **0.0008**（单独报告） |
| [I] IoU | min 0.829，mean 0.938，<0.80 计 0；blind min 0.835 |
| [7] ONNX providers | det/cls/rec 全部 `CPUExecutionProvider` |
| [9] 证据写出 | 已写出（见上） |

验收 2（300 样本数量和 SHA 与 S0 manifest 一致）：**PASS**（项 [0]）。
验收 3（召回率 / 分类型召回率 / clean FPR / OCR CER 分开报告）：
**PASS**，见 `METRICS_REPORT.json`（四项各自独立成项，未合并）。
验收 6（S0 独立 Oracle parity 仍为 100%）：**PASS**（300/300）。

### 边缘电池（诊断性质，不属于冻结门禁范围）

`parity_check.py` 边缘电池 13/26 匹配，与 T006 完全相同（同一组差异项，
含已知真实缺陷 F-01：`align_lines` 浮点比较，已按裁决路由 T013 P1 必修）。
冻结门禁范围是 manifest 固定记录，电池差异不改变门禁结果。
独立运行的 `scripts/parity_check.py` 同样退出码 0、固定记录 300/300，
见 `task_handoffs/T011/parity_report.json`、
`task_handoffs/T011/parity_stdout.log`。

## 3. 一致性：API / CLI / UI 三路（验收 5）

- 脚本：`scripts/consistency_check.py`（新增，T011 所有）
- 方法：同一输入经真实 uvicorn 服务（API）、真实 `textproof check`
  子进程（CLI）、真实 headless Chrome + CDP 点击（UI）三路输出 JSON，
  解析后逐字段语义比对
- 输入：`TP-S0-ZH-002`（S0 固定样本，MISMATCH）、`TP-CLN-001`
  （clean，MATCH）
- 结果：**两案三路 JSON 完全相同**（verdict、errors、warnings、spans、
  bbox、summary 全部一致），退出码 **0**
- 原始输出：`task_handoffs/T011/consistency_stdout.log`；
  机器可读结果：`task_handoffs/T011/consistency_report.json`
- 结论：**PASS**

## 4. 性能（验收 4）

见 `PERFORMANCE_REPORT.md`。摘要：1920×1080 合成图，预热 3 次后 30 次
测量，**P95 3.817s ≤ 5s，PASS**（P50 2.906s，均值 2.926s，最小 2.085s，
最大 3.825s）。原始测量数据：`task_handoffs/T011/perf_measurements.jsonl`。

## 5. 未改动项（冻结内容核对）

- `git status`：本 worktree 相对 `b0885dd` 只有新增文件，无任何已跟踪
  文件被修改——fixture、manifest、分母、S0 阈值、核心契约、测试预期、
  产品代码均未动。
- 新增文件：`scripts/benchmark_perf.py`、`scripts/consistency_check.py`、
  `FULL_TEST_REPORT.md`、`METRICS_REPORT.json`、`PERFORMANCE_REPORT.md`、
  `task_handoffs/T011/`（全部证据与交接包）。

## 6. 发现的问题（诚实记录）

1. **边缘电池 13/26（诊断）**：与 T006 完全相同，含已知缺陷 F-01
   （`align_lines` 浮点比较，单字符混淆 `O`→`0` 时误判）。不属于冻结
   门禁范围，不影响本次 PASS；已路由 T013 P1 必修（S0 裁决）。
   本任务未修产品代码、未改测试预期。
2. **性能图 live 判读为 MISMATCH**：1920×1080 性能图上的 4 行文字，
   OCR 漏读了中文词间空格（2 处 MISSING_CHARACTER）并把“减”读成“減”
   （1 处 SUBSTITUTION）。这是该合成图上的 OCR 读法差异，不影响计时
   （每次测量均跑完 OCR + 比较 + 报告全路径）；S0 300 样本的 CER 仍为
   0.0008。记录在 `PERFORMANCE_REPORT.md` §4，未改图、未挑数据。
3. **VM 上另有进程并行占用 CPU**：本次 S0 live 与性能测量期间，
   VM 上另有 `formal-exp-v7/pool/verify_pool_v7.py`（8 workers）与
   SpiderQuant P5R 进程在跑，测量值含该争用；P95 3.817s 仍有 1.18s
   余量。见 `PERFORMANCE_REPORT.md` §5。
4. **无真实失败**：本次全量回归无任何测试失败、无 S0 项失败、无
   parity 回退；无内容转入 T013（除已知的 F-01）。

## 7. 退出码汇总

| 命令 | 退出码 |
|---|---:|
| `python -m pytest -q` | 0 |
| `python scripts/verify_s0.py --manifest tests/fixtures/s0/manifest.json --force-live` | 0 |
| `python scripts/parity_check.py --manifest tests/fixtures/s0/manifest.json` | 0 |
| `python scripts/benchmark_perf.py`（30 次测量） | 0 |
| `python scripts/consistency_check.py` | 0 |

全部命令的 stdout/stderr/退出码见 `task_handoffs/T011/exit_codes.txt`
及各 `*_stdout.log` / `*_stderr.log`。
