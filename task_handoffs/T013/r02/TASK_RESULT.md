# T013-FIX-02 — TASK_RESULT（R-02 P1 + R-06/R-07/R-08 P2）

- TASK_ID：T013-FIX-02
- 分支：`t013-r02`（worktree `~/workspace/p033-textproof-t013-r02`，基线 `ffe53ea`，未合并）
- 修复 commit：`86fb673444ab5d144abfc7888dee2928a11a226f`
  （本文件与全量 pytest 日志为随后的第二个 commit，见文末）
- 审查依据：`~/workspace/p033-textproof-t011/review/REVIEW_FINDINGS.md` §2（R-02、R-06、R-07、R-08）
- 时间：2026-11-25 ~11:05–11:35 GMT

## R-02（P1）— 脚本位于隐私扫描树内，2 项隐私测试失败

- 根因：`tests/privacy/test_no_persistence.py` 的扫描范围是测试内定义的
  `src/**/*.py + scripts/*.py`。T011 新增的 `scripts/consistency_check.py`
  为调回环 API 而 `import socket/urllib` 并调用两处 `urllib.request.urlopen`，
  撞上 `test_forbidden_token_absent_from_sources[urlopen]` 与
  `test_no_network_client_import_in_sources`，全量 pytest 2 failed、436 passed。
  产品 `src/` 无网络代码，隐私承诺未破，是校验脚本位置问题。
- 修复（按主聊天 2026-11-25 ~10:40 裁决）：`git mv scripts/consistency_check.py`
  → `tests/consistency_check.py`（`tests/` 不在任何扫描范围内，且
  `tests/privacy/t010_privacy_helpers.py` 内已有同样用 urllib/socket 打回环的先例）。
  `REPO_ROOT = Path(__file__).resolve().parents[1]` 在新位置仍指向仓库根，无需改动；
  保留真实 HTTP 回环校验腿与严格的扫描门禁；否决的三条路（缩小扫描范围、curl 绕过、
  白名单）均未采用。同步更新两处 T011 文档命令路径：
  `task_handoffs/T011/TASK_RESULT.md:58` 与 `task_handoffs/T011/FULL_TEST_REPORT.md:83`
  （后者附注“T013 R-02 由 `scripts/` 移入 `tests/`”；两文件内其他
  `scripts/consistency_check.py` 提及为 T011 当时的历史记录，未改动）。
- 验证：`tests/privacy/test_no_persistence.py` 全过（24 项，含原失败的两项，
  单独重跑确认 `test_forbidden_token_absent_from_sources[urlopen]` 与
  `test_no_network_client_import_in_sources` 均为 PASSED）；
  `scripts/consistency_check.py` 已不存在。

## R-06（P2）— 一致性证据留存不足，ZH-002 的 IDENTICAL 无法独立复核

- 根因：两案共用同一 `workdir/cli-report.json`（后案覆盖前案），且 UI 侧共用同一下载
  文件名；`consistency_report.json` 只存 verdicts 与 `identical`，无完整报告或哈希。
  T011 留存物只有 TP-CLN-001 的 CLI 与 UI 两份报告，ZH-002 的三份报告与两案的 API
  报告均未留存。
- 修复（独立文件名 + SHA 双保险）：三路各写每案独立文件
  `api-<case>.json` / `cli-<case>.json` / `ui-<case>.json`（新 helper
  `_write_case_report`），并在 `consistency_report.json` 每案的 `reports` 字段记录
  每个文件的 SHA-256。比对逻辑本身未动。
- 验证：完整回环运行后独立复核——6 个文件全部存在，SHA-256 与 summary 记录逐一相符，
  每案三份报告解析后完全相等（见下）。

## R-07（P2）— `_http_post` / `_http_get` 接受任意 base，无回环约束

- 根因：两个 helper 是通用 HTTP 客户端，只凭调用方传入的 `base` 决定目标；当前唯一
  调用方 `LiveServer` 固定传 `http://127.0.0.1:{port}`，故当前无外发，但函数本身无任何
  回环校验。另就绪轮询用 bare `except Exception: pass` 静默吞掉全部异常，失败原因不可见。
- 修复：新增 `_require_loopback(base)`，两个 helper 入口断言
  `base.startswith("http://127.0.0.1:")`，否则 `AssertionError` 拒绝（断言在任何 socket
  打开之前触发）；就绪轮询改为记录后重试——首次失败打印到 stderr（一次），保留最近一次
  异常，60s 超时时 `RuntimeError` 附带最后一次错误。
- 验证：新增单元测试覆盖接受（`http://127.0.0.1:<port>`）与拒绝（localhost、0.0.0.0、
  https、127.0.0.1.evil.example、example.com、空串等 8 类），以及对真实本地回环服务器的
  GET/POST 往返；16 项新测试全部通过。

