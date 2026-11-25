# T010 任务结果（隐私、内存生命周期与离线安全）

- **分支：** `t010-privacy`（基于 master `74200c1`，T009 已合入）
- **工作目录：** `~/workspace/p033-textproof-t010`（worktree；主 worktree 未动）
- **日期：** 2026-11-25（GMT）
- **结论：§9 十项承诺逐项通过；验收 7 项全部通过；发现并修复两项真实问题（F-T010-01、F-T010-02）。**

## 验收命令实际输出

```text
$ .venv/bin/python -m pytest tests/privacy tests/offline -q
........................................................................ [ 78%]
....................                                                     [100%]
92 passed in 60.00s
```

- exit 0；stderr 为空；完整输出见 `test_stdout.log` / `test_stderr.log` / `exit_codes.txt`。
- 回归（两处产品修改波及范围）：
  `pytest tests/e2e/test_ui_static.py tests/integration/test_ocr_adapter.py
  tests/integration/test_api.py tests/integration/test_cli.py -q` →
  **128 passed**（37.15s）；另 `tests/e2e/test_ui_browser.py::test_clear_revokes_object_url_and_resets`
  （真实浏览器 + 真实 OCR）→ **1 passed**。
- 过程说明：首次完整运行 4 failed + 4 errors，均为本任务测试代码自身的 bug
  （`_is_loopback_host` 误判 `127.0.0.1`、fixture teardown 用错 `request.nodeid`、
  CLI 路径“零 socket 调用”被误断言为拦截失效），与一次 serve 探针设计错误
  （子命名空间监听的服务无法从父命名空间探测，且失败断言 `proc.stdout.read()` 死锁），
  均已修复并重跑通过；另有一次运行因该死锁被手动终止（不计入结果）。

## 逐项验收对照

| # | 验收标准 | 结果 | 命令 / 数字 |
|---|---|---|---|
| 1 | TextProof 发起外部网络请求数为 0 | ✅ 通过 | socket 拦截器：CLI check 0 次调用（0 connect / 0 DNS）；API check 仅 loopback（2 条记录：getaddrinfo + connect 到 127.0.0.1）；version/health 6 条全 loopback。strace：一次完整 CLI check **0 次 `connect()`**。`unshare -n` 下 CLI check / verify-s0 完成（该命名空间无任何可用网络，见下）。 |
| 2 | OCR 模型、字典、JS、CSS 和字体均来自本地文件 | ✅ 通过 | 3 个 ONNX + 字典 SHA-256 与冻结常量逐字节一致（`test_local_assets.py`）；适配器 `assets_dir` 即仓库 `assets/ocr`、providers 全 `CPUExecutionProvider`；UI 三文件零外部引用、零远程 `@font-face`、仅 system-ui 本地字体栈。 |
| 3 | 图片、期望文本和 OCR 全文不写日志、不写数据库、不写 localStorage | ✅ 通过 | 哨兵 expected 文本 + OCR 全文 + base64 前缀 + 绝对路径在真实 HTTP `/check` 的 textproof / uvicorn access / uvicorn error 三路日志中零出现；仓库内零 `.db` 文件；UI 源码零 storage API + 真实浏览器 storage trap 零访问。 |
| 4 | API 不把图片写入持久临时文件；multipart 默认落盘须改为内存处理并以测试证明 | ✅ 通过 | 核实：`/check` 用 JSON base64，**仓库内无 `UploadFile` / `multipart` / `tempfile`**（静态扫描）；两次 live `/check` 前后仓库 + fresh TMPDIR 文件集合零变化；strace `O_CREAT` 0 行。无落盘路径，无需改造。 |
| 5 | 服务端 stateless；请求完成后不保留图片和报告缓存 | ✅ 通过 | 两次连续不同请求响应互不含对方数据；两次 `/check` 前后文件集合零变化；无缓存文件产生。 |
| 6 | 清除 UI 后图片 object URL 被 revoke，报告和文本不可再从 UI 访问 | ✅ 通过 | 真实浏览器 E2E（stub OCR，返回与 live 相同的 `限时优` 单行）：清除后旧 blob URL `fetch` 被拒、预览隐藏、`src` 移除、输入/报告清空、按钮禁用；同流程 real-OCR 版由 T008 证明。 |
| 7 | loopback 外部监听拒绝；输入格式、大小、像素数和解码异常 fail-closed | ✅ 通过 | `validate_bind_host` 拒绝 10 类 host；`serve` 拒绝 `0.0.0.0`/公网 IP/`localhost`；运行中服务器 LISTEN 经 `/proc/net/tcp` 核对仅 `127.0.0.1`；13 类 fail-closed 输入在 HTTP 层逐一断言；PNG 改名 `.jpg` 仍按魔数识别。 |

## 发现的问题（诚实记录）

### F-T010-01 — UI 缺少 JSON 导出敏感文字提示（已修复）

- §9 要求 UI 提示导出可能包含敏感文字；修前 `index.html`/`app.js` 全文 grep “敏感”零命中。
- 修复：`src/textproof/ui/index.html` 页脚增加常驻提示
  “下载的 JSON 报告包含期望文本与 OCR 结果，可能包含敏感文字，请妥善保存，不要随意转发。”
  仅改文案 1 行；回归测试 `test_export_warning_present_in_ui`（源码 + 已服务页面双重断言）。

### F-T010-02 — ONNX Runtime 默认遥测写库（已修复）

