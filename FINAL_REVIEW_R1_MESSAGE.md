# P033 TextProof（字证）— 终审第 1 轮（新对话）

本消息是 P033 TextProof 的终审第 1 轮。请按冻结规格（v1.0.0）逐项核对提交物，独立验证你能验证的一切（文件哈希、文件清单、关键命令与指标），不要只复述我方结论。结论请按 §9 的格式给出，以 `FINAL_VERDICT: PASS` 或 `FINAL_VERDICT: FAIL` 收尾。

立项对话（构思 + 规格）：https://chatgpt.com/g/g-p-6ade5013e8ec8191b55dca46c27772e1-agent-project-automatic/c/6b062d7b-1ef0-83ed-b2dc-93478ac67246（GPT-6.2 + Extra High；构思思考 32m11s）。本轮终审在新对话进行，是终审第 1/5 轮。

请使用谷歌云盘以及任何需要的插件，如果有了的话就算了。

## 1. 项目与冻结身份

- **项目**：TextProof（字证）——AI 生成图片文字确定性校验器：本地 OCR + 字符级加权编辑距离，逐字证明图片文字是否符合用户期望文本；每条差异锚定到文本框坐标（bbox）；输出 `textproof.report/v1` JSON 报告；提供 CLI、本地 FastAPI（仅 loopback）与本地 Web UI。
- **目标用户**：中文创作者 / 电商卖家，用 ComfyUI / Qwen 生成带文字海报，需逐字核对海报文字（错字、缺字、数字错误）。
- **技术路线**：RapidOCR 3.10.0（ONNX Runtime 1.32.0，CPU-only）本地识别；字符级加权编辑距离比较；合成数据测试；全程离线，零真人参与；许可证 MIT。
- **规格**：v1.0.0，FROZEN 2026-11-25 ~01:39 GMT，VERIFIED ~01:51 GMT（主聊天亲自下载核对：四份规格文件大小与 SHA-256 与 GPT 给出值一致；DOCX 标题/表格与 MD 同步 67/40、14/4）。T001–T014，88h。
- **冻结 commit**：`93d1b7c65036bb16f596117f26a48f6ee62f99e1`（T014R3，R14-01 修复）；集成线 `t014-fix` HEAD `a9eb45f`；已合并进 master，合并提交 `16a3ef5`。
- **版本**：tool_version（产品报告版本）`0.1.0`；package_version（打包版本）`1.0.0`；spec_version（规格版本）`1.0.0`。三者是三个不同维度，不是版本不一致——请勿要求把 tool_version“修正”为 1.0.0。
- **冻结产物**：`source.zip`（512,109,756 B，SHA-256 `9c2305ed715e0e74e459e73348418a7011890a474af04cdc4de451a456d2c235`，699 个追踪文件）；wheel `textproof-1.0.0-py3-none-any.whl`（27,176,403 B，SHA-256 `9c880b88e401c618c91426c3009b3153c7da682fe461e42eb9802a55f33372a1`，32 条目，无字典文件）；wheelhouse 37 个 wheel（151,973,630 B，与 `requirements.lock` 37 包逐一对应）；`RELEASE_MANIFEST.json`（10 条 files + 37 条 wheelhouse 哈希/大小）；`SHA256SUMS.txt`；`SBOM_LICENSES.md`。

## 2. 规格要点（冻结 v1.0.0，§号为 PROJECT_BOOK.md 章节）

