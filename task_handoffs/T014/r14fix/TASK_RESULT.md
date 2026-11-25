# T014 重冻刷新（R3）— TASK_RESULT.md

- 任务 ID：T014-r14fix（T014R3：修独立复审 R14-01（P2）README 已失效的 U-01 限制描述，并按新冻结 commit 重冻）
- 分支：`t014-r14fix`；工作区：`~/workspace/p033-textproof-t014-r14fix`
- 输入 commit：`3f02b32`（T014R2 集成线 HEAD；T014 独立复审 FINAL_VERDICT: PASS，报告在 `~/workspace/p033-textproof-t014-review/task_handoffs/T014/review/REVIEW_REPORT.md`）
- 冻结 commit（本轮 README 修复）：`93d1b7c65036bb16f596117f26a48f6ee62f99e1`（= `3f02b32` + 仅 README 的 R14-01 修正）
- 输出 commit（本轮重冻提交）：`9befbee756eb5f739121b0af5717b5d9e8a32518`（21 文件）
- 本交接记录 commit：（提交后填入）
- 回退 commit：`3f02b32`（`git reset --hard 3f02b32` 即可回退；旧 release 产物随之恢复——那是 R2 的构建，含已失效的 README 旧句）

## 1. 改动文件（相对 3f02b32，见 changed_files.txt）

修改：`README.md`（冻结 commit 内，R14-01 一处表述）、`release/source.zip`、
`release/textproof-1.0.0-py3-none-any.whl`、`release/SHA256SUMS.txt`、
`release/RELEASE_MANIFEST.json`、`review/REVIEW_INDEX.md`、
`task_handoffs/T014/pkg/` 下证据（test_stdout.log、offline_install.log、
offline_smoke.txt、smoke_serve_probe.txt、verify_release.log、
verify_release_clean_dir.log）。

新增：`review/REVIEW_PACK_T014R3.md`、本交接目录 `task_handoffs/T014/r14fix/`
（本文件、changed_files.txt、test_commands.txt、test_stdout.log、test_stderr.log、
exit_codes.txt、smoke_run.sh、smoke_stdout.txt、smoke_stderr.txt）。

未修改：`release/SBOM_LICENSES.md`（复核一致，无需改动）、
`release/wheelhouse/`（37 个 wheel 逐文件哈希与 R2 一致，未重下、未升级）、
旧审查包 `review/REVIEW_PACK_T014.md`、`review/REVIEW_PACK_T014R2.md`、旧 T012 复制件、
`src/`、`tests/`、`schemas/`、fixture PNG、`tests/fixtures/s0/manifest.json`、
S0 门槛、输入输出契约、`tool_version`（仍 0.1.0）、`requirements.lock`、
`PROJECT_BOOK.md`、`IMPLEMENTATION_PLAN.md`、两份 `.docx`。

## 2. 逐项交付（IMPLEMENTATION_PLAN.md §T014 验收 1–9）

