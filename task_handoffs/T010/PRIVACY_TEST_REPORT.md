# TextProof 隐私测试报告（T010）

- **项目：** P033 TextProof（字证）
- **任务：** T010 — 隐私、内存生命周期与离线安全
- **依据：** `PROJECT_BOOK.md` §9（逐项对照见 §2）、`IMPLEMENTATION_PLAN.md` §T010
- **基线：** master `74200c1`（T009 已合入，S0 PASS）；分支 `t010-privacy`
- **日期：** 2026-11-25（GMT）
- **验收命令：** `python -m pytest tests/privacy tests/offline -q`
  （以项目 venv `.venv/bin/python` 运行；见 §4）

## 1. 结论

**§9 十项承诺逐项通过；验收 7 项全部通过。** 发现并修复两项真实问题：

| 编号 | 发现 | 性质 | 处理 |
|---|---|---|---|
| F-T010-01 | UI 缺少 §9 要求的 JSON 导出敏感文字提示 | §9 不合规（缺失提示） | 已修复：`src/textproof/ui/index.html` 增加常驻提示；有回归测试 |
| F-T010-02 | ONNX Runtime 1.32.0 官方构建默认开启 1DS 遥测：每次建会话向 `~/.cache/Microsoft/DeveloperTools/.onnxruntime/onnxruntime.db`（SQLite）写 5 条遥测事件 + 持久 deviceid | §9 不合规（写数据库、调用遥测；payload 不含用户数据，未观察到外发） | 已修复：适配器 import 时设 `ORT_DISABLE_TELEMETRY=1`；修复后 fresh 缓存目录零文件；有回归测试 + strace 证据 |

另有两项按 §9 原文即属“不承诺”范围，登记在 §3（不作为失败项）。

## 2. §9 逐项对照

| §9 承诺 | 判定 | 证据（测试 / 日志） |
|---|---|---|
| 图片、期望文本、OCR 结果只在本机进程和浏览器内存中处理 | ✅ 通过 | socket 拦截：CLI check / API check / version / health 全路径 0 外部连接、0 外部 DNS（`test_no_external_requests.py`）；strace：一次完整 CLI check 共 0 次 `connect()`（`test_strace.py`）；离线命名空间 `unshare -n` 下 CLI check 与 verify-s0（缓存结果）完成，serve 在命名空间内启动并证明仅监听 `127.0.0.1`（该命名空间的 loopback 无法启用、故无命名空间内 HTTP 检查，见 §6） |
| 不写数据库、不写 `localStorage`、不上传日志、不调用遥测、不发外部 HTTP 请求 | ✅ 通过（修后；见 F-T010-02） | 无数据库文件（`test_no_database_files_anywhere`）；UI 源码无任何 storage API + 真实浏览器 storage trap 零访问（`test_ui_clear_privacy.py`）；源码无 `tempfile`/`sqlite3`/遥测/`requests`/`httpx` import；ORT 遥测已关闭，fresh 缓存目录零文件（`test_ort_telemetry_disabled.py`）；日志无用户数据（见下行） |
| API 仅绑定 `127.0.0.1`；拒绝公网监听参数，或启动时强制校验 loopback | ✅ 通过 | `validate_bind_host` 拒绝 10 类非 loopback host；`serve` 拒绝 `0.0.0.0`/公网 IP/`localhost`；运行中服务器的 LISTEN socket 经 `/proc/net/tcp` 核对仅 `127.0.0.1`（`test_loopback_and_fail_closed.py`）；无 CORS 头 |
| 浏览器预览使用 object URL；清除时调用 revoke 并清空输入、预览和报告 | ✅ 通过 | 真实浏览器 E2E：清除后旧 blob URL `fetch` 被拒、预览隐藏、`src` 属性移除、输入/报告清空、按钮禁用（`test_ui_clear_privacy.py`；同流程 real-OCR 版见 T008） |
| 服务端 stateless；每个请求结束后不保留跨请求图片或报告对象 | ✅ 通过 | 两次连续不同请求的响应互不含对方数据（HTTP 层）；两次 `/check` 前后仓库 + TMPDIR 文件集合零变化（`test_no_persistence.py`） |
| 日志只记录请求状态、耗时、错误码和软件版本；不得记录图片字节、OCR 全文、期望文本、绝对路径或用户目录 | ✅ 通过 | 哨兵 expected 文本 + OCR 全文 + base64 前缀 + 绝对路径在真实 HTTP `/check` 的全部捕获日志（textproof / uvicorn access / uvicorn error）中零出现；OCR 失败路径只记异常类型名；CLI stderr 为空且只含稳定错误码（`test_no_persistence.py`，3 测试） |
| JSON 导出由用户显式触发；导出文件会包含期望文本与 OCR 结果，UI 必须提示其可能包含敏感文字 | ✅ 通过（修后；见 F-T010-01） | UI 增加常驻提示“下载的 JSON 报告包含期望文本与 OCR 结果，可能包含敏感文字，请妥善保存，不要随意转发。”；源码 + 已服务页面双重断言（`test_export_warning_present_in_ui`） |
| 不保证 OS swap、崩溃转储或浏览器进程内存被安全擦除；清除只承诺应用不再持有可访问引用，不宣称密码学级内存擦除 | ⚠️ 登记（见 §3） | 按 §9 原文即为不承诺项；本任务证明“不再持有可访问引用”（清除 E2E + stateless），不证明内存擦除 |
| 图片输入进行魔数、尺寸、像素数、解码异常和动画检查；不得信任文件扩展名 | ✅ 通过 | 13 类 fail-closed 输入在 HTTP 层逐一断言（MIME 不符、非法 base64、非图片字节、损坏 PNG、动画 WebP、尺寸超限、像素超限、超大、期望文本空/超长/超行）；PNG 改名 `.jpg` 仍按魔数识别为 PNG（`test_loopback_and_fail_closed.py`） |
| 禁止 shell 拼接、任意文件路径写入、外部 URL 图片加载或自动打开用户提供的 URL | ✅ 通过 | 源码无 `shell=True` / `os.system` / `eval(` / `exec(`；唯一 subprocess 调用是 CLI `verify-s0` 的固定 list argv；`load_image` 只接受 bytes、无路径参数；UI 只 fetch 同源 `/api/v1/*`，无外部 URL（`test_local_assets.py` / `test_loopback_and_fail_closed.py`） |

