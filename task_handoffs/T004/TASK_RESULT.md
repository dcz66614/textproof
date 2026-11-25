# TASK_RESULT.md — T004 规范化、行对齐、加权编辑距离与错误分类（P033 TextProof）

- 任务 ID：T004
- 输入 commit：`f90d577`（master：T001 + T002 + T003 均已合入，全量 72 测试通过）
- 输出 commit（代码与测试）：`cb1e3ba3941f1e844c8c32463a2eb2c12bd0de26`
- 分支：`t004-core-compare`（worktree `~/workspace/p033-textproof-t004`）
- 交接包 commit：见父代理的 git log（本文件包含在交接包 commit 中，故其哈希只能在提交后由外部读取；代码输出 commit 如上，不受交接包 commit 影响）
- 状态：**SUCCESS — 7 项验收标准全部满足**（逐项证据见 §2）
- 执行时间：2026-11-25 ~02:56–03:25 GMT
- 工作目录：`~/workspace/p033-textproof-t004`（`git worktree`，与主工作目录 master 检出隔离）

## 1. 实际改动文件（输出 commit cb1e3ba，13 个新增文件，0 修改）

| 文件 | 说明 |
|---|---|
| `src/textproof/core/normalize.py` | 新增：§4.3 规范化（NFC、全角 ASCII、空白折叠，130 行） |
| `src/textproof/core/line_order.py` | 新增：§4.4 阅读顺序（纵向重叠聚合行、x/y 排序，104 行） |
| `src/textproof/core/align_lines.py` | 新增：§7.2 行序列 DP（gap 0.35、歧义 0.05、阈值 0.70，258 行） |
| `src/textproof/core/weighted_edit.py` | 新增：§4.5/§7.3 加权编辑距离（冻结权重，233 行） |
| `src/textproof/core/classify.py` | 新增：§4.5/§7.4/§7.5 错误分类与片段合并（276 行） |
| `src/textproof/core/report.py` | 新增：§5.4 报告组装与 §7.6 verdict（390 行） |
| `src/textproof/core/__init__.py` | 新增：公共 API 导出（62 行） |
| `tests/unit/test_core/test_normalize.py` | 新增：13 个测试 |
| `tests/unit/test_core/test_line_order.py` | 新增：10 个测试 |
| `tests/unit/test_core/test_align_lines.py` | 新增：17 个测试（含 225 组暴力枚举交叉验证） |
| `tests/unit/test_core/test_weighted_edit.py` | 新增：15 个测试 |
| `tests/unit/test_core/test_classify.py` | 新增：14 个测试 |
| `tests/unit/test_core/test_report.py` | 新增：26 个测试（含 §8.1 四个固定样本） |

### 禁止文件未修改证明

- `git status` 在提交前只显示两个新增目录（`src/textproof/core/`、`tests/unit/test_core/`），无任何已跟踪文件修改。
- `git diff --name-only f90d577 -- PROJECT_BOOK.md PROJECT_BOOK.docx IMPLEMENTATION_PLAN.md IMPLEMENTATION_PLAN.docx requirements.lock pyproject.toml src/textproof/contracts.py src/textproof/io src/textproof/ocr tests/unit/test_image_loader.py tests/integration` 输出为空。
- 四份规格文件未修改；`requirements.lock`、`pyproject.toml` 未修改；未碰 T002/T003 的文件；未新增任何依赖，未联网安装。

## 2. 验收标准逐项证据

### 验收 1 — NFC、全角 ASCII 映射、空白处理与大小写敏感逐条符合 §4.3 ✅ PASS