| 验收 | 结果 |
|---|---|
| 1. source.zip 与冻结 commit 逐文件一致 | PASS：699 文件，文件名集合 + 逐文件 SHA-256 全部一致（`verify_release.py` 核对 `git archive 93d1b7c`）。新 source.zip 512,109,756 B，SHA `9c2305ed…`；体积较 R2 的 263,808,324 B 增大，因为锚定 commit 本身已包含 R2 的 `release/` 产物（旧 source.zip 263,808,324 B + 全部 wheelhouse，合计约 443 MB）与 T013-U01 打进包的模型复制（`src/textproof/assets/ocr/models/`，约 32 MB）——`git archive` 忠实收录冻结树，是重冻的预期结果 |
| 2. wheel 可安装；离线 wheelhouse 安装和运行 | PASS：新 wheel 27,176,403 B，SHA `9c880b88…`，32 条目（ui/* 3 个 + 模型 3 个 + 校验器 + setup 模块，无字典）；全新 venv `--no-index` 安装 exit 0；`check` exit 1 MISMATCH（E001，报告 VALID）；`serve` 健康 200 + UI 200；`verify-s0` 两次 exit 3（定义行为） |
| 3. 模型、字典、字体及第三方依赖均有来源、版本、SHA-256 和许可证记录 | PASS：THIRD_PARTY_NOTICES.md（未动）+ `release/SBOM_LICENSES.md`（本轮按冒烟 venv 元数据复核：37 包版本与许可记录逐项一致；唯一无许可声明仍是 `omegaconf` 2.4.0，见 U-03） |
| 4. 300 fixture、manifest、盲测清单和 S0 报告均包含在 source / review 交付物中 | PASS：均在 source.zip（锚定 commit 树，699 文件）与 review 交付物中 |
| 5. SHA256SUMS.txt 覆盖所有发布文件；独立重算一致 | PASS：39 条（source.zip + wheel + 37 wheelhouse wheel），`sha256sum -c` 与第二种逐文件重算脚本全部一致 |
| 6. DOCX 与 Markdown 同步 | 结构 PASS（标题 67/40、表格 14/4、同序、无缺节、无占位符）；正文漂移 7 行（U-02，未解决，未擅自重写 docx）。结论沿用 T014R2：`PROJECT_BOOK.md`/`.docx`、`IMPLEMENTATION_PLAN.md`/`.docx` 在 `1f02358` → `93d1b7c` 之间零改动（`git diff` 为空），故 T014R2 的核对结果仍然成立 |
| 7. REVIEW_INDEX / REVIEW_PACK 锚定最终冻结 commit；覆盖可追踪 | PASS：索引重锚定到 93d1b7c，699 文件全覆盖（399 行 + 1 聚合行 = 400 行）；`verify_review_pack.py` PASS；新包 `REVIEW_PACK_T014R3.md` 为定稿包，其中 §2 书面纠正 R2 包 §3 的失实结论 |
| 8. verify_release.py 从干净目录运行 PASS | PASS：工作树与干净目录（`git worktree add --detach` 的 93d1b7c 全新检出 + 复制产物）均为 **27/27 PASS**。注：仍未用 `git clone` 进 /tmp（512M tmpfs）；改用持久磁盘上的 detached worktree（等价的全新检出），验证用的临时 worktree 已删除（`git worktree remove --force`） |
| 9. 版本身份一致（commit、source.zip、wheel、测试日志） | PASS：commit 93d1b7c、source.zip、wheel 1.0.0、测试日志 495 passed 均一致 |

## 3. 执行命令与退出码（全部真实跑出，见 test_commands.txt 与各日志）

| 命令 | 退出码 | 结果 |
|---|---|---|
| `python scripts/setup_dictionary.py`（主树 venv） | 0 | 字典重建；SHA `b5f2bfe2…`；18,708 行 |
| 全量 pytest（`mkdir -p tmp; TMPDIR=$PWD/tmp .venv/bin/python -m pytest -q -p no:cacheprovider`） | 0 | **495 passed、0 failed**（382.51s；2 warnings，与 T013-U01 相同的 DecompressionBomb warnings） |
| `python scripts/verify_review_pack.py review/REVIEW_INDEX.md` | 0 | PASS（400 行；699 文件全覆盖） |
| `python scripts/verify_release.py --preflight` | 0 | PASS（12/12） |
| `python scripts/verify_release.py`（工作树） | 0 | **PASS（27/27）** |
| `python scripts/verify_release.py --root ~/workspace/t014r3-clean`（干净目录） | 0 | **PASS（27/27）** |
| `git archive 93d1b7c --format=zip` → source.zip | 0 | 512,109,756 B；699 文件；字典零命中 |
| `python -m build --wheel --no-isolation`（干净导出） | 0 | 27,176,403 B；32 条目；ui + 3 模型；字典零命中 |
| wheelhouse 对照锁文件（独立脚本） | 0 | 37/37 版本与哈希一致；无多余、无缺失；与 R2 wheelhouse 逐文件哈希一致 |
| SHA256SUMS 独立重算 | 0 | 39 条全部一致（两种方法） |
| SBOM 复核（冒烟 venv 元数据逐项对照） | 0 | 37 包一致；仅 omegaconf 无许可声明（U-03） |
| 离线安装（全新 venv，`--no-index --find-links release/wheelhouse`） | 0 | 37 包全部安装 |
| `textproof --help`（新 wheel） | 0 | 正常 |
| `textproof version`（新 wheel） | 0 | tool 0.1.0 / package 1.0.0 / spec 1.0.0 / rapidocr 3.10.0 / onnxruntime 1.32.0 / CPU-only |
| `textproof check` 冒烟（新 wheel，standalone） | 1 | 正确：`MISMATCH` + `E001 MISSING_CHARACTER`（缺字“惠”）；报告经 `validate_report_schema.py` 校验 VALID（1/1 valid） |
| `textproof serve`（新 wheel） | 0（探针） | 健康 200 + UI 200（含 TextProof 与“可能包含敏感文字”）；serve 进程随后以 SIGTERM 停止（exit 143，预期） |
| `textproof verify-s0`（新 wheel，默认 + 带 manifest） | 3 / 3 | 定义行为：`S0 manifest not found` / `verify-s0 requires a source checkout` |
| README 三处表述一致性 grep | 0（新句）/ 1（旧句零命中） | 旧句 `require a source checkout` 全文零命中；L61–64 改后表述与“Installing from the wheel”一节及“Known limitations”节一致 |
| 禁令串 grep（验证脚本全文） | 1（零命中） | `urlopen/urlretrieve/os.system/shell=True/requests/httpx/urllib/http.client/socket` 全文零命中（本轮未新增脚本；两验证脚本未改动，复核通过） |

## 4. 禁令遵守证明

- 未改 `src/`、`tests/`、`schemas/`、fixture PNG、`tests/fixtures/s0/manifest.json`、S0 门槛、契约、规格文件、旧审查包与旧 T012 复制件：`git diff 3f02b32 -- src tests schemas tests/fixtures/s0/manifest.json requirements.lock PROJECT_BOOK.md IMPLEMENTATION_PLAN.md PROJECT_BOOK.docx IMPLEMENTATION_PLAN.docx review/REVIEW_PACK_T014.md review/REVIEW_PACK_T014R2.md review/REVIEW_FINDINGS_T012.md review/REVIEW_INDEX_T012.md` 为空（0 行）。
- `tool_version` 仍 0.1.0（`src/textproof/core/report.py:100`；`verify_release.py --preflight` 核对通过）。
- 未加 ￥→¥ 映射：`src/` 零改动（上条 diff 为空），冻结内容不变。
- 未缩小隐私扫描范围、未加白名单、未用 curl 绕过（全量 pytest 495 项通过，含 T010 静态门禁）。
- 字典零命中：`git ls-files | grep ppocrv6_dict` = 0；source.zip 清单 0；wheel 32 条目 0；wheelhouse 文件名 0；SHA256SUMS.txt 文本 0。
- 未新增脚本，故无新脚本禁令串问题；两验证脚本未改动（其哈希与 3f02b32 一致，见清单）。
- README 只改 L61–64 一处表述（+4/−3 行）；旧句全文零残留，三处表述一致（见 §3 与 REVIEW_PACK_T014R3.md §3）。
- 未编造测试数据、截图或版本号；全部证据为真实运行输出（原始日志均在 `task_handoffs/T014/pkg/` 内；本轮冒烟脚本存于 `task_handoffs/T014/r14fix/smoke_run.sh`）。

## 5. R14-01 修复对照（旧包结论纠正）

| 项 | R2 包 `REVIEW_PACK_T014R2.md` §3 | 本轮事实 |
|---|---|---|
| README 复核结论 | “无已失效的限制描述” | **不属实**：L61–64 仍保留 U-01 修复前旧句（check/serve/verify-s0 均需源码 checkout），与 L203、L236 矛盾 |
| 修复 | — | commit `93d1b7c` 改写该句一处；全文 grep 旧句零残留；三处表述一致 |
| 旧包处理 | — | 原文保留，未改动；失实结论在本包 §2 与 `REVIEW_PACK_T014R3.md` §2 书面纠正 |

## 6. 未完成项 / 未解决项

| ID | 级别 | 内容 |
|---|---|---|
| U-02 | 非阻断 | DOCX 正文漂移：`PROJECT_BOOK.md` 7 处 T013 文字澄清未进 DOCX（结构同步：标题 67/40、表格 14/4、同序、无缺节、无占位符）。由规格方决定是否重生成 DOCX。 |
| U-03 | 非阻断 | `omegaconf` 2.4.0 在已安装发行版元数据中无许可声明（SBOM 如实标注，未推断）。 |
| — | — | 无其他未完成项。本轮任务全部完成。R14-01 与 U-01 均为已修复（见清单 `resolved_items`）。 |

## 7. 风险

- **source.zip 内含旧 release 产物且体积继续叠加**：锚定 commit 93d1b7c 本身已包含 R2 的 `release/`（旧 source.zip 263,808,324 B + wheelhouse），`git archive` 忠实收录，故新 source.zip 达 512,109,756 B。这是重冻的预期结果（冻结树即如此），`verify_release.py` 的逐文件一致性检查通过；但终审方应知晓：source.zip 内嵌了两份旧 release 快照。下一轮若再重冻，体积会继续叠加——建议未来冻结 commit 不再把 `release/` 产物入库，或由协调员定夺。
- **干净目录验证改用 worktree 而非 clone**：/tmp tmpfs 仅 512M；改用持久磁盘上的 `git worktree add --detach 93d1b7c`（全新检出，等价干净目录）后 27/27 通过。验证用的临时 worktree 已删除（`git worktree remove --force`）。
- **pytest 运行产物**：全量 pytest 在 `tests/e2e/evidence/` 写出截图与 network_requests.json（测试自身行为）；已删除，未入库。`tmp/`（venv-offline、smoke 文件、pytest TMPDIR）亦已删除。
- **冒烟日志字节一致**：本轮 `smoke_serve2.log` 与 `smoke_report_standalone.json` 与 R2 的逐字节一致（同一输入、同一确定性输出），故 git 未将其列为改动；新 wheel 的冒烟证据以 `offline_smoke.txt`（已更新 wheel SHA 与冻结 commit）、`smoke_serve_probe.txt`、`offline_install.log` 与 `smoke_stdout.txt` 为准。
- **SBOM 复核踩坑**：首次复核脚本对 venv python 用了 `Path.resolve()`，解析符号链接后走到系统 python（48 个发行版、旧版本），误报 FAIL；改用未解析路径 `tmp/venv-offline/bin/python` 后 37/37 PASS。教训已记入 `task_handoffs/T014/r14fix/test_commands.txt` §8。
- **旧冒烟日志的残留**：`task_handoffs/T014/pkg/smoke_serve.log` 仍是 T014 的 U-01 serve 崩溃日志（历史证据，未动）；本次通过的 serve 运行记在 `smoke_serve2.log` + `smoke_serve_probe.txt`，`offline_smoke.txt` 头部已注明。

## 8. 测试结果

- 全量 pytest：**495 passed、0 failed、exit 0**（382.51s；2 warnings；日志 `task_handoffs/T014/pkg/test_stdout.log`，副本见本目录 test_stdout.log）。
- `verify_review_pack.py`：PASS（400 行；699 文件全覆盖）。
- `verify_release.py`：工作树与干净目录均为 **27/27 PASS**。
- 离线冒烟（新 wheel）：安装 0、`--help` 0、`version` 0（0.1.0/1.0.0/1.0.0）、`check` exit 1 MISMATCH（E001，报告 VALID）、`serve` 健康/UI 200、`verify-s0` 两次 exit 3。

## 9. 回退

- 回退 commit：`3f02b32`。`git reset --hard 3f02b32` 即回到 T014R2 集成线（release 产物回到 R2 构建，README 回到含旧句的版本）；或 `git revert <本轮输出 commit>`。