- §5：报告格式 `textproof.report/v1` JSON Schema；verdict 取值 MATCH / MISMATCH；差异类型 SUBSTITUTION / MISSING_CHARACTER / EXTRA_CHARACTER / NUMERIC_CHANGE 等；每条差异含 expected_fragment / recognized_fragment / expected_span / bbox。
- §8.1：S0 固定样本 4 案——TP-S0-ZH-001（MISSING_CHARACTER）、TP-S0-ZH-002（SUBSTITUTION）、TP-S0-ZH-003、TP-S0-NUM-001（NUMERIC_CHANGE，￥28.00 vs ￥28.80）；每案“恰好 1 条差异”的口径按类型解读（见 §3 裁定）。
- §8.2–§8.3：300 样本检测召回率 ≥95%（替换/缺失/数字变化每类 ≥90%）；100 张 clean 图片误报率 ≤8%；JSON schema 合法率 100%；OCR CER 独立报告，不替代检错召回率。
- §8.4：生产模块与独立 Oracle 在固定字符/行 fixture 上 100% parity；Oracle 不 import 生产比较模块，独立会话、不同代码路径；`independent_verify.py` 从原始 PNG、manifest、expected output 独立复核，不只调用 `verify_s0.py`。
- §6.1–§6.2、§9：网络访问 0；ONNX Runtime provider 仅 CPU；隐私——不持久化用户数据、不记录用户文本、日志不含绝对路径；离线运行。
- §11.1：S0 报告须记录环境、版本、commit、全部 SHA、命令、退出码、指标、未执行项。

## 3. S0 门禁结果（T006，S0 VERDICT: PASS）

- S0 run ID：`S0-20261125-run2`（权威证据轮次；run1 因门禁脚本自身的检查 bug 退出 1）；输入 commit `732f07e`；报告日期 2026-11-25 GMT。证据见附件 `S0_REPORT.md` 与 `S0_MAINCHAT_VERDICT.md`。
- 9 项门禁逐项通过：召回率 **100.00%**（201/201，每类 100.00%）；clean 误报率 **0.00%**（0/100）；JSON schema 合法率 **100%**（300/300）；CER **0.0008**（单独报告）；IoU 最小 **0.829** / 均值 0.938；生产模块与 Oracle parity **300/300**；4 固定案例逐项核对 §8.1 全部 PASS；全程 `unshare -n` 下运行 exit 0，网络 0，三模型均为 `CPUExecutionProvider`。
- 主聊天亲自重跑裁定（~07:20 GMT，`verify_s0.py --force-live`，300 live OCR，exit 0，S0 VERDICT: PASS）：(a) NUM-001 live-OCR 多出 1 处 SUBSTITUTION（￥ U+FFE5 → ¥ U+00A5）——按 §8.1 的“按类型解读”采纳，即每类恰好 1 条差异，该分歧写入 S0_REPORT.md §6(a)，不加 ￥→¥ 映射；(b) target_region 校准合法。另：1920×1080 P95 运行时与 edge battery（14/26，诊断性）见 `PERFORMANCE_REPORT.md` 与 S0 报告，不计入门禁。
- S0 之后 T011–T014 未改动 S0 门槛、fixture PNG、manifest 与 I/O 契约（T014 禁令核查）；T014 两轮独立复审均重跑 S0 `--force-live`，PASS。

## 4. T001–T014 完成情况

| 任务 | 内容 | 证据 |
|---|---|---|
| T001 | 环境与锁文件：37 pins、753 hashes；rapidocr 3.10.0、onnxruntime 1.32.0 CPU-only | commit `394d507` |
| T002 | 输入契约（图片加载、文本归一化等） | 53 tests；commit `c1c45eb`，合并 `2fb2e13` |
| T003 | RapidOCR 模型（3 个 ONNX）+ 字典接入 | 19 tests；commit `48e88da`，合并 `f90d577` |
| T004 | 核心比较：加权编辑距离、行对齐、分类 | 167 tests；commit `cb1e3ba`，合并 `c5511e1` |
| T005 | 300 张 S0 fixture PNG（固定种子 20261125） | 7 tests；commit `6cfabb6`，合并 `1b425ce` |
| T006 | S0 门禁（见 §3） | 合并 `4ae03dd`；主聊天裁决 `S0_MAINCHAT_VERDICT.md` |
| T007 | 本地 FastAPI（仅 loopback） | 合并 `69d97cc` |
| T008 | 本地 Web UI | commit `3e9c3e8` |
| T009 | CLI + JSON schema + 导出；F-03 表单冻结 | commit `74200c1` |
| T010 | 隐私、不持久化、内存生命周期、离线安全 | 合并 `b0885dd` |
| T011 | 全量回归 | 施工员称 438 passed；主聊天亲自重跑发现 **2 failed**（隐私扫描与新 consistency_check.py 的 urllib 冲突，产品 src/ 无网络代码）；裁决：脚本移入 `tests/`，不缩小扫描范围；见 `T011_MAINCHAT_VERDICT.md` |
| T012 | 独立审查 | **31 项发现：0 P0 / 4 P1 / 7 P2 / 20 P3**；审查员亲自重跑 2 failed / 436 passed，与主聊天一致 |
| T013 | 修复 T012 发现（R-01 浮点比较改精确十进制、R-02 脚本移位、R-04 日志绝对路径泄漏等） | 主聊天亲自重跑：全量 pytest **489 passed**、S0 `--force-live` PASS、R-01 复现脚本不再复现；独立复审 FINAL_VERDICT: PASS；合并 `9cfaace`；见 `T013_MAINCHAT_VERDICT.md` |
| T014 | 冻结/打包：R-03 字典许可、R-13 发布文件、U-01 wheel 修复、重冻 | 主聊天裁决 PASS（见 §6）；两轮独立复审 PASS（见 §5）；合并 `16a3ef5` |

