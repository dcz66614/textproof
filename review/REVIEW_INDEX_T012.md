# P033 TextProof — T012 审查索引（REVIEW_INDEX.md）

- 审查对象：冻结候选 commit `ffe53ea1fb7e1d31f536abd732c258ffc50aae56`（分支 `t011-full-regression`），工作树 `~/workspace/p033-textproof-t011`
- 审查报告：`review/REVIEW_FINDINGS.md`（findings R-01…R-31：P1 × 4、P2 × 7、P3 × 20，P0 × 0）
- 本表每行的字节数、SHA-256、行数均取自冻结 commit 本身（`git show HEAD:<path>`），不受工作树脏文件影响。
- 覆盖率：**全文读 61 / 应读 75（81.3%）**；部分读 14；未读 0。
  - “应读”= 代码与数据文件 67（src/ 20、scripts/ 9、oracle/ 2、schemas/ 1、tests/ 35）+ 规格与配置文档 8。
  - 不计入分母：300 张 fixture PNG（数据文件，其 SHA 由 verify_s0.py 重算验证）；`tests/e2e/evidence/` 下 2 个未追踪的测试运行产物；`__pycache__`。
  - 14 项部分读的共同佐证：其行为由协调员亲自重跑的全量 pytest（436 passed）覆盖；oracle 文件另由 S0 parity 300/300 与 ZH-001 独立复核佐证；fixture JSON 由程序核对。

## 1. 覆盖表