- 顺序即规格顺序：NFC → CRLF/CR 统一 LF → 全角 ASCII（U+FF01–U+FF5E，偏移 0xFEE0）+ 全角空格 U+3000 → 每行 strip + 水平空白折叠为一空格。
- 测试：`test_nfc_composes_combining_marks`（e + U+0301 → U+00E9，2 码点 → 1 码点）、`test_fullwidth_ascii_mapped_to_halfwidth`、`test_fullwidth_space_mapped_to_space`、`test_crlf_and_cr_unified_to_lf`、`test_consecutive_horizontal_whitespace_folded_to_one_space`、`test_case_is_preserved_case_sensitive`。
- 字面解读（已写入模块 docstring）：U+FFE5 `￥` 不在全角 ASCII 范围内，不映射；`，`/`！`（U+FF0C/U+FF01）在范围内，映射为 `,`/`!`，而 `。`（U+3002）不在范围内，保持原样——测试 `test_punctuation_is_kept` 逐项锁定。

### 验收 2 — gap 0.35、margin 0.05、高代价阈值 0.70 ✅ PASS

- 常量：`GAP_PENALTY = 0.35`、`AMBIGUITY_MARGIN = 0.05`、`HIGH_COST_PAIR_THRESHOLD = 0.70`（`align_lines.py`），测试 `test_frozen_constants` 逐字断言。
- 边界：配对代价恰好 0.70 允许配对（`test_pair_cost_exactly_070_is_allowed`，7/10 替换）；0.80 禁止（`test_pair_cost_080_is_forbidden`）；1.00（`abc`/`xyz`）禁止，拆为缺失行 + 额外行（`test_align_high_cost_pair_becomes_missing_plus_extra`）。
- 歧义：第二优按**不同对齐结果**（配对集合）精确计算，见 §4 的算法说明与 225 组暴力枚举交叉验证（`test_second_best_matches_brute_force_on_exhaustive_small_cases`）。

### 验收 3 — 字符权重逐项符合 §4.5；视觉混淆对即使低权重也必须报告差异 ✅ PASS

- 常量：相同 0、混淆对 0.65、标点替换 0.50、数字替换 1.25、其他替换 1.00、缺失/额外 1.00（`weighted_edit.py`，`test_frozen_cost_constants`）。
- 混淆对集合为规格所列 6 对（`O/0`、`I/1`、`I/l`、`1/l`、`S/5`、`B/8`），大小写敏感；小写 `o`/`0` 不在列，属其他替换 1.00（`test_lowercase_o_vs_zero_is_not_a_listed_confusion_pair`，依据：规格混用大小写是刻意的，且 §4.3 大小写敏感）。
- 标点替换要求两侧均为 Unicode 类别 P（`test_punctuation_substitution_costs_050`、`test_punctuation_vs_letter_is_other_substitution`）。
- 低权重仍报告：`test_confusion_pair_still_costs_and_still_diffs`（`O`→`0` 距离 0.65 且为一条 `substitute` op）、`test_confusion_pair_is_still_reported_as_a_difference`（分类为 `SUBSTITUTION`）。

### 验收 4 — 数字到数字替换为 NUMERIC_CHANGE；数字缺失/额外仍为 MISSING/EXTRA_CHARACTER ✅ PASS

- `classify_substitution`：两侧均为 `Nd` 才判 `NUMERIC_CHANGE`（§7.4），其余替换为 `SUBSTITUTION`。
- 测试：`test_digit_to_digit_is_numeric_change`、`test_missing_digit_is_missing_character_not_numeric_change`、`test_extra_digit_is_extra_character_not_numeric_change`。

### 验收 5 — 字符 span 为规范化后码点索引，左闭右开 ✅ PASS

- 全部 span 由 DP 推进位置算出（`classify._merge_ops`），对缺失字符 recognized 侧为空 span（插入点）、对额外字符 expected 侧为空 span；§8.1 样本逐项锁定（见 §3）。
- NFC 长度变化例：`test_nfc_composes_combining_marks`（规范化后 1 码点）与 report 测试 `test_report_keeps_raw_text_but_spans_index_normalised_text`（全角期望 `ＡＢＣ` 的 span `[2,3]` 索引规范化后文本）。

### 验收 6 — 缺失整行无 bbox 时输出 null；字符差异 bbox 为 OCR 文本行框 ✅ PASS

