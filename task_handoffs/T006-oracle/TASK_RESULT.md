# TASK_RESULT — T006-oracle（P033 TextProof 独立 Oracle）

## 任务 ID

T006-oracle：S0 门禁独立 Oracle 实现（仅 Oracle + 自测；`verify_s0.py` /
`independent_verify.py` / `S0_REPORT.md` 不在本次任务范围内，未做）。

## 输入 / 输出

- 输入 commit：`1b425ce`（T001–T005 已合入，全量 174 测试通过时的 HEAD）
- 输出 commit（代码）：`8f89548`（`oracle/` + `tests/oracle/`，分支 `t006-oracle`）
- Handoff 包提交：见交付汇报（本文件无法包含自身的提交哈希；包内容与代码提交一致，见下）
- 工作目录（worktree）：`~/workspace/p033-textproof-oracle`（分支 `t006-oracle`，自 `1b425ce` 建）
- 回退 commit：`1b425ce`（删除分支 `t006-oracle` / 丢弃 worktree 即可回退；主工作目录未动）

## 实际改动文件

```
oracle/__init__.py
oracle/reference_compare.py
tests/oracle/test_reference_compare.py
task_handoffs/T006-oracle/TASK_RESULT.md
task_handoffs/T006-oracle/changed_files.txt
task_handoffs/T006-oracle/git_diff.patch
task_handoffs/T006-oracle/test_commands.txt
task_handoffs/T006-oracle/test_stdout.log
task_handoffs/T006-oracle/test_stderr.log
task_handoffs/T006-oracle/exit_codes.txt
task_handoffs/T006-oracle/SHA256SUMS.txt
```

## 禁止文件未修改证明

- `git diff --name-only 1b425ce 8f89548` 仅含上述 3 个代码/测试文件。
- 四份规格文件（`PROJECT_BOOK.md` / `PROJECT_BOOK.docx` /
  `IMPLEMENTATION_PLAN.md` / `IMPLEMENTATION_PLAN.docx`）、
  `requirements.lock`、`pyproject.toml` 均未修改；未碰其他任务的文件。
- 主工作目录 `~/workspace/p033-textproof`（master）未动：任务开始前已有的
  `M SPECS_VERIFICATION.md` 与 `?? task_handoffs/T001/` 状态在任务结束时原样存在，
  未新增任何改动。
- 独立性：只读了任务允许的材料（项目书 §4.3–§4.6、§5、§7、§8.1；
  实施计划 §5.1 与 T006 卡；`tests/fixtures/s0/manifest.json` 与
  `expected_output.json`；T002 `contracts.py` 与 T003 `rapidocr_adapter.py`
  的字段形态）。未读 `src/textproof/core/` 下任何文件、未读
  `p033-textproof-t004` worktree、未读 `tests/unit/test_core/`、
  未读 `task_handoffs/T004/`。`oracle/reference_compare.py` 仅用标准库
  （`re`、`unicodedata`、`fractions`、`typing`），不 import `textproof`。
  自测 `test_oracle_is_independent` 以源码 grep + AST 导入检查 +
  全新子进程导入检查三重断言这一点。
- 说明：任务中途一次 repo-wide grep（查 `LOW_OCR_CONFIDENCE` 出现位置）
  的输出命中了禁读路径 `tests/unit/test_core/test_report.py` 的一行。
  该文件从未被打开，其内容未被用作实现依据；警告对象形态的决定
  （`{"code", ...}`）仅依据项目书 §5.3 本身（警告枚举是 code 枚举）。
  特此记录，供复核者知悉。

## 实现概要

`oracle/reference_compare.py`（纯比较，不读图、不调 OCR）：

- §4.3 规范化：NFC、CRLF/CR→LF、全角 ASCII（U+FF01–U+FF5E）→半角、
  全角空格→空格、每行 strip + 空白折叠、大小写敏感、标点保留；
  字符索引为规范化后 Unicode 码点、左闭右开。
- §4.4/§7.2 行对齐：全局序列 DP，配对代价为归一化加权编辑距离，
  gap 0.35；配对代价 > 0.70 不配对（等价于 DP 自然选择，见下）；
  平局优先级 配对 > 缺失期望行 > 额外 OCR 行；歧义用“不同配对集合的
  最优与次优代价差 < 0.05”判定（精确算法：禁配对边重跑 DP +
  前向/后向表定价含非最优配对的对齐）。
