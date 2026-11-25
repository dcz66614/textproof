# T011 主聊天裁决 — 2026-11-25 ~10:40 GMT

## 结论：T011 不通过（NOT PASS）

- 构建者报告（`task_handoffs/T011/TASK_RESULT.md`）称全量 pytest **438 passed、0 failed**，6 项验收全部 PASS。
- **主聊天亲自重跑**（`~/workspace/p033-textproof-t011`，主工作树 `.venv`，`TMPDIR` 指到 worktree 内 `tmp/`）：
  **`2 failed, 436 passed, 2 warnings in 205.11s`**，退出码非 0。
- 构建者的 438-pass 结论在当前树上**不可复现**。可能原因：构建者在最后一次修改
  `scripts/consistency_check.py` 之后没有重跑全量套件（或跑的不是最终树）。
  无论原因，TASK_RESULT 的验收 1 结论作废，以主聊天重跑为准。

## 失败详情（已定位到行）

1. `tests/privacy/test_no_persistence.py::test_forbidden_token_absent_from_sources[urlopen]`
   — token `urlopen` 出现在 `scripts/consistency_check.py:77`、`:86`。
2. `tests/privacy/test_no_persistence.py::test_no_network_client_import_in_sources`
   — `scripts/consistency_check.py:40:import socket`、`:45:import urllib.error`、`:46:import urllib.request`。

根因：T011 新增的 `scripts/consistency_check.py` 为测 API/CLI/UI 一致性，
用 `urllib.request.urlopen` 访问本机回环 API；而 T010 的隐私测试扫描
`src/**/*.py` + `scripts/*.py`，禁止 `urlopen` token 与任何
`requests|httpx|urllib|http.client|socket` 导入。产品代码 `src/` 本身无网络
代码，隐私承诺未破；冲突在**校验脚本的位置**，不在产品。

## 其他验收项（未亲自重跑，以构建者日志 + 协调员复核为准）

- 验收 2（300 样本 SHA 一致）、3（召回 100%、分类型各 100%、clean FPR 0%、CER 0.0008）、
  4（P95 3.817s ≤5s）、5（三路 JSON 一致）、6（S0 PASS、parity 300/300）：构建者日志退出码均为 0；
  协调员在集成树上亲自重跑 S0 也为 PASS（exit 0，300 张 live OCR）。
- 边缘电池 13/26（诊断）与 T006 相同，含已知真实缺陷 F-01；不属冻结门禁。
- **主聊天未亲自重跑 S0 与性能测量**，以上两项以他人日志为准，终审时以 T012/T013 的独立复核为准。

## 裁决：修复路径与顺序

**修复方向（主聊天定，不再问 Sam）：把回环客户端校验脚本移出被扫描树。**
`scripts/consistency_check.py` 从 `scripts/` 移到 `tests/`（不在 T010 扫描的
`src/**/*.py` + `scripts/*.py` 范围内），保留真实 HTTP 回环校验腿与严格的扫描门禁。
明确否决的路径：
- （a）缩小扫描范围（只扫 `src/`）—— 等于改门禁定义，需 ADR 且削弱 fail-closed 保证；
- （b）改写脚本绕开 token/导入检查（如 subprocess curl）—— 绕过测试字面、违背其本意；
- （c）在测试里加白名单 —— 改测试预期，T011 计划明文禁止。

**顺序：先 T012 审，后 T013 修。** 按冻结计划链 T011 → T012 → T013：
- T011 不合并（失败 commit `ffe53ea` 留在分支 `t011-full-regression`，不进 main）。
- T012 独立审查冻结候选 commit `ffe53ea`（全新会话，不改代码），须独立复核上述 2 个
  隐私失败与 F-01，并按计划产出 `REVIEW_FINDINGS.md`。
- T013 再统一修复：2 个隐私失败（按本裁决的移位方案）+ F-01（align_lines 精确十进制比较
  + 回归测试）+ T012 的全部 findings；修复后由独立复审会话验证。
- T011 计划的失败回退（“真实失败转入 T013”）与此一致；不在 T011 内改测试预期。

## 记录

- T007–T010 已合并入 main（HEAD `b0885dd`），不受影响。
- 协调员 #3（T007–T014）已结束；T012 派新协调员。
