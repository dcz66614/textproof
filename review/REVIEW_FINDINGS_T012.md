# P033 TextProof — T012 独立代码审查报告（REVIEW_FINDINGS.md）

- 审查对象：冻结候选 commit `ffe53ea1fb7e1d31f536abd732c258ffc50aae56`（分支 `t011-full-regression`），工作树 `~/workspace/p033-textproof-t011`
- 审查会话：全新协调员会话（ad01b03c）+ 三个全新子审查会话（契约 / 资产与模式 / 隐私与网络）；审查者未修改任何生产源码、测试预期、manifest、release 文件
- 审查时间：2026-11-25 ~10:40–11:00 GMT
- 输入：T011 commit `ffe53ea`、PROJECT_BOOK.md（v1.0.0）、IMPLEMENTATION_PLAN.md、T011_MAINCHAT_VERDICT.md、S0_MAINCHAT_VERDICT.md
- 方法：只读分析 + 本地哈希核对 + 协调员亲自运行的复现（全量 pytest、F-01 双案复现、TP-S0-ZH-001 独立复核、F-04 运行时复核、METRICS 交叉核对）
- 输出：本文件 + `REVIEW_INDEX.md`（覆盖表）+ `review/repro_f01.py`（R-01 复现脚本）+ `review/pytest_rerun.log`（全量 pytest 重跑日志）+ `review/drafts/`（三份子审查草稿）

## 0. 结论总览

| 项 | 结论 |
|---|---|
| Findings 总数 | **31**（P1 × 4、P2 × 7、P3 × 20），P0 × 0 |
| T011 验收 1（全量 pytest） | **FAIL（已确认）**：协调员亲自重跑 `2 failed, 436 passed, 2 warnings, 226.79s, exit 1`，与主聊天重跑一致；构建者“438 passed”不可复现。唯一失败源是 R-02（见下） |
| S0 门禁 | **不受影响**：S0 仍 PASS（协调员 #3 在集成树上重跑 exit 0；主聊天亲自重跑 verify_s0 --force-live exit 0）；本审查独立复核 TP-S0-ZH-001 亦 PASS |
| 最严重缺陷 | R-01（P1）：`align_lines` 浮点比较，两种已复现的表现形态；300 fixture 零触发，不影响 S0 指标，但改变真实输入的错误集合，T013 必修 |
| 审查覆盖 | 全文读 60 / 应读 74（81%）；部分读 14；未读 0。核心文件（src/、scripts/、schemas/、oracle/、privacy/offline/S0/unit 测试、规格 §4–§10）全部全文读过。详见 REVIEW_INDEX.md |
| 是否可进 T013 | **是**：P1 共 4 项均有明确修复路径；无 P0。T013 须关闭全部 P1，逐项修复或记录 P2，复审后方可进 T014 |

### 严重级别口径（本审查）

- **P0**：使产品、冻结契约或 S0 裁决失效的阻断缺陷。本次 0 项。
- **P1**：必须修——冻结契约/隐私条款在生产代码中的真实违反，或门禁测试失败；T013 关闭，复审验证。
- **P2**：建议修——校验器/证据/门禁脚本层面的不一致或缺口；T013 逐项修复或书面记录为非阻断并说明影响。
- **P3**：记录——规格措辞、文档、纵深防御缺口；T013/T014 酌情处理，不得静默丢弃。

### 编号说明

为避免与 S0 报告已有的 F-01–F-04 撞号，本审查 findings 统一编号 **R-01…R-31**。子审查草稿内的原编号映射见每条末尾的“草稿来源”。S0 的 F-01（align_lines 浮点缺陷）与本审查 R-01 是同一缺陷的不同证据：S0 只记录了 0.05 歧义边界一案，本审查补上了 0.70 配对阈值一案（更严重）并给出精确触发输入。

## 1. 六项验收逐项结论

### 验收 1 — 核对 §4–§9 契约与实现一致

**结论：基本一致，1 项 P1（R-01）、1 项 P2（R-11），8 项 P3。**

§4.2 输入约束（格式/魔数/尺寸/像素/动画/期望文本上限）、§4.3 规范化 6 步、§4.5/§7.3 权重（0/0.65/0.50/1.25/1.00/1.00）与混淆对 6 对、§7.4 数字分类、§7.5 坐标关联、§7.6 置信度与 verdict、§5.2/§5.3 枚举、§5.4 JSON 样例、§5.5 API/CLI、§6 架构、§8.1 四样本固定路径、§8.2 300 样本构成、§9 隐私文本对照——逐条核对表见 `review/drafts/contract.md` §1（§4–§9 逐字对照）与 `review/drafts/privacy_network.md` §4（§9 文本对照）。除 R-01/R-11 外全部 PASS。§9 的网络扫描细节由隐私子审查独立核查（验收 5）。

### 验收 2 — 核查 OCR 模型 / 字典 / 字体许可与离线资产哈希

**结论：哈希与版本全部一致；1 项 P1（R-03 字典许可 UNVERIFIED）、2 项 P3。**

- 3 个 .onnx 模型、字典、字体、OFL.txt 的 SHA-256 与字节数与 THIRD_PARTY_NOTICES.md / assets/ocr/SHA256SUMS.txt / rapidocr_adapter.py 常量逐项一致（子审查亲自 sha256sum，见草稿 §1 表）。
- `assets/ocr/SHA256SUMS.txt` 覆盖 assets/ocr/ 下除自身外的全部 4 个文件，无遗漏。
- rapidocr 3.10.0、onnxruntime 1.32.0 CPU-only、fastapi 0.165.0、uvicorn 0.54.0、pydantic 2.14.4、Pillow 11.3.0 在 pyproject/lock/适配器/API_CONTRACT 五处一致；lock 无 onnxruntime-gpu、无 rapidocr-onnxruntime；lock SHA 与 ENVIRONMENT.md 记录一致（8726d13c…）。
- 唯一 UNVERIFIED 许可：识别字典 ppocrv6_dict.txt（R-03）。模型 Apache-2.0、RapidOCR 源码 Apache-2.0、ONNX Runtime MIT、字体 OFL-1.1 均已核实。src//tests//scripts/ 扫描无未登记的第三方资产。

### 验收 3 — 独立复核 TP-S0-ZH-001 原始 PNG、期望文本、实际 OCR 结果、错误类型和坐标

**结论：PASS（协调员亲自复核，非转述）。**

- 原始 PNG：`tests/fixtures/s0/TP-S0-ZH-001.png`，SHA-256 `7d3a5c0b8e8da3b59c0090f5ccba20cfe81b533df07c1ef83fcb7fef79cec660`，与 manifest 一致；7985 B；1200×480。
- 期望文本 `限时优惠`，绘制文本 `限时优`（omission，第 3 位字符 `惠`）；期望 verdict MISMATCH；期望 1 条 MISSING_CHARACTER，span [3,4]/[3,3]。
- 协调员运行 `scripts/independent_verify.py --case TP-S0-ZH-001`（live OCR，17s）：实际 OCR 认出 `限时优`，错误 MISSING_CHARACTER，expected_span [3,4]、recognized_span [3,3]、fragment `惠`、bbox [491.0,190.0,713.0,291.0]、bbox_scope ocr_line、confidence 0.99929；Oracle 输出完全一致；IoU(live bbox, target_region [486,189,714,291]) = 0.964 ≥ 0.80；**INDEPENDENT VERIFICATION: PASS**。
- METRICS_REPORT.json 与 task_handoffs/T011/s0/s0_metrics.json 抽查一致：召回 201/201（分类型 70/70、71/71、60/60），CER 0.00080128（S=1、D=1、I=0、N=2496）。

