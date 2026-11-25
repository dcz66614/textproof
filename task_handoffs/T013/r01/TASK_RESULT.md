# T013-FIX-01 (R-01) — TASK_RESULT

- TASK_ID: T013-FIX-01 (R-01, P1 必修)
- 冻结基线：`ffe53ea1fb7e1d31f536abd732c258ffc50aae56`（分支 `t011-full-regression`）
- 工作树：`~/workspace/p033-textproof-t013-r01`，分支 `t013-r01`
- 日期：2026-11-25 ~11:02–11:20 GMT

## 根因

规格 §4.4/§7.2 冻结的是精确十进制算术，但 `align_lines` / `weighted_edit`
的 DP 用二进制浮点累加 0.65 / 0.50 / 1.25 等十进制小数：

- A 案（0.70 配对阈值）：40 字符行（20 个混淆替换 0.65 + 12 个数字替换
  1.25 + 8 个相同字符），精确加权距离 28、精确配对代价 28/40 = 0.70，
  应允许配对；实测浮点距离 28.000000000000004、代价 0.7000000000000001
  > 0.70，`pair_cost` 返回 inf，行被拆为 MISSING_LINE + EXTRA_LINE。
- B 案（0.05 歧义边界）：单字符 `O`→`0`，最优 0.65、次优 0.70，精确差
  恰好 0.05，不应判歧义；实测浮点差 0.04999999999999993 < 0.05，
  生产误判 `ambiguous=True`（Oracle 用 Fraction 判得正确）。
- 机理：DP 按不同求和顺序累积舍入误差；回溯的 `==` 只是复算同一
  表达式，无法纠正。

复现（修复前，工作树内 `review/repro_f01.py`）：exit 0，两案均复现。
修复后同一脚本：exit 1，两案均符合精确预期（pair_cost 0.7、pairs
[(0,0)]；ambiguous False）。

## 修复

修复 commit：`d26adcc89ac558cce6bf3b473983f5b31a7d4f73`（分支 `t013-r01`，
父 commit `ffe53ea`；本文件以单独 commit 记在该修复 commit 之上）

方法：**Fraction 精确算术**（非 epsilon 比较）——所有内部代价比较与
歧义判定改用精确十进制值的 `Fraction`，公共 API 仍返回 `float`
（`float(Fraction("0.65"))` 与字面量 `0.65` 逐位相同），调用方无感知，
只有被误判的决策被纠正。

- `src/textproof/core/weighted_edit.py`
  - 新增 `_FRACTION_*` 精确常量（由各 float 常量的十进制字符串构造，
    与冻结 float 常量成对、不会漂移）与 `_substitution_cost_fraction`。
  - 新增 `_dp_table_fraction`（精确 DP，唯一事实来源）与
    `_weighted_edit_distance_fraction`；旧 `_dp_table` 改为其 float 视图。
  - `weighted_edit_distance` / `weighted_edit_ops` 改走精确表；回溯
    `==` 改为精确 `Fraction` 比较。
- `src/textproof/core/align_lines.py`
  - 新增 `_GAP_PENALTY` / `_AMBIGUITY_MARGIN` /
    `_HIGH_COST_PAIR_THRESHOLD` 精确常量（`Fraction(str(...))`）。
  - 新增 `_pair_cost_fraction`（精确阈值比较；恰好 0.70 允许，`None`
    表示禁用）；`pair_cost` 改为其 float 包装（inf 语义不变）。
  - `_pair_cost_matrix` 返回 `Fraction | None`（`None` = 禁用对）；
    `_best_table` / `_suffix_best_table` 全表精确 `Fraction`
    （gap 步总可达，故表恒有限，无需 inf 哨兵）。
  - 回溯三处 `==` 改为精确比较；第二最优改用 `Fraction | None`
    （`None` = 无竞争对齐，即无穷）；歧义判定为精确
    `(second - total) < 1/20`。
- 未改动：冻结常量值、tool_version、输入输出契约、manifest、S0 门槛、
  规格；未加 ￥→¥ 映射；未碰其他 finding 的文件。

附带修正（同一 R-01 机理，测试 oracle 自身）：穷举小 case 的暴力对照
`_brute_force_two_best`（`tests/unit/test_core/test_align_lines.py`）
原用 float 累加，3 个 gap 求和得 1.0499999999999998 而非 1.05，与修复后
的精确生产值冲突；改为精确 `Fraction` 枚举，断言形式与意图不变
（生产值须与独立枚举一致）。

## 新增回归测试与结果

`tests/unit/test_core/test_align_lines.py`（3 项）：

- `test_pair_cost_exactly_070_with_confusion_and_digit_substitutions`
  （R-01 A 案）：pair_cost == 0.70；`align_lines` 配对 [(0, 0)]，
  total 0.70；第二最优亦 0.70（配对与缺失+额外平局），ambiguous True。
- `test_ambiguity_margin_exactly_005_is_not_ambiguous`（R-01 B 案）：
  total 0.65、second 0.70、ambiguous False。
- `test_gap_penalties_sum_to_exact_decimal`：3 个 gap 精确合计 1.05。

`tests/unit/test_core/test_weighted_edit.py`（1 项）：

- `test_weighted_edit_distance_exact_decimal_accumulation`：
  20×0.65 + 12×1.25 精确等于 28.0；回溯仍走 32 步全对角最优路径。

 targeted 运行：
`pytest tests/unit/test_core/test_align_lines.py
tests/unit/test_core/test_weighted_edit.py tests/unit/test_core/test_report.py
tests/unit/test_core/test_classify.py` → **77 passed**。

## 全量 pytest 结果

命令：`TMPDIR=$PWD/tmp .venv/bin/python -m pytest -q -p no:cacheprovider`
（工作树根目录；`/tmp` 为 512M tmpfs，故 TMPDIR 指到工作树内 `tmp/`）

结果：**2 failed, 440 passed, 2 warnings, 871.82s (0:14:31)**。

- 2 项失败与基线 `ffe53ea` 完全相同，均为 R-02（属 T013-FIX-02 职责，
  不属本任务、未碰）：
  - `tests/privacy/test_no_persistence.py::test_forbidden_token_absent_from_sources[urlopen]`
  - `tests/privacy/test_no_persistence.py::test_no_network_client_import_in_sources`
  （`scripts/consistency_check.py` 的 `urlopen` / `socket` import
  撞上 T010 隐私扫描；产品 `src/` 无网络代码。）
- 440 passed = 基线 436 passed + 本任务新增 4 项回归测试；无其他失败。
- 耗时 871.82s 远高于基线 226.79s，原因是 VM 当时负载极高
  （load ~21：SpanRelay 并行任务 + 另一 T013 worktree 同时跑全量），
  非本次改动所致（Fraction DP 只影响短行 DP，OCR 占主导）。