| 文件 | 字节数 | SHA-256 | 行数 | 读取状态 | 备注 |
|---|---:|---|---|---|---|
| `PROJECT_BOOK.md` | 44552 | `0fc4ef3bb5925326…` | 771 | 部分读 | §4–§10 全文读；§0–§3、§12–§16 未读（不在 §4–§9 验收范围内） |
| `IMPLEMENTATION_PLAN.md` | 35772 | `2d2ac3f3b6eec920…` | 632 | 全文读 | contract 子审查全文 632 行 |
| `API_CONTRACT.md` | 8218 | `32209a2cb1c2dbef…` | 177 | 全文读 | assets 子审查全文 |
| `ENVIRONMENT.md` | 5173 | `f5132aa65acf3556…` | 97 | 全文读 | 协调员全文 97 行 |
| `THIRD_PARTY_NOTICES.md` | 7995 | `d6ef530a6620883d…` | 138 | 全文读 | assets 子审查全文 |
| `pyproject.toml` | 1249 | `5bcebcc11ab184e5…` | 38 | 全文读 | assets 子审查全文 |
| `requirements.lock` | 66057 | `8726d13cb20bb731…` | 858 | 全文读 | assets 子审查全文浏览 + 精确行核对 |
| `tests/fixtures/s0/fonts/FONT_NOTICE.md` | 1840 | `026cca64f5143dbe…` | 33 | 全文读 | assets 子审查全文 |
| `src/textproof/__init__.py` | 219 | `e232dd2b615ad7e4…` | 8 | 全文读 | privacy + contract |
| `src/textproof/api/__init__.py` | 1639 | `fabf726b5c51ba6d…` | 45 | 全文读 | privacy + contract |
| `src/textproof/api/app.py` | 6816 | `1f11d0a29a871186…` | 195 | 全文读 | privacy + contract + assets |
| `src/textproof/api/routes.py` | 12819 | `4ac80099e11cda23…` | 374 | 全文读 | privacy + contract + assets |
| `src/textproof/cli.py` | 13257 | `e6bd45bdee373dd8…` | 342 | 全文读 | privacy + contract + assets |
| `src/textproof/contracts.py` | 6901 | `bda7c3cc4ced5d2c…` | 170 | 全文读 | privacy + contract + assets |
| `src/textproof/core/__init__.py` | 1525 | `c9f14b8c7b9eab1e…` | 62 | 全文读 | privacy + contract |
| `src/textproof/core/align_lines.py` | 9676 | `2f1d96ab50b8a74a…` | 258 | 全文读 | privacy + contract + 协调员（F-01 复现） |
| `src/textproof/core/classify.py` | 10158 | `24269e43a5de0997…` | 276 | 全文读 | privacy + contract + assets（节选） |
| `src/textproof/core/line_order.py` | 3723 | `1cd7d449d6b8a7c0…` | 104 | 全文读 | privacy + contract + assets（节选） |
| `src/textproof/core/normalize.py` | 4756 | `8e4ba5e1c67b205b…` | 130 | 全文读 | privacy + contract + assets |
| `src/textproof/core/report.py` | 14069 | `78479b9996da0929…` | 390 | 全文读 | privacy + contract + assets |
| `src/textproof/core/weighted_edit.py` | 8127 | `4a1f207576218760…` | 233 | 全文读 | privacy + contract |
| `src/textproof/io/__init__.py` | 299 | `1384c9dd8046da9f…` | 15 | 全文读 | privacy + contract |
| `src/textproof/io/image_loader.py` | 10844 | `4ce009315c1c9ecd…` | 304 | 全文读 | privacy + contract + assets（节选） |
| `src/textproof/ocr/__init__.py` | 66 | `6df53f43ddb2a2c9…` | 1 | 全文读 | privacy + contract |
| `src/textproof/ocr/rapidocr_adapter.py` | 17757 | `e4f54b23c584911b…` | 422 | 全文读 | privacy + contract + assets |
| `src/textproof/ui/index.html` | 3393 | `5de3f39e260f9740…` | 86 | 全文读 | privacy 全文 |
| `src/textproof/ui/app.js` | 18134 | `066c64a376963525…` | 512 | 全文读 | privacy 全文 + assets（关键段） |
| `src/textproof/ui/style.css` | 4590 | `bfac91af09d053fe…` | 221 | 部分读 | grep 核对（无 @font-face / url( / 外部引用） |
| `scripts/benchmark_perf.py` | 11178 | `f0f1d3d5564b8def…` | 296 | 全文读 | privacy 全文 |
| `scripts/compute_s0_metrics.py` | 19734 | `70f8b09855f2d4f6…` | 460 | 全文读 | privacy 全文；contract 节选复核 gate_pass |
| `scripts/consistency_check.py` | 10664 | `0c4a8a8fccc07dcd…` | 272 | 全文读 | privacy + assets 全文 |
| `scripts/env_probe.py` | 3594 | `41b7cf5c7776f756…` | 113 | 全文读 | privacy 全文 |
| `scripts/generate_fixtures.py` | 40131 | `261e4b12193323e9…` | 888 | 全文读 | privacy 全文；assets 字体相关行 |
| `scripts/independent_verify.py` | 13865 | `48c112e88dd82708…` | 303 | 全文读 | privacy 全文；协调员运行 ZH-001 复核 |
| `scripts/parity_check.py` | 18327 | `82309bd4f744d857…` | 397 | 全文读 | privacy 全文 |
| `scripts/validate_report_schema.py` | 20161 | `84b7a27a4b604c3c…` | 455 | 全文读 | privacy + assets 全文 |
| `scripts/verify_s0.py` | 16817 | `4ec3e58a5b3d55d3…` | 354 | 全文读 | privacy + contract 全文 |
| `oracle/__init__.py` | 146 | `a2613c46c556b794…` | 5 | 全文读 | 协调员全文 5 行 |
| `oracle/reference_compare.py` | 29172 | `afb372da91ac762e…` | 751 | 部分读 | docstring + 结构 + 全模式 grep；行为由 S0 parity 300/300 与 ZH-001 独立复核佐证 |
| `schemas/textproof.report.v1.schema.json` | 14575 | `b8028e3eeea7bff7…` | 466 | 全文读 | assets + contract 全文 |
| `tests/conftest.py` | 531 | `fc93418905888936…` | 15 | 全文读 | 协调员全文 15 行 |
| `tests/e2e/cdp.py` | 16988 | `47009d9af065df2c…` | 476 | 部分读 | grep 核对 tempfile/subprocess/rmtree 相关行；未全文读 |
| `tests/e2e/conftest.py` | 3601 | `8f73712200ac42af…` | 124 | 部分读 | grep 核对；行为由全量 pytest 佐证 |
| `tests/e2e/test_ui_browser.py` | 14115 | `ccc834bd9292cef9…` | 324 | 部分读 | grep 核对；行为由全量 pytest 佐证 |
| `tests/e2e/test_ui_static.py` | 6630 | `33121c2e57303ca6…` | 177 | 全文读 | privacy 全文 |
| `tests/integration/test_api.py` | 20768 | `e91b3b3cd9dd66d0…` | 556 | 部分读 | assets 节选 :28,76,244-280；行为由全量 pytest 佐证 |
| `tests/integration/test_cli.py` | 22288 | `1fe47b4ebdbbda48…` | 596 | 部分读 | grep 核对；行为由全量 pytest 佐证 |
| `tests/integration/test_ocr_adapter.py` | 9476 | `bde07674a724a0d1…` | 262 | 部分读 | assets 节选 :38-39,192-231；行为由全量 pytest 佐证 |
| `tests/offline/_serve_probe.py` | 3215 | `50a33630c18093ee…` | 89 | 全文读 | privacy 全文 |
| `tests/offline/conftest.py` | 715 | `273f7edc7f8e6a83…` | 25 | 全文读 | privacy 全文 |
| `tests/offline/t010_offline_helpers.py` | 1889 | `f8e62ffc95aa924a…` | 63 | 全文读 | privacy 全文 |
| `tests/offline/test_offline_namespace.py` | 6369 | `5e5b6dea00bacf5d…` | 155 | 全文读 | privacy 全文 |
| `tests/offline/test_offline_static.py` | 2661 | `bb6297c1ab88af98…` | 64 | 全文读 | privacy 全文 |
| `tests/offline/test_strace.py` | 3166 | `0bbb86f8a7806fe8…` | 91 | 全文读 | privacy 全文 |
| `tests/oracle/test_reference_compare.py` | 25575 | `2ad774444d2210dc…` | 609 | 部分读 | grep 核对；行为由全量 pytest 佐证 |
| `tests/privacy/conftest.py` | 2092 | `36e3632f02058590…` | 75 | 全文读 | privacy 全文 |
| `tests/privacy/t010_privacy_helpers.py` | 7987 | `509eff9d3705b521…` | 218 | 全文读 | privacy 全文 |
| `tests/privacy/test_local_assets.py` | 5002 | `6e53815e69e01b1d…` | 126 | 全文读 | privacy 全文 |
| `tests/privacy/test_loopback_and_fail_closed.py` | 9203 | `c7eff4387fc1f453…` | 241 | 全文读 | privacy 全文 |
| `tests/privacy/test_no_external_requests.py` | 4257 | `d14f9088f370c6fa…` | 109 | 全文读 | privacy 全文 |
| `tests/privacy/test_no_persistence.py` | 9147 | `da35b0b2f62d172e…` | 245 | 全文读 | privacy 全文 |
| `tests/privacy/test_ort_telemetry_disabled.py` | 2838 | `bd730cfd44dfd78b…` | 68 | 全文读 | privacy 全文 |
| `tests/privacy/test_ui_clear_privacy.py` | 8066 | `bd390525bc861604…` | 225 | 全文读 | privacy 全文 |
| `tests/s0/test_s0_gate.py` | 7225 | `af48acd901af820f…` | 169 | 全文读 | contract 全文 |
| `tests/unit/test_core/test_align_lines.py` | 6540 | `83a8349dfe030bdf…` | 194 | 全文读 | contract 全文 |
| `tests/unit/test_core/test_classify.py` | 4825 | `d554644f840023ff…` | 134 | 全文读 | contract 全文 |
| `tests/unit/test_core/test_line_order.py` | 2938 | `66d3db854ffe36b9…` | 100 | 全文读 | contract 全文 |
| `tests/unit/test_core/test_normalize.py` | 2624 | `efe17a5efdee30b4…` | 79 | 全文读 | contract 全文 |
| `tests/unit/test_core/test_report.py` | 12117 | `136a27b469f89aea…` | 326 | 全文读 | contract 全文 |
| `tests/unit/test_core/test_weighted_edit.py` | 4061 | `c84e38cc0a02d853…` | 123 | 全文读 | contract 全文 |
| `tests/unit/test_fixtures_s0.py` | 7149 | `3546d61a229b2713…` | 175 | 全文读 | contract 全文 |
| `tests/unit/test_image_loader.py` | 17956 | `ff5bd365276b76e6…` | 529 | 部分读 | grep 核对；行为由全量 pytest 佐证 |
| `tests/fixtures/s0/manifest.json` | 302924 | `cc9a0ea9ed75fda8…` | 12550 | 部分读 | 程序核对：计数 + 4 条 S0 人工读；300 条 SHA 由 verify_s0 重算通过 |
| `tests/fixtures/s0/expected_output.json` | 175217 | `a2e55725a2c8ffdb…` | 6805 | 部分读 | 程序核对：4 条 S0 人工读；300 条与 manifest 一致 |
| `tests/fixtures/s0/blind_subset.json` | 7722 | `a90fb851cd02e9f9…` | 257 | 部分读 | 程序核对：60 张 20/14/14/12，全部属于 manifest |

## 2. 六项验收结论（与 REVIEW_FINDINGS.md §1 一致）

| 验收 | 结论 |
|---|---|
| 1. §4–§9 契约与实现一致 | 基本一致：P1 × 1（R-01）、P2 × 1（R-11）、P3 × 8；其余 PASS |
| 2. 模型/字典/字体许可与离线资产哈希 | 哈希与版本全部一致；P1 × 1（R-03 字典许可 UNVERIFIED）、P3 × 2 |
| 3. TP-S0-ZH-001 独立复核 | PASS（协调员亲自运行 independent_verify.py，live OCR；IoU 0.964；Oracle 一致） |
| 4. JSON schema、CLI exit code、API/UI/CLI 一致性 | 主干一致；P2 × 2（R-05、R-06）、P3 × 3 |
| 5. 日志、缓存、临时文件、网络访问、loopback 绑定 | 产品侧基本通过；P1 × 2（R-02、R-04）、P2 × 2（R-07、R-08）、P3 × 6 |
| 6. 每 finding 含路径、行号、影响、复现命令、严重级别 | 满足（31 条全部） |
| 7. 覆盖率（全文读 / 应读） | **61 / 75（81.3%）**；部分读 14；未读 0 |

## 3. 审查证据索引

| 证据 | 位置 | 说明 |
|---|---|---|
| 审查报告正本 | `review/REVIEW_FINDINGS.md` | findings R-01…R-31，逐项验收结论，T013 交接 |
| 本索引 | `review/REVIEW_INDEX.md` | 覆盖表（本文件） |
| R-01 复现脚本 | `review/repro_f01.py` | 双案复现；exit 0 = 缺陷存在，修复后应 exit 1 |
| 全量 pytest 重跑日志 | `review/pytest_rerun.log` | 协调员亲自重跑：2 failed, 436 passed, 2 warnings, 226.79s, exit 1 |
| 契约一致性草稿 | `review/drafts/contract.md` | §4–§9 逐条核对表；findings 12 项 |
| 资产/模式草稿 | `review/drafts/assets_schema.md` | 哈希核对表；findings 9 项 |
| 隐私/网络草稿 | `review/drafts/privacy_network.md` | grep 命中总表；findings 10 项 |
| T011 构建者报告 | `task_handoffs/T011/TASK_RESULT.md` | 称 438 passed（本审查重跑不复现，见 R-02） |
| T011 主聊天裁决 | `T011_MAINCHAT_VERDICT.md`（主工作树） | T011 不通过；修复方向：脚本移出扫描树；先 T012 审后 T013 修 |
| S0 主聊天裁决 | `S0_MAINCHAT_VERDICT.md` | S0 PASS；F-01→T013 P1；F-03→T009；NUM-001 按类型计数读法 |
| S0 报告 | `S0_REPORT.md` | S0 证据集；F-01–F-04 记录 |
| T011 指标/性能报告 | `METRICS_REPORT.json`、`PERFORMANCE_REPORT.md`、`FULL_TEST_REPORT.md` | 协调员抽查 METRICS 与 s0_metrics 一致 |

## 4. 说明与残余风险


- 计划书 T012 验收命令 `python scripts/verify_review_pack.py review/REVIEW_INDEX.md` 无法执行：该脚本在冻结候选内不存在（全树 find 确认；见 REVIEW_FINDINGS.md R-30）。本索引按计划 §13/§14 要求的格式（路径、字节数、SHA-256、行数、读取状态）编制，可供该脚本建成后直接校验。
- `review/REVIEW_INDEX.md` 本身在审查前不存在，由本审查新建；T014 将其定稿为发布证据索引。
- 工作树脏状态（审查前已存在）：`task_handoffs/T006/live_ocr_results.jsonl` 与 `s0_metrics.json` 被 S0 重跑改动过（未提交）；`tests/e2e/evidence/` 与 `tmp/` 为测试运行产物（未追踪）。本表数据取自 commit，不受其影响。
- 未覆盖的残余风险：14 项部分读文件（见上表）；`tests/e2e/cdp.py` 未全文读；外部 URL 内容（RapidOCR 许可页、ModelScope、PaddleOCR 上游）未验证可达性——哈希与本地文件一致已核。