### 验收 4 — 审查 JSON schema、CLI exit code、API / UI / CLI 一致性

**结论：主干一致；2 项 P2（R-05、R-06），3 项 P3。**

- Schema `textproof.report/v1`：顶层 required 10 键、verdict 4 值、错误 7 值、警告 4 码、errors[] 13 键、ocr_lines[] 5 键、summary 4 键与 §5.4 样例及 report.py 输出逐项一致；F-03 冻结形态（缺失侧 span/bbox/scope/confidence 为 null）三方一致。
- CLI 退出码：0 MATCH / 1 MISMATCH / 2 REVIEW_REQUIRED / 3 输入无效 / 4 OCR 失败 / 5 内部错误，与 §5.5 一致；argparse 用法错误覆写为 3（避免撞 2）；CLI 与 API 同调 `run_check`，同一 schema。
- API/UI/CLI 三路：脚本比对逻辑严密（解析后全字段递归、三组两两比对），未发现三路实际分歧；但证据留存不足（R-06），ZH-002 的 IDENTICAL 无法从留存物独立复核。
- 校验器公式分歧（R-05）：孤立 CR 输入会被 CLI 以 exit 5 误拒。

### 验收 5 — 核查日志、缓存、临时文件、网络访问和 loopback 绑定

**结论：产品侧基本通过；2 项 P1（R-02、R-04）、2 项 P2（R-07、R-08），6 项 P3。**

- API 仅绑 127.0.0.1：`app.py:48,53,56-71` 精确字符串比对，拒绝 0.0.0.0/::1/localhost/空串/公网 IP；无 CORS 中间件；`test_loopback_and_fail_closed.py` 从 /proc/net/tcp 核对 LISTEN 为 0100007F。
- UI 三文件无外部引用、只调同源相对路径、无浏览器存储 API、导出敏感提示在位、clearAll() 撤销 object URL。
- ORT telemetry：`rapidocr_adapter.py:59` import 时无条件置 `ORT_DISABLE_TELEMETRY=1`；产品内 onnxruntime/rapidocr 仅此一处 import。
- 产品 src/：零 socket/urllib/requests/httpx import；零 tempfile；零缓存对象；零 .db 文件；唯一文件写是 CLI `--json` 用户显式导出；logger 调用仅 4 处（固定文案/类型名/行数/监听地址），无 basicConfig/FileHandler。
- 失败：R-02（2 项隐私测试失败，T011 阻断）、R-04（资产缺失时绝对路径进日志，运行时已证实）。
- 全树 grep 475 行命中已逐项判定（见 `review/drafts/privacy_network.md` §3）：除 R-02 外，src//scripts/ 内无真实网络客户端；UDP 路径全树 0 命中。

### 验收 6 — 每个 finding 标明文件路径、行号、影响、复现命令、严重级别

**结论：满足。** 全部 31 条均含文件:行、影响、复现命令、严重级别；行号均为审查员亲自读到或 grep 到的行号；复现命令除注明“静态核对”者外均已实际执行（协调员的 pytest 重跑、F-01 双案、ZH-001、F-04 运行时复核）或由子审查员实测（哈希、字符串算术、diff）。

### 验收 7 — 审查覆盖率（已实际读取文件数 / 应读取文件数）

**结论：60 / 74 全文读（81%）；部分读 14；未读 0。**

应读 74 = 代码与数据文件 67（src/ 20、scripts/ 9、oracle/ 2、schemas/ 1、tests/ 35）+ 规格与配置文档 7。14 项部分读为：PROJECT_BOOK.md（§0–§3、§12–§16 未读；§4–§10 已读）、style.css（grep）、oracle/reference_compare.py（docstring+结构+grep；其行为由 S0 parity 300/300 与本审查 ZH-001 独立复核佐证）、tests/e2e/cdp.py、tests/e2e/conftest.py、tests/e2e/test_ui_browser.py、tests/integration/test_api.py、test_cli.py、test_ocr_adapter.py、tests/oracle/test_reference_compare.py、tests/unit/test_image_loader.py（以上均为 grep/节选；其行为由全量 pytest 436 passed 佐证）、tests/fixtures/s0/manifest.json、expected_output.json、blind_subset.json（程序核对：300 条 SHA 由 verify_s0 重算通过、计数与盲测构成已验证、4 条 S0 人工读过）。逐文件表见 REVIEW_INDEX.md。核心文件全部全文读过，覆盖完整。

## 2. Findings 清单（R-01…R-31）

### P1（4 项，必须修；T013 关闭，复审验证）

#### R-01 — P1：`align_lines` 浮点比较误判（两种已复现的表现形态）

- 文件：`src/textproof/core/align_lines.py:118`（`cost > 0.70` 返回 inf）、`:206/:211/:214`（回溯浮点 `==`）、`:248–251`（次优代价异序相加后与 0.05 比较）；同类模式 `src/textproof/core/weighted_edit.py:211,221,224`（回溯 `==`）
- 影响：规格 §4.4/§7.2 冻结的是精确十进制算术。已复现两案：
  - **A（0.70 配对阈值，更严重）**：40 字符行（20 个混淆替换 + 12 个数字替换 + 8 个相同字符），精确加权距离 28、精确配对代价 28/40 = 0.70，应允许配对；实测浮点距离 28.000000000000004、代价 0.7000000000000001 > 0.70，`pair_cost` 返回 inf，`align_lines` 将该行拆为 MISSING_LINE + EXTRA_LINE。报告丢失全部 20 条 SUBSTITUTION 与 12 条 NUMERIC_CHANGE，改为两条行级错误——错误类型、span、片段、bbox 关联全部改变。
  - **B（0.05 歧义边界）**：单字符 `O`→`0`，最优 0.65、次优 0.70，精确差恰好 0.05，不应判歧义；实测浮点差 0.04999999999999993 < 0.05，生产误判 `ambiguous=True`（Oracle 用 Fraction 判得正确）。
  - 机理：0.65/0.50 等十进制小数在二进制中不是精确值，DP 按不同求和顺序累积舍入误差；`min()` 在数学平局的候选间按浮点噪声选胜者；回溯的 `==` 只是复算同一表达式，无法纠正。
  - 范围：300 fixture 零触发（短行浮点恰好干净），S0 指标零影响；但长行、多混淆对的真实输入可触发。S0 报告的 F-01 只记录了 B 案；本审查补上 A 案与精确触发输入。
- 复现：`~/workspace/p033-textproof/.venv/bin/python review/repro_f01.py`（工作树根目录；exit 0 = 两案均复现缺陷，修复后应 exit 1）。或单行：`python3 -c "import sys; sys.path.insert(0,'src'); from textproof.core.align_lines import align_lines, pair_cost; E='O'*20+'8'*12+'a'*8; O='0'*20+'0'*12+'a'*8; print(pair_cost(E,O), [(p.expected_index,p.ocr_index) for p in align_lines([E],[O]).pairs])"`，预期 `0.7 [(0,0)]`，实测 `inf [(None,0),(0,None)]`。
- 修复方向（供 T013 定夺）：以 `Fraction` 精确算术或带 epsilon 的比较重做代价比较与歧义判定；`weighted_edit.py` 回溯同 pattern 一并处理；新增回归测试锁定 A 案（40 字符构造行）与 B 案（0.05 边界歧义）。
- 草稿来源：contract F-01（独立复现，非抄 S0 结论）；协调员亲自复现双案。

#### R-02 — P1：`scripts/consistency_check.py` 位于 T010 隐私扫描树内，致 2 项隐私测试失败（T011 合并阻断项）

