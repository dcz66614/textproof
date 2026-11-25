# P033 TextProof — T014 重冻审查包 R3（REVIEW_PACK_T014R3.md）

- 锚定 commit：`93d1b7c65036bb16f596117f26a48f6ee62f99e1`（分支 `t014-r14fix`；T014R3 重冻源码 commit = T014R2 集成线 `3f02b32` + 仅 README 的 R14-01 修正）
- 审查索引：`review/REVIEW_INDEX.md`（453 行：399 个文件 + 1 行 PNG 聚合；锚定 commit 追踪文件 699 个，全部覆盖）
- 发布清单：`release/RELEASE_MANIFEST.json`
- 验证命令：`python scripts/verify_release.py`（全量）、`python scripts/verify_review_pack.py review/REVIEW_INDEX.md`
- **结论：全部通过。R14-01 已修复并经新 wheel 实测；`verify_release.py` 为 PASS（27/27，工作树与干净目录一致）。未解决项只剩非阻断的 U-02、U-03。本包是本次重冻的定稿包；旧包 `review/REVIEW_PACK_T014.md` 记录 U-01 失败证据、`review/REVIEW_PACK_T014R2.md` 记录 R2 重冻，原文保留，未改动。**

## 1. 冻结与版本身份

| 项 | 值 |
|---|---|
| 冻结源码 commit | `93d1b7c65036bb16f596117f26a48f6ee62f99e1`（= `3f02b32` + 仅 README 的 R14-01 修正；`git diff 3f02b32 93d1b7c --stat` 只有 `README.md` 1 个文件，+4/−3 行；不含 `release/`、`review/` 生成物与 T014 交接日志，那些在随后的 release 提交中入库） |
| 追踪文件数（锚定 commit） | 699（含 300 张 S0 fixture PNG） |
| `source.zip` | 512,109,756 B，SHA-256 `9c2305ed715e0e74e459e73348418a7011890a474af04cdc4de451a456d2c235`，699 个文件，与锚定 commit 逐文件一致（`verify_release.py` 核对：文件名集合 + 逐文件 SHA-256）。体积较 R2 的 263,808,324 B 增大，因为锚定 commit 本身已包含 R2 的 `release/` 产物（旧 source.zip 263,808,324 B + 全部 wheelhouse，合计约 443 MB）与 T013-U01 打进包的模型复制（`src/textproof/assets/ocr/models/`，约 32 MB）；`git archive` 忠实收录冻结树，这是重冻的预期结果，不是污染 |
| wheel | `textproof-1.0.0-py3-none-any.whl`，27,176,403 B，SHA-256 `9c880b88e401c618c91426c3009b3153c7da682fe461e42eb9802a55f33372a1`；METADATA：Name `textproof`，Version `1.0.0`，License MIT；32 个条目：包文件 + `textproof/ui/*`（3 个）+ `textproof/assets/ocr/models/*.onnx`（3 个）+ dist-info，无字典文件 |
| wheelhouse | 37 个 wheel（与 `requirements.lock` 37 个包逐一对应，版本与哈希逐项核对），151,973,630 B；与 R2 的 wheelhouse 逐文件哈希一致，未重下、未升级 |
| `tool_version`（产品版本） | `0.1.0`（`src/textproof/core/report.py`；每份报告所带版本） |
| `package_version`（打包版本） | `1.0.0`（`pyproject.toml`；wheel METADATA 一致） |
| `spec_version`（规格版本） | `1.0.0`（`src/textproof/api/routes.py`） |
| 三版本关系 | 三个不同维度，非不一致——只解释，不“修复”（T012 审查 §3 第 1 项已确认；`textproof version` 三者区分输出，实测一致） |
| 字典 | `assets/ocr/dictionaries/ppocrv6_dict.txt` 不在锚定 commit 内、不在 `source.zip`、wheel、wheelhouse 中（`git archive` 清单与 zip 清单双重验证零命中）；许可 UNVERIFIED（THIRD_PARTY_NOTICES.md §4）；全新检出须先跑 `scripts/setup_dictionary.py`（实测 exit 0、SHA `b5f2bfe2…`、18,708 行） |

