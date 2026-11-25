# P033 TextProof — T014 审查包（REVIEW_PACK_T014.md）

- 锚定 commit：`167594e0442090c057baba7c067c323dd88cf530`（分支 `t014-pkg`；T014 冻结源码 commit）
- 审查索引：`review/REVIEW_INDEX.md`（297 行：296 个文件 + 1 行 PNG 聚合；锚定 commit 追踪文件 596 个，全部覆盖）
- 发布清单：`release/RELEASE_MANIFEST.json`
- 验证命令：`python scripts/verify_release.py`（全量）、`python scripts/verify_review_pack.py review/REVIEW_INDEX.md`
- **结论：除 U-01（阻断）外全部通过。`verify_release.py` 当前为 FAIL，仅因 U-01 的离线冒烟检查未通过；其余全部检查通过。本包不得作为“终审已通过”的依据——须先走 T013 修复轮次（或由终审明确接受 U-01 的限制），再重新冻结。**

## 1. 冻结与版本身份

| 项 | 值 |
|---|---|
| 冻结源码 commit | `167594e0442090c057baba7c067c323dd88cf530`（含 R-13 发布文件与 R-30 审查脚本；不含 `release/`、`review/` 生成物与 T014 交接日志，那些在随后的 release 提交中入库） |
| 追踪文件数（锚定 commit） | 596（含 300 张 S0 fixture PNG） |
| `source.zip` | 42,734,094 B，SHA-256 `82a01a1480c8f7fe545a86ca8ca3f3287afea7ab939aa6fed31e196b167ef0ad`，596 个文件，与锚定 commit 逐文件一致（`verify_release.py` 核对：文件名集合 + 逐文件 SHA-256） |
| wheel | `textproof-1.0.0-py3-none-any.whl`，51,656 B，SHA-256 `939dbb5774394a8fdbee2099f9eb94c4271e839984b7600b0f35c0dddfb8478b`；METADATA：Name `textproof`，Version `1.0.0`，License MIT；23 个条目，全部为 `textproof/` 包文件 + dist-info，无字典文件 |
| wheelhouse | 37 个 wheel（与 `requirements.lock` 37 个包逐一对应，版本与哈希逐项核对），151,973,630 B |
| `tool_version`（产品版本） | `0.1.0`（`src/textproof/core/report.py`；每份报告所带版本） |
| `package_version`（打包版本） | `1.0.0`（`pyproject.toml`；wheel METADATA 一致） |
| `spec_version`（规格版本） | `1.0.0`（`src/textproof/api/routes.py`） |
| 三版本关系 | 三个不同维度，非不一致——只解释，不“修复”（T012 审查 §3 第 1 项已确认；`textproof version` 三者区分输出，实测一致） |
| 字典 | `assets/ocr/dictionaries/ppocrv6_dict.txt` 不在锚定 commit 内、不在 `source.zip`、wheel、wheelhouse 中（`git archive` 清单与 zip 清单双重验证零命中）；许可 UNVERIFIED（THIRD_PARTY_NOTICES.md §4）；全新检出须先跑 `scripts/setup_dictionary.py`（实测 exit 0、SHA `b5f2bfe2…`、18,708 行） |

## 2. T012 → T013 证据链