- 文件：`scripts/consistency_check.py:40`（`import socket`）、`:45`（`import urllib.error`）、`:46`（`import urllib.request`）、`:77` 与 `:86`（`urllib.request.urlopen`）
- 影响：`tests/privacy/test_no_persistence.py` 两项失败——`test_forbidden_token_absent_from_sources[urlopen]`（token 在 :77、:86）与 `test_no_network_client_import_in_sources`（import 在 :40、:45、:46）。协调员亲自重跑全量 pytest：`2 failed, 436 passed, 2 warnings, 226.79s, exit 1`，与主聊天重跑一致；构建者“438 passed”不可复现。用途本身无真实外发：唯一实际目标是 `LiveServer` 内固定的 `http://127.0.0.1:{port}`（:98、:102），`_free_port` 只绑 `127.0.0.1:0`；失败是静态扫描口径与文件位置问题，不是外发行为。产品 `src/` 无网络代码，隐私承诺未破。
- 复现：`cd ~/workspace/p033-textproof-t011 && TMPDIR=$PWD/tmp ~/workspace/p033-textproof/.venv/bin/python -m pytest -q -p no:cacheprovider`（日志 `review/pytest_rerun.log`，exit 1）；或 `grep -n urlopen scripts/consistency_check.py`。
- 修复方向（已由主聊天 2026-11-25 ~10:40 裁决，本审查独立确认）：把该脚本移出被扫描树（`scripts/` → `tests/`，例如 tests/e2e/ 旁的校验脚本位），保留真实 HTTP 回环校验腿与严格的扫描门禁；否决缩小扫描范围、curl 绕过、白名单三条路。依据：扫描范围定义在测试内（`src/**/*.py + scripts/*.py`），`tests/` 不在任何扫描范围内，且 `tests/` 内已有同样用 urllib/socket 打回环的先例（`t010_privacy_helpers.py:31-33,94` 等）。移动后须同步更新两处文档命令路径（`task_handoffs/T011/TASK_RESULT.md:58`、`FULL_TEST_REPORT.md:83`）。
- 严重级别说明：隐私子审查员曾标 P0；协调员裁定为 P1——它是 T011 合并阻断项（已裁决），但产品本身无缺陷、S0 门禁不受影响、修复路径已定且机械；P0 保留给产品/规格层面的阻断缺陷。
- 草稿来源：privacy F-01（P0→协调员改判 P1，见上）；assets F-C1（P1）；协调员亲自重跑确认。

#### R-03 — P1：识别字典许可仍为 UNVERIFIED（公开再分发前必修；T014 既定职责）

- 文件：`THIRD_PARTY_NOTICES.md:79`（节标题 `## 4. Recognition dictionary — SEPARATELY VERIFIED, LICENCE UNVERIFIED`）、`:83–88`（字典表：18,708 行 / 74,947 B / SHA `b5f2bfe2…` / 许可 `未核实 (UNVERIFIED)`）、`:116–118`（不得凭模型许可推断为 Apache-2.0；T014 公开再分发前必须复核）
- 影响：字典**内容**已核实无误（三方字节一致：registry dict_url 下载件、PaddleOCR 上游文件、模型内嵌 character 元数据；适配器每次启动交叉校验本地字典与模型内嵌列表 + 行数 18,708；本审查实测 SHA `b5f2bfe2bdd94484…` 与声明一致），但**许可**未核实。按 PROJECT_BOOK.md §10.2 与 T003 验收标准 7，在许可解决前不得把字典作为单独文件随公开版本再分发。**不阻塞 T012 审查本身**（属 T014 发布门），但阻塞公开 release。
- 复现：`grep -n UNVERIFIED THIRD_PARTY_NOTICES.md`；`sha256sum assets/ocr/dictionaries/ppocrv6_dict.txt`（哈希本身与声明一致，问题只在许可栏）。
- 草稿来源：assets F-A1。

#### R-04 — P1：资产缺失时绝对路径写入服务器日志（冻结 §9 违反；运行时已证实）

- 文件：`src/textproof/ocr/rapidocr_adapter.py:211,217–218,222,228–229`（资产缺失/哈希不符的 `FileNotFoundError`/`ValueError` 消息内含绝对资产路径 `{path}`）；`src/textproof/api/routes.py:336`（`check()` 通用 `except Exception` 后 `logger.exception`）、`src/textproof/api/app.py:135`（`_unhandled_handler` 内 `logger.exception`）
- 影响：资产缺失时，`get_ocr_adapter()`（`routes.py:267`，首次请求时懒加载创建）在 `run_check` 的 OCR_FAILED 捕获范围之外（`:268–279` 只包 `recognize()`），`FileNotFoundError` 冒泡到 `check()` 的通用 except，经 `logger.exception` 把含绝对路径的 traceback 写进日志。违反 PROJECT_BOOK.md §9“日志不得记录绝对路径”及 `test_http_check_logs_contain_no_user_data`（断言 `/home/` 与仓库绝对路径不在日志中）。协调员在 /tmp 的独立副本上运行时复核（隐藏一个模型文件后发真实 /check）：HTTP 500 INTERNAL_ERROR，server.log 中出现 `FileNotFoundError: OCR model asset missing: /tmp/f04-probe/assets/ocr/models/PP-OCRv6_det_small.onnx. Refusing to download at runtime (offline-only operation).`，traceback 链 routes.py:328 → :267 → :172 → rapidocr_adapter.py:173 → :210。触发条件是部署损坏（资产缺失），属真实可达路径，非理论分支。
- 复现（协调员已执行，探针副本已清理）：`git worktree add --detach /tmp/f04-probe ffe53ea`，隐藏 `assets/ocr/models/PP-OCRv6_det_small.onnx`，起 `textproof.cli serve --host 127.0.0.1 --port 8899`，POST `/api/v1/check`（任意 PNG + 期望文本），查 server.log 中绝对路径。
- 修复方向：adapter 报错消息只用相对路径或文件名（`path.name`），或在 `run_check` 内把资产构造失败映射为 OCR_FAILED 且不记录异常消息；并为资产缺失路径补一项日志断言测试。
- 严重级别说明：隐私子审查员原标 P2（静态推导、未运行时复核）；协调员运行时证实后升为 P1——冻结 §9 条款在生产请求路径上的真实违反。
- 草稿来源：privacy F-04（P2→协调员运行时证实后升 P1）。

### P2（7 项，建议修；T013 逐项修复或书面记录为非阻断并说明影响）

#### R-05 — P2：手写校验器的 `summary.expected_lines` 公式与生产计数不一致（孤立 CR 输入会被 CLI 以 exit 5 误拒）

- 文件：`scripts/validate_report_schema.py:404–405`（`"expected_lines": report.get("expected_text", "").count("\n") + 1`）；对照 `src/textproof/core/report.py:248,272,345`（summary 均用 `len(expected_norm)`）；`src/textproof/core/normalize.py:104–110` 与 `src/textproof/io/image_loader.py:292–293`（先把 `\r\n`/`\r` 统一为 `\n` 再切分）
- 影响：期望文本含孤立 CR（`\r` 不成对、无 `\n`）时两公式分歧：`'a\rb'` → validator 1 vs report 2（协调员亲自算术复核；`'a\r'` 同理；CRLF/LF 均一致）。于是 `textproof check` 对此类合法输入会产出合法报告，却在自检（`cli.py:236–241`）中被判违规 → exit 5“内部错误”。现实概率低（CR-only 行尾罕见；S0 样本无此情形），且 fail-closed 方向安全（误拒而非误放），故 P2。
- 复现：`python3 -c "raw='a\rb'; print('validator:', raw.count(chr(10))+1); print('report:', len(raw.replace(chr(13)+chr(10),chr(10)).replace(chr(13),chr(10)).split(chr(10))))"`，应得 validator 1 / report 2。
- 修复方向：校验器按“统一换行后再切分”计数（与 image_loader.py:292–293 同规则）。
- 草稿来源：assets F-B1；协调员亲自复核公式与算术。

