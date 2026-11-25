# FIX-R1-04 验证报告：修订 S0 报告并如实记录已知限制

- 任务：FIX-R1-04（修复终审 R1 的两个 P2：S0_REPORT.md 准确性）
- 工作目录：`~/workspace/p033-textproof/`，分支 `fix-r1`，HEAD `16a3ef5`
- 执行时间：2026-11-25 ~20:00–20:15 GMT
- 状态：S0_REPORT.md 已修订（未提交）；未改动任何门禁阈值、样本集、manifest；未改动 S0 PASS 结论本身。
- 本文件：`task_handoffs/FIX-R1/fix-r1-04-verification.md`

## 1. Parity 实测：边缘电池 14/26（exit 0）

实测命令（锁 venv）：

```text
$ .venv/bin/python scripts/parity_check.py --manifest tests/fixtures/s0/manifest.json
fixed fixtures: 300/300 match (100.0%)
edge battery (diagnostic): 14/26 match; differing: ['empty_expected_empty_ocr', 'empty_expected_one_ocr', 'low_conf_match', 'low_conf_diff', 'missing_line', 'extra_line', 'high_cost_pair', 'confusion_lower_o', 'trailing_newline', 'same_row_two_boxes_x_order', 'same_row_diff_centre', 'multi_sub_mixed_types']
```

- 退出码：0；stderr 为空。完整输出另存于 `/tmp/fix-r1-04-parity-stdout.log`（本机临时文件，非交付物）。
- 本次运行未带 `--out`，未写任何 `parity_report.json`，未覆盖任何历史记录（脚本仅在显式 `--out` 时写文件，见 `scripts/parity_check.py:366-381`）。
- 与终审 R1 报告（`P033_FINAL_REVIEW_R1.md:121`：GPT 实测 14/26）一致；与 T013 交接记录一致。

### 1.1 13/26 的起源与翻转原因（逐轮考证）

| 轮次 | 边缘电池 | 差异项 | 出处 |
|---|---|---|---|
| T006（S0 裁决） | **13/26** | 13 项，含 `confusion_upper_O` | `task_handoffs/T006/parity_report.json`（`edge_battery.matching=13, differing=13`）、`task_handoffs/T006/test_stdout.log:23,135`、`task_handoffs/T006/TASK_RESULT.md:126` |
| T009 重跑 | 13/26 | 同 T006（含 `confusion_upper_O`） | `task_handoffs/T009/TASK_RESULT.md:53,109`、`task_handoffs/T009/s0_rerun/verify_s0_cli.log:8` |
| T010 离线验证 | 13/26 | 同 T006 | `task_handoffs/T010/evidence/verify_s0_offline_stdout.log:8` |
| T011 全量回归 | 13/26 | 同 T006（含 `confusion_upper_O`） | `task_handoffs/T011/parity_report.json`（`matching=13`）、`task_handoffs/T011/parity_stdout.log:3`、`task_handoffs/T011/METRICS_REPORT.json`（`oracle_parity.edge_battery_diagnostic.matched=13`） |
| T013（R-01 修复后） | **14/26** | 12 项，`confusion_upper_O` 转为一致 | `task_handoffs/T013/T013_INTEGRATION.md:51`、`T013_MAINCHAT_VERDICT.md:23` |
| T014 R1 独立复审 | 14/26 | 同 T013 | `tmp/archive-staging/REVIEW_REPORT_T014_R1.md:132`（§5 #12） |
| 本次实测（FIX-R1-04） | **14/26** | 12 项（见上） | 本节实测输出 |

翻转的一案是 `confusion_upper_O`（期望 `O`、OCR 行 `0`，§4.4 歧义边界 0.05）：