- T012 独立审查（冻结候选 `ffe53ea`）：findings R-01…R-31（P0 × 0、P1 × 4、P2 × 7、P3 × 20），覆盖率全文读 61/75。报告正本与索引以复制件收入本包（§6）。
- T013 修复与复审：P0/P1 全部关闭（R-01 精确算术、R-02 脚本移出扫描树、R-03 归属 T014、R-04 日志去绝对路径）；P2 逐项修复或书面非阻断；P3 批量处置（`task_handoffs/T013/p3/P3_DISPOSITION.md`）。R-31（锁文件“33 个包”）已由 T013 修复：`ENVIRONMENT.md` §4 现为 37 个包；T014 独立复核 `grep -cE '^[a-z0-9_.-]+==[0-9]' requirements.lock` = 37、`grep -c 'sha256:'` = 753、lock SHA `8726d13c…` 不变。
- T013 主聊天裁决（`T013_MAINCHAT_VERDICT.md`）：T013 PASS；全量 pytest 489 passed；S0 `--force-live` PASS（召回 100%、clean FPR 0%、CER 0.0008、IoU 最小 0.829、parity 300/300）。
- T014 复核：全量 pytest 在本 worktree 重跑 **489 passed、0 failed、exit 0**（142.19s；日志 `task_handoffs/T014/pkg/test_stdout.log`）。注：首次重跑中途被 VM 重启打断（SIGTERM，属环境事故、非产品失败；重启后完整重跑通过）。T010 静态门禁含新脚本在内 17 项在脚本写入后单独重跑全部通过（`test_forbidden_token_absent_from_sources` + `test_no_network_client_import_in_sources`）；最终版脚本由随后完整重跑的 489 项覆盖（该重跑在 `verify_release.py` 加入冒烟检查后执行）。

## 3. T014 验证证据（本轮实测）

| 检查 | 命令 / 方法 | 结果 |
|---|---|---|
| 字典重建 | `.venv/bin/python scripts/setup_dictionary.py`（主树 venv） | exit 0；SHA `b5f2bfe2bdd9448429e3e82b51c789775d9b42f2403d082b00662eb77e401c5d`；18,708 行 |
| 全量 pytest | `TMPDIR=$PWD/tmp .venv/bin/python -m pytest -q -p no:cacheprovider` | **489 passed、0 failed、exit 0**（142.19s；2 warnings） |
| `verify_review_pack.py` | `python scripts/verify_review_pack.py review/REVIEW_INDEX.md` | **PASS**（297 行；596 文件全覆盖；聚合行重算一致） |
| `verify_release.py --preflight` | `python scripts/verify_release.py --preflight` | **PASS**（12/12） |
| `verify_release.py` 全量 | `python scripts/verify_release.py` | **FAIL — 仅离线冒烟一项未通过（U-01）**；其余全部通过（见 `task_handoffs/T014/pkg/verify_release.log`） |
| source.zip 一致性 | `verify_release.py` 内核对 `git archive <锚定 commit>` | 596 文件，文件名集合 + 逐文件 SHA-256 全部一致；字典零命中 |
| wheelhouse 对照锁文件 | `verify_release.py` 内逐包核对版本与文件哈希 | 37/37 包各 1 个 wheel；每文件 SHA-256 均在锁文件该包的哈希列表中；无多余 wheel |
| SHA256SUMS.txt | 独立重算（`verify_release.py` 内） | 覆盖 source.zip + wheel + 37 个 wheelhouse wheel，全部一致 |
| 离线安装 | 全新 venv；`pip install --no-index --find-links release/wheelhouse release/textproof-1.0.0-py3-none-any.whl` | **exit 0**；37 个包全部安装（`Successfully installed ... textproof-1.0.0`；日志 `task_handoffs/T014/pkg/offline_install.log`） |
| `textproof --help`（已安装 wheel） | 离线 venv 内运行 | exit 0 |
| `textproof version`（已安装 wheel） | 离线 venv 内运行 | exit 0；tool 0.1.0 / package 1.0.0 / spec 1.0.0 / rapidocr 3.10.0 / onnxruntime 1.32.0 / providers 仅 `CPUExecutionProvider` |
| `textproof check` 冒烟（已安装 wheel，standalone） | 离线 venv 内运行，`TP-S0-ZH-001.png` + 期望文本 `限时优惠` | **exit 5，未出报告（U-01）**；stderr：`textproof: internal error: generated report failed schema validation.`（两次独立运行复现；证据 `task_handoffs/T014/pkg/smoke_check_standalone.log` + `offline_smoke.txt`） |
| `textproof serve`（已安装 wheel） | 离线 venv 内运行，`--host 127.0.0.1 --port 8792` | **启动崩溃 exit 1**；`RuntimeError: Directory '.../site-packages/textproof/ui' does not exist`（U-01 同根；证据 `smoke_serve2.log`） |
| 对照：同一 check，主树源码 | `PYTHONPATH=src .venv/bin/python -m textproof.cli check ...` | exit 1，verdict `MISMATCH`，错误 `MISSING_CHARACTER`（正确；报告 `smoke_report_repo.json`） |
| 诊断：已安装 wheel + `PYTHONPATH=<checkout>` | 离线 venv 内运行同一 check（另在 venv 内软链 `assets/ocr` 到安装位置） | exit 1，verdict `MISMATCH`，`MISSING_CHARACTER`（正确；报告 `smoke_report_wpp.json`）——证明唯一故障点是校验器导入路径，OCR 本身正常 |

