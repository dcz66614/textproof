# TASK_RESULT.md — T006 S0 门禁与独立复核（P033 TextProof）

- 任务 ID：T006
- 输入 commit：`732f07e188770460ef4ba3551b03691987118dcc`（master：T001–T005
  与独立 Oracle 均已合入，全量 217 个测试通过）
- 输出 commit（代码与报告）：`0ad56d6b3d00a6dece099eb833de3c1563f8c2ab`
- 交接包 commit：见父代理的 git log（本文件包含在交接包 commit 中，故其哈希
  只能在提交后由外部读取；代码输出 commit 如上，不受交接包 commit 影响）
- 分支：`t006-s0-gate`（worktree `~/workspace/p033-textproof-t006`）
- 状态：**SUCCESS — S0 VERDICT: PASS，9 项门禁逐项通过**（逐项证据见 §2；
  完整记录见 `S0_REPORT.md`；最终 PASS 由主聊天复核后裁决）
- 执行时间：2026-11-25 ~05:48–06:30 GMT
- 工作目录：`~/workspace/p033-textproof-t006`（`git worktree`，与主工作目录
  master 检出隔离）

## 1. 实际改动文件（输出 commit 0ad56d6，8 个新增文件，0 修改）

| 文件 | 说明 |
|---|---|
| `S0_REPORT.md` | S0 报告：顶部 verdict PASS、逐项证据、两项书面裁定、发现 F-01–F-04 |
| `scripts/verify_s0.py` | S0 门禁总控：9 项逐项判定，exit 0 当且仅当全过 |
| `scripts/independent_verify.py` | 独立复核：不调用 `verify_s0.py`；重算哈希、开原始 PNG、跑 live OCR、双实现逐字段核对 |
| `scripts/parity_check.py` | 固定 300 parity + 26 项边缘电池 + 裁定分组 |
| `scripts/compute_s0_metrics.py` | 300 张 live OCR 指标：召回率 / FPR / CER / IoU / schema / 计时 |
| `scripts/validate_report_schema.py` | §5 手工 schema 校验器（stdlib only；锁内无 `jsonschema` 可用） |
| `tests/s0/test_s0_gate.py` | 12 个 S0 pytest（四样本双实现、300 parity、Oracle 独立性、CPU provider、schema、NUM-001 live 锁定） |
| `task_handoffs/T006/` | 交接包（本文件 + 日志 + patch + 哈希 + 运行证据；见 §7） |

### 禁止文件未修改证明

- `git status` 在提交前只显示新增文件（5 个 scripts、tests/s0/、
  S0_REPORT.md、task_handoffs/T006/），无任何已跟踪文件修改。
- `git diff --name-only 732f07e -- PROJECT_BOOK.md PROJECT_BOOK.docx
  IMPLEMENTATION_PLAN.md IMPLEMENTATION_PLAN.docx requirements.lock
  pyproject.toml` 输出为空。
- 四份规格文件未修改；`requirements.lock`、`pyproject.toml` 未修改；未碰
  T002–T005 与 Oracle 的文件；未新增依赖，未联网安装。

## 2. 验收标准逐项证据（T006 任务卡 9 项）

### 验收 1 — Oracle 不 import 生产比较模块；独立会话、不同代码路径 ✅ PASS

- AST 检查：`oracle/reference_compare.py` 只导入标准库
 （`re`、`unicodedata`、`fractions`、`typing`），无任何 `textproof` 导入；
  同一断言在 Oracle 自测中以全新子进程复核（43 通过）。
- Oracle 由独立会话（T006-oracle）仅按项目书实现，未读生产核心代码。

### 验收 2 — 生产模块与 Oracle 在固定字符/行 fixture 上 100% parity ✅ PASS

- `scripts/parity_check.py`：manifest 的 300 张 fixture，以 `drawn_text`
  作单条固定 OCR 行记录（bbox = `target_region_xyxy`，confidence 0.99），
  双实现逐案例比对 verdict + 错误类型 + 片段 + span + bbox + warning
  codes + summary：**300/300 一致，0 差异**。