## 3. 无法证明 / 不承诺项登记（按完成定义）

1. **U-T010-01 — 密码学级内存擦除（§9 原文明示不承诺）。**
   §9 原文：“不保证操作系统 swap、崩溃转储或浏览器进程内存被安全擦除；清除功能只承诺应用不再持有可访问引用，不宣称密码学级内存擦除。”
   本任务证明的是后者：清除后旧 blob URL 不可访问、DOM 与内存引用清空、服务端无跨请求残留。进程内存、swap 与崩溃转储中是否残留字节无法由应用层测试证明，也不属于 §9 的承诺范围。登记为“不承诺”，不是失败。
2. **U-T010-02 — 历史遥测 outbox 残留（F-T010-02 的遗留部分）。**
   修复前运行产生的 `~/.cache/Microsoft/DeveloperTools/.onnxruntime/onnxruntime.db`（含 2 条旧事件，见 §5）与 `deviceid` 仍在磁盘上。修复只保证此后不再产生新事件，不删除既有文件（不在本任务 worktree 内，未获清理授权）。其 payload 经解码确认不含用户数据（仅 OS/CPU/ORT 版本/可执行路径/会话 GUID/设备哈希）。是否删除由协调员决定。
3. **U-T010-03 — 依赖库内部的未来网络行为。**
   本任务证明的是本次运行的全部产品路径（CLI / API / serve / UI / verify-s0）在 socket 层、strace 层、离线命名空间层均零外部连接。`requests` 以 rapidocr 传递依赖的形式存在于 venv 中（`requirements.lock`：`requests==2.34.2  # via rapidocr`），但产品代码从不 import 它；若未来版本依赖变更，须重跑本套测试。无法对“所有未来版本的依赖”作一次性证明。

## 4. 验收命令实际输出

最终验收运行（2026-11-25 ~09:30 GMT，修复全部测试 bug 与 serve 探针设计问题后）：

```text
$ .venv/bin/python -m pytest tests/privacy tests/offline -q
........................................................................ [ 78%]
....................                                                     [100%]
92 passed in 60.00s
```

- 命令：`.venv/bin/python -m pytest tests/privacy tests/offline -q`
  （`TEXTPROOF_PRIVACY_EVIDENCE_DIR=task_handoffs/T010/evidence`，证据日志落盘）