- §4.5/§7.3 字符 DP：整数百分制精确计算，权重 0 / 0.65 / 0.50 /
  1.25 / 1.00 / 1.00；回溯优先级 对角 > 缺失 > 额外；连续同类操作
  合并为一条错误记录（ZH-003 的 "20" 合并为 1 条）。
- §7.4：双 Nd 数字替换 → `NUMERIC_CHANGE`；数字缺失/额外仍为
  `MISSING_CHARACTER` / `EXTRA_CHARACTER`。
- §7.5：字符差异 bbox 取 OCR 行框；`MISSING_LINE` bbox 为 null；
  不伪造单字框。
- §7.6：行置信度 < 0.65 逐行加 `LOW_OCR_CONFIDENCE` 警告；有警告
  或歧义时 verdict 至少 `REVIEW_REQUIRED`；无可用 OCR 文本且期望
  非空 → `OCR_FAILED` + `OCR_EMPTY` 警告；无差异无警告 → `MATCH`。
- 阅读顺序：按 OCR 框垂直中心、再 x1、再 `source_order` 重排；
  `line_index` 为重排后的零基索引。

## 执行命令与退出码

工作目录 `~/workspace/p033-textproof-oracle`；
Python：`/home/hatch/workspace/p033-textproof/.venv/bin/python`（Python 3.12，锁依赖）。
完整命令见 `test_commands.txt`；退出码见 `exit_codes.txt`。

| # | 命令 | 退出码 | 结果 |
|---|---|---:|---|
| 1 | 验收：`pytest tests/oracle/test_reference_compare.py -q` | 0 | 43 passed |
| 2 | `pytest tests/unit -q`（回归检查） | 0 | 155 passed，2 warnings |
| 3 | `pytest tests/unit/test_core tests/oracle/test_reference_compare.py -q`（core 先导入顺序） | 0 | 138 passed |
| 4 | 全量：`pytest -q`（修复后） | 0 | 217 passed，2 warnings |
| 5 | JSON 序列化抽查（ZH-001 报告） | 0 | 可序列化，verdict MISMATCH |

验收日志：`test_stdout.log`（`43 passed in 0.39s`）、`test_stderr.log`（空）。

## 测试结果（自测内容）

`tests/oracle/test_reference_compare.py`，43 个测试，全部通过：

- S0 golden（4 个）：ZH-001 恰好 1 条 `MISSING_CHARACTER`（惠，[3,4]）、
  ZH-002 恰好 1 条 `SUBSTITUTION`（品/口，[1,2]）、NUM-001 恰好 1 条
  `NUMERIC_CHANGE`（8/0，[4,5]）、ZH-003 恰好 1 条 `MISSING_CHARACTER`
  （20，[4,6]）；逐项核对类型、片段、span、bbox（= manifest target_region）、
  verdict `MISMATCH`、summary；并先核对 manifest 与 expected_output.json
  两份冻结文件彼此一致。
- 300 样本普查：每张 fixture 以 drawn text 作单行固定 OCR 行
  （框取 target_region），verdict 与错误类型多重集与 expected_output.json
  全 300 项一致（span 不断言：重复字符时等价最小对齐的位置可互换）。
- 规范化：全角 ASCII/空格、NFC（e + U+0301）、CRLF/CR、空白折叠、
  大小写敏感、标点保留、全角 ￥ 不映射、空串/尾换行的字面分行。
- 权重：混淆对 0.65（且仍产生错误记录）、标点 0.50、数字 1.25、
  其他 1.00；小写 o/0、s/5 不在混淆对内。
- 对齐/歧义边界：高代价 > 0.70 走缺失+额外行；缺失行 bbox null、
  `bbox_scope: "none"`；额外行保留 OCR 框；阅读顺序按框重排；
  重复行歧义（代价差 0）；边界 0.05（差恰好 0.05 不歧义，差 0 歧义）。
- 置信度/verdict：0.5 行 → 警告 + `REVIEW_REQUIRED`；无差异低置信
  仍 `REVIEW_REQUIRED`；阈值严格小于（0.65 无警告，0.64 有）；
  空 OCR → `OCR_FAILED` + `OCR_EMPTY`；空期望 + 空 OCR → `MATCH`。