- T004 与 Oracle 的三处字面解读（混淆对集合、标点双侧要求、gap 顺序）
  全部一致（边缘电池逐项核对，见 S0_REPORT.md §3.2）。
- 边缘电池（诊断，不属于冻结门禁范围）：26 项中 13 项一致；13 项差异逐项
  列出并裁定（S0_REPORT.md §3.3）：R 组 10 项为规格未写明的表示字段
  （缺失侧 span null vs [0,0]、`bbox_scope` null vs "none"、警告对象形态）；
  V1 空期望+空 OCR（生产 `OCR_FAILED` 有 §7.6 原文支持；产品内不可达）；
  V2 单字符混淆替换 `O`→`0`（**已证实的生产浮点缺陷**，见 §5 F-01）；
  V3 同行多框阅读顺序（生产按 §4.4 正确，Oracle 偏差，见 §5 F-02）。
  范围声明：若终审将 parity 理解为全输入域 100%，F-01 与 F-03 使该理解下
  的 parity 不成立；本报告按任务卡字面范围（manifest 固定记录）给 PASS，
  分歧点已写明供主聊天裁决。

### 验收 3 — 四个固定案例逐项核对 §8.1 ✅ PASS

- 固定 OCR 行记录路径：生产与 Oracle 双实现对 `expected_output.json`
  逐字核对类型、片段、span、bbox、verdict：四案全部 PASS。
- live OCR 路径（`independent_verify.py` 逐案）：ZH-001（IoU 0.964）、
  ZH-002（0.955）、ZH-003（0.924）恰好 1 条预期错误；NUM-001 见 §4(a)。

### 验收 4 — 300 样本检测召回率 ≥95%；每类 ≥90% ✅ PASS

- live OCR 全流程实测：**召回率 100.00%（201/201）**；替换 100.00%
  （70/70）、缺失 100.00%（71/71，含 ZH-003 的 2 字符 `"20"`）、
  数字变化 100.00%（60/60）。漏检 0 项。
- 计分规则：注入差异计为检出当且仅当 live 报告含同类型错误，其
  `expected_span` 覆盖注入 span 且 `expected_fragment` 包含注入片段。

### 验收 5 — 100 张 clean 图片误报率 ≤8% ✅ PASS

- **误报率 0.00%（0/100）**（verdict `MISMATCH` 计，§8.3 字面口径）；
  clean 非 `MATCH` 率亦为 0.00%（0/100）。verdict 分布：`MATCH` 100 张
  （恰为 clean）、`MISMATCH` 200 张（恰为 injected）。

### 验收 6 — JSON schema 合法率 100%；OCR CER 独立报告 ✅ PASS

- 300 份 live 报告经 `validate_report_schema.py`（按 §5 逐字段/枚举/类型
  校验，校验方法与依据的 §5 条款见该脚本 docstring）：**300/300 有效，
  0 违规**，合法率 100%。
- OCR CER **0.0008**（S=1，D=1，I=0，N=2496），独立报告，未替代检错召回率。
  两个 CER 字符即 live OCR 与图绘文本的全部差异：NUM-001 的 `￥`→`¥`、
  SUB-055 的空格丢失（`TOP 当季上馈` → `TOP当季上馈`）；其余 298 张逐字一致。
- 正式的 `.schema.json` 文件是 T009 的交付物（见 §6 未完成项）。

### 验收 7 — 网络访问 0；ONNX Runtime provider 仅 CPU ✅ PASS

- 两轮完整门禁运行均在 `unshare -n`（空网络命名空间）下执行，全程 exit 0
  且 300 张 live OCR 全部完成；脚本本身无任何 socket 调用；适配器构造时验
  模型 SHA 并传显式本地 `model_path`，从不走下载分支。
