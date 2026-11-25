# T013-FIX-05 — R-09 + R-10 + R-11（S0 门禁脚本）TASK_RESULT

- TASK_ID：T013-FIX-05
- 分支：`t013-r09`（worktree `~/workspace/p033-textproof-t013-r09`）
- 基线：`ffe53ea1fb7e1d31f536abd732c258ffc50aae56`（T011 冻结候选）
- 范围：`scripts/verify_s0.py`、`scripts/compute_s0_metrics.py`（仅注释）、
  `S0_REPORT.md`（仅一处标注）、新增 `tests/unit/test_verify_s0.py`
- 未碰：`tests/s0/test_s0_gate.py`（锁定断言 untouched）、`normalize.py`
  （无 ￥→¥ 映射）、fixture PNG、manifest、S0 门槛、输入输出契约、
  `tool_version`、其他 finding 的文件

## R-09（P2）：`S0 VERDICT: PASS` 未覆盖 §8.4 全部硬门

- 根因：`verify_s0.py` 的 `all_pass` 只合取脚本内 7 项（manifest、Oracle
  独立性、parity、固定四样本、live 指标、CPU-only provider、证据输出），
  不含 §8.4 item 8（`independent_verify.py`，独立脚本）与 item 7 的网络
  一半（只靠 `unshare -n` 下运行证明）。但打印的 `S0 VERDICT: PASS`
  无限定，读者只看脚本输出会误以为 §8.4 已全部成立。
- 修复：选 (a) 限定表述。新增首行 `VERIFY_S0 ITEMS: PASS
  (script-checked items only)`；`S0 VERDICT` 行改为
  `S0 VERDICT: PASS (script-checked items only; NOT the full §8.4
  verdict — see NOTE)`；NOTE 重写，逐项列出脚本覆盖项与未覆盖项
  （item 8 独立脚本 + item 7 网络一半须 `unshare -n` 运行证明），并指明
  完整 §8.4 裁决在 `S0_REPORT.md` / `S0_MAINCHAT_VERDICT.md`。
  模块 docstring 同步写明 verdict 的限定范围。7 项本身的通过/失败语义
  未变（判定代码 untouched）。
- 保留字面 `S0 VERDICT: PASS` 的原因（有意为之，非遗漏）：
  `tests/offline/test_offline_namespace.py:151` 断言该字面串出现在
  `verify_s0.py` 输出中，且任务禁改现有测试预期；纯改名会使该 T010
  测试失败。限定词与原串同行，误读空间已消除。如协调员希望彻底改名，
  须由该测试的 owner 同步更新 `:151`（不在本次可改文件范围内）。

## R-10（P2）：`gate_pass` 未执行 §8.3 运行时间门槛

- 根因：`gate_pass` 只判 5 项（召回 ≥95%/每类 ≥90%、clean FPR ≤8%、
  schema 100%、IoU below_0.80==0），无 timing 分支；且 300 张 fixture
  全是 1200×480，不是 §8.3 规定的 1920×1080——在 1200×480 的 P95 上
  硬加 ≤5s 判定测的是错误尺寸。
- 修复：未加任何 timing 判定。`gate_pass` 增加注释，说明 §8.3 运行时间
  门槛（1920×1080 预热 P95 ≤5s）有意不在此判定、原因（fixture 尺寸不符，
  1200×480 P95 不是规格尺寸下的测量），以及该门槛由 T011 性能报告判定
  （实测 P95 3.817s，PASS）。`S0_REPORT.md` §5 计时段只加一处标注：
  “T011 性能报告实测：1920×1080 预热后 P95 3.817s ≤ 5s，PASS（见
  PERFORMANCE_REPORT.md）；§8.3 运行时间门槛由 T011 性能报告判定，
  不属于 verify_s0.py。”其余结果未动。

## R-11（P2，已裁决事项的追踪）：live NUM-001 的 2 条错误与 §8.1 字面不符