- `MISSING_LINE`：`bbox_xyxy: null`、`bbox_scope: null`、`confidence: null`（`test_missing_line_error_has_null_bbox`、`test_missing_line_has_null_bbox_and_whole_line_span`）。
- 字符差异与 `EXTRA_LINE` 的 bbox 均为其所在 OCR 行的完整框，从不合成单字框（四个 §8.1 样本测试均断言 `bbox_xyxy == [120, 180, 520, 252]`；`test_extra_line_error_carries_its_own_line_bbox`）。

### 验收 7 — 相同输入重复运行产生相同 JSON 语义结果 ✅ PASS

- 平局优先级固定：字符 DP 回溯“对角 → 缺失 → 额外”（`test_backtrack_prefers_diagonal_on_tie`：`ab`→`ba` 两条最优脚本均 2.00，固定选两次替换）；行对齐回溯“匹配/替换 → 缺失期望行 → 额外 OCR 行”。
- 测试：`test_repeated_runs_give_identical_ops`、`test_align_is_deterministic`、`test_same_input_produces_identical_json_semantics`（两次 `compare`/`build_report` 的 `json.dumps(sort_keys=True)` 逐字节相等）。
- 无集合、无随机、无时间、无网络参与比较路径。

## 3. §8.1 四个固定样本（固定 OCR line records，不依赖 OCR 引擎）

| 样本 | 期望 | OCR | 结果 |
|---|---|---|---|
| TP-S0-ZH-001 | `限时优惠` | `限时优` | 恰好 1 条 `MISSING_CHARACTER`，fragment `惠`，span `[3,4]`/`[3,3]`，bbox 指向 OCR 行，verdict `MISMATCH` |
| TP-S0-ZH-002 | `新品上市` | `新口上市` | 恰好 1 条 `SUBSTITUTION`，fragment `品`/`口`，span `[1,2]`，bbox 指向 OCR 行 |
| TP-S0-NUM-001 | `￥28.80` | `￥28.00` | 恰好 1 条 `NUMERIC_CHANGE`，fragment `8`/`0`，span `[4,5]`，bbox 指向 OCR 行 |
| TP-S0-ZH-003 | `新客立减20元` | `新客立减元` | 恰好 1 条 `MISSING_CHARACTER`，fragment `20`，span `[4,6]`/`[4,4]`（相邻缺失合并一条），bbox 指向 OCR 行 |

## 4. 关键算法判断（写在代码 docstring 中，此处摘要）

1. **歧义按对齐结果算，不按 DP 路径算。** 初版按每单元 top-2 路径代价算歧义时，`abc`/`xyz`（最优解唯一：缺失+额外）被误判歧义——两条最优路径只是 gap 顺序置换，配对集合相同。改为精确 second-best distinct alignment：(a) 逐个禁掉最优对齐的对角配对重算最优；(b) 对最优对齐未配对的行对，用前后向 DP 表算强制配对代价；代价 >0.70 的配对不作为竞争对齐。正确性由 225 组（`{"a","b"}` 长度 ≤3 的全部序列对）暴力枚举交叉验证：`total_cost`、`second_best_cost`、`ambiguous` 三项全部一致。
2. **gap 顺序的既定语义。** 回溯从终点倒推、优先级对角 > 缺失 > 额外，因此 trailing 的缺失+额外在时间顺序上表现为“额外在前、缺失在后”（`test_align_high_cost_pair_becomes_missing_plus_extra` 锁定）。配对集合不受影响；报告的错误顺序即对齐顺序。
3. **片段合并。** 相邻同类 op 合并为一个错误（`20` 缺失为一条），类型变化或中间有匹配即断开。span 按 DP 推进位置算，缺失/额外字符的对侧为空 span（插入点）。
4. **Verdict 规则（§7.6）。** 无可用 OCR 文本 → `OCR_FAILED` + `OCR_EMPTY` 警告，不发明 `MISSING_LINE`；歧义 → `REVIEW_REQUIRED` + 单条 `AMBIGUOUS_ALIGNMENT`，不输出确定性字符结论；有错无警告 → `MISMATCH`；有错有警告 / 仅有警告 → `REVIEW_REQUIRED`（含差异行低置信度情形）；无错无警告 → `MATCH`。低置信度阈值 0.65（等于阈值不算低）。
5. **报告文本的原始/规范化分工（§4.3.6）。** 顶层 `expected_text`/`recognized_text` 与 `ocr_lines[].text` 保留原始文本；错误级的 `expected_text`/`recognized_text` 为规范化行文本（span 索引它们）。
6. **`tool_version` 取 `"0.1.0"`**（IMPLEMENTATION_PLAN.md“产品版本初始目标：0.1.0”；PROJECT_BOOK.md §5.4 样例）。`pyproject.toml` 的 `1.0.0` 是打包版本，本任务无权改，差异登记为风险（见 §5）。
7. **未实现的警告码。** §5.3 列出的 `POSSIBLE_MULTI_COLUMN` 与 `ROTATED_TEXT_NOT_SUPPORTED` 在 §4/§7 中无检测规则，本任务不发明检测器、不发射（见 §5）。