- det / cls / rec 三模型 `get_providers()` 均为 `["CPUExecutionProvider"]`
  （启动断言 +  pytest `test_onnx_providers_cpu_only` 通过）。

### 验收 8 — `independent_verify.py` 独立复核 TP-S0-ZH-001 ✅ PASS

- 不调用 `verify_s0.py`：重算 PNG SHA-256（与 manifest 一致）、Pillow 打开
  原始 PNG（PNG 1200×480）、读 manifest 期望文本、跑 live OCR、双实现独立
  比较、逐字段核对输出。ZH-001：**INDEPENDENT VERIFICATION: PASS**
  （live `限时优`，IoU 0.964）。
- 另逐案复核 ZH-002（PASS，IoU 0.955）、ZH-003（PASS，IoU 0.924）、
  NUM-001（PASS，子集模式；见 §4(a)）。

### 验收 9 — S0 报告记录环境、版本、commit、所有 SHA、命令、退出码、指标、未执行项 ✅ PASS

- 见 `S0_REPORT.md` 全文（§2 环境与哈希、§8 命令与退出码、§9 未执行项）。

## 3. 验收命令与退出码

| # | 命令 | 退出码 | 结果 |
|---|---|---|---|
| 1 | `/home/hatch/workspace/p033-textproof/.venv/bin/python -m pytest -q` | **0** | **229 passed**，2 warnings（T002 既有的 Pillow `DecompressionBombWarning`），179.62s |
| 2 | `unshare -n /home/hatch/workspace/p033-textproof/.venv/bin/python scripts/verify_s0.py --manifest tests/fixtures/s0/manifest.json`（`--force-live`） | **0** | S0 VERDICT: PASS（stderr 为空） |
| 3 | `/home/hatch/workspace/p033-textproof/.venv/bin/python scripts/independent_verify.py --case TP-S0-ZH-001` | **0** | INDEPENDENT VERIFICATION: PASS |

补充命令：`parity_check.py` exit 0（300/300；边缘电池 13/26）；
`independent_verify.py` ZH-002 / ZH-003 / NUM-001 exit 0；
NUM-001 `--strict-live` exit **1**（by design，见 §4(a)）。
三条验收命令全部 exit 0，T006 完成。

## 4. 两项必须书面裁定的问题（结论摘要；全文见 S0_REPORT.md §6）

### (a) TP-S0-NUM-001 的 live-OCR ￥→¥ 问题 — 裁定：样本仍满足 §8.1

live 逐字输出：OCR 读作 `¥28.00`（置信度 0.93004），报告含
E001 `SUBSTITUTION`（`￥`→`¥`，span [0,1]）与 E002 `NUMERIC_CHANGE`
（`8`→`0`，span [4,5]），verdict `MISMATCH`。
裁定：§8.1 原文“恰好 1 条 `NUMERIC_CHANGE`”只约束 `NUMERIC_CHANGE` 的
条数（本样本 live 路径恰好 1 条，fragment 与 span 逐字符合）；同表 ZH-003
的“至少 1 条”证明该栏按类型计数；固定路径下本样本恰好只有 1 条错误，
两种读法都通过；§4.3 不映射 `￥`（U+FFE5 不在 U+FF01–U+FF5E 内），
比较核心如实报告该差异是正确的。**未删错误、未改 fixture、未改 manifest、
未提交 ADR。** 若复核采用“总错误数恰好为 1”的读法，则该样本不满足 §8.1、
S0 应为 FAIL——分歧点已写明供主聊天裁决。

### (b) target_region 校准方法 — 裁定：方法合法，盲测验证成立

独立重跑 live OCR：全部 300 张 IoU 最小 **0.829**、均值 0.938、低于 0.80
的 0 张；盲测 60 张最小 **0.835**、均值 0.940、低于 0.80 的 0 张
（与 T005 报告值逐数一致）。规则是墨迹几何的确定性函数
（`height = 70 + 0.7*ink_height - 0.05*ink_width`；
`width = ink_width + 40 - 0.02*ink_width`），本任务从 `ink_bbox_xyxy`
重算复现 manifest 的 `target_region_xyxy`：**300/300 一致**。盲测 60 张
未参与拟合、未用于调参（看到 S0 结果后未重拟合）。**无一张 IoU < 0.80，
无 S0 发现。**