#### R-06 — P2：一致性证据留存不足——ZH-002 的“IDENTICAL”无法从留存物独立复核

- 文件：`scripts/consistency_check.py:135`（两案共用同一 `workdir / "cli-report.json"`，后案覆盖前案）、`:158–159`（每案先删 `downloads/textproof-report.json`）、`:174`（UI 下载同一文件名）；`task_handoffs/T011/consistency_report.json`（只存 verdicts + `identical` + `differences`，无完整报告/哈希）
- 影响：`TP-S0-ZH-002` 的三份报告与两案的 API 报告均未留存；留存物只有 TP-CLN-001 的 CLI 与 UI 两份报告。`consistency_report.json` 称两案 `identical: true`，其中 ZH-002 一案只能凭脚本 stdout 与报告 JSON 本身采信，无法独立复核。脚本比对逻辑本身无问题（全字段递归比对）。另：留存的 CLN-001 两份报告仅在数值写法上不同（`393.0` vs `393`，UI 经 JS `JSON.stringify` 重序列化所致，语义相等——**不是**三路分歧，但报告 JSON 未记录这一细节，复核者自行 diff 时会看到差异）。
- 复现：`ls task_handoffs/T011/consistency_work/ task_handoffs/T011/consistency_work/downloads/`；`diff <(python3 -m json.tool task_handoffs/T011/consistency_work/cli-report.json) <(python3 -m json.tool task_handoffs/T011/consistency_work/downloads/textproof-report.json)`（仅 8 处 `393.0` vs `393` 写法差异）。
- 修复方向：每案写独立文件名（如 `cli-<case>.json` / `api-<case>.json` / `ui-<case>.json`），或在 `consistency_report.json` 中记录每份报告的 SHA-256。
- 草稿来源：assets F-B2。

#### R-07 — P2：`_http_post` / `_http_get` 接受任意 `base`，无回环约束

- 文件：`scripts/consistency_check.py:69–89`（`_http_post` :69–80、`_http_get` :83–89）
- 影响：两个 helper 是通用 HTTP 客户端，只凭调用方传入的 `base` 决定目标；当前唯一调用方 `LiveServer` 固定传入 `http://127.0.0.1:{port}`，故当前无外发，但函数本身没有任何回环校验，若日后被复用传入外部 `base` 即直接外发。另 `_http_get` 在就绪轮询中吞掉全部异常（:105–109 的 bare `except Exception: pass`），失败原因不可见。
- 复现：`sed -n '69,113p' scripts/consistency_check.py`（静态核对）。
- 修复方向：随 R-02 迁移时同修——在两个 helper 入口断言 `base.startswith("http://127.0.0.1:")`（或改为只接受 `port` 参数、内部拼接回环地址），并把就绪轮询的异常吞没收窄为记录后重试。
- 草稿来源：privacy F-02。

#### R-08 — P2：`consistency_check.py` 把 fixture 文本写盘且无清理，并打印到 stdout

- 文件：`scripts/consistency_check.py:132–135`（`workdir/expected.txt` 写期望文本、`cli-report.json` 写完整报告）、`:220–223`（`workdir = args.out.parent / "consistency_work"`，无任何删除逻辑）、`:235–236`（打印 expected / drawn_text）、`:250–260,265–266`（结果 JSON 含 expected_text / drawn_text 写 `--out`）
- 影响：写入的是已提交的 S0 合成 fixture 文本（与 manifest.json 内相同内容），非真实用户数据，且输出目录由调用方指定，属验证证据；但模式上与 §9“日志不得记录 OCR 全文、期望文本”相冲突——同一脚本若日后被指向真实用户图片，期望文本与完整报告将以明文留在 `consistency_work/` 与 `--out` JSON 中，且 `expected.txt` 永不删除。另 `cli-report.json` 在两次 case 间被覆写复用（:135、:153），残留的上一次报告在覆写前可读。
- 复现：`grep -n -E 'write_text|mkdir|unlink|rmtree|remove' scripts/consistency_check.py`（静态核对）。
- 修复方向：跑完后删除 `workdir/expected.txt` 与 `cli-report.json`（或改用 `tempfile.TemporaryDirectory`——注意该脚本将移入 `tests/`，届时可用 `tmp_path` 模式），并在 docstring 中声明其输出含 fixture 文本、不得用于真实用户图片。
- 草稿来源：privacy F-03。

#### R-09 — P2：`verify_s0.py` 的 `S0 VERDICT: PASS` 未覆盖 §8.4 全部硬门（独立复核与网络 0 不在脚本判定内）

- 文件：`scripts/verify_s0.py:308–310`（`results["7_cpu_only"]` 的 `network` 字段只是一段字符串：“proven by unshare -n execution; see S0_REPORT.md §7”）、`:338–348`（`all_pass` 只合取 7 项，不含 item 8；随后打印 `S0 VERDICT: PASS` 与 NOTE 说明 item 8 未运行）
- 影响：§8.4 的 S0 PASS 条件包括“独立复核样本通过”（item 3，要求运行 `independent_verify.py`）与“网络访问 0”（item 6）。脚本自身既不运行独立复核，也不检查网络：不用 `unshare -n` 直接跑也能在 CPU-only 一项上通过并打印 PASS。读者只看脚本输出会误以为 §8.4 已全部成立，实际成立依赖脚本外的程序（unshare 执行 + 另跑独立脚本 + S0_REPORT.md 文字记录）。S0 整体已通过主聊天裁决的完整证据集，本条不追溯否定 S0。
- 复现：静态核对（读 :308–310 与 :338–348 即可确认）。
- 修复方向：把 `S0 VERDICT` 改为 `VERIFY_S0 ITEMS PASS` 之类限定表述，或在脚本内显式要求 `independent_verify.py` 的输出文件存在且通过、以及要求调用方传入“已在网络命名空间隔离下运行”的显式标志，否则 item 7 记为未验证。
- 草稿来源：contract F-02。

#### R-10 — P2：`gate_pass` 未执行 §8.3 运行时间门槛（1920×1080 预热 P95 ≤5s），且度量图片并非该尺寸

- 文件：`scripts/compute_s0_metrics.py:390–406`（`gate_pass` 只检查 recall ≥95%、每类 ≥90%、clean FPR ≤8%、schema 100%、IoU below_0.80==0 五项，无 timing 检查）；`:363–367`（timing P95 只记录不判定）；`tests/fixtures/s0/manifest.json` 全部 300 张为 1200×480（非 §8.3 规定的 1920×1080）
- 影响：§8.3 表格把运行时间列为门槛（“≤5s”），但 S0 门禁的机器判定不包含它；即使 P95 超 5 秒，`verify_s0.py` 仍可打印 PASS。另：300 张 fixture 均为 1200×480，metrics 中的 P95 不是 §8.3 指定尺寸下的测量，性能门槛实际由 T011 性能报告另行覆盖（T011 实测 P95 3.817s，PASS）。
- 复现：静态核对（读 `gate_pass` 全文即可确认无 timing 分支）。
- 修复方向：在 `gate_pass` 中加入 timing 判定（或明确将该门槛标注为“由 T011 性能报告判定，不属于 verify_s0.py”并写入 S0_REPORT.md），避免 S0 PASS 被误读为包含性能门槛。
- 草稿来源：contract F-03。

#### R-11 — P2：live 路径 TP-S0-NUM-001 产出 2 条错误，与 §8.1“恰好 1 条 NUMERIC_CHANGE”字面不符；门禁只查固定路径，掩盖了该分歧

