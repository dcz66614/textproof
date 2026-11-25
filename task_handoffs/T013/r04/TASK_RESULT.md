# T013-FIX-03 — R-04（P1）修复结果

- TASK_ID：T013-FIX-03（R-04，P1 必修）
- 审查来源：`~/workspace/p033-textproof-t011/review/REVIEW_FINDINGS.md` §2 R-04
- 冻结候选：`ffe53ea`（分支 `t011-full-regression`）
- 工作分支：`t013-r04`（worktree `~/workspace/p033-textproof-t013-r04`）
- 修复 commit：`09d101c`（另有本文件交接 commit，见下）
- 日期：2026-11-25 ~11:00–11:25 GMT

## 根因

资产缺失时，`get_ocr_adapter()`（`src/textproof/api/routes.py:267`，首次请求懒加载）
在 `run_check` 的 OCR_FAILED 捕获范围之外（该范围只包 `recognize()`），
`FileNotFoundError` 冒泡到 `check()` 的通用 `except Exception`，
经 `logger.exception` 把含绝对路径的 traceback 写进日志。
两处同时有问题：

1. `src/textproof/ocr/rapidocr_adapter.py:211,217–218,222,228–229`（`_verify_assets`）：
   四条资产缺失/哈希不符报错消息内含绝对资产路径 `{path}` /
   `{self.dict_path}`。
2. `src/textproof/api/routes.py`：引擎构造失败无 OCR_FAILED 映射，
   直通通用 handler 的 `logger.exception`（含 traceback）。

审查员已在 /tmp 独立副本上运行时证实（基线行为）：隐藏一个模型文件后
真实 `/check` 得 HTTP 500 INTERNAL_ERROR，server.log 出现
`FileNotFoundError: OCR model asset missing: /tmp/f04-probe/assets/ocr/models/PP-OCRv6_det_small.onnx. Refusing to download at runtime (offline-only operation).`

## 修复（(a) + (b) 组合，最小改动）

- (a) `src/textproof/ocr/rapidocr_adapter.py`（`_verify_assets`）：四条报错消息
  只用文件名（`PP-OCRv6_det_small.onnx` 等 / `DICT_FILE[0]`），不再插值绝对路径。
  纵深防御：即使该异常从别的路径逃逸，消息本身也不含绝对路径。
- (b) `src/textproof/api/routes.py`（`run_check`）：把 `get_ocr_adapter()` 包进
  `try/except (FileNotFoundError, ValueError, RuntimeError)`，映射为与
  `recognize()` 失败完全相同的 `ApiError`（500 `OCR_FAILED` /
  `ocr_engine_error`），只记 `logger.error("OCR failed: %s", type(exc).__name__)`
  ——不记异常消息、不记 traceback。`OCRAdapterError` 是 `RuntimeError` 子类，
  已被覆盖。
- 未动：`src/textproof/api/app.py`（(b) 已使资产缺失不再到达通用 handler，
  无需动）、`check()` 通用 handler、CLI（CLI 只打印稳定错误码，本来就不含路径）、
  `tool_version`、manifest、S0 门槛、输入输出契约、其他 finding 的文件。
- 离线行为不变：资产缺失仍拒绝运行时下载，请求仍失败（500），只是错误码由
  INTERNAL_ERROR 变为更准确的 OCR_FAILED，且日志干净。未改为静默成功或自动下载。

## 新增回归测试

`tests/privacy/test_no_persistence.py::test_missing_asset_logs_contain_no_absolute_path`
（两半，同一测试内）：

- (a) 真实 `RapidOCRAdapter(assets_dir=<空 tmp 目录>)` 抛 `FileNotFoundError`，
  断言消息含文件名 `PP-OCRv6_det_small.onnx`、不含 `str(tmp_path)`、不含任何 `/`。
