# T007 — FastAPI 本地 API 与健康检查：TASK_RESULT

- 任务 ID：T007
- 规格：`PROJECT_BOOK.md` v1.0.0 / `IMPLEMENTATION_PLAN.md` §T007（冻结契约，未修改）
- 执行时间：2026-11-25 ~07:23–07:45 GMT
- 输入 commit：`38c5fcf`（master，S0 PASS 裁决）
- 输出 commit：一次提交到 `t007-api` 分支（哈希见本任务向协调员的汇报；
  交接包文件本身在该提交内，无法在提交前预知自身哈希，故此处不填一个
  会在提交后失效的哈希）
- 工作目录：`/home/hatch/workspace/p033-textproof-t007`（worktree，分支 `t007-api`）
- 状态：**SUCCESS**（6 项验收标准全部满足，见 §2）

## 1. 执行命令与退出码

| # | 命令 | 退出码 |
|---|---|---|
| 1 | `git worktree add ~/workspace/p033-textproof-t007 -b t007-api master` | 0 |
| 2 | 冒烟：`create_app` + `validate_bind_host` + `run_check` 错误映射（直接调用） | 0（4/4 错误码匹配；路由延迟包含已核实，见 §3） |
| 3 | `python -m pytest tests/integration/test_api.py -q`（第一次） | 1（45 passed，1 failed，见 §3） |
| 4 | `python -m pytest tests/integration/test_api.py -q`（修复后，验收命令） | **0（46 passed，0 failed，22.40s）** |
| 5 | `python -m pytest tests/unit -q`（回归确认） | 0（155 passed，19.31s） |
| 6 | `python task_handoffs/T007/capture_fixtures.py`（fixture + loopback 证明采集） | 0（1 成功 + 13 错误 fixture + loopback 证明） |

完整日志：`test_stdout.log`（第 4 次运行）、`test_stderr.log`（空）。
Python 均为 T001 venv：`/home/hatch/workspace/p033-textproof/.venv/bin/python`
（Python 3.12.3；fastapi 0.165.0、uvicorn 0.54.0、pydantic 2.14.4，与锁文件一致）。

## 2. 验收标准逐项证据

### 验收 1 — `GET /api/v1/health` 与 `/version` 正常 ✅ PASS

- 真实 uvicorn 服务器（127.0.0.1 临时端口）+ urllib 实测：
  `test_health`、`test_version`、`test_version_alias` 均通过。
- `/api/v1/health` → 200 `{"status":"ok","service":"textproof",
  "tool_version":"0.1.0","schema":"textproof.report/v1"}`。
- `/api/v1/version`（及别名 `/version`）→ 200，含 `spec_version 1.0.0`、
  `rapidocr_version 3.10.0`、`onnxruntime_version 1.32.0`、
  `providers ["CPUExecutionProvider"]`；不构造 OCR 引擎即可回答。

### 验收 2 — `POST /api/v1/check` 接收三字段，返回 `textproof.report/v1` ✅ PASS

- `test_check_success`：固定样本 `TP-S0-ZH-001`（1200×480 PNG，期望
  `限时优惠`）经真实 HTTP 返回 200，报告 `schema=textproof.report/v1`、
  `verdict=MISMATCH`、恰好 1 条 `MISSING_CHARACTER`（`expected_fragment=惠`、
  `recognized_fragment=""`、`expected_span=[3,4]`、`recognized_span=[3,3]`、
  `bbox_scope=ocr_line`，bbox 等于 OCR 行框，与 manifest `target_region_xyxy`
  的 IoU ≥ 0.80），`image.sha256` 与 manifest 一致
  （`7d3a5c0b…`），`summary={expected_lines:1, ocr_lines:1, error_count:1,
  warning_count:0}`。
- 响应中不含 `image_base64`。

### 验收 3 — 绑定固定 `127.0.0.1`；公网 IP / `0.0.0.0` 必须拒绝 ✅ PASS

- `validate_bind_host`：`0.0.0.0`、`198.19.0.2`、`8.8.8.8`、`localhost`、
  `::1`、空串、空白、`example.com`、`127.0.0.2`、`0` 全部以 `ValueError`
  拒绝；仅 `127.0.0.1` 通过（10 个拒绝用例 + 1 个接受用例）。
- `serve(host="0.0.0.0"/"198.19.0.2"/"localhost")` 在 uvicorn 启动前即
  抛 `ValueError`（`test_serve_rejects_non_loopback_host`）。
