# TextProof 本地 API 契约（T007）

- 产品版本（`tool_version`）：`0.1.0`
- 规格版本：`1.0.0`（`PROJECT_BOOK.md`）
- 报告 schema：`textproof.report/v1`（`PROJECT_BOOK.md` §5）
- 服务实现：`src/textproof/api/`（`app.py` + `routes.py`）
- 冻结依赖：`fastapi==0.165.0`、`uvicorn==0.54.0`、`pydantic==2.14.4`
  （`requirements.lock`，不升级、不新增）

## 1. 绑定约束（硬性）

- 服务**只绑定 `127.0.0.1`**，默认端口 `8765`
  （`PROJECT_BOOK.md` §5.5 CLI 示例：`textproof serve --host 127.0.0.1 --port 8765`）。
- 任何其他 host（`0.0.0.0`、公网/内网 IP、主机名、`localhost`、`::1`、
  空字符串）都会在 uvicorn 启动**之前**被 `validate_bind_host()` 以
  `ValueError` 拒绝，不会静默开放监听。
- **不启用 CORS**：本包不注册任何 CORS 中间件，响应中没有
  `Access-Control-Allow-Origin`。外部站点无法跨域调用本机 API。
- 启动方式：`python -m textproof.api.app [--host 127.0.0.1] [--port 8765]`；
  `--host` 只接受 `127.0.0.1`。

## 2. 端点

### `GET /api/v1/health`

健康状态，不包含任何用户数据。

响应 `200`：

```json
{
  "status": "ok",
  "service": "textproof",
  "tool_version": "0.1.0",
  "schema": "textproof.report/v1"
}
```

### `GET /api/v1/version`

版本信息。只报告冻结版本常量，**不构造 OCR 引擎**，因此在首次
`/check` 之前即可回答。

响应 `200`：

```json
{
  "service": "textproof",
  "tool_version": "0.1.0",
  "schema": "textproof.report/v1",
  "spec_version": "1.0.0",
  "rapidocr_version": "3.10.0",
  "onnxruntime_version": "1.32.0",
  "providers": ["CPUExecutionProvider"]
}
```

`GET /version` 是同一响应的别名（任务卡措辞中的 `/version`）。

### `POST /api/v1/check`

对一张图片做一次完整核对，返回 `textproof.report/v1` 报告
（字段定义见 `PROJECT_BOOK.md` §5.4，API 不改动 schema）。

请求体（JSON，`Content-Type: application/json`，未知字段会被拒绝）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `image_mime` | string | 必须是 `image/png`、`image/jpeg`、`image/webp` 之一，且必须与图片魔数检测出的格式一致 |
| `image_base64` | string | 图片字节的严格 base64 编码（不接受空白/缺失填充）；解码后不得超过 25 MiB |
| `expected_text` | string | 期望文本；T002 规则：非空、≤5,000 码点、≤100 行 |

成功响应 `200`：`textproof.report/v1` 报告全文（`schema`、
`tool_version`、`verdict`、`image{sha256,format,width,height,
coordinate_system}`、`expected_text`、`recognized_text`、`ocr_lines`、
`errors`、`warnings`、`summary`）。响应中**不包含图片 base64**。

处理流程（只做接线，不重写已有逻辑）：

1. MIME 白名单 → 严格 base64 解码（先做编码长度预检，超长直接拒绝，
   不解码、不分配大内存）→ T002 `load_image`（魔数、25 MiB / 8192 px /
   40 MP、EXIF orientation、动画 WebP 拒绝）→ MIME 与检测格式一致性 →
   T002 `validate_expected_text` → T003 `RapidOCRAdapter.recognize`
   （CPU-only，离线本地模型）→ T004 `build_report`。
2. 图片字节只在请求局部变量中存在；返回后即丢弃引用，不写磁盘、
   不写数据库、不跨请求缓存。进程内唯一的长驻对象是 OCR 引擎单例
   （模型权重，不含任何请求数据）。
3. OCR 识别出**零可用文本**时不是 HTTP 错误：返回 `200`，报告
   `verdict` 为 `OCR_FAILED` 并带 `OCR_EMPTY` 警告（`PROJECT_BOOK.md`
   §7.6）。只有 OCR 引擎本身抛异常时才返回 HTTP `500` + `OCR_FAILED`
  （见 §4）。

## 3. 调用示例

```bash
# 启动（只监听本机）
python -m textproof.api.app --port 8765

curl http://127.0.0.1:8765/api/v1/health
curl http://127.0.0.1:8765/api/v1/version

# 核对（IMAGE_B64 为图片的 base64；不要在日志里记录它）
curl -X POST http://127.0.0.1:8765/api/v1/check \
  -H 'Content-Type: application/json' \
  -d "{\"image_mime\":\"image/png\",\"image_base64\":\"$IMAGE_B64\",\"expected_text\":\"限时优惠\"}"
```