- 文件：`tests/s0/test_s0_gate.py:155–169`（锁定 live 行为：`SUBSTITUTION ￥→¥ span [0,1]` + `NUMERIC_CHANGE 8→0 span [4,5]`，verdict MISMATCH）；`scripts/verify_s0.py:30–40` docstring 同样记录该 live 行为；`src/textproof/core/normalize.py:52–59`（￥ U+FFE5 不在全角 ASCII 映射范围内，字面正确）
- 影响：因果链完整且双方各自合规：§4.3 只映射全角 ASCII，￥ 不映射（字面正确）；live OCR 把绘制的 ￥（U+FFE5）读作 ¥（U+00A5），二者是不同字符，必然多一条 `SUBSTITUTION`。于是 §8.1“恰好 1 条 NUMERIC_CHANGE”在 live 路径上不可满足——除非增加一条规格没有的 ￥→¥ 映射，或把“恰好 1 条”重读为“恰好 1 条 NUMERIC_CHANGE（另可有其他类型错误）”。`verify_s0.py` 的 item 3 只用固定记录核对 §8.1，live 路径不在该检查内；`compute_s0_metrics.score` 的召回只计注入字符是否被检出、FPR 只计 clean 图，额外 `SUBSTITUTION` 对两项指标均无影响，同样看不见该分歧。目前该重读只写在 S0_REPORT.md §6(a)（主聊天裁决），未冻结进项目书或 expected_output。**本条是已裁决事项的追踪，不是新发现**：主聊天 S0 裁决已采纳按类型计数读法并把分歧点书面留给终审；本条要求把该读法冻结进规格（或门禁），不要为消灭该条错误而给 §4.3 增加 ￥→¥ 映射。
- 复现：静态核对（读 `test_s0_gate.py:155–169` 的锁定断言与 `verify_s0.py` 的固定路径检查）。
- 修复方向（二选一，供 T013/T014 定夺）：(a) 把 S0 裁决的按类型计数读法冻结进 PROJECT_BOOK.md §8.1（改“恰好 1 条 NUMERIC_CHANGE”为“恰好 1 条 NUMERIC_CHANGE 类型的错误”并注明 live OCR 的 ￥→¥ 读法）；或 (b) 在 `verify_s0.py` 增加 live 路径 NUM-001 断言（恰好 1 条 NUMERIC_CHANGE + 允许 1 条 ￥→¥ SUBSTITUTION），使门禁直接覆盖该样本的 live 行为。
- 草稿来源：contract F-04。

### P3（20 项，记录；T013/T014 酌情处理）

#### R-12 — P3：字体许可/版本/哈希未汇总进 `THIRD_PARTY_NOTICES.md`（记录分散在两处）

- 文件：`THIRD_PARTY_NOTICES.md:135–138`（§6 仅称“T005 fixture font, Noto Sans SC / OFL, is a separate deliverable”，无版本/哈希/许可全文位置）；对照 `tests/fixtures/s0/fonts/FONT_NOTICE.md:10–14`（版本 2.004-H2、SHA `a3041811…`、OFL-1.1、OFL.txt SHA `1c05c68c…`）与 `scripts/generate_fixtures.py:90–96,371–372`（`FONT_SHA256` 常量 + 每次运行校验）。另 `tests/integration/test_ocr_adapter.py:38–39` 用的系统字体 Noto Sans CJK SC / DejaVu Sans 在 THIRD_PARTY_NOTICES.md:135–137 仅泛称“system fonts”，未具名。
- 影响：PROJECT_BOOK.md §10.2 要求的字体记录（OFL、来源、版本、哈希）实质已满足，但发布审查者须在两处拼合；THIRD_PARTY_NOTICES.md:5–7 称“记录每一个 T003 使用的第三方资产”，字体属 T005，严格说不在其自述范围——口径应写明。
- 复现：`grep -n 'Noto Sans SC' THIRD_PARTY_NOTICES.md` vs `cat tests/fixtures/s0/fonts/FONT_NOTICE.md`。
- 草稿来源：assets F-A2。

#### R-13 — P3：`LICENSE` / `README.md` / `SECURITY.md` 在 T011 树中缺失（T014 既定职责）

- 文件：（缺失本身）`ls LICENSE README.md SECURITY.md` 均 `No such file or directory`；要求来源 PROJECT_BOOK.md:561（§10.1：仓库必须包含 `LICENSE`、`THIRD_PARTY_NOTICES.md`、依赖清单和模型资产清单）、:378（§6.3 布局含 `LICENSE`）、:614（§11.3 交付物第 4 项含 `README.md`、`LICENSE`、`THIRD_PARTY_NOTICES.md`、`SECURITY.md`）；`THIRD_PARTY_NOTICES.md:3–4` 自述 `LICENSE`“to be added by T014 if not yet present”。
- 影响：`THIRD_PARTY_NOTICES.md:3` 首句“TextProof's own source code is MIT (see `LICENSE`…)”当前指向不存在的文件；模型/字典资产清单与依赖清单（`SHA256SUMS.txt`、`requirements.lock`）齐全。属 T014 发布打包既定工作，不阻塞 T012。
- 复现：`ls LICENSE README.md SECURITY.md`。
- 草稿来源：assets F-A3；协调员亲自确认缺失。

#### R-14 — P3：`textproof verify-s0` 失败透传 exit 1，与 §5.5 的“1 = MISMATCH”同值异义

- 文件：`scripts/verify_s0.py:350`（`return 0 if all_pass else 1`）；`src/textproof/cli.py:276–300`（`_verify_s0` 原样透传；T009 TASK_RESULT.md 亦称透传是有意的）；PROJECT_BOOK.md:329–336（§5.5 表：1 = `MISMATCH`）
- 影响：S0 门失败时 `textproof verify-s0` 退出 1；任何按 §5.5 解读退出码的包装脚本会误读为一次 `check` 的 MISMATCH。PROJECT_BOOK.md §8 与 IMPLEMENTATION_PLAN.md 只定义了 `S0_FAIL` 概念，未规定 `verify-s0` 的数字退出契约。
- 复现：`grep -n 'return 0 if all_pass' scripts/verify_s0.py`。
- 修复方向（二选一并写进文档）：在 §5.5 或 T006 卡中明文规定 `verify-s0` 的 0/1 通过/失败契约与 §5.5 表无关；或失败时映射为 5（内部错误）/3。
- 草稿来源：assets F-B3。

#### R-15 — P3：Schema + 手写校验器 jointly 仍放行“存在侧行索引为 null”的错误对象（生产从不产出，仅纵深防御缺口）

- 文件：`schemas/textproof.report.v1.schema.json` 的 MISSING_LINE 条件块（:45–72）只约束缺失侧（recognized_span/ocr_line_index/bbox/confidence 为 null），未要求存在侧 `expected_line_index` 非空；EXTRA_LINE 块（:74–98）同理未要求 `ocr_line_index` 非空；字符错误块（:130–163）未约束双行索引。`scripts/validate_report_schema.py:292–341` 同样只校验“缺失侧为 null + 存在侧 span 非空”，:265–270 仅要求行索引“null 或 ≥0 整数”，未要求存在侧非空；亦未校验行索引指向既存行。
- 影响：手工构造的 `MISSING_LINE`（`expected_line_index: null`）可同时通过 schema 与手写校验器。生产从不产出此类对象（`classify.py:234–252` 的 `missing_line_difference` 必填 `expected_line_index`；`:255–276` 的 `extra_line_difference` 必填 `ocr_line_index`；字符错误双索引由 `report.py:338–347` 的对齐对保证），故为纵深防御缺口而非实际缺陷。
- 复现：构造含 `"type": "MISSING_LINE", "expected_line_index": null` 的报告，分别以 schema 与 `validate_report_schema.py` 校验——两者均不报错（仅读码判定，未执行；属静态结论）。
- 草稿来源：assets F-B4。