- T011 记录的旧差异（`task_handoffs/T011/parity_report.json`）：生产 `REVIEW_REQUIRED` + 单条 `AMBIGUOUS_ALIGNMENT`；Oracle `MISMATCH` + `SUBSTITUTION`。S0_REPORT.md §3.3 V2 已诊断根因：次优（缺失+额外行，0.35+0.35=0.70）与最优（配对，混淆代价 0.65）之差十进制下恰好为 0.05，不小于 0.05，不应判歧义；生产用二进制浮点 `0.7 - 0.65 == 0.04999999999999993 < 0.05` 误判歧义（已证实的生产缺陷 F-01）。
- 修复：T013 R-01，commit `d26adcc`（“exact Fraction arithmetic for align_lines / weighted_edit”，随 T013 合并 `9cfaace`），`align_lines` / `weighted_edit` 内部代价比较与歧义判定改用精确 `Fraction` 算术（见 `src/textproof/core/align_lines.py:56-63,89-99` 与 `task_handoffs/T013/r01/TASK_RESULT.md:19,32-33`）。
- **归因纠正**：T014 R1 复审报告（§5 #12）把翻转写成“0.05 歧义边界附近的 OCR/判定抖动”，该表述不准确——边缘电池用固定合成记录（`scripts/parity_check.py:235-236`：`confusion_upper_O` 期望 `O`、OCR 行 `0`、固定 bbox），**不经过 live OCR**，不存在 OCR 抖动；翻转的确定性原因是 R-01 的精确算术修复。S0_REPORT.md V2 已按此准确表述（见 §3）。
- 其余 12 项差异未变：R 组 10 项（表示字段，F-03）+ V1 1 项（空期望+空 OCR，F-04）+ V3 1 项（同行多框阅读顺序，F-02）。`task_handoffs/T006/parity_report.json` 仍为 T006 裁决时 13/26 的原始记录，未改动。

## 2. 计时归属考证：两组数字各属于哪一次运行

重算方法：取各轮 `live_ocr_results.jsonl` 300 行的 `seconds` 字段；P50 为中位数，P95 按 `scripts/compute_s0_metrics.py:362-363,374-380` 的 `_percentile` 线性插值（`rank = 0.95 * (n-1)`），max 为最大值。与各轮 `s0_metrics.json` 的 `timing_seconds` 逐数对照。

| 数字组 | P50 | P95 | Max | 归属 | 来源文件 |
|---|---|---|---|---|---|
| **A（旧报告值）** | 1.33s | 1.77s | 3.13s | **无磁盘出处，不可归属任一轮次** | 仅见于 S0_REPORT.md 初版（commit `0ad56d6`，T006 建报告时写入）；全树检索无任何日志/JSON 含该组数字；T006 交接包只保留了 run2 的逐图计时，run1 的逐图计时未保留；且 T006 交接记录的 run1/run2“逐数一致”只覆盖召回率、FPR、CER、IoU 最小值四项，不含计时（`task_handoffs/T006/TASK_RESULT.md:176-177`、S0_REPORT.md §8 run1 说明） |
| **B（GPT 重算值 = run2 实测）** | **2.1235s** | **2.7147s** | **3.2683s** | **T006 权威轮次 run2**（`verify_s0.py --force-live`，S0 报告的权威证据轮次） | `task_handoffs/T006/live_ocr_results.jsonl` 重算：P50 2.1235、P95 2.7147、max 3.2683；与 `task_handoffs/T006/s0_metrics.json` 的 `timing_seconds`（P50 2.1235、P95 2.714725、max 3.2683）逐数一致；GPT 在 `P033_FINAL_REVIEW_R1.md:219-231` 从同一 jsonl 重算并与同一 s0_metrics.json 对照，得到同一组数字 |
| C | 1.4198s | 2.2830s | 5.2882s | T009 S0 重跑 | `task_handoffs/T009/s0_rerun/live_ocr_results.jsonl` 重算 + `task_handoffs/T009/s0_rerun/s0_metrics.json` 一致 |
| D | 2.2322s | 2.9777s | 3.5225s | T011 S0 重跑 | `task_handoffs/T011/s0/live_ocr_results.jsonl` 重算 + `task_handoffs/T011/s0/s0_metrics.json` 一致（T011 METRICS_REPORT.json 亦作相同记录） |

结论：