## 5. 两轮独立复审（均为新会话、未参与修复）

**首轮复审**（`t014-review`，commit `51880ad`）— **FINAL_VERDICT: PASS**。亲自重跑：全量 pytest **495 passed**；`verify_release.py` **27/27 PASS**；`verify_review_pack.py` PASS（389 行，688 文件全覆盖）；全新 venv 离线安装冒烟全过（check exit 1 MISMATCH、serve 200、verify-s0 两次 exit 3）；S0 `--force-live` 重跑 PASS。发现：1×P2（R14-01：README 残留已失效的 U-01 限制描述，与同文件后文矛盾）+ 3×P3（R14-02 source.zip 嵌套、R14-03 U-02、R14-04 U-03）。**无 P0、无 P1 未关闭。**

**增量复审**（`t014-review2`，commit `59bf0df`，针对 R14-01 修复与重冻）— **FINAL_VERDICT: PASS**。确认 R14-01 已真正修复并经新 wheel 实测；旧句零残留、三处表述一致；亲自重跑：全量 pytest **495 passed**、`verify_release.py` **27/27 PASS**、`verify_review_pack.py` PASS（400 行，699 文件全覆盖）；`git archive 93d1b7c` 与 source.zip 699 文件逐文件 SHA-256 全部一致，mismatch 0；字典零命中（git 清单 / source.zip / wheel / wheelhouse / SHA256SUMS.txt 全部 0 命中）。新发现仅 4 项 P3 文档表述小瑕疵（R14R-01 索引行数口径、R14R-02 DOCX 漂移行数口径、R14R-03 嵌套沿用、R14R-04 U-03 沿用）。**无 P0、无 P1 未关闭。**

两轮复审报告全文见附件 `REVIEW_REPORT_T014_R1.md` 与 `REVIEW_REPORT_T014_R2.md`；审查包见 `REVIEW_PACK_T014R3.md`（定稿包；旧包 R2 的一处失实结论已在 R3 包中书面纠正，R2 包原文保留未改动）。

## 6. 主聊天亲自核实（T014 裁决，见附件 T014_MAINCHAT_VERDICT.md）

1. **全量 pytest：495 passed，exit 0**（集成树 `t014-fix` HEAD `a9eb45f`，196.89s，2 warnings 均为已知 DecompressionBombWarning）。第一遍跑出 28 failed + 10 errors（457 passed），与协调员声称不符；查因是主工作区缺字典文件（T014/R-03 把它移出 git 追踪后，本工作区从未重建；全部失败均为 `FileNotFoundError`，属环境缺件，不是产品缺陷）。按新流程 `scripts/setup_dictionary.py` 本地重建（SHA-256 `b5f2bfe2bdd9448429e3e82b51c789775d9b42f2403d082b00662eb77e401c5d`、18,708 行）后重跑通过。
2. **verify_release.py：27/27 PASS，exit 0**，与协调员声称一致。
3. **字典不在 git 追踪中**：`git ls-files` 中 `ppocrv6_dict.txt` 零命中；`.gitignore` 已列两处字典路径。R-03 合规方案成立：许可维持 UNVERIFIED（RapidOCR 官方许可页 §2/§6 明确把 `dict_url` 字典排除在 Apache-2.0 之外；PaddleOCR 仓库级 LICENSE 未指明覆盖该数据文件；文件本身无许可头），字典本地重建、不联网。
4. **两轮独立复审报告均含 FINAL_VERDICT: PASS**；**冻结 commit `93d1b7c` 存在**。

