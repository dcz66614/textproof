# T009 — CLI、JSON schema 与导出：TASK_RESULT

- 分支：`t009-cli-schema`（基于 master `3e9c3e8`，T008 已合入，S0 PASS）
- 工作目录：`~/workspace/p033-textproof-t009`（worktree；主 worktree 未动）
- 验收命令：`python -m pytest tests/integration/test_cli.py -q`
  → **40 passed，0 failed**（`.venv` Python，11.16s；日志见 `test_stdout.log`，
  stderr 为空）
- 回归（校验器收紧的影响面）：
  - `tests/unit + tests/integration/test_api.py + tests/oracle`：**244 passed**
  - `tests/s0`：**12 passed**
  - CLI `verify-s0` 重跑 S0（复用缓存的 300 条 live 结果，`s0_rerun/`）：
    **S0 VERDICT: PASS，exit 0**——四案全 PASS、parity 固定记录 300/300、
    召回 100%、clean 误报 0%、schema 合法率 100%（收紧后的校验器）、
    IoU 最小 0.829、CPU-only。

## 逐项验收对照

| # | 验收标准 | 结果 |
|---|---|---|
| 1 | `check`、`serve`、`verify-s0`、`version` 四条命令可用 | PASS。真实运行各至少一次（`commands/`）：`version` exit 0；`check` 真实 OCR：ZH-001 exit 1（MISMATCH，1 条 MISSING_CHARACTER `惠`）、干净图 exit 0（MATCH）、空白图 exit 4（OCR_FAILED）；`serve` 真实子进程绑 127.0.0.1:8899，`/api/v1/health` 返回 `ok`，`/api/v1/version` 正确；`verify-s0` exit 0，S0 PASS。 |
| 2 | `check` 输出与 API 相同 JSON schema | PASS。`check` 直接调用 T007 `run_check`（同一比较路径：T002 `load_image` + T003 `RapidOCRAdapter` + T004 `build_report`，无第二套错误算法）；测试 `test_check_output_matches_api` 断言同一输入下 CLI 报告 dict 与 API `run_check` 返回 dict 完全相等，且两者都通过校验。 |
| 3 | 退出码 0–5 与 §5.5 一致 | PASS，逐码有测试：0 MATCH、1 MISMATCH、2 REVIEW_REQUIRED（低置信警告）、3 输入无效（缺失文件/垃圾图片/空期望/超长期望/非法 UTF-8/不可写 `--json` 路径/用法错误）、4 OCR 失败（引擎抛错；verdict OCR_FAILED 亦为 4）、5 内部错误（`run_check` 抛未预期异常；生成的报告自校验失败亦为 5）。argparse 用法错误改为 exit 3（argparse 默认 2 与 REVIEW_REQUIRED 冲突，已在 `cli.py:_Parser` 中覆盖并测试）。 |
| 4 | JSON 导出不含图片 base64、绝对路径、用户 home path | PASS。测试用位于用户 home 下的临时目录中的输入跑 `check`，断言 stdout 中无 home 路径、无图片绝对路径、无图片 base64、无 `image_base64` 字段；stderr 同样不含路径（文件读取失败只报固定文案不复述路径；`ApiError.detail` 只是 snake_case 码）。 |
| 5 | 所有报告通过 JSON Schema 校验 | PASS。7 个样例报告（S0 四案固定报告 + CLI 真实 OCR 的 MISMATCH/MATCH/OCR_FAILED 各 1）手工校验器 **7/7 VALID**，系统 `jsonschema`（仅作证据交叉校验，不在冻结锁中、不是测试依赖）**7/7 VALID**；schema 文件本身是合法 draft 2020-12。Oracle 形态的 4 类否定变体（见 F-03）手工校验器与 jsonschema 均 **4/4 拒绝**。 |

## F-03 口径统一决定（P1，规格澄清）

S0 报告发现的三处规格未写明处，T009 冻结为**生产侧已有写法**，只允许一种，
写入 `schemas/textproof.report.v1.schema.json` + 收紧的
`scripts/validate_report_schema.py`（两者口径一致，报告须同时通过两者）：