- S0_REPORT.md 第 214-216 行的 1.33/1.77/3.13（A 组）**不能**与 run2 的 2.1235/2.7147/3.2683（B 组）同时作为同一轮结果；A 组在磁盘上无对应运行记录，不得再作为任一轮次的计时引用。
- B 组是唯一可归属到 S0 权威轮次（T006 run2）的计时；C、D 两组是 T009、T011 各自重跑的计时，各轮内 jsonl 与 s0_metrics.json 自洽，轮间差异属同机不同时段的 CPU 争用所致（T011 PERFORMANCE_REPORT.md §5 亦记录测量期有并行进程争用 CPU）。
- 各轮的 `ocr_line_count` 分布均为 `{1: 300}`（见 §5）。

## 3. S0_REPORT.md 逐项修改清单

文件现为 476 行（原 419 行）；`git diff --numstat S0_REPORT.md`：**69 行新增、12 行删除**。S0 PASS 结论、门禁阈值、样本集、manifest 均未动。行号为修改后文件行号。

### 修改 1 — §3.3 标题（L99）

- 前：`### 3.3 门禁范围之外的诊断：26 项边缘电池（13/26 一致）`
- 后：`### 3.3 门禁范围之外的诊断：26 项边缘电池（14/26 一致）`

### 修改 2 — §3.3 引言（L103-106）

- 前：`**不属于冻结门禁范围**，结果 13 项一致、13 项有差异。差异逐项列出并裁定如下；完整逐字段 diff 见 \`task_handoffs/T006/parity_report.json\` 的 \`edge_battery.differences\`。`
- 后：`**不属于冻结门禁范围**，结果 14 项一致、12 项有差异。差异逐项列出并裁定如下；完整逐字段 diff 见 \`task_handoffs/T006/parity_report.json\` 的 \`edge_battery.differences\`（该文件是 T006 裁决时 13/26 的原始记录；当前代码实测 14/26，见 §8 补充命令行；翻转的一案为 \`confusion_upper_O\`，见 V2）。`

### 修改 3 — §3.3 V2 修复状态（L140-146）