### U-01 根因（已定位，非猜测）

1. `textproof check`：`src/textproof/cli.py` `_validate_report()`（约 :85–96）以 `Path(__file__).resolve().parents[2]` 定位仓库根并 `from scripts.validate_report_schema import validate_report`。源码布局下该路径是仓库根，导入成功；已安装布局下 `parents[2]` 是 `<venv>/lib/python3.12`，其下无 `scripts/`，导入失败 → 按 fail-closed 设计返回“validator unavailable” → exit 5。校验器本身只依赖标准库、不读磁盘 schema 文件，因此不是 schema 文件缺失问题。
2. `textproof serve`：`src/textproof/api/app.py:94` 以包内相对路径挂载 `textproof/ui` 静态目录；wheel 不含 `ui/*`（`pyproject.toml` 无 package-data 配置、无 MANIFEST.in；wheel 23 个条目全为 `.py` + dist-info），启动即 `RuntimeError`。
3. 同根的第三处：`textproof verify-s0` 用 `REPO_ROOT / "scripts" / "verify_s0.py"` 与默认 manifest 路径（`cli.py:285`、`REPO_ROOT`），checkout 外同样找不到文件。
4. 此外 API check 还需要 OCR 资产位于安装位置的 `assets/ocr`（模型 + 本地重建的字典），wheel 内本无此内容——属待定设计（模型是否进 wheel、字典排除如何处理），不在本次修复讨论内。
5. 既往从未发现的原因：全部 489 项测试均在源码树内运行（根 `conftest.py` 把 `src/` 插进 `sys.path`，包不安装进 venv），没有任何测试安装 wheel 后运行。因此 T012/T013 均未覆盖此路径。T014 的离线冒烟是第一次执行该路径。

修复方向（供 T013 轮次定夺，T014 不擅自实施）：源码侧把校验器与 UI 打包进 `textproof` 包内（或改为按包内路径解析），并决定 wheel 的资产边界；`verify-s0` 同理。纯打包层面的变通（如把 `scripts/` 作为顶层包塞进 wheel）被否决：它修不好 `verify-s0`、会向 wheel 混入全部验证脚本、且 `pyproject.toml` 不在 T014 文件所有权内——属需规格方定夺的设计变更，不是打包细节。

## 4. R-30 处置（取代 T013 的豁免记录）

T013 交接把 `verify_review_pack.py` 记为“豁免（由 T012 REVIEW_INDEX.md 替代）”。T014 按任务要求优先选择**补齐而非豁免**：`scripts/verify_review_pack.py` 已新建并通过（§3）。它按 `REVIEW_INDEX.md` 的锚定 commit（`git archive` 取数）逐行核对路径、字节数、SHA-256、行数，并核对覆盖完整性（含 300 张 PNG 的聚合行）；T012 的索引格式（路径、字节数、SHA-256、行数、读取状态）被沿用，SHA 改为完整 64 位（T012 用 16 位截断）。豁免记录就此作废。

## 5. DOCX 同步核对