## 7. 未解决的非阻断项（诚实披露，请终审裁定是否阻断）

- **U-02（DOCX 正文漂移，P3）**：PROJECT_BOOK.md 有 7 处 T013 文字澄清未进 DOCX（§4.2 行数口径、§4.4 行聚合口径、§4.5 混淆对集合、§5.3 保留码、§5.5 verify-s0 退出码注、§7.2 歧义口径与错误顺序、§7.6 OCR_FAILED 映射）。结构同步（标题 67/67、表格 14/4、同序、无缺节、无占位符）；澄清均为文字口径明确化，无算法/阈值改动，MD 为准的冻结契约未变。由规格方决定是否重生成 DOCX。
- **U-03（omegaconf 2.4.0 SBOM 无许可声明，P3）**：发行版元数据中无许可声明，如实标注、未推断。
- **source.zip 体积叠加（512MB，P3，R14-02/R14R-03）**：冻结 commit 本身入库了上一轮重冻的 `release/` 产物，source.zip 含三层嵌套——L0 本轮 512,109,756 B / 766 条目 / 699 文件（SHA-256 `9c2305ed…`）；L1（T014R2 产物）263,808,324 B / 754 文件（SHA-256 `9fb6ca97…`）；L2（T014R1 产物）42,734,094 B / 654 文件（SHA-256 `82a01a14…`），L2 内 `release/` 条目为 0，嵌套到此为止。逐文件一致性已核实：L0 除 `release/` 外的 724 条目 vs L1 的 712 条目，L1 独有文件 0 个，L0 独有 12 个（R2 审查包 + 11 个重冻交接文件），同名文件仅 README 内容变（R14-01 修复）。归档策略：本轮归档冻结版原样（SHA 已入清单、经 27/27 核对、两轮复审核对同一 SHA，重建会断开证据链）；GitHub 快照将用干净导出排除 `release/` 嵌套；未来冻结不再把 `release/` 生成物入库。详见附件 `FREEZE_ARCHIVE_NOTE.md` §2–§3。
- **R14R-01 / R14R-02（P3）**：R3 包两处行数口径表述含混（索引“453 行：399 个文件 + 1 行 PNG 聚合”；DOCX 漂移“+11/−7 行”为含 diff 头的计数），内容正确，数字本身无误。

## 8. 附件清单（Google Drive，文件夹 P033-textproof）

文件夹：https://drive.google.com/drive/folders/1ovRjSwX2eioP8XGzZa_I_arpauOsrRBr
冻结归档子文件夹 `FREEZE_93d1b7c_T014_2026-11-25`：https://drive.google.com/drive/folders/1UWRhmLOE66DbFDCizbQD8AIXzjkiPN_u