- 前（尾句）：“……S0 指标零影响。修复属一行量级（以精确十进制/分数比较代替浮点比较），但本任务禁改 T004 文件，故不修复、只记录，列为 T013 P1（或 T004 跟进修复 + 回归测试）。”
- 后（尾句改为）：“……S0 指标零影响。**修复状态（终审 R1 前更新）：T013 R-01 已修复**——\`align_lines\` / \`weighted_edit\` 的内部代价比较与歧义判定改用精确 \`Fraction\` 算术（commit \`d26adcc\`，随 T013 合并 \`9cfaace\`；见 \`task_handoffs/T013/r01/TASK_RESULT.md\`）。修复后本案生产与 Oracle 一致（\`MISMATCH\` + \`SUBSTITUTION\`），边缘电池由 13/26 变为 14/26。本案翻转的原因是该确定性代码修复：边缘电池用固定合成记录（\`scripts/parity_check.py\` 内 \`confusion_upper_O\`：期望 \`O\`、OCR 行 \`0\`），不经过 live OCR，与 OCR 读法抖动无关。”
- V2 的缺陷诊断原文（浮点 `0.7 - 0.65` 误判歧义）原样保留，作为历史根因记录。

### 修改 4 — §3.3 范围声明（L158-163）

- 前：“……则 F-01（生产浮点缺陷）与 F-03（规格未写明的表示字段）使 parity 在该理解下不成立，S0 应为 FAIL。”
- 后：“……则 F-03（规格未写明的表示字段）使 parity 在该理解下不成立，S0 应为 FAIL（F-01 生产浮点缺陷已由 T013 R-01 修复，当前实测 14/26，见 V2；其余 12 项差异均为 R 组 / V1 / V3 类表示与口径分歧）。”
- 其余句子（按任务卡字面范围给 PASS、分歧点写明供主聊天复核）不变。§9.4 的 F-01 行此前已写“T013 修复……终审前关闭”，与本次更新一致，未动。

### 修改 5 — §5 计时段（L222-233）

- 前：`计时（1200×480 fixture，单 warmed adapter，OCR+比较每图）：P50 1.33s、P95 1.77s、max 3.13s。`
- 后：`计时（1200×480 fixture，单 warmed adapter，OCR+比较每图；权威轮次 run2）：P50 2.1235s、P95 2.7147s、max 3.2683s——由 \`task_handoffs/T006/live_ocr_results.jsonl\` 300 行的 \`seconds\` 字段重算（P50 为中位数，P95 按 \`scripts/compute_s0_metrics.py\` 的 \`_percentile\` 线性插值），与同目录 \`task_handoffs/T006/s0_metrics.json\` 的 \`timing_seconds\`（P50 2.1235、P95 2.714725、max 3.2683）逐数一致。本报告初版（commit \`0ad56d6\`）所写的 P50 1.33s / P95 1.77s / max 3.13s 在磁盘上无对应运行记录可考：T006 交接包只保留了 run2 的逐图计时，run1 的逐图计时未保留，且 T006 交接记录的 run1/run2“逐数一致”只覆盖召回率、FPR、CER、IoU 最小值四项，不含计时；T009 重跑（P50 1.4198s / P95 2.2830s / max 5.2882s）与 T011 重跑（P50 2.2322s / P95 2.9777s / max 3.5225s）的计时也各不相同（同机不同时段的 CPU 争用所致，各轮 \`live_ocr_results.jsonl\` 与 \`s0_metrics.json\` 自洽）。故 1.33/1.77/3.13 不得再作为任一轮次的计时引用；本节以 run2 实测为准。`
- 后续句子（§8.3 运行时间门槛针对 1920×1080、NOT_MEASURED、归 T011 性能报告、T011 P95 3.817s ≤ 5s PASS）原样保留。注：T011 的 3.817s 仍正确归属为 T011 的历史测量；并行任务 FIX-R1-03 在 `PERFORMANCE_REPORT.md` 另记了一轮 FIX-R1 重新测量（P95 4.458s），见 §7。

### 修改 6 — §8 补充命令表（L361）

- 前：`| \`python scripts/parity_check.py --manifest tests/fixtures/s0/manifest.json\` | 0 | 固定 300/300；边缘电池 13/26（见 §3.3） |`
- 后：`| \`python scripts/parity_check.py --manifest tests/fixtures/s0/manifest.json\` | 0 | 固定 300/300；边缘电池 14/26（见 §3.3；T006 裁决时为 13/26，T013 R-01 修复 F-01 后翻转为 14/26） |`

### 修改 7 — 新增 §10 已知限制（非门禁）（L440-476，全文见 §4）

- 位置：文件末尾，§9.5 之后；未改动任何现有章节编号。
- 内容：10(a) 多行中文海报端到端覆盖不足；10(b) ￥/¥ 混淆。

### 未改动项（已核实）

- S0_REPORT.md 内**没有**“两轮独立复审均重跑 S0”这类说法：全文检索 `复审`/`重跑`，仅有两处与复审无关的表述——§7（原 L314）“两轮完整门禁运行（run1、run2）”指 S0 自己的两轮门禁运行，§6(b)（原 L279）“独立重跑结果（本任务实测，非引用 T005）”指 T006 自己的重跑；均未改动，无需修正，也未凭空添加任何复审表述。
- 残留的 `13/26` 三处均为有意的历史归属表述（L105：T006 原始记录；L144：由 13/26 变为 14/26；L361：T006 裁决时为 13/26）；残留的 `1.33/1.77/3.13` 两处均为有意的溯源说明（L227、L233：初版值无出处、不得再引用）。
- 第 1 节 `verdict` 分布、§6(a) ￥→¥ 裁定、§9.4 发现汇总表均未动。

## 4. 新增 §10 已知限制节全文（S0_REPORT.md L440-476）