- 真实服务器监听证明：`ss -tln` 显示 `127.0.0.1:37503 LISTEN`；
  `/proc/net/tcp` 中该端口唯一 LISTEN 行是 `0100007F:927F`（即
  127.0.0.1，state 0A）；`127.0.0.1:37503` 连接成功。
  证明文件：`loopback_proof.txt`。
- 环境说明：本 VM 出站 TCP 会被出口代理（`198.19.0.1:3128`）拦截，
  向非 loopback IP `connect_ex` 即使无人监听也会返回成功，因此不用它
  作证明；测试与证明均以 `/proc/net/tcp` + `ss` 监听表为准（首次实现
  用 `connect_ex` 曾因此误报 1 失败，见 §3）。

### 验收 4 — 图片字节只在内存中解码；请求结束后无跨请求缓存 ✅ PASS

- `test_stateless_no_cross_request_leak`：先后 POST `TP-S0-ZH-001` 与
  `TP-S0-ZH-002`，第二份报告的 `sha256`/`expected_text`/`recognized_text`
  均为第二张图的数据，响应中不含第一张图的任何文本。
- `test_check_does_not_write_files`：一次 `/check` 前后，`src/` 与
  `tests/` 下的文件集合完全相同（无新文件落盘）。
- 实现上：图片字节只存在于请求局部变量，`load_image` 后即 `del` 原始
  字节引用；进程内唯一长驻对象是 OCR 引擎单例（模型权重，不含请求数据）。

### 验收 5 — 超限输入、错误 MIME、非法 base64、空文本、OCR 失败返回明确错误码 ✅ PASS

全部 13 个错误码均有真实 HTTP fixture（`fixtures/error_*.json`，
请求 + 状态码 + 响应信封）与参数化测试覆盖：

| 错误码 | HTTP | 测试用例 |
|---|---|---:|
| `INVALID_IMAGE_MIME` | 400 | `image/gif`；PNG 配 `image/jpeg`（mime_mismatch） |
| `INVALID_BASE64` | 400 | `!!!not-base64!!!`；空字符串 |
| `INVALID_IMAGE_FORMAT` | 400 | 非图片字节 |
| `INVALID_IMAGE` | 400 | PNG 魔数 + 垃圾数据（解码失败） |
| `ANIMATED_IMAGE_NOT_SUPPORTED` | 400 | Pillow 生成的动画 WebP |
| `IMAGE_DIMENSION_EXCEEDED` | 400 | 9000×10 PNG（仅 IHDR，无图像数据） |
| `IMAGE_TOO_MANY_PIXELS` | 400 | 8000×6000 PNG（仅 IHDR，48 MP） |
| `IMAGE_TOO_LARGE` | 400 | 超长 base64（解码前按编码长度拒绝） |
| `EXPECTED_TEXT_EMPTY` | 400 | `""`；`"   "` |
| `EXPECTED_TEXT_TOO_LONG` | 400 | 5001 码点 |
| `EXPECTED_TEXT_TOO_MANY_LINES` | 400 | 101 行 |
| `INVALID_REQUEST` | 422 | 缺字段、错类型、未知字段、非 JSON 体 |
| `OCR_FAILED` | 500 | 注入抛异常的 stub 引擎（直接调用 + 真实 HTTP 各 1 次） |

错误信封统一为 `{"error":{"code","message","detail"}}`，`detail` 为
snake_case 原因码，不含用户文本、图片字节与路径；无裸 500（仅
`OCR_FAILED` 与最后防线 `INTERNAL_ERROR` 为有明确码的 500）。
完整码表见 `API_CONTRACT.md` §4。另：OCR 零可用文本不是 HTTP 错误，
按 §7.6 返回 200 + 报告 `verdict=OCR_FAILED`（核心 `report.py` 已有此行为，
API 不另造分支）。

### 验收 6 — API 与核心 CLI/直接调用对同一 fixture 的 JSON 语义结果一致 ✅ PASS

- `test_api_matches_core`：`TP-S0-ZH-001` 的 API 响应 dict 与直接调用
  `load_image` + `RapidOCRAdapter.recognize` + `core.report.build_report`
  的结果**逐字段完全相等**（`assert api_report == direct`）。
- 注：T009 CLI 尚未施工（不在本任务范围），故一致性对照以"核心直接调用"
  为基准；CLI 完成后须复用同一 `build_report`，不得另造判定（已写入
  `API_CONTRACT.md` §5）。

## 3. 发现的问题（诚实记录）