- 结果：**92 passed，0 failed，0 error，exit 0**；stderr 为空。
- 完整输出：`task_handoffs/T010/test_stdout.log` / `test_stderr.log` / `exit_codes.txt`。
- 过程说明：首次完整运行 4 failed + 4 errors，均为本任务测试代码自身的 bug
  （`_is_loopback_host` 误判 `127.0.0.1`、fixture teardown 用错 `request.nodeid`、
  CLI 路径“零 socket 调用”被误断言为拦截失效），与一次 serve 探针设计错误
  （在子命名空间监听的服务无法从父命名空间探测，且失败断言 `proc.stdout.read()` 死锁），
  均已修复并重跑通过；另有一次运行因该死锁被手动终止（不计入结果）。
  产品代码在验收中未被改动以迎合测试——两处产品修复（F-T010-01 / F-T010-02）均在测试之前完成。

## 5. 发现详情

### F-T010-01 — UI 缺少 JSON 导出敏感文字提示（已修复）

- **§9 要求：** “JSON 导出由用户显式触发；导出文件会包含期望文本与 OCR 结果，UI 必须提示其可能包含敏感文字。”
- **修前实测：** `src/textproof/ui/index.html` + `app.js` 全文 grep “敏感”零命中；下载按钮旁无任何提示，下载完成状态仅为“JSON 报告已下载。”。
- **修复：** `index.html` 页脚增加常驻提示（`id="export-warning"`）：
  “下载的 JSON 报告包含期望文本与 OCR 结果，可能包含敏感文字，请妥善保存，不要随意转发。”
  仅改 UI 文案，不改契约、算法与模型许可。
- **回归测试：** `test_export_warning_present_in_ui`（源码 + 已服务页面双重断言）。

### F-T010-02 — ONNX Runtime 默认遥测写库（已修复）

- **发现手段：** strace（`strace -f -e trace=openat,connect`）跟踪一次完整 CLI check。
- **修前实测（对照实验，`XDG_CACHE_HOME=/tmp/t010-ort-control`）：**
  一次 CLI check 创建 `deviceid` + `onnxruntime.db`（SQLite，表 `events` / `settings`），
  写入 5 条事件：`SessionCreation`、`SessionCreationEnd`、`ProcessInfo`、`EpDeviceUsage`、`ModelLoadEnd`。
  payload 逐条解码：仅含 OS（Ubuntu 24.04.5 LTS）、CPU 型号、架构、ORT 版本（1.32.0）、可执行文件绝对路径、会话 GUID、设备哈希；
  **不含图片字节、期望文本、OCR 文本**（`限时`字节与哨兵均未在 payload 中出现）。
  同次运行 strace 记录 **0 次 `connect()`**，即本次运行中无上传发生；但 `events` 表含 `retry_count` / `reserved_until` 字段，
  属待上传 outbox 结构，按 `onnxruntime/Privacy.md`，1DS 后端会通过 HTTPS 发往 Microsoft。
- **依据：** `onnxruntime/Privacy.md`（随 1.32.0 安装）：“Telemetry is turned **ON** by default in the official builds …
  it uses the cross-platform 1DS telemetry SDK … to send the same trace events to Microsoft's telemetry backend over HTTPS.”
  关闭方式：“Set `ORT_DISABLE_TELEMETRY=1` before ONNX Runtime initializes … prevents the uploader, events, and persistent
  device identifier from being created for the process lifetime.”
- **修复：** `src/textproof/ocr/rapidocr_adapter.py` 模块顶层、任何 ORT import 之前设
  `os.environ["ORT_DISABLE_TELEMETRY"] = "1"`（无条件赋值：§9 禁止遥测，环境变量中的 `=0` 不得重新开启）。
  该模块是仓库内唯一 import `onnxruntime` / `rapidocr` 的地方（均为方法内 lazy import），覆盖 CLI / API / serve / verify-s0 全部入口。
- **修复验证（`XDG_CACHE_HOME=/tmp/t010-ort-fixed`）：** 一次 CLI check 后 fresh 缓存目录**零文件**（无 `deviceid`、无 `.db`），
  且核对结果仍为 MISMATCH（OCR 不受影响）。
- **回归测试：** `test_ort_telemetry_disabled.py`（import 断言 + 子进程 fresh 缓存断言）与 `test_strace.py`
  （`O_CREAT` 仅限 `__pycache__`、0 次 `connect()`）。

## 6. 测试方法说明（诚实边界）