```text
## 10. 已知限制（非门禁）

以下两项是终审 R1（P2）指出的已知限制。它们**不是冻结规格的门槛**（§8.3
的 S0 PASS 条件未列多行 clean 样本，也未列货币符号等价要求），**不改变
S0 VERDICT: PASS**；本节只作如实记录，供下一版本改进。本轮不扩大 S0 样本集、
不改动冻结门禁。

### 10(a) 多行中文海报的端到端覆盖不足

- 300 张 S0 fixture 的 live OCR 每图只返回 1 行：`task_handoffs/T006/live_ocr_results.jsonl`
  与 `task_handoffs/T011/s0/live_ocr_results.jsonl` 的 `ocr_line_count` 分布均为
  `{1: 300}`。生产代码支持多行对齐（`src/textproof/core/align_lines.py`），
  合成行对齐测试 `tests/unit/test_core/test_align_lines.py::test_align_multi_line_mixed_case`
  通过，但 300 张图没有覆盖真实多行 OCR 输出。
- 唯一的多行实测是 T011 的 1920×1080 四行性能样本
  （`task_handoffs/T011/perf_image_1920x1080.png`，4 行：`限时优惠 全场5折` /
  `新品上市 会员专享` / `新客立减20元` / `SALE 50% OFF ￥28.80`）：
  30 次测量的 verdict 均为 `MISMATCH`——OCR 漏读两处中文词间空格
  （`限时优惠 全场5折` → `限时优惠全场5折`等，2 条 `MISSING_CHARACTER`），
  并把第 3 行的「减」读成「減」（1 条 `SUBSTITUTION`）
  （见 `task_handoffs/T011/PERFORMANCE_REPORT.md` §4）。该样本只用于 §8.3
  计时门槛（P95 3.817s ≤ 5s），判读结果不计入门禁。
- 下一版本：增加多行 clean 样本（终审 R1 P2 建议）。

### 10(b) ￥/¥ 混淆：字符级应保留，电商场景属误报

- 按字符级精确比较，`￥`（U+FFE5）→ `¥`（U+00A5）的差异应保留：§4.3 规范化
  只把 U+FF01–U+FF5E 的全角 ASCII 映射为半角，`￥` 不在该范围内，**不得**映射
  （见 §6(a)；`src/textproof/core/normalize.py` 亦如是；T013 裁决确认“无 ￥→¥ 映射”）。
  把两者视为相同需要 ADR 与 Owner 批准，本报告无权改动。
- 但对电商价格海报用户，live OCR 把图绘的 `￥` 读作 `¥` 会形成额外误报：
  TP-S0-NUM-001 的 live 路径因此多出 1 条 `SUBSTITUTION`（§6(a) 已裁定样本仍满足
  §8.1）；300 张 CER 的 S=1 即此一例。单行样本里另有一例同类 OCR 空格行为：
  TP-SUB-055 的 `TOP 当季上馈` → `TOP当季上馈`（空格丢失，D=1；见 §5 CER 说明与
  §9.3），注入替换本身仍被检出。
- 下一版本：增加货币符号样本与口径说明（终审 R1 P2 建议），评估电商场景的误报
  影响；是否引入任何等价映射须另行 ADR。
```

## 5. 两轮 T014 复审 S0 重跑情况核实（供 R2 草稿披露用）

核实对象：Drive 归档副本 `tmp/archive-staging/REVIEW_REPORT_T014_R1.md` 与 `REVIEW_REPORT_T014_R2.md`（与 `FINAL_REVIEW_R1_MESSAGE.md:89-90` 所列 Drive 文件同名），并以审查工作区原文交叉核对（`~/workspace/p033-textproof-t014-review/task_handoffs/T014/review/REVIEW_REPORT.md` 与 `~/workspace/p033-textproof-t014-review2/task_handoffs/T014/review2/REVIEW_REPORT.md`，与归档副本逐字节一致；本机另有 `review/REVIEW_PACK_T014R2.md`、`review/REVIEW_PACK_T014R3.md` 审查包为旁证）。

### R1：重跑了 S0 — 确认