1. **行级错误缺失侧 span 一律 `null`**（MISSING_LINE 的 `recognized_span`、
   EXTRA_LINE 的 `expected_span`、AMBIGUOUS_ALIGNMENT 的双侧 span）。
   拒绝 Oracle 的 `[0, 0]`。理由：
   - `[0, 0]` 已有真实含义：字符缺失在行首时空 span 就是 `[0, 0]`
    （例：`MISSING_CHARACTER` 的 `recognized_span [0, 0]`），不能同时表示“无此侧”；
     `null` 与“无此侧”一一对应，无歧义。
   - 与同对象的其他缺失侧字段一致：`expected_line_index`/`ocr_line_index`、
     `bbox_xyxy`、`confidence` 在缺失侧时已全是 `null`；`§4.3.6` 规定 span 索引进
     “规范化行文本”，缺失侧根本没有行文本可供索引。
   - 生产实现（T004）自始就是 `null`；冻结为生产写法使既有输出**零改动**。
2. **`bbox_scope` 一律 `"ocr_line"`（有框时）或 `null`（无框时）**；拒绝 `"none"`。
   理由：`§5.4` 只定义了 `"ocr_line"` 这一个取值，`"none"` 无原文依据；
   `null` 是生产已有写法，且与 `bbox_xyxy: null`、`confidence: null` 一致。
3. **警告对象形态：一律 `{code, message}`，仅 `LOW_OCR_CONFIDENCE` 附加
   `ocr_line_index`；无 `confidence` 字段。**理由：`§5.3` 只规定警告码枚举，
   未规定对象形态；行置信度已存在于 `ocr_lines[]` 条目与错误对象中，警告再带一个
   `confidence` 含义未定义（是哪条行的？与 `ocr_line_index` 是否一致？），属于重复
   数据；生产已有写法即此形态。

统一后确认：生产代码（`report.py`/`classify.py`）**一行未改**，既有输出数值/语义
不变——S0 四案固定报告逐项仍 PASS，parity 固定记录仍 **300/300**，S0 重跑仍 PASS
（见上）。边缘电池仍为 13/26（与 T006 相同）：那是生产与 Oracle 之间的诊断性差异，
Oracle **有意不改**——它是独立参照实现，不是生产报告，不受生产 schema 约束；
parity 门禁范围（300 固定记录）不受影响。

## tool_version 口径决定

- `tool_version` 保持 **`"0.1.0"`**，不改 `pyproject.toml`。
- 三个版本号含义不同，不存在真正的冲突：
  - 产品版本 `tool_version = "0.1.0"`：IMPLEMENTATION_PLAN §0.3“产品版本初始目标：
    `0.1.0`”；PROJECT_BOOK §5.4 样例写明 `"tool_version": "0.1.0"`；报告字段。
  - 规格版本 `spec_version = "1.0.0"`：PROJECT_BOOK v1.0.0 / IMPLEMENTATION_PLAN §0.3。
  - 打包版本 `pyproject.toml version = "1.0.0"`：包的发行版本，数值上与规格版本
    相同但属于不同维度的编号（包版本 ≠ 产品版本）。
- `version` 命令同时输出三者并加标签区分（`tool_version` / `package_version` /
  `spec_version`），外加 `rapidocr_version 3.10.0`、`onnxruntime_version 1.32.0`、
  `providers ["CPUExecutionProvider"]`、`schema textproof.report/v1`。
  开发 checkout 中包未安装时 `package_version` 诚实报告 `"not-installed"`，
  不编造数字。

## 实现说明

- 新增：`src/textproof/cli.py`（argparse，标准库；四命令均为薄封装）、
  `schemas/textproof.report.v1.schema.json`（draft 2020-12，`$id`
  `https://textproof.local/schemas/textproof.report.v1.schema.json`）、
  `tests/integration/test_cli.py`（40 测试）。
