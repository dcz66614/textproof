# T008 完成报告 — 本地 Web UI 与错误框交互

- 分支：`t008-ui`（worktree `~/workspace/p033-textproof-t008`，基于 master `69d97cc`，T007 已合入，S0 PASS）
- 验收命令：`.venv/bin/python -m pytest tests/e2e -q`（在 worktree 内执行；`python` 指 T001 冻结 venv）
- 验收结果：**31 passed，0 failed，24.25s，exit 0**（见 `test_stdout.log` / `exit_codes.txt`）
- 回归：`tests/unit tests/integration` 全量 **220 passed**（45.92s），T007 API 未受静态挂载影响
- 依赖：零新增、零升级（只用冻结依赖：FastAPI 自带的 `starlette.staticfiles`；浏览器测试用 stdlib 实现的最小 CDP 客户端驱动 Playwright 缓存中的 Chrome 159，不下载、不安装）

## 实现

- `src/textproof/ui/index.html` / `app.js` / `style.css`：单页本地界面，按 PROJECT_BOOK.md §3.2 布局（顶部产品名 + “离线 / 本机运行” + 版本；左栏上传/图片信息/期望文本/开始·重新核对；中央预览 + OCR 行框覆盖层；右栏 verdict/错误数/错误清单/复核提示/选中错误详情；底部下载 JSON/复制摘要/清除；空状态文案）。
- `src/textproof/api/app.py`（唯一改动，非 UI 文件）：`create_app()` 在 API router 之后挂载 `StaticFiles(ui/, html=True)` 到 `/`，API 路由优先；无 CORS、无 docs UI、无新依赖。API schema、算法阈值均未动。
- UI 只调同源相对地址 `/api/v1/check` 与 `/api/v1/version`；上传用 FileReader → base64 → POST；下载用 Blob + `URL.createObjectURL`（立即 revoke）；清除用 `URL.revokeObjectURL` + 清空全部内存状态 + 复位 DOM；全程不写任何浏览器持久存储。

## 逐项验收对照

1. **上传、编辑期望文本、开始核对、重新核对、下载 JSON、清除均可操作** — PASS。真实浏览器 E2E：`test_full_flow_mismatch_and_highlight`（上传 TP-S0-ZH-001 + 真实 OCR）、`test_recheck_after_editing_expected_text`（改期望文本为图面文字 → 第 2 次核对变 MATCH，状态含“第 2 次”）、`test_download_json_report`（下载文件解析后 `schema == textproof.report/v1`、`verdict == MISMATCH`、与页面原始 JSON 一致）、`test_copy_summary`、`test_clear_revokes_object_url_and_resets`。全部用真实鼠标点击（CDP `Input.dispatchMouseEvent`）与真实文件输入（`DOM.setFileInputFiles`）完成。
2. **图片预览、OCR 行框、错误清单联动** — PASS。`test_full_flow_mismatch_and_highlight`：预览上 ≥1 个 `.ocr-box`，点击错误项后 `.ocr-box.selected` 出现；截图 `ui_mismatch_highlight.png`（SHA-256 `73c3687c…`）可见红框精确套住“限时优”。
3. **选中错误高亮其 OCR 行 bbox；缺失整行显示“无可定位 OCR 框”** — PASS。`test_missing_line_shows_no_locatable_box`：干净图 TP-CLN-001 + 期望文本加一行“第二行缺失文字” → `MISSING_LINE`，详情含“无可定位 OCR 框”，且无 `.ocr-box.selected`；截图 `ui_missing_line.png`（SHA-256 `9443aa35…`）。注：S0 manifest 300 张中无整行缺失 fixture（只有 clean/omission/substitution/numeric_change 四类），故缺失整行用“干净图 + 额外期望行”构造，这是如实记录的构造方式，不是现成 fixture。
4. **REVIEW_REQUIRED、低置信度、OCR_FAILED 文案明确，不误导为确定错误** — PASS。静态断言：文案含“识别结果不确定，需要人工查看原图片区域”（§3.2 原文）、“待确认”、“不是确定的错误”；不含“已证明图片一定写错”“图片一定写错”。浏览器断言：`test_ocr_failed_is_labelled_pending_not_error`（桩 OCR 引擎抛错 → API `OCR_FAILED` 500 → 页面显示“OCR 失败（待确认）”，错误清单写“未列出确定错误”，无 E001）。低置信文案用 `WARNING_TEXT.LOW_OCR_CONFIDENCE` 渲染；REVIEW_REQUIRED verdict 文案为“待确认：存在低置信度、对齐歧义或需要复核的内容，不是确定的错误”。（低置信警告的浏览器端渲染未单独跑一条 live 流程——S0 干净图的 OCR 置信度均 >0.65，触发 LOW_OCR_CONFIDENCE 需人为构造低置信 OCR 行；文案本身由静态测试 + `renderWarnings` 代码路径覆盖，见“发现的问题/局限”。）
5. **无 CDN、外链字体、第三方脚本、外部图片 URL** — PASS。静态扫描：`tests/e2e/test_ui_static.py::test_no_external_references` 对三文件做 8 类模式扫描（`https?://`、协议相对域名、`@import`、`url(http`、`src|href=http`、googleapis/gstatic、cdn、unpkg/jsdelivr/cdnjs）全部零命中；`grep -rniE 'https?://|cdn|fonts.googleapis|googleapis'` 三文件零命中。运行时证明：浏览器网络日志 `network_requests.json` 只有 7 条请求，全部同源（`/`、`/style.css`、`/app.js`、`/api/v1/version`、`/favicon.ico`、`/api/v1/check` POST，另 1 条同源 `blob:` 预览图）。本 VM 出站 TCP 会被出口代理拦截，故未用 connect_ex 式断言，改用 CDP `Network.requestWillBeSent` 计数（按任务卡要求）。
6. **清除时撤销 object URL，清空浏览器内存状态，不写 localStorage** — PASS。静态：三文件不含 `localStorage` / `sessionStorage` / `indexedDB` / `document.cookie` 字面。运行时：`test_clear_revokes_object_url_and_resets` 证明清除后旧 `blob:` URL `fetch` 被拒（revoked）、预览隐藏、输入与报告清空、按钮复位；另有注入式存储访问陷阱（`Page.addScriptToEvaluateOnNewDocument`）在三个流程测试中全程记录到零次存储访问，且 `localStorage.length == 0`。