#### R-16 — P3：`GET /api/v1/version` 不含 `package_version`，而 CLI `version` 含之（字段集不对称）

- 文件：`src/textproof/api/routes.py:301–313`（`version()` 返回 service / tool_version / schema / spec_version / rapidocr_version / onnxruntime_version / providers，无 `package_version`）；对照 `src/textproof/cli.py:311–322`（`_version()` 另含 `package_version`，未安装时诚实报 `"not-installed"`）
- 影响：两者均符合各自的文档形状（API_CONTRACT.md §2 的 version 示例本就不含 `package_version`），不是违规；但同一产品的两个版本端点字段集不同，消费者横向比对时会缺一字段。
- 复现：`grep -n package_version src/textproof/api/routes.py src/textproof/cli.py`（前者 0 命中）。
- 草稿来源：assets F-B5。

#### R-17 — P3：多份验证脚本把 fixture 文本打印到 stdout

- 文件：`scripts/independent_verify.py:177–178`（打印 expected_text / drawn_text）、`:221–224,232–237,247–248`（打印完整错误列表、逐字 OCR 文本与完整生产报告 JSON）；`scripts/compute_s0_metrics.py:453–455`（打印 missed 的注入片段）；`scripts/parity_check.py:388–389`（打印含 expected_text / recognized_text 的 diff）；`scripts/verify_s0.py:263–264`（打印含 fragments 的 checks）；`scripts/benchmark_perf.py:222`（打印固定 poster 期望文本）
- 影响：全部是已提交的合成 fixture 文本、走 stdout 证据通道，非产品运行时日志；与 R-08 同属“验证脚本不受产品日志口径约束但字面冲突”的模式。记录即可；若日后任一脚本被复用于真实用户图片，应先去文本打印。
- 复现：`grep -n 'print(' scripts/independent_verify.py scripts/compute_s0_metrics.py scripts/parity_check.py scripts/verify_s0.py scripts/benchmark_perf.py`（静态核对）。
- 草稿来源：privacy F-05。

#### R-18 — P3：证据输出中含本机绝对路径与主机名

- 文件：`scripts/benchmark_perf.py:149–153`（`_model_files` 把 `~/.cache/rapidocr` 下每个 `.onnx` 的绝对路径写进 summary JSON；:135–137 遍历 `Path.home() / ".cache" / "rapidocr"`）；`scripts/env_probe.py:61`（`disk_path` 为脚本绝对路径）、`:63`（`python_executable`）、`:67`（`hostname`）；`scripts/verify_s0.py:334–336`（打印 `[9] evidence written to {out_dir}`，`out_dir` 默认是绝对路径）
- 影响：内容是环境元数据、非用户内容；但与 §9“日志不得记录绝对路径”的字面口径有张力（产品日志口径 vs 证据报告）。记录即可；如需收紧，可在 summary 中把模型路径记为相对路径或只记文件名 + SHA-256。
- 复现：`grep -n -E 'home\(\)|hostname|out_dir' scripts/benchmark_perf.py scripts/env_probe.py scripts/verify_s0.py`（静态核对）。
- 草稿来源：privacy F-06。

#### R-19 — P3：网络拦截仪器的 UDP 覆盖缺口

- 文件：`tests/privacy/t010_privacy_helpers.py:129–131,141–171`（`SocketRecorder` 只拦截 `connect` / `connect_ex` / `getaddrinfo`，不拦截 `sendto` / `sendmsg`）；`tests/offline/test_strace.py:269`（strace 只 trace `openat,connect`）
- 影响：UDP 外发路径无仪器覆盖；但全树 grep `sendto|sendmsg|recvfrom|SOCK_DGRAM|datagram` **0 命中**，且 `src/` 内唯一 socket 使用在 R-02 的脚本中，因此残余风险只是仪器缺口，不是已发现的通道。另 `_is_loopback_host`（`t010_privacy_helpers.py:102–115`）把 `""`、`None`、`"localhost"` 判为回环放行——与产品 `validate_bind_host` 的严格精确比对（拒绝 `localhost` 与空串）口径不同，但这是测试仪器的分类器，不是产品行为。
- 复现：`grep -rn -E 'sendto|sendmsg|SOCK_DGRAM|datagram' src scripts tests oracle`（0 命中）。
- 草稿来源：privacy F-07。

#### R-20 — P3：文件快照的监视范围有边界；`__pycache__` 遍布全树

- 文件：`tests/privacy/t010_privacy_helpers.py:50`（`_WATCHED_SUBDIRS = ("src", "tests", "assets", "scripts", "schemas")`）、`:204–218`（`take_snapshot` 只扫这些目录）；`tests/privacy/test_no_persistence.py:59–62`（另加 `TMPDIR`）
- 影响：快照不能证明 `task_handoffs/`、`tmp/`、`~/.cache` 等位置无写入；`test_check_writes_no_files` 的结论以其监视范围为限（ORT 遥测 outbox 由独立的 `test_ort_telemetry_disabled.py` 覆盖，不在此项内）。`__pycache__` / `*.pyc` 在全树 16 个目录存在，是解释器产物，测试明确排除（:196–201），不含用户数据。
- 复现：`find . -name __pycache__ -type d | wc -l`（16）；读 `t010_privacy_helpers.py:50,196–218`。
- 草稿来源：privacy F-08。

#### R-21 — P3：Chrome profile 临时目录清理不可靠，有残留

- 文件：`tests/e2e/cdp.py:392`（`tempfile.mkdtemp(prefix="textproof-chrome-")`）、`:459–476`（`stop()` 内 `shutil.rmtree(self.profile, ignore_errors=True)`）
- 影响：工作树 `tmp/` 下实测残留 `tmp/textproof-chrome-fvtgk8vn/`（无 Chrome 进程在跑），其内仅有 `Default/.org.chromium.Chromium.Network Persistent State.71CbMr` 一个锁文件，无浏览数据；另有 `tmp/org.chromium.Chromium.*` 单例目录残留。`ignore_errors=True` 使清理失败静默。残留物不含用户数据，记录即可；如需收紧，可在 `stop()` 后断言 profile 目录已消失。
- 复现：`ls tmp/ | grep -i chrom`（静态核对）。
- 草稿来源：privacy F-09。

#### R-22 — P3：`sys.path.insert(0, REPO_ROOT)` 的标准库遮蔽 footgun

- 文件：`src/textproof/cli.py:86–88`（**产品运行时**，每次 `check` 的 `_validate_report` 都执行）、`scripts/compute_s0_metrics.py:76–77`、`scripts/verify_s0.py:178–179`、`scripts/parity_check.py:73–74`、`scripts/independent_verify.py:67–68`、`scripts/consistency_check.py:50–52`、`scripts/benchmark_perf.py:58–59`；同模式见 `tests/conftest.py:13–15`
- 影响：把仓库根目录插到 `sys.path` 首位；当前根目录无与标准库同名文件，故无实际遮蔽，仅为纵深防御备注。若日后根目录出现 `json.py` 之类文件会被优先导入。
- 复现：`grep -rn 'sys.path.insert(0' src scripts tests/conftest.py`（静态核对）。
- 草稿来源：privacy F-10。

#### R-23 — P3：歧义判定按“不同对齐”而非规格字面的“不同路径”计数