DOCX_SYNC_VERDICT: STRUCTURE PASS / BODY-TEXT DRIFT (7 lines in PROJECT_BOOK.md, recorded as unresolved item U-02; IMPLEMENTATION_PLAN.md fully in sync)

核对方法（标准库 `zipfile` + XML 解析，无新增依赖；脚本 `/tmp/docx_check.py`，结果写入本节）：

| 项 | PROJECT_BOOK | IMPLEMENTATION_PLAN |
|---|---|---|
| MD 标题数 vs DOCX 样式段落数（Title + Heading） | 67 vs 67 | 40 vs 40 |
| 标题文本逐项同序 | 一致 | 一致 |
| 表格数（DOCX `w:tbl`） | 14（与 SPECS_VERIFICATION.md 一致） | 4（一致） |
| 缺节 | 无 | 无 |
| 占位符（TODO/TBD/XXX/占位） | 无真实占位符（两处命中均为正文词语：“占位框”在证据表内、“占位符”在验收标准条文本身） | 同左 |
| 正文漂移 | **7 行改动**：T013 commit `7540c4f` 对 MD 的文字澄清（§4.5 混淆对集合、§5.3 保留码、§5.5 verify-s0 退出码注、§7.2 歧义按配对集合计 + 错误顺序段、§7.6 OCR_FAILED 映射；`git diff 394d507 HEAD` 计 +11/−7 行），DOCX 仍冻结在 T001 基线 | **0 行**：`git diff 394d507 HEAD` 无变化 |

结论：结构同步；正文漂移只影响 `PROJECT_BOOK.md` 的 7 处 T013 文字澄清，DOCX 未同步更新。按任务要求不擅自重写 DOCX，记为未解决项 U-02 报回。

## 6. T012 审查复制件说明

`review/REVIEW_FINDINGS_T012.md` 与 `review/REVIEW_INDEX_T012.md` 是自 T011 审查工作树（`~/workspace/p033-textproof-t011/review/`）逐字复制的文件，未作任何改动：

| 文件 | SHA-256 | 与原件一致 |
|---|---|---|
| `REVIEW_FINDINGS_T012.md` | `35b2260d2d79ac375cd4499f54084dc03744b8c44d6f0174bec6b75e0c30f3c9` | 是 |
| `REVIEW_INDEX_T012.md` | `f91dd1a022fd00f8abcd91a643eac78744745287905b78cb525ecf921f89715a` | 是 |

T012 的覆盖结论（61/75 全文读、14 项部分读）原文保留，不由 T014 改写；T014 的覆盖表（`REVIEW_INDEX.md`）是另一份文件，锚定 T014 冻结 commit、覆盖全部 596 个追踪文件。

## 7. 已知未解决项

| ID | 级别 | 内容 | 影响与下一步 |
|---|---|---|---|
| U-01 | **阻断** | 已安装 wheel 无法 standalone 运行 `check`（exit 5）与 `serve`（启动崩溃）；`verify-s0` 同根。根因见 §3。 | T014 验收 2（wheel 安装 + 运行）未达成；`verify_release.py` 为 FAIL。须 T013 修复轮次（源码改动）后重新冻结、重建 wheel、重跑冒烟；或由终审明确接受该限制（则须同步更新 §11.2/§11.3 的交付承诺）。 |
| U-02 | 非阻断 | DOCX 正文漂移：`PROJECT_BOOK.md` 7 处 T013 文字澄清未进 DOCX（见 §5）。 | 结构同步，无缺节。由规格方决定是否重生成 DOCX；T014 不擅自重写。 |
| U-03 | 非阻断 | SBOM 中 1 个包（`omegaconf` 2.4.0）在已安装发行版元数据中无许可声明（`release/SBOM_LICENSES.md` 如实标注，未推断）。 | 须在使用前另行核对上游 LICENSE；不影响安装与运行。 |

## 8. 交付物清单