## 发现的问题（诚实记录）

1. **覆盖层定位曾错位（已修复）**：初版 `.overlay` 以整个预览列为基准；窄图/竖图居中时百分比框会错位。截图复核时发现并修复：图片与覆盖层改包进 `.preview-stage`（`position: relative`，按图片实际显示尺寸收缩），新增 `test_preview_overlay_matches_image_geometry`（400×800 竖图，stage 矩形与图片矩形误差 ≤1px）。横图渲染前后截图哈希相同（`73c3687c…`），竖图用例通过。
2. **测试曾误报两处（已修复，非产品问题）**：(a) 存储陷阱脚本自身在第二次导航时读取 `window.indexedDB` 触发了前一份陷阱——改为经 `Window.prototype` 描述符读取；(b) 重新核对的等待条件用子串 `"一致"`，被旧 verdict 中的“不一致”提前命中——改为等状态出现“第 2 次”。
3. **局限**：浏览器测试用本机 Playwright 缓存的 Chrome 159（`~/.cache/ms-playwright/chromium-1255/chrome-linux64/chrome`），非新装浏览器；截图是真实渲染（非 DOM 断言代替）。`tests/e2e/evidence/` 为测试生成物，未提交（可重生成）；交接包内为其副本。低置信警告的浏览器端渲染未单独跑 live 流程（见第 4 项括号）。
4. 执行中出现过一次 execution-risk 检查提示（称内容未通过检查），但命令本身 exit 0 且无操作被拒绝，按既往教训（AGENTS.md 2026-11-20）以实际 exit 码为准继续工作；无任何命令被实际拦截。

## 交接包内容

- `TASK_RESULT.md`（本文件）、`changed_files.txt`、`test_stdout.log`、`test_stderr.log`（空）、`exit_codes.txt`（`exit=0`）
- `ui_mismatch_highlight.png`、`ui_missing_line.png`（真实无头浏览器截图）
- `network_requests.json`（外部请求拦截日志：7 条请求，全同源 + 同源 blob）
- `downloaded_report.json`（浏览器实际下载的 JSON 报告：TP-S0-ZH-001，MISMATCH，E001 MISSING_CHARACTER“惠”，bbox `[491, 190, 713, 291]`）

## 改动文件

见 `changed_files.txt`：`src/textproof/api/app.py`（+13/−2 行，静态挂载）、新增 `src/textproof/ui/{index.html,app.js,style.css}`、`tests/e2e/{conftest.py,cdp.py,test_ui_static.py,test_ui_browser.py}`、本交接包。未改动 API schema、算法、锁文件与其他任务文件；未合入 master。