- 文件：`src/textproof/core/align_lines.py`（模块 docstring 及 :225–251）；`tests/unit/test_core/test_align_lines.py:155–194`（穷举小 case 的暴力对照按配对集合比较，与实现一致）
- 影响：规格 §4.4/§7.2 写的是“两个最优对齐路径代价差小于 0.05”。若按字面路径计数，任一缺失+额外行对（两种 gap 顺序，代价差为 0）都会被判歧义，门禁将大面积误报 `REVIEW_REQUIRED`。实现按配对集合去重是唯一合理的读法，且有穷举测试背书。本条只是记录该解释未冻结成文。
- 复现：静态核对。
- 修复方向：在 §7.2 补一句“歧义按不同配对集合计，gap 顺序不同不计为不同对齐”。
- 草稿来源：contract F-05。

#### R-24 — P3：混淆对集合按穷尽处理，但规格用的是“如”（非穷尽措辞）

- 文件：`src/textproof/core/weighted_edit.py:95–107`（恰 6 对）；模块 docstring 明确承认“如”但只实现所列集合
- 影响：o/0、D/0、Z/2 等未列出的视觉混淆对按 1.00 而非 0.65 计费。只影响 DP 的对齐选择，不影响错误是否产生（字符不同必有记录，`classify.py` 保证）。规格未冻结更大的集合，实现是唯一可辩护的字面选择。
- 复现：静态核对。
- 修复方向：在 §4.5 把“如”改为“即以下集合”或补冻结扩展规则；不改代码。
- 草稿来源：contract F-06。

#### R-25 — P3：警告码 `POSSIBLE_MULTI_COLUMN` 与 `ROTATED_TEXT_NOT_SUPPORTED` 从未发出

- 文件：`src/textproof/core/report.py:201–260`（只发出 `LOW_OCR_CONFIDENCE` 与 `OCR_EMPTY`）；模块 docstring 说明无检测器故不发明
- 影响：§5.3 说警告枚举“至少包括”四码，schema 亦允许四码，子集发出合规；但 §7.6 提到的“不支持的布局警告”触发条件在 §4/§7 全书无定义，无法判定何时应发出。无错报、无漏报可言——规则本身缺失。
- 复现：静态核对。
- 修复方向：不建议凭空发明检测器；建议在规格中明确这两码是保留码、暂无检测器，或冻结检测规则后再实现。
- 草稿来源：contract F-07。

#### R-26 — P3：§7.6 承诺的空识别区分未实现——引擎失败与空识别均落为 `OCR_FAILED`

- 文件：`src/textproof/core/report.py:239–260`（无可用文本 → `OCR_FAILED` + `OCR_EMPTY`）；`src/textproof/api/routes.py:270–280`（引擎异常 → `ApiError CODE_OCR_FAILED`）
- 影响：§7.6 称“OCR 无可用文本时为 `OCR_FAILED` 或 `REVIEW_REQUIRED`，具体按引擎失败 / 空识别区分”，但未冻结哪种情形对应哪种 verdict；实现把两种情形都判为 `OCR_FAILED`（CLI exit 4）。无测试能区分二者，属解释空间而非可证伪的偏差。
- 复现：静态核对。
- 修复方向：在 §7.6 冻结映射（例如引擎异常 → `OCR_FAILED`，空识别 → `OCR_FAILED` 并附 `OCR_EMPTY`，或空识别 → `REVIEW_REQUIRED`），再据以实现。
- 草稿来源：contract F-08。

#### R-27 — P3：gap 连续段的错误输出顺序为 extra-then-missing，与直觉的 chronological 顺序相反

- 文件：`src/textproof/core/align_lines.py`（模块 docstring 已承认）、`src/textproof/core/report.py`；回溯段 :199–222（自后向前决定步骤）；`tests/unit/test_core/test_align_lines.py:71–80` 与 `tests/unit/test_core/test_report.py:253–260` 锁定该顺序（`["EXTRA_LINE", "MISSING_LINE"]`）
- 影响：配对集合正确，错误 id 顺序（E001/E002）与直觉的“先缺失后额外”相反。规格 §4.4 的平局规则约束的是对齐选择而非错误列表顺序，§5.4 亦未冻结错误排序，故合规；但下游按顺序消费错误列表时会看到该顺序。
- 复现：静态核对。
- 修复方向：在 §5.4 或 §7.2 注明错误按对齐顺序编号、gap 段顺序以回溯实现为准，或由 T013 改为 chronological 输出（需同步改两处锁定测试）。
- 草稿来源：contract F-09。

#### R-28 — P3：期望文本行数统计把尾随换行算作一行

- 文件：`src/textproof/io/image_loader.py:292–293`（`unified.split("\n")`；`"a\n"` 切出 `("a", "")` 计 2 行）；`:294–298`（>100 行拒绝）
- 影响：100 行文本加一个尾随换行会被判 101 行而拒绝，尽管用户直觉是 100 行。规格“最多 100 行”未定义尾随换行的计数方式；`normalize.py` 保留空行（行数诚实）与该计数一致。属边界口径问题。
- 复现：`python3 -c "print(len('a\n'.split(chr(10))))"` → 2。
- 修复方向：在 §4.2 注明尾随空行是否计入 100 行；不改代码。
- 草稿来源：contract F-10。

#### R-29 — P3：行聚合只与最后一行比较区间，链式并入与跨行重叠的口径未冻结

- 文件：`src/textproof/core/line_order.py:63`（按中心 y 访问）、`:70`（只与最后一行区间 `y1 <= hi and y2 >= lo` 比较）、`:72`（并入后区间取并集）、`:74`（否则开新行）
- 影响：区间通过链式重叠可无限延伸（如 A[0,20]、B[15,35]、C[30,50] 逐个并入同一行）；反之一个框与较早行重叠但与最后一行不重叠时会开新行。规格 §4.4 只说“按文本框垂直中心与纵向重叠聚合为行”，未冻结比较对象（全部行 / 最后一行）与传递性，实现是合理解读之一。
- 复现：静态核对。
- 修复方向：在 §4.4 冻结聚合口径（比较对象与是否允许链式并入）；不改代码。
- 草稿来源：contract F-11。

#### R-30 — P3：计划书引用的四处交付物在冻结候选内不存在（T012 验收命令当前无法执行）

- 文件：（缺失）`scripts/verify_release.py`、`release/` 目录、`scripts/verify_review_pack.py`、`review/REVIEW_INDEX.md`（审查前）
- 影响：IMPLEMENTATION_PLAN.md §1 要求 T014 以 `verify_release.py` PASS 收尾、T012 验收命令为 `python scripts/verify_review_pack.py review/REVIEW_INDEX.md`，但四者均不在冻结候选内。按计划分工，前两者属 T014、后两者属 T012/T014 的收尾工作，不构成 T001–T011 的契约违反；但 T012 的验收命令当前无法执行——本审查改以 REVIEW_INDEX.md（本审查新建，格式按计划 §13/§14 要求：每文件路径、字节数、SHA-256、行数、读取状态）作为覆盖证据，`verify_review_pack.py` 的缺失本身记为本条。
- 复现：`ls release/ scripts/verify_release.py scripts/verify_review_pack.py review/REVIEW_INDEX.md`（审查前均报不存在；REVIEW_INDEX.md 现由本审查创建）。
- 修复方向：T012 收尾时说明 `verify_review_pack.py` 的来源（新建或豁免），T014 补齐 `verify_release.py` 与 `release/`。
- 草稿来源：contract F-12；协调员亲自确认（全树 find 无 `verify_review_pack.py` 与 `verify_release.py`）。

#### R-31 — P3：`ENVIRONMENT.md` 称锁文件“共 33 个包”，实为 37 个