| 文件 | 大小（B） | Drive 链接 |
|---|---|---|
| source.zip（冻结源包） | 512,109,756 | https://drive.google.com/file/d/1IWsa7zPflkPbFq_PKhO8wC964NwbZ3EW/view |
| textproof-1.0.0-py3-none-any.whl | 27,176,403 | https://drive.google.com/file/d/1saaVScWA6gTP7HOidIkK4pnZ97Oa_47v/view |
| RELEASE_MANIFEST.json | 11,738 | https://drive.google.com/file/d/1zg6ERxs-lS4O0F1UwFaaDRuK7dUHnYjH/view |
| SHA256SUMS.txt | 4,680 | https://drive.google.com/file/d/1dhm_WcUZClee7S3c0-5whQEubrQcFWAE/view |
| SBOM_LICENSES.md | 2,766 | https://drive.google.com/file/d/16sEK8-6D7Eyj_tzfBhbFf2zaxb-pA_F-/view |
| REVIEW_PACK_T014R3.md（定稿审查包） | 15,308 | https://drive.google.com/file/d/19IhdjgU82wSpN2TthlX8q7d7lSfd_Xpv/view |
| REVIEW_REPORT_T014_R1.md（首轮独立复审） | 26,019 | https://drive.google.com/file/d/1jfRseMAIwnKd60BmwpSX7-y2Jk-8Zi_N/view |
| REVIEW_REPORT_T014_R2.md（增量独立复审） | 24,921 | https://drive.google.com/file/d/1C3-xUkBrxIWA4zmyqeqUWIIuLPC8AYSc/view |
| T014_MAINCHAT_VERDICT.md（主聊天裁决） | 3,062 | https://drive.google.com/file/d/1ngvtJHXLbL4lgFBRvOJeerlyadrdug78/view |
| S0_REPORT.md | 29,600 | https://drive.google.com/file/d/1GOrWfqRu5FZq4ZtBvl5co0_MTtRDZzs7/view |
| S0_MAINCHAT_VERDICT.md | 4,308 | https://drive.google.com/file/d/1eQCybptd49K2pp335BJHd1NT_3P7KtQA/view |
| FREEZE_ARCHIVE_NOTE.md（归档说明：嵌套结构、字典排除、快照策略） | 9,809 | https://drive.google.com/file/d/10FR9liKXF0roqYZKW2eN6ThguXOeiEUM/view |

冻结规格（已在 P033-textproof 文件夹根目录，2026-11-25 ~01:44 归档，Drive MD5 已验证一致）：
| 文件 | 大小（B） | Drive 链接 |
|---|---|---|
| PROJECT_BOOK.md | 44,552 | https://drive.google.com/file/d/1wFI_OAfye3_ft_ktiRt5dgTsTsGa1I_g/view |
| PROJECT_BOOK.docx | 64,339 | https://drive.google.com/file/d/1Pprli78AucDctlpNacNLMbafTMfx8J86/view |
| IMPLEMENTATION_PLAN.md | 35,772 | https://drive.google.com/file/d/1-_xCz6jUrhDsOliUCiV_vHvEi_OfeMzJ/view |
| IMPLEMENTATION_PLAN.docx | 58,745 | https://drive.google.com/file/d/11ocoNski5C8y3QYP9LifDMcKoeE9uZdl/view |

关键哈希（供你独立核对）：source.zip SHA-256 `9c2305ed715e0e74e459e73348418a7011890a474af04cdc4de451a456d2c235`；wheel SHA-256 `9c880b88e401c618c91426c3009b3153c7da682fe461e42eb9802a55f33372a1`；字典重建 SHA-256 `b5f2bfe2bdd9448429e3e82b51c789775d9b42f2403d082b00662eb77e401c5d`（18,708 行；字典不在任何归档包内，全新检出须先跑 `scripts/setup_dictionary.py` 本地重建）。核对清单见 `RELEASE_MANIFEST.json` 与 `SHA256SUMS.txt`。

## 9. 请终审方做的核查

1. 阅读冻结规格（§2 所列章节）与全部附件；按规格章节逐项核对产品行为、报告格式、S0 门禁、隐私边界——**门禁定义本身也要核对**：S0 的验收口径是否等于规格原文要求，而不只是重跑门禁脚本。
2. 独立核对冻结产物：source.zip 的文件清单与逐文件 SHA-256（对照 `RELEASE_MANIFEST.json`）、wheel 条目、wheelhouse 与 `requirements.lock` 的对应关系、字典零命中。
3. 抽查关键证据：S0 9 项门禁的证据链、4 固定案例的逐项核对、Oracle parity、T011→T013 的失败发现与修复链、两轮独立复审的重跑记录。
4. 裁定 §7 的 4 项未解决项是否阻断本次交付；如有任何一项应升级为 P0/P1，请明确写出。
5. 结论格式（请逐字给出）：先列 findings（P0/P1/P2/P3 分级，每项写明规格锚点、证据、是否阻断），再给 `FINAL_VERDICT: PASS` 或 `FINAL_VERDICT: FAIL`，并列 `BLOCKERS:` 清单（PASS 时写 `BLOCKERS: NONE`）。只有 `FINAL_VERDICT: PASS` 才能交付；FAIL 请给出必须修复的最小集合。

请使用谷歌云盘以及任何需要的插件，如果有了的话就算了。