## 4. 错误码表

所有失败都返回统一信封（不是裸 500、不是 FastAPI 默认体）：

```json
{"error": {"code": "INVALID_BASE64", "message": "…", "detail": "invalid_base64"}}
```

`detail` 是短 snake_case 原因码，**不含用户文本、图片字节、文件路径**。
`message` 是通用说明，不含用户数据。

| 错误码 | HTTP | 触发条件 |
|---|---|---:|
| `INVALID_REQUEST` | 422 | 请求体不是合法 JSON；缺少字段；字段类型错误；含未知字段 |
| `INVALID_IMAGE_MIME` | 400 | `image_mime` 不在白名单；或与图片魔数检测出的格式不一致 |
| `INVALID_BASE64` | 400 | `image_base64` 为空或不是严格 base64 |
| `IMAGE_TOO_LARGE` | 400 | 解码后图片超过 25 MiB（编码长度超过上限时在解码前即拒绝） |
| `IMAGE_DIMENSION_EXCEEDED` | 400 | 宽或高超过 8192 px |
| `IMAGE_TOO_MANY_PIXELS` | 400 | 像素总数超过 40,000,000 |
| `INVALID_IMAGE_FORMAT` | 400 | 魔数不是 PNG / JPEG / WebP |
| `INVALID_IMAGE` | 400 | 图片为空、损坏、解码失败、魔数与解码格式不一致、尺寸非法 |
| `ANIMATED_IMAGE_NOT_SUPPORTED` | 400 | 动画 WebP |
| `EXPECTED_TEXT_EMPTY` | 400 | 期望文本为空或全空白 |
| `EXPECTED_TEXT_TOO_LONG` | 400 | 期望文本超过 5,000 码点 |
| `EXPECTED_TEXT_TOO_MANY_LINES` | 400 | 期望文本超过 100 行 |
| `INVALID_INPUT` | 400 | 其他 T002 输入拒绝（兜底码，仍为明确的 400 而非 500） |
| `OCR_FAILED` | 500 | OCR 引擎抛异常（模型/推理失败）。零可用文本不属于此类，见 §2 |
| `INTERNAL_ERROR` | 500 | 未预期的内部异常（最后防线；日志只记异常类型，不记用户数据） |
| `NOT_FOUND` | 404 | 未知路径 |

错误码与 T002 `InvalidInputError.reason` 的映射见
`src/textproof/api/routes.py::_REASON_TO_CODE`；每个 T002 原因都有
确定的 API 码，不存在"未知原因 → 裸 500"的路径。

## 5. 一致性

API 与核心使用**同一条比较路径**：`POST /api/v1/check` 与直接调用
`load_image` + `RapidOCRAdapter.recognize` + `core.report.build_report`
对同一输入返回**逐字段完全相同的 JSON**（`tests/integration/test_api.py::
test_api_matches_core`，固定样本 `TP-S0-ZH-001`）。CLI（T009）也必须
复用同一核心函数，不得另造判定。

## 6. 测试说明（诚实记录的偏差）

任务卡要求"用 FastAPI TestClient 做 HTTP 层测试"，但 `TestClient`
依赖 `httpx`，而 `httpx` **不在冻结的 `requirements.lock` 中**，T001
venv 里也没有安装（`from starlette.testclient import TestClient` 直接
报"需要安装 httpx"）。新增 `httpx` 属于新增依赖，T007 无权自行决定，
故未安装、未改锁文件。

替代方案（已实施，见 `tests/integration/test_api.py`）：测试启动**真实
uvicorn 服务器**（绑定 `127.0.0.1` 的临时端口，后台线程），用标准库
`urllib` 经真实 loopback socket 发请求。这比 TestClient 覆盖更强：
它验证了真实 HTTP 栈、真实绑定地址和真实监听 socket（`/proc/net/tcp`
中该端口只在 `127.0.0.1` 上处于 LISTEN）。如协调员希望补 TestClient，
需在 T001 锁文件中以测试依赖形式加入 `httpx`（由协调员决定，本任务
不做）。

注意：本 VM 的出站 TCP 会被出口代理（`198.19.0.1:3128`）拦截，因此
"向本机非 loopback IP `connect_ex`" 不是有效的监听证明（即使无人监听
也会返回成功）；loopback 唯一性以 `/proc/net/tcp` + `ss -tln` 的监听表
为准，测试与交接证明均按此法（见 `task_handoffs/T007/loopback_proof.txt`）。

## 7. 不在本契约内的事

- 不提供公网监听、CORS、鉴权、TLS、限流、批量接口。
- 不持久化任何请求数据；不写日志到图片/文本内容（日志只记错误码、
  异常类型、状态与耗时）。
- 不修改核心算法、JSON schema、OCR 模型路径与隐私约束（`PROJECT_BOOK.md`
  §9）；违反这些约束的请求一律 fail-closed。