## 5. 发现（门禁范围外；汇总）

| 编号 | 发现 | 严重度 | 处置建议 |
|---|---|---|---|
| F-01 | 生产 `align_lines` 浮点比较误判歧义（`O`→`0`：0.7−0.65 在浮点下 = 0.04999999999999993 < 0.05；精确十进制差恰好 0.05，不应判歧义；Oracle 正确） | P1（生产缺陷；S0 零影响，300 fixture 0 触发） | T013 修复：精确十进制/分数比较 + 回归测试；终审前关闭 |
| F-02 | Oracle 阅读顺序与 §4.4 字面不符（同行多框按中心而非按 x 排） | 低（无 fixture 影响） | Oracle 跟进修正或登记为已知偏差 |
| F-03 | 行级错误缺失侧 span（null vs [0,0]）、`bbox_scope`（null vs "none"）、警告对象形态：规格未写明，无法按原文裁定 | P1（规格澄清） | T009 冻结 JSON schema 时统一口径 |
| F-04 | 空期望 + 空 OCR 的 verdict：生产 `OCR_FAILED`（有 §7.6 原文支持），Oracle `MATCH`（无原文依据） | 低（产品内不可达，T002 拒空白期望） | Oracle 跟进对齐 §7.6 |

## 6. 未完成项与风险

- **未完成项：** §8.3 运行时间（1920×1080 预热后 P95 ≤5s）未测量——冻结
  fixture 为 1200×480，记为 NOT_MEASURED，归 T011；正式 `.schema.json`
  文件是 T009 的交付物，本任务以手工校验器按 §5 校验并留日志；API / UI /
  CLI 一致性、隐私与离线全量测试属 T007–T014。
- **已登记、不改：** `tool_version` `"0.1.0"` 与 `pyproject.toml` `1.0.0`
  不一致（留给 T009/终审统一口径）；字典许可状态转述 T003。
- **过程记录：** 第一轮门禁运行因 `verify_s0.py` 自身的独立性检查 bug
  （子串 `"textproof" in source` 误判 Oracle 文档字符串中的冻结 schema 名）
  退出 1；修复为 AST 导入检查后（只改本任务脚本）run2 全项通过、退出 0；
  两轮指标数逐数一致，run2 为权威轮次。另有两次较长 exec 调用返回
  “审批超时”提示，但命令实际已执行并返回完整输出与退出码（以实际退出码
  与日志为准，未重复执行；按任务指示向父代理报告此提示）。
- **风险：** §6(a) 与 §3.3 的范围声明写明的两处裁定分歧点（NUM-001 总数
  读法、parity 全输入域读法）若被复核推翻，S0 应为 FAIL；本报告按任务卡
  字面范围给 PASS，最终由主聊天裁决。

## 7. 交接包内容（`task_handoffs/T006/`）

`TASK_RESULT.md`、`changed_files.txt`、`git_diff.patch`、
`test_commands.txt`、`test_stdout.log`、`test_stderr.log`、
`exit_codes.txt`、`SHA256SUMS.txt`，及运行证据 `s0_metrics.json`、
`parity_report.json`、`live_ocr_results.jsonl`（300 条 live OCR 记录）、
`schema_validation.log`（300/300 VALID）。

## 8. 回退

- 回退 commit：`732f07e`（输入 commit；本任务只新增文件，删除分支
  `t006-s0-gate` 与 worktree `~/workspace/p033-textproof-t006` 即完整回退）。
- 未动用失败回退：未降低指标、未删除 fixture、未修改分母（召回率分母 201、
  clean 分母 100 均为 manifest 原值）。