- `REVIEW_REPORT_T014_R1.md` §0（L8）：审查范围含“S0 门禁 `--force-live`”。
- §5 #12（L132）：“S0 门禁：`TMPDIR=$PWD/tmp <venv>/bin/python scripts/verify_s0.py --manifest tests/fixtures/s0/manifest.json --force-live` | **PASS，exit 0**（约 9.5 分钟；日志存于复审工作区内 scratch `tmp/r14_s0.log`，未入库）：召回 **100.00%**；clean FPR **0.00%**（0/100）；parity **300/300**；schema 合法率 100%；CER **0.0008**；IoU 最小 **0.829**；四固定案例全部 PASS；`S0 VERDICT: PASS`。……另：诊断性质的边缘电池本轮为 14/26（T006 裁决时 13/26）”。
- GPT 在 `P033_FINAL_REVIEW_R1.md`（“第三，T014 第二轮是否重跑 S0”）中亦确认“R1 报告确实记录了 verify_s0.py --force-live 重跑”。

### R2：未重跑 S0 — 确认

- `REVIEW_REPORT_T014_R2.md` §0 方法注（L17）：“S0 门禁 `--force-live` 本轮**未重跑**，判断依据见 §5 第 12 项：本次冻结相对上一轮唯一改动是 README 文字（`git diff 3f02b32 93d1b7c` 仅 `README.md` +4/−3 行），src/tests/schemas/fixture/manifest/S0 门槛零改动，README 文字不可能影响 OCR 行为或门禁结果；上一轮 S0 已重跑 PASS，该结论仍然成立。”
- §5 #13（L111）：“S0 门禁 `--force-live` | **本轮未重跑**。依据：冻结相对上一轮唯一改动是 README 文字（§2.1）；src/tests/schemas/fixture/manifest/S0 门槛零改动（§3）；上一轮 S0 已重跑 PASS（召回 100.00%、clean FPR 0.00%、parity 300/300、CER 0.0008、IoU 最小 0.829，见上一轮报告 §5 #12）。README 文字不可能改变门禁结果，故上一轮结论仍然成立。”
- R2 的审查范围（L7）亦只列 pytest、`verify_release.py`、`verify_review_pack.py`、离线安装冒烟，未列 S0。

### 结论与 R2 草稿披露要求

- **“T014 两轮独立复审均重跑 S0 `--force-live`，PASS”（`FINAL_REVIEW_R1_MESSAGE.md:33`）不准确**：仅 R1 重跑，R2 明确未重跑（以 R1 结论沿用）。GPT 在 `P033_FINAL_REVIEW_R1.md` 中同样判定该描述不准确，但不阻断交付（功能代码无变化）。
- 该错误说法**不在 S0_REPORT.md 内**，故 S0_REPORT.md 无需为此修正；错误仅存于终审 R1 的提交消息（`FINAL_REVIEW_R1_MESSAGE.md:33`，该文件不在本次修订范围内）。
- **R2 草稿不得再写“两轮均重跑 S0”**；正确表述为：R1 重跑 S0 `--force-live` PASS（exit 0）；R2 未重跑 S0，因相对上一轮冻结唯一改动为 README 文字，沿用 R1 的 S0 结论。
- 旁证：`review/REVIEW_PACK_T014R3.md:29` 对 R2 包的书面纠正针对的是 README U-01 旧句漏检，与 S0 重跑问题无关；R3 包未就 S0 重跑作纠正。

## 6. 已知限制两项的证据出处（补记）

### 6(a) 多行覆盖