- 独立性：源码无 `textproof` 导入、仅标准库导入、全新子进程导入
  Oracle 不引入 `textproof`。

过程记录：首次全量运行时 216 通过 + 1 失败，失败是我自测的
`test_oracle_is_independent`——它断言进程内 `textproof.core not in
sys.modules`，全量运行时其他测试模块先导入了生产代码，属测试本身的
顺序依赖缺陷，与 Oracle 无关。已改为全新子进程断言，修复后全量
217 通过（exit 0）。另有两次长 exec（全量套件）出现运行时“审批超时”
提示，但命令实际已执行并返回了完整输出与退出码（以实际退出码为准，
未重复执行；按指示向父 agent 报告此提示）。

## 与规格字面有歧义的三处取值（已选解读）

1. **混淆对集合**（§4.5 “如 O/0、I/1/l、S/5、B/8”——“如”表示举例，
   未穷尽）：只用字面列出的字符，`O/0`、`I/1`、`I/l`、`1/l`、`S/5`、
   `B/8`。小写 `o/0`、`s/5`、`b/8` 不算混淆对（权重 1.00）。
2. **歧义的“两条最优路径”**（§4.4）：按“不同对齐”理解，对齐由其
   配对集合决定。仅交换相邻删除/插入步骤的两条 DP 路径是同一对齐，
   不计为两条路径；否则任何“缺失行 + 额外行”情形都会因 del/ins
   顺序调换而被判歧义。次优代价取配对集合不同的最优对齐（实现：
   对最优配对逐一禁边重跑 DP，并用前向/后向表定价所有含非最优配对
   的对齐，取最小）。
3. **行分行字面规则**（§4.3 未写空串/尾换行；`contracts.py` 称
   “LF-separated segments”）：按字面 `"\n"` 切分，`""` 为 1 个空行，
   尾换行产生 1 个尾空行；空期望 + 空 OCR 按“无差异无警告”判 `MATCH`。

其余取值见 `oracle/reference_compare.py` 模块 docstring（共 13 条，
含：标点替换要求双侧均为标点；> 0.70 禁配对与 DP 自然选择等价；
`AMBIGUOUS_ALIGNMENT` 放在 `errors` 且歧义时不输出确定性字符结论；
同类连续操作合并、异类替换拆分；`MISSING_LINE` 用 `bbox_scope: "none"`；
警告为 `{"code", "message", ...}` 对象；`image` 块恒在、未知字段为 null；
`tool_version` 默认 `"0.1.0"`（§5.4 样例值）；阅读顺序重排规则；
￥（U+FFE5，非 ASCII）不映射）。

## 未完成项

- `verify_s0.py`、`scripts/independent_verify.py`、`S0_REPORT.md`
  （T006 卡所列其他输出）：不在本次任务范围内，未做。S0 门禁的
  生产实现 ↔ Oracle parity 比对、300 样本指标、网络封锁证据等
  需由后续 T006 集成工作完成。
- 未跑真实 OCR：Oracle 只做纯比较，S0 样本的 golden 输入是按任务
  要求用图绘文本 + manifest target_region 框构造的固定 OCR 行记录，
  不是 RapidOCR 实测输出。

## 风险

- 警告对象形态、错行 `bbox_scope` 取值、`AMBIGUOUS_ALIGNMENT`
  放在 `errors` 还是 `warnings`、歧义时是否压制全部行级结论，
  均为规格未写明的自选解读；若生产实现选了不同形态，parity
  比对时需以冻结 schema（T009）为准再对齐。
- 300 普查未断言 span：重复字符场景下等价最小对齐的 span 位置
  可能与生产实现不同，这是算法固有自由度，不是错误；parity
  应以 verdict + 错误类型为准、span 逐例复核。
- Oracle 与生产实现的 parity 尚未跑（属 S0 集成步骤，不在本任务内）；
  本任务只证明 Oracle 自身符合规格字面。
- 两次长 exec 出现运行时“审批超时”提示（命令实际已执行完毕，
  输出与退出码完整）；若父 agent 需要，可复核该提示的来源。