| 交付物 | 位置 | 说明 |
|---|---|---|
| 源码包 | `release/source.zip` | §1；与锚定 commit 逐文件一致 |
| wheel | `release/textproof-1.0.0-py3-none-any.whl` | §1；可安装；standalone 运行受 U-01 限制 |
| 离线安装包 | `release/wheelhouse/`（37 个 wheel） | 与锁文件逐包核对 |
| 哈希清单 | `release/SHA256SUMS.txt` | 覆盖 source.zip + wheel + 37 个 wheelhouse wheel |
| 发布清单 | `release/RELEASE_MANIFEST.json` | 冻结 commit、产物哈希、已知未解决项（含 U-01 blocking） |
| SBOM / 许可报告 | `release/SBOM_LICENSES.md` | 37 个包逐项许可（元数据来源；1 项未声明，见 U-03） |
| 审查索引 | `review/REVIEW_INDEX.md` | 锚定 commit；596 文件全覆盖；`verify_review_pack.py` PASS |
| 本审查包 | `review/REVIEW_PACK_T014.md` | 本文件 |
| T012 审查复制件 | `review/REVIEW_FINDINGS_T012.md`、`review/REVIEW_INDEX_T012.md` | §6；逐字复制 |
| 发布验证脚本 | `scripts/verify_release.py`、`scripts/verify_review_pack.py` | 锚定 commit 内；禁令串 grep 零命中 |
| 发布文件 | `LICENSE`、`README.md`、`SECURITY.md` | R-13；README 含 U-01 已知限制说明 |
| 交接与证据 | `task_handoffs/T014/pkg/` | TASK_RESULT.md、测试日志、离线冒烟原始日志、`offline_smoke.txt`、`verify_release.log` |

## 9. FIX-R1 增补（2026-11-25，终审 R1 P1-01 修复后）

DOCX_SYNC_VERDICT: SYNCED (FIX-R1) — PROJECT_BOOK.docx 已从当前 MD（46,114 B，SHA-256 `8a2b6e565df88a2f6371879cdcfbb613500c8cc2ecee50376b8da95d7ecc496a`）用 `scripts/md_to_docx.py`（python-docx）重新生成；IMPLEMENTATION_PLAN 两份未动（与工作区逐字节一致）。

- 新 DOCX：62,512 B，SHA-256 `97706fc9c542670245dbc28e31e174e3824f4c7164dfc8ca4251bba4e0508464`；Title 1 + 66 个标题段落 = 67，表格 14 个，67 个标题与 MD §0–§16 逐项同序；新旧 DOCX 段落级 diff 除 7 处 T013 澄清外零差异；7 处澄清（尾随换行、行聚合、混淆对集合、保留警告码、verify-s0 退出码、歧义对齐+错误排序、OCR_EMPTY 映射）逐一在新 DOCX 提取文本中按锚定字符串命中。验证报告见 `task_handoffs/FIX-R1/fix-r1-01-verification.md`；同步前后证据副本见 `task_handoffs/FIX-R1/drive_before/` 与 `drive_after/`。
- Drive 同步：PROJECT_BOOK.md（`1wFI_OAfye3_ft_ktiRt5dgTsTsGa1I_g`）与 PROJECT_BOOK.docx（`1Pprli78AucDctlpNacNLMbafTMfx8J86`）已用 `files update` 替换为新版（ID 不变），替换后重新下载逐字节/SHA 核对一致。
- 本增补只追加，不改动 §5 与 §7 的原文：§5 的 "BODY-TEXT DRIFT" 与 §7 的 U-02 行是 T014 当时的历史记录；U-02 自本增补起视为已解决（见新审查包 `review/REVIEW_PACK_FIXR1.md` §1）；U-03（omegaconf 许可）亦在本轮解决——其 wheel 内附 LICENSE 文件首行即 "BSD 3-Clause License"（Copyright (c) 2018 Omry Yadan），SBOM 已记为 BSD-3-Clause（见 `release/SBOM_LICENSES.md`）。