## 5. 未完成项与风险

- **未完成项：无。** T004 任务卡的 6 个输出文件与 7 项验收标准全部完成；`tests/unit/test_core` 95 测试全部通过。
- **风险 1（需 T006 注意）：`tool_version` 与 `pyproject.toml` 版本不一致。** 报告写 `0.1.0`（计划书与 §5.4 样例），而 `pyproject.toml` 写 `1.0.0`。本任务未改 `pyproject.toml`（禁改）。建议 T009（CLI/schema）或终审时统一口径：若 `tool_version` 应跟随包版本，需由规格方裁定，不是 T004 自行改权重/常量。
- **风险 2（需 T006 Oracle 注意）：三处字面解读可能与独立 Oracle 有分歧。** (a) 混淆对集合仅取规格所列 6 对，小写 `o`/`0` 不算；(b) 标点替换要求两侧均为类别 P；(c) gap 顺序为额外在前、缺失在后。均已在代码 docstring 与测试中显式锁定；若 Oracle 取不同解读，应以项目书为准裁定，不得由施工者自行调参（失败回退条款）。
- **风险 3：`POSSIBLE_MULTI_COLUMN` / `ROTATED_TEXT_NOT_SUPPORTED` 警告无检测器。** §4/§7 未给规则，T004 不发射。若 S0 或后续任务需要，需先在规格中定义检测规则。
- **风险 4：`AMBIGUOUS_ALIGNMENT` 错误的字段形态是本任务的定义**（单条、行索引/span/bbox 均为 null、附全量规范化文本），规格只规定了类型与 verdict，未规定字段细节。S0 样本均不歧义，不影响 S0；若终审要求不同形态，属规格澄清，不是算法错误。
- **无 ADR。** 算法与 §4/§7 无冲突，未改任何权重/阈值，故无需提交 ADR。

## 6. 执行命令、退出码与测试结果

| 命令 | 退出码 |
|---|---:|
| `/home/hatch/workspace/p033-textproof/.venv/bin/python -m pytest tests/unit/test_core -q`（验收命令） | 0（95 passed，0.70s） |
| `/home/hatch/workspace/p033-textproof/.venv/bin/python -m pytest -q`（全量回归） | 0（167 passed，2 warnings，19.20s；167 = 72 旧 + 95 新） |

- 全量 2 个 warnings 均为 T002 旧测试的 Pillow `DecompressionBombWarning`（40,008,000 像素测试图），与 T004 无关。
- 测试日志：`test_stdout.log`、`test_stderr.log`（空）、`exit_codes.txt`。
- 依赖未变、未联网（比较核心不 import OCR/网络模块；测试只用合成文本与固定 OCR line records；零真人、零真实图片）。

## 7. 回退 commit

- 回退目标：`f90d577`（输入 commit；`git worktree` 隔离，master 未动）。
- 回退方式：删除 worktree `~/workspace/p033-textproof-t004` 与分支 `t004-core-compare`，或 `git revert cb1e3ba`（仅新增文件，revert 即清空）。