- 文件：`ENVIRONMENT.md §4`（“锁定的依赖（`requirements.lock`，共 33 个包，全部带精确版本与哈希）”）；对照 `requirements.lock` 实测 37 个包、753 个 SHA-256 哈希条目（`grep -cE '^[a-z0-9_.-]+==[0-9]'` = 37；`grep -c 'sha256:'` = 753）；lock SHA-256 `8726d13cb20bb731b491a4119629c176b699f035b75d8547d853ca3585d1564d` 与 ENVIRONMENT.md 记录一致（文件本身未变）
- 影响：仅文档数字错误（T001 构建者自述 33，主聊天 T001 验证时已记为 37）；锁文件本身无误。记录即可。
- 复现：见上两条 grep 命令。
- 草稿来源：协调员亲自核对（新增）。

## 3. 已明确排除的“非 finding”

以下三项在审查中被提出、核实后**不列为 finding**，T013 不得“修复”它们：

1. **`tool_version "0.1.0"` 与 pyproject `"1.0.0"` 不是不一致**：0.1.0 是冻结产品版本（PROJECT_BOOK §5.4 样例、IMPLEMENTATION_PLAN §0.3“产品版本初始目标：0.1.0”、API_CONTRACT.md:3、T009 口径决定），1.0.0 是打包版本，另有规格版本 1.0.0；三者在 CLI `version` 中已区分输出。简报所称“S0 裁决指出不一致”在本树 `S0_MAINCHAT_VERDICT.md` 全文 grep 中无文字可稽。
2. **￥ 不映射是正确的**：￥（U+FFE5）不在 §4.3 全角 ASCII 映射范围（U+FF01–U+FF5E）内，不映射是字面合规；NUM-001 live 多一条 SUBSTITUTION 是 OCR 读法所致，见 R-11，不得为消灭该条错误而给 §4.3 增加 ￥→¥ 映射。
3. **UI 数值写法 `393.0` vs `393` 不是三路分歧**：留存的 CLN-001 CLI 与 UI 两份报告仅差数值写法（UI 经 `JSON.stringify` 重序列化），数值语义相等；脚本按数值等值比较判 identical，符合其文档规则。

## 4. 协调员亲自执行的复核（证据索引）

| 复核项 | 命令 / 方法 | 结果 |
|---|---|---|
| 全量 pytest 重跑 | `TMPDIR=$PWD/tmp .venv/bin/python -m pytest -q -p no:cacheprovider`（日志 `review/pytest_rerun.log`） | **2 failed, 436 passed, 2 warnings, 226.79s, exit 1**；失败与主聊天重跑一致，构建者“438 passed”不可复现 |
| R-01 A 案（0.70 阈值） | `review/repro_f01.py`（case A） | 复现：d_w 28.000000000000004 → 代价 0.7000000000000001 → inf → [(None,0),(0,None)] |
| R-01 B 案（0.05 边界） | `review/repro_f01.py`（case B）+ `align_lines(["O"],["0"])` | 复现：浮点差 0.04999999999999993 < 0.05 → ambiguous=True；精确差恰好 0.05 |
| TP-S0-ZH-001 独立复核 | `scripts/independent_verify.py --case TP-S0-ZH-001`（live OCR） | PASS：PNG 哈希一致；OCR 认出“限时优”；MISSING_CHARACTER span [3,4]/[3,3]；bbox [491,190,713,291]；IoU 0.964；Oracle 完全一致 |
| R-04 运行时复核 | /tmp 独立副本（`git worktree add --detach /tmp/f04-probe ffe53ea`），隐藏一个模型文件，起真实 API 服务，POST /api/v1/check | 证实：HTTP 500；server.log 含绝对路径 traceback（FileNotFoundError，链 routes.py:328→:267→:172→adapter :173→:210）；探针副本已清理 |
| METRICS 交叉核对 | `METRICS_REPORT.json` vs `task_handoffs/T011/s0/s0_metrics.json` | 一致：召回 201/201（70/70、71/71、60/60），CER 0.00080128（S=1、D=1、I=0、N=2496） |
| tool_version 口径 | 读 IMPLEMENTATION_PLAN §0.3、T009 TASK_RESULT.md 口径决定节、grep S0_MAINCHAT_VERDICT.md | 三版本不同维度，无冲突；S0 裁决文件无相关文字 |
| 资产哈希抽查 | `sha256sum` 模型/字典/字体（子审查员全量；协调员抽查 lock 计数与 SHA） | 3 模型 + 字典 + 字体 + OFL 全部匹配；lock 37 包 / 753 哈希，SHA 与 ENVIRONMENT.md 记录一致 |
| 盲测子集 | 程序核对 `blind_subset.json` vs `manifest.json` | 60 张，20/14/14/12，全部属于 manifest；expected_output.json 300 条 |

## 5. 给 T013 的交接

- **P1 必修（4 项）**：R-01（align_lines 精确算术 + 回归测试，含 A 案 40 字符行与 B 案 0.05 边界）、R-02（consistency_check.py 移入 `tests/` + 同修 R-07 回环断言；同步更新两处文档命令路径）、R-03（字典许可复核——属 T014 发布门，T013 须确认责任方与截止点，不得在 T013 内静默放行公开分发）、R-04（adapter 报错去绝对路径 + 资产缺失日志断言测试）。
- **P2（7 项）**：R-05、R-06、R-07、R-08、R-09、R-10、R-11——逐项修复或书面记录为非阻断并说明影响；R-11 的两种修复方向二选一，不得增加 ￥→¥ 映射。
- **P3（20 项）**：R-12…R-31——酌情处理；其中 R-13（LICENSE/README/SECURITY）与 R-03 同属 T014 发布打包；R-30（verify_review_pack.py / verify_release.py 缺失）须在 T013/T014 交接时明确来源。
- **禁止**：不得为通过测试而改测试预期、fixture 原图、manifest 或 S0 阈值；不得把 `tool_version` “修复”为 1.0.0；不得缩小 T010 隐私扫描范围、不得加白名单、不得用 curl 绕过（R-02 裁决已定）。
- **复审要求**：修复后由新的独立会话复审（非原修复者自评）；复审须重跑全量 pytest、S0、离线与隐私测试并全部通过；P0/P1 = 0 方可进 T014。
- **未覆盖的残余风险**：14 项部分读文件（见 REVIEW_INDEX.md，以 grep/节选/程序核对 + 全量 pytest 436 passed 佐证，未全文读）；`tests/e2e/cdp.py` 未全文读（Chrome 驱动实现细节）；外部 URL 内容（RapidOCR 许可页、ModelScope、PaddleOCR 上游）未验证可达性——哈希与本地文件一致已核。

## 6. 审查过程记录

- 协调员未合并任何东西，未改 main（main 仍为 `b0885dd`）；审查期间对冻结候选 commit `ffe53ea` 的唯一写操作在 `review/` 内（本文件、`REVIEW_INDEX.md`、`repro_f01.py`、`pytest_rerun.log`、`drafts/` 三份草稿）。
- 工作树脏状态说明（审查前已存在，非审查造成）：`task_handoffs/T006/live_ocr_results.jsonl` 与 `s0_metrics.json` 被主聊天/S0 重跑改动过（未提交）；`tests/e2e/evidence/` 与 `tmp/` 为测试运行产物（未追踪）。审查未改动 `src/`、`tests/`（除测试运行产物外）、`scripts/`、`schemas/`、`oracle/`、`assets/`、`requirements.lock`、`pyproject.toml` 的任何追踪文件——`git status` 可验。
- F-04 探针副本（/tmp/f04-probe）已删除并取消 worktree 注册；探针服务已停（端口 8899 无监听）。
- 附注：审查中一次 `pkill -f` 误杀了执行它的 shell 自身（命令行含被杀模式串），属已知 shell 陷阱；已改按端口/PID 核查，未影响审查结论。