- 发现手段：strace 跟踪一次完整 CLI check。
- 修前实测（对照实验，fresh `XDG_CACHE_HOME`）：一次 CLI check 创建 `deviceid` +
  `onnxruntime.db`（SQLite，表 `events`/`settings`），写入 **5 条遥测事件**
  （`SessionCreation`、`SessionCreationEnd`、`ProcessInfo`、`EpDeviceUsage`、`ModelLoadEnd`）。
  payload 逐条解码：仅 OS / CPU 型号 / 架构 / ORT 版本 / 可执行文件绝对路径 / 会话 GUID / 设备哈希，
  **不含图片字节、期望文本、OCR 文本**；同次运行 0 次 `connect()`，即本次运行中无上传发生；
  但 `events` 表属待上传 outbox，按 `onnxruntime/Privacy.md`，1DS 后端会经 HTTPS 发往 Microsoft。
- 依据：`onnxruntime/Privacy.md`（随 1.32.0 安装）：“Telemetry is turned **ON** by default in the
  official builds … uses the cross-platform 1DS telemetry SDK … to send the same trace events to
  Microsoft's telemetry backend over HTTPS.” 关闭方式为 `ORT_DISABLE_TELEMETRY=1`（须在 ORT 初始化前设置）。
- 修复：`src/textproof/ocr/rapidocr_adapter.py` 模块顶层、任何 ORT import 之前设
  `os.environ["ORT_DISABLE_TELEMETRY"] = "1"`（无条件赋值；§9 禁止遥测，环境变量中的 `=0` 不得重新开启）。
  该模块是仓库内唯一 import `onnxruntime` / `rapidocr` 的地方（均为方法内 lazy import），覆盖全部入口。
- 修复验证（fresh `XDG_CACHE_HOME`）：一次 CLI check 后缓存目录**零文件**，核对结果仍为 MISMATCH。
- 回归测试：`test_ort_telemetry_disabled.py`（import 断言 + 子进程 fresh 缓存断言）与 `test_strace.py`。

## 无法证明项登记（按完成定义，见 PRIVACY_TEST_REPORT.md §3）

1. **U-T010-01 — 密码学级内存擦除**：§9 原文明示不承诺；本任务证明“不再持有可访问引用”，不证明内存擦除。
2. **U-T010-02 — 历史遥测 outbox 残留**：修复前运行产生的 `~/.cache/.../.onnxruntime/onnxruntime.db`
   （2 条旧事件）与 `deviceid` 仍在磁盘上；修复只保证此后不再产生。是否删除由协调员决定（不在 worktree 内，未获清理授权）。
3. **U-T010-03 — 依赖库内部的未来网络行为**：`requests` 以 rapidocr 传递依赖形式存在于 venv 中，
   产品代码从不 import 它；本次运行的三层证据（socket 拦截、strace、离线命名空间）覆盖全部产品路径，
   未来依赖变更须重跑本套测试。

## 测试方法诚实边界（摘要，详见 PRIVACY_TEST_REPORT.md §6）

- 不用 `connect_ex` 断言（本 VM 出站 TCP 被出口代理拦截，`connect_ex` 会误报成功）；改用 socket 拦截器 + strace + `unshare -n` 三层。
- `unshare -n` 在本 VM 上不授予 `CAP_NET_ADMIN`：命名空间内 `lo` 保持 DOWN 且无法拉起，
  连 `127.0.0.1` 的 connect 都报 `ENETUNREACH`；且 `/sys/class/net` 在此 VM 上不随命名空间隔离
  （会列出父空间的 `host0`），不能作证据，改用命名空间感知的 `/proc/net/route`（空路由表）与
  `/proc/net/tcp`。因此 serve 的离线测试只证明“命名空间内启动并仅监听 `127.0.0.1`”，
  不做命名空间内 HTTP 检查；HTTP 半侧由 `tests/privacy/` 的 live-server 测试覆盖。
- 清除 E2E 用 stub OCR（返回与 live 相同的 `限时优` 单行）；同流程 real-OCR 版由 T008 证明。
- verify-s0 离线测试复用已提交的缓存 live 结果（300 条），15 秒 PASS；`--force-live` 全量重跑约 11 分钟，由 T006 与主聊天裁决覆盖。
- 依赖已冻结，未升级、未新增依赖；未改输入输出契约、算法、模型许可。

## 变更文件

- `tests/privacy/`（新增 8 个文件：conftest、helpers、6 个测试模块）
- `tests/offline/`（新增 6 个文件：conftest、helpers、3 个测试模块、`_serve_probe.py`）
- `PRIVACY_TEST_REPORT.md`（新增）
- `src/textproof/ui/index.html`（+1 行：导出敏感提示）
- `src/textproof/ocr/rapidocr_adapter.py`（+23 行：`ORT_DISABLE_TELEMETRY=1` + 注释）
- `task_handoffs/T010/`（交接包：本文件、报告副本、changed_files.txt、test_stdout.log、
  test_stderr.log、exit_codes.txt、evidence/：socket 拦截日志 ×4、浏览器网络请求日志、
  strace 日志、verify-s0 离线输出、文件系统写入观察记录）

## 需协调员决定

1. 是否删除 `~/.cache/Microsoft/DeveloperTools/.onnxruntime/` 下修复前残留的 `onnxruntime.db`（2 条旧遥测事件）
   与 `deviceid`（U-T010-02）。其 payload 不含用户数据，但属待上传 outbox。
2. 两处产品修复（UI 提示文案、适配器遥测开关）是否接受为 T010 范围内——均不改契约/算法/模型许可，
   直接服务 §9 合规；如需走 T013，测试与报告均已就绪，产品修复可单独 revert。