## R-08（P2）— 脚本把 fixture 文本写盘且无清理，并打印到 stdout

- 根因：`workdir/expected.txt` 与 `cli-report.json` 写盘后永不删除；stdout 打印
  `expected` / `drawn_text`；`--out` JSON 含期望文本与完整报告。内容是已提交的 S0 合成
  fixture 文本，但模式上与 §9“日志不得记录期望文本”相冲突，若日后被指向真实用户图片，
  明文会残留在 `consistency_work/` 与 `--out` JSON 中。
- 修复：跑完后在 `finally` 中删除共享 scratch——`workdir/expected.txt`、
  `workdir/cli-report.json`（遗留名）、`downloads/textproof-report.json`
  （新 helper `_cleanup_scratch`，失败时也清理；每案证据文件保留）；
  stdout 只打印 case id 与三路 verdict，不再打印 fixture 文本；
  docstring 增加声明：输出含 fixture 期望/绘制文本与完整 fixture 报告，
  不得用于真实用户图片。
- 验证：完整回环运行后检查——`expected.txt`、`cli-report.json`、
  `downloads/textproof-report.json` 均不存在；本次运行 stdout（存档于
  `task_handoffs/T013/consistency/stdout.log`）只含 case id 与 verdict；
  stderr 为空（服务器一次即就绪，无轮询失败记录）。

## 新增 / 改动测试与结果

- 新增 `tests/unit/test_consistency_check.py`（16 项，全部通过）：
  R-02 位置锁定（1）、回环接受（2）、回环拒绝（8）、helper 在连接前拒绝非回环（1）、
  真实回环服务器 GET/POST（1）、每案文件命名与 SHA（1）、scratch 清理保留证据（1）、
  docstring fixture 声明（1）。
- 改动：`tests/consistency_check.py`（由 `scripts/` 移入并重写上述四项修复）、
  两处 T011 文档命令路径。未改动任何现有测试预期、fixture PNG、manifest、S0 门槛、
  输入输出契约、扫描范围。

## 完整回环校验（真实 LiveServer + CLI + Chrome UI）

- 命令：`python tests/consistency_check.py --manifest tests/fixtures/s0/manifest.json --out task_handoffs/T013/consistency/consistency_report.json`
- 结果：exit 0，约 2 分钟；两案三路全部 IDENTICAL——
  `TP-S0-ZH-002` 三路 MISMATCH、`TP-CLN-001` 三路 MATCH；`all_identical: true`。
- 证据：`task_handoffs/T013/consistency/`（未覆盖 `task_handoffs/T011/` 历史证据）：
  `consistency_report.json`、`stdout.log`、`stderr.log`（空）、
  `consistency_work/` 下 6 份每案报告；SHA-256（独立复核与 summary 记录一致）：
  - TP-S0-ZH-002 api `d4901b6dfb87d3cedd2966705f75f447ac2238fa4a16927ed04aa3dd659813ed`
  - TP-S0-ZH-002 cli `5325a3f32f6fc05fc839ad0d859614ab0a7b6fba2961c5509d1d6150af2137c5`
  - TP-S0-ZH-002 ui `fde7633f755d339b19fa269eea8df433d2762f0f3384437f31a932f42bf50336`
  - TP-CLN-001 api `7ca9eba95db6b0e77ee12df05c23e3a4588fe2d1a3aec4aeadc3f73aeaa8d6a9`
  - TP-CLN-001 cli `ac028604ec5ebd37c019dab43d68850fa8b3a0b08dae03c1a893e1b220e35dba`
  - TP-CLN-001 ui `c92d398000545fc073c807ae42d43ea6f964be5774dacd4c757961efa9907b94`

## 全量 pytest

- 命令：`TMPDIR=$PWD/tmp ~/workspace/p033-textproof/.venv/bin/python -m pytest -q -p no:cacheprovider`
- 结果：**454 passed，2 warnings，exit 0，887.73s（14:47）**。
  计数说明：T011 基线 438 项（436 passed + 2 failed）+ 本任务新增 16 项 = 454，
  原失败的两项现已通过，无其他失败。
  2 条 warnings 均为既有 `tests/unit/test_image_loader.py` 的 Pillow
  `DecompressionBombWarning`（40,008,000 像素测试图），与本次改动无关。
- 日志：`task_handoffs/T013/r02/full_pytest.log`。
- 未改动项：`tests/e2e/evidence/`（全量跑产生的 e2e 截图/下载，276K，未跟踪、未提交，
  非本任务文件）。

## 修复 commit

- 代码与证据 commit：`86fb673444ab5d144abfc7888dee2928a11a226f`
  （T013 R-02/R-06/R-07/R-08：移动脚本、回环断言、每案证据、清理 scratch）
- 本文件与全量 pytest 日志随同一分支的后续 commit 提交（`git log --oneline t013-r02` 可查）。
