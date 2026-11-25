# 文件系统写入观察记录（T010）

## 方法（两层，互相独立）

### A. 快照法（`tests/privacy/test_no_persistence.py::test_check_writes_no_files`）

- 两次 live `/check`（真实 OCR）前后，对 `src/`、`tests/`、`assets/`、`scripts/`、`schemas/` 及一个 fresh `TMPDIR`
  做文件集合比对；`__pycache__` / `*.pyc` / `.pytest_cache` 排除（解释器与 pytest 产物，非产品写入）。
- 结果：**两次检查前后文件集合完全相同**（测试通过，见验收输出）。

### B. strace 系统调用层（`tests/offline/test_strace.py`）

- 命令（测试内自动执行，日志见 `evidence/strace_cli_check.log`，1,319 行）：
  `strace -f -e trace=openat,connect -o <log> <venv python> -m textproof.cli check
  --image tests/fixtures/s0/TP-S0-ZH-001.png --expected-file <txt>`
- 结果（本次验收运行的日志）：
  - `connect(` 系统调用：**0 次**（日志中 7 处含 “connect” 字样均为 `openat` 打开的
    `connection.py` / `connectionpool.py` 等文件名，无一次真实 connect 调用）。
  - 含 `O_CREAT` 的 `openat`：**0 行**——本次运行连 `__pycache__` 字节码写入都没有（已缓存）。
  - fresh `XDG_CACHE_HOME` 下：**零文件**（无 ONNX Runtime 遥测 outbox，见 F-T010-02）。

## 快照法不覆盖的范围（诚实记录）

- 快照法只看仓库内目录与 `TMPDIR`，**不看 `~/.cache`**。F-T010-02（ONNX Runtime 遥测库
  `~/.cache/Microsoft/DeveloperTools/.onnxruntime/onnxruntime.db`）正是 strace 层抓到的，
  不是快照法抓到的。两层分工已在 `PRIVACY_TEST_REPORT.md` §6 写明。
- 修复前对照（`XDG_CACHE_HOME=/tmp/t010-ort-control`）：一次 CLI check 创建 `deviceid` +
  `onnxruntime.db`，写入 5 条遥测事件；修复后（`/tmp/t010-ort-fixed`）：fresh 缓存目录零文件。