## 2. R14-01 缺陷与修复（独立复审发现，P2）

- 缺陷：`README.md` 约 L61–64（“From the release wheel (offline)”一节末尾）仍写着 U-01 修复前的旧句：“`textproof --help` and `textproof version` work standalone. See **Known limitations** below: `check`, `serve` and `verify-s0` from an installed wheel currently require a source checkout.”——自 T013-U01 修复后，`check` 与 `serve` 已可在已安装 wheel 下独立运行（复审员在全新离线 venv 亲自证实）；该句还与同一文件后文直接矛盾：L203 “Installing from the wheel (no source checkout needed)”说 check/serve 可独立运行，L236 “Known limitations”写“(None currently recorded. The previous U-01 … was fixed…)”。
- 修复（commit `93d1b7c`，本轮冻结 commit 本身）：该句改写为——“`textproof --help` and `textproof version` work standalone, and so do `check` and `serve` once the dictionary has been rebuilt (see "Installing from the wheel" below). Only `verify-s0` requires a source checkout (it exits 3 without one).”——只改这一处表述；README 其他部分、任何其他文件内容均未改动（`git diff 3f02b32 93d1b7c --stat` 只有 `README.md`）。
- README 变化：10,418 B → 10,469 B；246 行 → 247 行；SHA-256 `eabd5523…` → `136b2877…`（见新锚定索引行）。
- **对 R2 包的书面纠正**：`review/REVIEW_PACK_T014R2.md` §3 的 README 复核行称“无已失效的限制描述：U-01 限制已改为‘Installing from the wheel’使用说明；‘Known limitations’节为‘(None currently recorded.)’，与修复状态一致”——该结论不属实，漏检了 L61–64 的旧句。本包特此纠正；R2 包原文保留，未改动。

## 3. T014R3 验证证据（本轮实测，新 wheel）

| 检查 | 命令 / 方法 | 结果 |
|---|---|---|
| 字典重建 | `.venv/bin/python scripts/setup_dictionary.py`（主树 venv） | exit 0；SHA `b5f2bfe2bdd9448429e3e82b51c789775d9b42f2403d082b00662eb77e401c5d`；18,708 行 |
| 全量 pytest | `TMPDIR=$PWD/tmp .venv/bin/python -m pytest -q -p no:cacheprovider` | **495 passed、0 failed、exit 0**（382.51s；2 warnings；日志 `task_handoffs/T014/pkg/test_stdout.log`） |
| `verify_review_pack.py` | `python scripts/verify_review_pack.py review/REVIEW_INDEX.md` | **PASS**（400 行；699 文件全覆盖；聚合行重算一致） |
| `verify_release.py --preflight` | `python scripts/verify_release.py --preflight` | **PASS**（12/12） |
| `verify_release.py` 全量 | `python scripts/verify_release.py` | **PASS（27/27）**；见 `task_handoffs/T014/pkg/verify_release.log` |
| `verify_release.py` 干净目录 | 全新 detached worktree + 复制 `release/`、`review/`、`task_handoffs/T014/pkg/` 后 `--root` 运行 | **PASS（27/27）**；见 `task_handoffs/T014/pkg/verify_release_clean_dir.log` |
| source.zip 一致性 | `verify_release.py` 内核对 `git archive 93d1b7c` | 699 文件，文件名集合 + 逐文件 SHA-256 全部一致；字典零命中 |
| wheelhouse 对照锁文件 | `verify_release.py` 内逐包核对版本与文件哈希（本轮另以独立脚本复核） | 37/37 包各 1 个 wheel；每文件 SHA-256 均在锁文件该包的哈希列表中；无多余 wheel；与 R2 wheelhouse 逐文件哈希一致 |
| SHA256SUMS.txt | 独立重算（`sha256sum -c` + 第二种逐文件重算脚本） | 覆盖 source.zip + wheel + 37 个 wheelhouse wheel（39 条），全部一致 |
| 离线安装（新 wheel） | 全新 venv；`pip install --no-index --find-links release/wheelhouse release/textproof-1.0.0-py3-none-any.whl` | **exit 0**；37 个包全部安装（`Successfully installed ... textproof-1.0.0`；日志 `task_handoffs/T014/pkg/offline_install.log`） |
| `textproof --help`（新 wheel） | 离线 venv 内运行 | exit 0 |
| `textproof version`（新 wheel） | 离线 venv 内运行 | exit 0；tool 0.1.0 / package 1.0.0 / spec 1.0.0 / rapidocr 3.10.0 / onnxruntime 1.32.0 / providers 仅 `CPUExecutionProvider` |
| `textproof check` 冒烟（新 wheel，standalone） | 离线 venv 内运行，`TP-S0-ZH-001.png` + 期望文本 `限时优惠`（无 checkout 在路径上） | **exit 1，verdict `MISMATCH`，错误 `E001 MISSING_CHARACTER`（缺字“惠”），报告经 `scripts/validate_report_schema.py` 校验 VALID（1/1 valid）**（`task_handoffs/T014/pkg/smoke_report_standalone.json`；U-01 已修复的直接证据） |
| `textproof serve`（新 wheel） | 离线 venv 内运行，`--host 127.0.0.1 --port 8792` | **启动成功**；健康检查 200（`status ok`）+ UI 200（含 TextProof 与“可能包含敏感文字”）；探针记录 `task_handoffs/T014/pkg/smoke_serve_probe.txt` |
| `textproof verify-s0`（新 wheel） | 离线 venv 内运行（默认 + 带 manifest 各一次） | 两次均为 **exit 3**（定义行为：默认 `S0 manifest not found`；带 manifest 时 `verify-s0 requires a source checkout`），符合 T013-U01 §2.3 |
| SBOM 复核 | 冒烟 venv 已安装发行版元数据逐项对照 `release/SBOM_LICENSES.md` | 37 包版本与许可记录全部一致；唯一无许可声明的仍是 `omegaconf` 2.4.0（U-03，如实保留）；SBOM 文件无改动 |
| README 复核 | 全文 grep 三处表述一致性 | 旧句零残留（`require a source checkout` 全文零命中；`See **Known limitations**` 零命中）：L61–64 改后表述（check/serve 在一次性重建字典后可独立运行；仅 verify-s0 需 checkout，exit 3）与“Installing from the wheel”一节及“Known limitations”节（None currently recorded）一致 |