- 修改：`scripts/validate_report_schema.py` 仅收紧为冻结口径——`tool_version`
  须恰为 `"0.1.0"`；`bbox_scope` 只接受 `"ocr_line"`/`null`；按错误类型强制
  span 形态（MISSING_LINE/EXTRA_LINE/AMBIGUOUS_ALIGNMENT 的缺失侧 span 为
  `null`，字符错误双侧 span 必有，MISSING_LINE/EXTRA_LINE 的缺失侧行索引为
  `null`）；警告对象只允许 `{code, message, ocr_line_index?}` 且
  `ocr_line_index` 仅 `LOW_OCR_CONFIDENCE` 可带；`ocr_lines[].confidence`
  须为 [0,1] 数字。CLI `check` 在写出前用该校验器自检报告，自检失败 → exit 5。
- 未改动：`report.py`、`classify.py`、Oracle、parity 脚本、`pyproject.toml`、
  `requirements.lock`（无新增依赖；`jsonschema` 仅在系统 Python 上作证据交叉
  校验，不进锁、不进测试）。离线：全程无网络访问。
- `verify-s0` 是 `scripts/verify_s0.py` 的子进程薄封装（不复制逻辑），透传
  `--manifest/--blind/--expected-output/--out-dir/--force-live`，退出码原样透传；
  manifest 缺失时先 exit 3。

## 发现的问题（诚实记录）

1. **schema 文件初版 `$id` 写错**：初版 `$id` 用了报告 schema 名
   `"textproof.report/v1"`（不是合法 URI），导致 `jsonschema` 解析相对 `$ref`
   时报 `RefResolutionError: unknown url type`。已修正为合法 URI
   `https://textproof.local/schemas/textproof.report.v1.schema.json`；
   报告内 `schema` 字段值仍为 `textproof.report/v1`（§5.1 名称，与 `$id`
   是两个东西，已在 schema 描述中注明）。修正后 jsonschema 交叉校验全过。
   该问题由交叉校验抓到，手写校验器本身不受影响（它不解析 `$id`）。
2. **否定用例脚本取错条目**：第一次跑 jsonschema 否定校验时，脚本改了
   `errors[0]`（MISSING_CHARACTER），`[0, 0]` 对字符错误是合法空 span，
   误报为“未拒绝”。实为脚本错误：MISSING_LINE 是 `errors[1]`。修正为按
   `type == "MISSING_LINE"` 定位后，4/4 否定变体均被拒绝。测试文件中的否定
   用例自始就是按类型定位的，未受此影响。
3. **`package_version` 在开发 checkout 中为 `"not-installed"`**：包未装进
   venv，测试以源码运行，故 `version` 诚实报告未安装；安装后会显示 `1.0.0`。
   这不是缺陷，是有意的诚实回退（见上）。
4. **边缘电池仍 13/26**：与 T006 相同，属诊断范围、非门禁范围；其中 R 组差异
   是 Oracle 保留了自己的表示法（见 F-03），生产侧已统一。终审前不得再出现
   两种生产口径——现已不存在。
5. **无其他失败**：验收命令 40/40；回归 244 + 12 全部通过；S0 重跑 PASS。

## 交接包内容（`task_handoffs/T009/`）

- `TASK_RESULT.md`（本文件）、`changed_files.txt`、`test_stdout.log`、
  `test_stderr.log`（空）、`exit_codes.txt`
- `commands/`：四条命令真实运行日志——`version.out/.err`、
  `check_zh001.out/.err`（exit 1）、`check_clean.out/.err`（exit 0）、
  `check_blank.out/.err`（exit 4）、`serve.out/.err` +
  `serve_health.out`（health `ok` + version）
- `samples/`：`report_zh001_mismatch.json`（真实 OCR）、
  `report_clean_match.json`、`report_ocr_failed.json`、
  `s0_fixed_TP-S0-*.json`（四案固定报告）
- `schema_validation_report.txt`：手工校验器 7/7 + jsonschema 7/7 + 否定 4/4
- `s0_rerun/`：CLI `verify-s0` 重跑证据（`verify_s0_cli.log`、
  `s0_metrics.json`、`parity_report.json`、`schema_validation.log`、
  缓存的 `live_ocr_results.jsonl` 300 条）