- 300 张均为单行 OCR：T006 与 T011 的 `live_ocr_results.jsonl` 各 300 行，`ocr_line_count` 分布均为 `{1: 300}`（本次独立统计；另见 §2 末）。
- 生产代码支持多行对齐：`src/textproof/core/align_lines.py`；合成测试 `tests/unit/test_core/test_align_lines.py::test_align_multi_line_mixed_case`（三行期望/OCR 行配对 (0,0)/(1,1)/(2,2)，`ambiguous is False`）通过。
- 四行性能样本：`task_handoffs/T011/perf_image_1920x1080.png`（1920×1080，SHA-256 `2bd4573f286c4d3c14a0f93351264511fff7f85919f4e9fbc858a3693c5f8f03`，种子 20261125）；4 行内容与 30 次 MISMATCH、2 处空格漏读、1 处「减」→「減」见 `task_handoffs/T011/PERFORMANCE_REPORT.md` §2、§4；30 次测量记录见 `task_handoffs/T011/perf_measurements.jsonl`（30 行，verdict 均为 `MISMATCH`）。
- 规格未列为门槛：`PROJECT_BOOK.md` §8.3 验收指标表（固定合成样本数 300、召回率 ≥95%、单类 ≥90%、误报率 ≤8%、schema 100%、CER 记录值、外网 0、仅 CPU、运行时间 1920×1080 P95 ≤5s）与 §8.3 下 S0 PASS 条件均无多行 clean 样本要求；§8.1 四固定样本亦均为单行。

### 6(b) ￥/¥ 混淆

- 字符级应保留：§4.3 规范化只映射 U+FF01–U+FF5E（`PROJECT_BOOK.md:181` §4.3；`src/textproof/core/normalize.py:21-22,51-54,67-68` 明确 `￥` U+FFE5 不在映射范围内）；S0_REPORT.md §6(a) 已裁定比较核心如实报告 `￥`→`¥` 为差异是正确的，删掉或等价化需 ADR 与 Owner 批准；`T013_MAINCHAT_VERDICT.md:21` 确认禁令遵守“无 ￥→¥ 映射”。
- 电商场景误报：TP-S0-NUM-001 live OCR `¥28.00`（置信度 0.93004）vs 图绘 `￥28.00`，多出 1 条 `SUBSTITUTION`（S0_REPORT.md §6(a) 逐字输出；`task_handoffs/T006/s0_metrics.json` 的 `s0_live.TP-S0-NUM-001`）；CER 的 S=1 即此一例（`task_handoffs/T006/s0_metrics.json` 的 `cer`：S=1、D=1、I=0、N=2496）。
- 边缘电池另有固定记录案 `fullwidth_yen`（期望 `￥28.80`、OCR 行 `￥28.00`，`scripts/parity_check.py:241-242`），两侧一致，不在本次 12 项差异内。
- 规格未列为门槛：§8.3 / §8.1 均无货币符号等价要求；`PROJECT_BOOK.md:54` 的用户故事虽含 `￥28.80` 海报，但未规定 ￥/¥ 等价。

## 7. 范围遵守与并行工作说明

- 未改动：任何门禁阈值、样本集（300 PNG、manifest）、`scripts/`、`src/`、S0 PASS 结论；未提交任何东西；未切换分支（仍在 `fix-r1`，HEAD `16a3ef5`）。
- 本任务仅修改了 `S0_REPORT.md`（69 增 / 12 删）并新增本验证报告。工作区内另有两处并行修改**不是本任务所为**，特此区分：
  - `PERFORMANCE_REPORT.md`（138 行新增）：并行任务 FIX-R1-03 的 FIX-R1 重新测量（1920×1080 P95 4.458s ≤ 5s，PASS）；S0_REPORT.md §5 保留的“T011 P95 3.817s”仍正确归属为 T011 的历史测量，未因此改动。
  - `PROJECT_BOOK.docx`（二进制改动）：并行任务所为（终审 R1 P1-01 相关），未触碰。
- 本报告引用的 `tmp/archive-staging/`（Drive 归档副本）与审查工作区互相印证：R1 报告原文在 `~/workspace/p033-textproof-t014-review/task_handoffs/T014/review/REVIEW_REPORT.md`，R2 报告原文在 `~/workspace/p033-textproof-t014-review2/task_handoffs/T014/review2/REVIEW_REPORT.md`；两份均与 `tmp/archive-staging/` 的 `REVIEW_REPORT_T014_R1.md` / `REVIEW_REPORT_T014_R2.md` 逐字节一致（`diff -q` 无差异），§5 引用的行号与结论在两边完全相同。