### U-01 仍已修复（对照旧包 §3 的失败证据）

| 旧失败（T014，旧 wheel 939dbb57…） | 新结果（T014R3，新 wheel 9c880b88…） |
|---|---|
| `check` exit 5，`generated report failed schema validation` | `check` exit 1，`MISMATCH` + `E001 MISSING_CHARACTER`，报告经包内校验 VALID |
| `serve` 启动崩溃 exit 1，`textproof/ui does not exist` | `serve` 启动成功，健康 200 + UI 200 |
| `verify-s0` 在 checkout 外找不到 runner/manifest（未定义行为） | 两次 exit 3，文案明确定义（见上表） |

## 4. R-30 处置（沿用 T014R2）

`scripts/verify_review_pack.py` 按 `REVIEW_INDEX.md` 的锚定 commit（`git archive` 取数）逐行核对路径、字节数、SHA-256、行数，并核对覆盖完整性（含 300 张 PNG 的聚合行）；T012 的索引格式（路径、字节数、SHA-256、行数、读取状态）被沿用，SHA 为完整 64 位（T012 用 16 位截断）。T013 交接中的豁免记录已作废（见旧包 §4）。

## 5. DOCX 同步核对

DOCX_SYNC_VERDICT: STRUCTURE PASS / BODY-TEXT DRIFT (7 lines in PROJECT_BOOK.md, recorded as unresolved item U-02; IMPLEMENTATION_PLAN.md fully in sync)

核对方法与 T014 相同（标准库 `zipfile` + XML 解析，无新增依赖；结果沿用 T014R2 的核对，因为 `PROJECT_BOOK.md`、`PROJECT_BOOK.docx`、`IMPLEMENTATION_PLAN.md`、`IMPLEMENTATION_PLAN.docx` 在 `1f02358` → `93d1b7c` 之间零改动，`git diff` 为空）：

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