- 根因：live 路径 TP-S0-NUM-001 产出 2 条错误（SUBSTITUTION ￥→¥ +
  NUMERIC_CHANGE 8→0），与 §8.1“恰好 1 条 NUMERIC_CHANGE”字面不符；
  但 §8.1 计数修饰的是带类型的错误（主聊天 S0 裁决 §6(a) 已采纳按类型
  计数读法，分歧点书面留给终审）。门禁此前只查固定记录路径，live 行为
  不在门禁检查内。￥（U+FFE5）不在 §4.3 全角 ASCII 映射范围内，不映射
  是字面合规——不得为消灭该条错误而加映射。
- 修复：选 (b)。`verify_s0.py` 新增 `check_live_num_001(s0_live)`，
  在 main() 中以 `[3L]` 项接入 `all_pass`（即影响 exit code）：
  live 结果中 TP-S0-NUM-001 必须恰好 1 条 NUMERIC_CHANGE
  （fragment `8`/`0`、span `[4,5]`/`[4,5]`），至多 1 条额外错误且必须
  是已知 SUBSTITUTION（`￥`→`¥`、span `[0,1]`/`[0,1]`），verdict 须为
  MISMATCH。额外 SUBSTITUTION 是“允许”而非“要求”（live OCR 若读对
  ￥，单条 NUMERIC_CHANGE 也通过）。该断言只读 live 结果
  （`metrics["s0_live"]`）；固定记录路径（item 3）仍要求恰好 1 条错误，
  未变。`normalize.py` 与 §4.3 未动，无 ￥→¥ 映射。

## 验证

- 新增回归测试 `tests/unit/test_verify_s0.py`：**9 passed**（2.89s）
  - `test_live_num_001_two_errors_pass`（2 条错误通过）
  - `test_live_num_001_single_numeric_only_pass`（单条 NUMERIC_CHANGE 通过）
  - `test_live_num_001_three_errors_fail`（3 条错误失败）
  - `test_live_num_001_two_numeric_fail`（2 条 NUMERIC_CHANGE 失败）
  - `test_live_num_001_wrong_extra_error_fail`（非 ￥→¥ 的额外错误失败）
  - `test_live_num_001_wrong_numeric_span_fail`（NUMERIC_CHANGE span 错误失败）
  - `test_live_num_001_missing_entry_fail`（缺失样本 fail-closed）
  - `test_live_num_001_wrong_verdict_fail`（verdict 非 MISMATCH 失败）
  - `test_gate_pass_does_not_judge_timing_p95`（R-10：P95=99.0 与 3.817 均通过 gate）
- `scripts/verify_s0.py` 固定记录模式（缓存 live 结果，tmp out-dir）：
  exit 0；7 项原语义不变（parity 300/300、召回 100%、FPR 0%、schema
  100%、IoU 最小 0.829、四样本固定路径各 1 条错误）；新增 `[3L] live
  TP-S0-NUM-001: PASS`；输出为限定后的 verdict + NOTE。
- 反向控制（篡改缓存副本使 NUM-001 变成 3 条错误）：`[3L] FAIL`、
  verdict FAIL、exit 1——新断言确实能拦住门禁。
- 全量 pytest：`TMPDIR=$PWD/tmp ... -m pytest -q -p no:cacheprovider`，
  **2 failed, 445 passed, 2 warnings, 945.68s, exit 1**。2 项失败是已知
  R-02（`tests/privacy/test_no_persistence.py` 的 urlopen 两项，属另一
  T013 修复项，不在本任务范围）；基线为 2 failed、436 passed，本次
  445 passed = 436 + 9 个新增测试，零新增失败。全程耗时 15:45（VM
  并行负载高，非环境失败）。

## 提交

- 修复 commit：`9b54c0f484e47ffa1f270d24176e86662c75a319`（分支 `t013-r09`，未合并）
- 未跑 `--force-live` 全量（11 分钟），按任务要求留给协调员合并后跑。
- `tests/e2e/evidence/` 为全量 pytest 运行中 e2e 测试生成的产物，未提交。
