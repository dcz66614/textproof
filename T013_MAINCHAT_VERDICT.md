# P033 TextProof — T013 主聊天裁决：PASS

- 裁决时间：2026-11-25 ~12:21 GMT
- 裁决对象：T013 集成线 `t013-fix`，HEAD `3643e42`（基线冻结候选 `ffe53ea`，即 T011 分支）
- 独立复审：新会话 `t013-review`，commit `fc25ff0`，`task_handoffs/T013/review/REVIEW_REPORT.md` 第 12 行 `FINAL_VERDICT: PASS`
- 复审报告与集成线 diff 核查：`t013-review` 相对 `t013-fix` 只多 92 行复审报告；`ffe53ea → 3643e42` 共 38 个文件，+2411/−148，与复审员声称一致。

## 主聊天亲自重跑（集成树 `~/workspace/p033-textproof-t013`，主树 `.venv`）

1. **全量 pytest：489 passed、0 failed、exit 0**（324.42s；日志 `/tmp/t013_mainchat_pytest.log`）
   —— 与构建者、复审员的 489 passed 完全一致；T011 的 2 项隐私失败已修复（含 `tests/privacy/test_no_persistence.py` 两项）。
2. **S0 `--force-live`（300 张 live OCR）：exit 0、S0 VERDICT: PASS**（753s；日志 `/tmp/t013_mainchat_s0.log`）
   —— 召回 100.00%（201/201）、clean FPR 0.00%（0/100）、schema 100%、CER 0.0008、IoU 最小 0.829 / 均值 0.938、parity 固定记录 300/300、[3L] live NUM-001 PASS、CPU-only；与 S0 裁决时（2026-11-25 ~07:20 GMT）的数值逐项一致。
3. **R-01 复现脚本**（T012 `review/repro_f01.py`，在 T013 树上重跑）：**exit 1，两案均不再复现**
   —— A 案 pair_cost 0.70、配对 [(0,0)]；B 案 ambiguous=False。

## 裁决：T013 PASS

- T012 的 31 项 findings 全部处置：P1 除 R-03 按裁决归属 T014 外全部关闭；P2/P3 全部已修或书面记录为非阻断，无静默丢弃。
- 禁令遵守：tool_version 仍为 0.1.0；隐私扫描范围未缩小、无白名单、无 curl；无 ￥→¥ 映射；未改测试预期、fixture PNG、manifest、S0 门槛、输入输出契约。`test_align_lines.py` 穷举 oracle 由 float 改为 Fraction 枚举（R-01 同一机理在 oracle 自身的修正），断言意图不变，复审判定可接受，主聊天认同。
- 注意事项（转 T014，不阻断本裁决）：
  1. **R-03（字典许可 UNVERIFIED）与 R-13（LICENSE/README/SECURITY 缺失）仍是 T014 发布前必修项**；许可解决前不得把字典随公开版本再分发。
  2. 边缘电池 14/26（S0 裁决时 13/26），诊断性质、非门禁项。
  3. R-09 保留字面 `S0 VERDICT: PASS`（`tests/offline/test_offline_namespace.py:151` 断言该字面串且禁改测试预期）。
  4. 复审报告自称复审时间“12:00–13:30 GMT”，与协调员 12:01 完成的时间线不符——应为笔误/模板时间，不影响结论（本裁决的全部关键结论均由主聊天亲自重跑证实，不依赖该报告的时间自述）。
  5. 集成 worktree 内 `task_handoffs/T006/` 三个 JSON 为 S0 重跑改动，属证据输出、非源码。

## 后续

- 合并 T011 + T013 链（`t013-fix`，含冻结候选 `ffe53ea`）进 main。
- 派 T014（冻结/打包；R-03 字典许可、R-13 发布文件为必修）。
- 之后：Drive 归档 → 终审（新对话，GPT-6.2 + Extra High）→ PASS → 公开上传 GitHub。