- **不用 `connect_ex` 断言：** 本 VM 出站 TCP 会被出口代理 `198.19.0.1:3128` 拦截，`connect_ex` 对未监听端口也会返回成功
  （T007/T008 已证实）。本任务改用三层证据：① 进程内 socket 拦截器（loopback 放行、非 loopback 拦截并记日志）；
  ② strace 系统调用层（`connect` / `openat`）；③ `unshare -n` 离线命名空间（仅 `lo` 接口，外部 connect 报
  `Network is unreachable`，先以对照探针证实隔离真实有效）。
- **文件系统写入观察：** 两层。① 快照法：两次 live `/check` 前后对 `src/`、`tests/`、`assets/`、`scripts/`、`schemas/` 及 fresh `TMPDIR`
  做文件集合比对（排除 `__pycache__` / `*.pyc` / `.pytest_cache`，属解释器产物）；② strace `openat` 的 `O_CREAT` 记录。
  快照法不覆盖 `~/.cache`——正是 strace 抓到 F-T010-02 的原因；报告如实记录这一分工。
- **日志扫描：** 用哨兵 expected 文本（`SENTINEL-T010-限时优惠-7f3a9`，仅本次测试使用）跑真实 HTTP `/check`，响应体含哨兵
  （证明真的跑了），而 textproof / uvicorn access / uvicorn error 三路捕获日志中哨兵、OCR 全文、base64 前缀、绝对路径均零出现。
- **localStorage：** 静态（源码零 storage API 引用）+ 真实浏览器运行时陷阱（T008 的 trap：`window.__tpStorageAccess` 为空且
  `localStorage.length == 0`），两者都在验收命令内重跑。
- **清除 E2E 的 OCR 是 stub：** `test_ui_clear_privacy.py` 用 stub 适配器（返回与 live OCR 相同的 `限时优` 单行）以保持快速；
  同流程的 real-OCR 版由 T008 的 `test_clear_revokes_object_url_and_resets` 证明，本任务不重复声称。
- **verify-s0 离线测试用缓存结果：** `unshare -n` 下的 verify-s0 复用已提交的 `task_handoffs/T006/live_ocr_results.jsonl`
  （300 条记录），15 秒、PASS。`--force-live` 全量重跑（约 11 分钟）不在验收命令内，由 T006 与主聊天裁决覆盖。
- **离线命名空间的环境限制（已查清，非产品问题）：** 本 VM 的 `unshare -n` 不授予 `CAP_NET_ADMIN`，
  命名空间内 `lo` 保持 DOWN 且无法拉起（`ip link set lo up` → `Operation not permitted`），连 `127.0.0.1`
  的 connect 都报 `ENETUNREACH`；且 `/sys/class/net` 在此 VM 上不随命名空间隔离（会列出父空间的 `host0`），
  不能作为隔离证据。因此：① 隔离对照改用 `/proc/net/route`（空路由表，无默认路由）+ 外部 connect 失败
  （`/proc/net/*` 是命名空间感知的）；② serve 的离线测试只证明“命名空间内启动并仅监听 `127.0.0.1`”
  （`/proc/net/tcp` 读表），不做命名空间内 HTTP 检查；HTTP 半侧由 `tests/privacy/` 的 live-server 测试覆盖。
  命名空间内无可用网络（含 loopback）——隔离强度高于普通命名空间。
- **未改动项：** 依赖已冻结，未升级、未新增依赖（`httpx` 仍不在 lock 中，T007 的决定维持）；未改输入输出契约、算法、模型许可。
  两处修复：UI 提示文案 1 行；适配器遥测开关 1 处赋值 + 注释。

## 7. 文件清单

- `tests/privacy/`：`conftest.py`、`t010_privacy_helpers.py`、`test_no_external_requests.py`、
  `test_no_persistence.py`、`test_local_assets.py`、`test_loopback_and_fail_closed.py`、
  `test_ui_clear_privacy.py`、`test_ort_telemetry_disabled.py`
- `tests/offline/`：`conftest.py`、`t010_offline_helpers.py`、`test_offline_namespace.py`、
  `test_strace.py`、`test_offline_static.py`、`_serve_probe.py`（命名空间内 serve 探针，非测试文件）
- `PRIVACY_TEST_REPORT.md`（本文件）
- 修复：`src/textproof/ui/index.html`（导出提示）、`src/textproof/ocr/rapidocr_adapter.py`（`ORT_DISABLE_TELEMETRY=1`）
- 交接包：`task_handoffs/T010/`（TASK_RESULT.md、本报告副本、changed_files.txt、test_stdout.log、test_stderr.log、
  exit_codes.txt、evidence/：socket 拦截日志、浏览器网络请求日志、strace 日志、verify-s0 离线输出）