T012 的覆盖结论（61/75 全文读、14 项部分读）原文保留，不由 T014 改写；T014 的覆盖表（`REVIEW_INDEX.md`）是另一份文件，锚定 T014R3 重冻 commit、覆盖全部 699 个追踪文件。

## 7. 已知未解决项

| ID | 级别 | 内容 | 影响与下一步 |
|---|---|---|---|
| R14-01 | **已修复** | README L61–64 仍保留 U-01 修复前的旧限制描述（check/serve/verify-s0 均需源码 checkout），与“Installing from the wheel”及“Known limitations”矛盾；R2 包 §3 称“无已失效的限制描述”的结论因此不属实。修复 commit `93d1b7c`（仅 README 一处表述）；验证：全文 grep 旧句零残留、三处表述一致（见 §3）；R2 包的失实结论在本包 §2 书面纠正。 | 已关闭；本包 §2–§3 为证据。 |
| U-01 | **已修复** | 已安装 wheel 无法 standalone 运行 `check`（exit 5）与 `serve`（启动崩溃）；`verify-s0` 同根。修复 commit `717b813`（合并进 `1f02358`）；验证：新 wheel 离线冒烟 `check` exit 1 MISMATCH、`serve` 健康/UI 200、`verify_release.py` 27/27 PASS。 | 已关闭；本包 §3 为证据。旧失败记录见 `REVIEW_PACK_T014.md` §3（原文保留）。 |
| U-02 | 非阻断 | DOCX 正文漂移：`PROJECT_BOOK.md` 7 处 T013 文字澄清未进 DOCX（见 §5）。 | 结构同步，无缺节。由规格方决定是否重生成 DOCX；T014 不擅自重写。 |
| U-03 | 非阻断 | SBOM 中 1 个包（`omegaconf` 2.4.0）在已安装发行版元数据中无许可声明（`release/SBOM_LICENSES.md` 如实标注，未推断）。 | 须在使用前另行核对上游 LICENSE；不影响安装与运行。 |

## 8. 交付物清单

| 交付物 | 位置 | 说明 |
|---|---|---|
| 源码包 | `release/source.zip` | §1；与锚定 commit 逐文件一致 |
| wheel | `release/textproof-1.0.0-py3-none-any.whl` | §1；可安装；standalone 运行已验证 |
| 离线安装包 | `release/wheelhouse/`（37 个 wheel） | 与锁文件逐包核对；与 R2 逐文件哈希一致 |
| 哈希清单 | `release/SHA256SUMS.txt` | 覆盖 source.zip + wheel + 37 个 wheelhouse wheel |
| 发布清单 | `release/RELEASE_MANIFEST.json` | 冻结 commit、产物哈希、已知未解决项（U-01、R14-01 已修复） |
| SBOM / 许可报告 | `release/SBOM_LICENSES.md` | 37 个包逐项许可（元数据来源；1 项未声明，见 U-03） |
| 审查索引 | `review/REVIEW_INDEX.md` | 锚定 commit；699 文件全覆盖；`verify_review_pack.py` PASS |
| 本审查包 | `review/REVIEW_PACK_T014R3.md` | 本文件 |
| 旧审查包 | `review/REVIEW_PACK_T014.md`、`review/REVIEW_PACK_T014R2.md` | 旧冻结包，U-01 失败证据与 R2 重冻记录，原文保留；R2 包 §3 的失实结论见本包 §2 纠正 |
| T012 审查复制件 | `review/REVIEW_FINDINGS_T012.md`、`review/REVIEW_INDEX_T012.md` | §6；逐字复制 |
| 发布验证脚本 | `scripts/verify_release.py`、`scripts/verify_review_pack.py` | 锚定 commit 内；禁令串 grep 零命中 |
| 发布文件 | `LICENSE`、`README.md`、`SECURITY.md` | R-13；README 含安装后使用说明，R14-01 旧句已修正 |
| 交接与证据 | `task_handoffs/T014/pkg/`（冒烟与测试证据）、`task_handoffs/T014/r14fix/`（本轮重冻交接） | TASK_RESULT.md、测试日志、离线冒烟原始日志、`offline_smoke.txt`、`verify_release.log` |