- (b) 把 `textproof.api.routes.get_ocr_adapter` 猴补丁为抛旧式绝对路径消息的
  `FileNotFoundError`，调 `run_check`（真实 fixture PNG + sentinel 期望文本），
  断言抛 `ApiError` 且 `code == "OCR_FAILED"`，且 caplog 中不出现绝对资产路径、
  临时目录路径、`/home/`。

验证该测试能抓缺陷：用 `git stash` 临时撤掉两个生产文件改动后重跑，
测试 FAIL（(a) 半在旧消息中看到绝对路径）；恢复改动后 PASS。

## 相关测试结果

- 新增测试单跑：PASS；`test_ocr_failure_log_contains_no_user_data`：PASS。
- `tests/privacy/ + tests/integration/test_api.py`：**2 failed、128 passed**
  （106.80s）。2 项失败是基线已有的 R-02 两项
  （`test_forbidden_token_absent_from_sources[urlopen]`、
  `test_no_network_client_import_in_sources`，均指向
  `scripts/consistency_check.py` 的 urlopen/socket——属 R-02 修复员范围，
  与本次改动无关；T012 报告基线同样为 2 failed）。
- 其余 128 项（含新增 R-04 测试与全部隐私/API 测试）全部通过。

## 运行时探针复核（按审查报告 §4 方法）

- 探针副本：`git worktree add --detach /tmp/f04-probe-r04 t013-r04`
  （含修复 commit `09d101c`），隐藏
  `assets/ocr/models/PP-OCRv6_det_small.onnx`，起真实服务
  `textproof.cli serve --host 127.0.0.1 --port 8899`
  （`PYTHONPATH=<probe>/src`，日志重定向到 `server.log`），
  用 TP-S0-ZH-001 真实 PNG POST `/api/v1/check`。
- 结果：**HTTP 500，`{"error":{"code":"OCR_FAILED","message":"OCR failed to produce a result.","detail":"ocr_engine_error"}}`**；
  `server.log` 全文仅一行：`OCR failed: FileNotFoundError`。
  grep 零命中：`/tmp/f04-probe-r04`（0）、`/home/`（0）、
  `PP-OCRv6_det_small.onnx`（0）、`Traceback`（0）、旧消息原文（0）。
- 对比基线（审查员证实）：HTTP 500 INTERNAL_ERROR + traceback 含绝对资产路径。
  修复后：仍 500 失败、仍拒绝下载，但错误码改为 OCR_FAILED 且日志无绝对路径。
- 清理已完成：服务按 PID 停掉（端口 8899 已关闭、无残留进程）、模型文件已恢复、
  探针 worktree 已注销删除（`git worktree remove --force /tmp/f04-probe-r04`）。

## 全量 pytest 结果

- 命令：`TMPDIR=$PWD/tmp ~/workspace/p033-textproof/.venv/bin/python -m pytest -q -p no:cacheprovider`
- 结果：**2 failed、437 passed、2 warnings，891.90s（0:14:51）**。
- 与基线对比（T012 报告：2 failed、436 passed，226.79s）：通过数 +1（新增 R-04
  测试），失败数不变——仍是 R-02 的两项（`scripts/consistency_check.py`
  的 urlopen/socket 扫描命中），与本次改动无关。
- 耗时说明：891.90s 远高于基线 226.79s，是环境原因——运行时另有三路 T013
  全量 pytest（t013-r02 / r05 / r09）与 SpanRelay 任务并行，1.5 核 VM 负载
  10+，四路各只分到约 14% CPU；本进程本身一直在跑（状态 R），不是卡死。
  测试结果本身（2 failed / 437 passed）不受耗时影响。

## 未改事项 / 注意事项

- 未合并到 `master` 或 `t011-full-regression`；分支 `t013-r04` 仅含修复 commit
  `09d101c` + 本交接文件 commit。
- 未改任何现有测试预期、fixture PNG、manifest、S0 门槛、输入输出契约、tool_version。
- R-02 的 2 项全量失败留待 R-02 修复员（`scripts/consistency_check.py` 移入 `tests/`）。