1. **TestClient 不可用（偏差，已用更强方案替代，未新增依赖）。**
   任务卡要求用 FastAPI TestClient，但 `starlette.testclient.TestClient`
   依赖 `httpx`，而 `httpx` 不在冻结 `requirements.lock` 中，T001 venv
   也未安装（导入即报"需要安装 httpx"）。按任务指令"如需新依赖先停下报
   协调员"，本任务**没有**安装 httpx、没有改锁文件。替代方案：测试启动
   真实 uvicorn 服务器（127.0.0.1 临时端口，后台线程），用标准库 urllib
   经真实 loopback socket 发请求——覆盖比 TestClient 更强（真实 HTTP 栈、
   真实绑定地址、真实监听 socket）。已写入 `API_CONTRACT.md` §6 与测试
   文件头。如协调员希望补 TestClient，需在锁文件中以测试依赖形式加入
   httpx（请协调员决定）。
2. **首次验收运行 1 失败（已修复，属测试写法问题，非产品问题）。**
   `test_server_listens_only_on_loopback` 最初用 `connect_ex` 连本机
   非 loopback IP（198.19.0.2:41201）断言"连不上"，结果返回 0——因为本 VM
   出站 TCP 被出口代理（198.19.0.1:3128）拦截，`connect_ex` 成功不代表
   有监听。改为读 `/proc/net/tcp` 监听表（端口只在 127.0.0.1 上 LISTEN）
   后通过。产品代码未因此改动。
3. **FastAPI 0.165 的路由是延迟包含的。** `create_app()` 后
   `app.routes` 只有 `_IncludedRouter`，路由在首次请求/启动时才展开；
   这是框架行为，端点实测均可达，不影响功能。冒烟脚本曾因此误报，
   已改用真实服务器验证。
4. **`test_check_error_cases[too_many_pixels]` 的 Pillow 警告。**
   48 MP 的 PNG 头会触发 `DecompressionBombWarning`（预期行为：正是要
   测的拒绝路径），已在测试文件顶部用 `filterwarnings` 明确忽略该警告，
   最终运行 0 warnings。
5. **无其他问题。** 未发现核心算法、schema、OCR 模型路径、隐私约束方面
   的冲突；未修改任何冻结文件（见 §4）。

## 4. 实际改动文件（只新增，零修改）

```
API_CONTRACT.md                          # 新增：端点、字段、错误码表、绑定约束
src/textproof/api/__init__.py           # 新增：包导出
src/textproof/api/app.py                # 新增：create_app / validate_bind_host / serve / main
src/textproof/api/routes.py             # 新增：CheckRequest / run_check / health / version / check
tests/integration/test_api.py           # 新增：46 个测试，覆盖 6 项验收
task_handoffs/T007/                     # 新增：交接包（本文件、日志、fixture、证明）
```

- `git status --short` 在提交前只显示以上新增项（`??`），**没有任何 `M` 修改**。
- 未修改：`src/textproof/contracts.py`、`src/textproof/io/image_loader.py`、
  `src/textproof/ocr/rapidocr_adapter.py`、`src/textproof/core/*`、
  `requirements.lock`、`pyproject.toml`、全部 fixture 与 manifest。
- 未新增依赖，未升级依赖。`httpx` 未安装（见 §3.1）。

## 5. 交付物

- 源码：`src/textproof/api/app.py`、`src/textproof/api/routes.py`、
  `src/textproof/api/__init__.py`
- 契约：`API_CONTRACT.md`（根目录）
- 测试：`tests/integration/test_api.py`（46 测试）
- 交接包 `task_handoffs/T007/`：`TASK_RESULT.md`（本文件）、
  `changed_files.txt`、`git_diff.patch`、`test_commands.txt`、
  `test_stdout.log`、`test_stderr.log`、`exit_codes.txt`、`SHA256SUMS.txt`、
  `capture_fixtures.py`（fixture 采集脚本）、`loopback_proof.txt`、
  `fixtures/`（1 成功 + 13 错误 + health/version，共 16 个 JSON）

## 6. 未完成项 / 风险

- 无未完成项。T009 CLI 一致性对照待 CLI 施工后由 T011 全量回归复核
  （不在本任务范围）。
- `python -m textproof.api.app` 的 `--host` 参数接受任意字符串后由
  `validate_bind_host` 拒绝；这是有意的 fail-closed 设计（拒绝发生在
  uvicorn 启动前）。

## 7. 回退 commit

- 输入 commit（S0 PASS）：`38c5fcf`
- 回退目标：`git checkout t007-api` 前的状态即输入 commit；或
  `git reset --hard 38c5fcf`（worktree 内）。
