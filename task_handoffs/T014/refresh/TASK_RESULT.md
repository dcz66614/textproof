# T014 重冻刷新（R2）— TASK_RESULT.md

- 任务 ID：T014-refresh（T014R2：按新冻结 commit 1f02358 重建全部 release 产物；U-01 修复已合并）
- 分支：`t014-refresh`；工作区：`~/workspace/p033-textproof-t014-refresh`
- 输入 commit：`1f02358f1c44b4de4a7d6e0b80dd97bef633a5b6`（T014 集成线 HEAD = main + R-03 + R-13 + T014 打包 + T013-U01 修复）
- 输出 commit（本轮重冻提交）：`e1fab5026e29e05e8ad6483e68ca712d37bf66c8`（22 文件）
- 本交接记录 commit：（提交后填入）
- 回退 commit：`1f02358`（`git reset --hard 1f02358` 即可回退；旧 release 产物随之恢复——但那是含 U-01 缺陷的旧构建）

## 1. 改动文件（相对 1f02358，见 changed_files.txt / git_diff.patch）

修改：`release/source.zip`、`release/textproof-1.0.0-py3-none-any.whl`、
`release/SHA256SUMS.txt`、`release/RELEASE_MANIFEST.json`、
`review/REVIEW_INDEX.md`、
`task_handoffs/T014/pkg/` 下证据（test_stdout.log、exit_codes.txt、
offline_install.log、offline_smoke.txt、smoke_serve2.log、
verify_release.log、verify_release_clean_dir.log）。

新增：`review/REVIEW_PACK_T014R2.md`、
`task_handoffs/T014/pkg/smoke_serve_probe.txt`、
本交接目录 `task_handoffs/T014/refresh/`（本文件、changed_files.txt、
git_diff.patch、test_commands.txt、test_stdout.log、test_stderr.log、
exit_codes.txt、SHA256SUMS.txt、smoke_run.sh）。

未修改：`release/SBOM_LICENSES.md`（复核一致，无需改动）、
`release/wheelhouse/`（37 个 wheel 逐文件哈希与 T014 一致，未重下、未升级）、
旧审查包 `review/REVIEW_PACK_T014.md`、旧 T012 复制件、
`src/`、`tests/`、`schemas/`、fixture PNG、`tests/fixtures/s0/manifest.json`、
S0 门槛、输入输出契约、`tool_version`（仍 0.1.0）、`requirements.lock`、
`PROJECT_BOOK.md`、`IMPLEMENTATION_PLAN.md`、两份 `.docx`。

## 2. 逐项交付（IMPLEMENTATION_PLAN.md §T014 验收 1–9）

| 验收 | 结果 |
|---|---|
| 1. source.zip 与冻结 commit 逐文件一致 | PASS：688 文件，文件名集合 + 逐文件 SHA-256 全部一致（`verify_release.py` 核对 `git archive 1f02358`）。新 source.zip 263,808,324 B，SHA `9fb6ca97…`；体积较 T014 的 42,734,094 B 增大，因为锚定 commit 本身已包含 T014 的 `release/` 产物（旧 source.zip + 全部 wheelhouse，约 195 MB）与 T013-U01 打进包的模型复制（`src/textproof/assets/ocr/models/`，约 32 MB）——`git archive` 忠实收录冻结树，是重冻的预期结果 |
| 2. wheel 可安装；离线 wheelhouse 安装和运行 | PASS：新 wheel 27,176,403 B，SHA `cffd5183…`，32 条目（ui/* 3 个 + 模型 3 个 + 校验器 + setup 模块，无字典）；全新 venv `--no-index` 安装 exit 0；`check` exit 1 MISMATCH（E001）；`serve` 健康 200 + UI 200；`verify-s0` 两次 exit 3（定义行为） |
| 3. 模型、字典、字体及第三方依赖均有来源、版本、SHA-256 和许可证记录 | PASS：THIRD_PARTY_NOTICES.md（未动）+ `release/SBOM_LICENSES.md`（本轮按新 wheel/锁文件复核：37 包版本与许可记录与构建 venv 元数据逐项一致；唯一无许可声明仍是 `omegaconf` 2.4.0，见 U-03） |
| 4. 300 fixture、manifest、盲测清单和 S0 报告均包含在 source / review 交付物中 | PASS：均在 source.zip（锚定 commit 树，688 文件）与 review 交付物中 |
| 5. SHA256SUMS.txt 覆盖所有发布文件；独立重算一致 | PASS：39 条（source.zip + wheel + 37 wheelhouse wheel），独立重算全部一致 |
| 6. DOCX 与 Markdown 同步 | 结构 PASS（标题 67/40、表格 14/4、同序、无缺节、无占位符）；正文漂移 7 行（U-02，未解决，未擅自重写 docx）。结论沿用 T014：`PROJECT_BOOK.md`/`.docx`、`IMPLEMENTATION_PLAN.md`/`.docx` 在 `167594e` → `1f02358` 之间零改动（`git diff` 为空），故 T014 的核对结果仍然成立 |
| 7. REVIEW_INDEX / REVIEW_PACK 锚定最终冻结 commit；覆盖可追踪 | PASS：索引重锚定到 1f02358，688 文件全覆盖（388 行 + 1 聚合行 = 389 行）；`verify_review_pack.py` PASS；新包 `REVIEW_PACK_T014R2.md` 为定稿包 |
| 8. verify_release.py 从干净目录运行 PASS | PASS：工作树与干净目录（`git worktree add --detach` 的 1f02358 全新检出 + 复制产物）均为 **27/27 PASS**。注：首次尝试用 `git clone` 进 /tmp 失败——/tmp 是 512M tmpfs，仅剩 159M，clone 写对象时报 No space left on device（环境限制，非产品问题）；改用持久磁盘上的 detached worktree（等价的全新检出）后通过 |
| 9. 版本身份一致（commit、source.zip、wheel、测试日志） | PASS：commit 1f02358、source.zip、wheel 1.0.0、测试日志 495 passed 均一致 |

## 3. 执行命令与退出码（全部真实跑出，见 test_commands.txt 与各日志）

| 命令 | 退出码 | 结果 |
|---|---|---|
| `python scripts/setup_dictionary.py`（主树 venv） | 0 | 字典重建；SHA `b5f2bfe2…`；18,708 行 |
| 全量 pytest（`mkdir -p tmp; TMPDIR=$PWD/tmp .venv/bin/python -m pytest -q -p no:cacheprovider`） | 0 | **495 passed、0 failed**（176.27s；2 warnings，与 T013-U01 相同的 DecompressionBomb warnings） |
| `python scripts/verify_review_pack.py review/REVIEW_INDEX.md` | 0 | PASS（389 行；688 文件全覆盖） |
| `python scripts/verify_release.py --preflight` | 0 | PASS（12/12） |
| `python scripts/verify_release.py`（工作树） | 0 | **PASS（27/27）** |
| `python scripts/verify_release.py --root ~/workspace/t014r2-clean`（干净目录） | 0 | **PASS（27/27）** |
| `git archive 1f02358 --format=zip` → source.zip | 0 | 263,808,324 B；688 文件；字典零命中 |
| `python -m build --wheel --no-isolation`（干净导出） | 0 | 27,176,403 B；32 条目；ui + 3 模型；字典零命中 |
| wheelhouse 对照锁文件（独立脚本） | 0 | 37/37 版本与哈希一致；无多余、无缺失 |
| SHA256SUMS 独立重算 | 0 | 39 条全部一致 |
| SBOM 复核（venv 元数据逐项对照） | 0 | 37 包一致；仅 omegaconf 无许可声明（U-03） |
| 离线安装（全新 venv，`--no-index --find-links release/wheelhouse`） | 0 | 37 包全部安装 |
| `textproof --help`（新 wheel） | 0 | 正常 |
| `textproof version`（新 wheel） | 0 | tool 0.1.0 / package 1.0.0 / spec 1.0.0 / rapidocr 3.10.0 / onnxruntime 1.32.0 / CPU-only |
| `textproof check` 冒烟（新 wheel，standalone） | 1 | 正确：`MISMATCH` + `E001 MISSING_CHARACTER`（缺字“惠”）；报告通过包内校验 |
| `textproof serve`（新 wheel） | 0（探针） | 健康 200 + UI 200（含 TextProof 与“可能包含敏感文字”）；serve 进程随后以 SIGTERM 停止（exit 143，预期） |
| `textproof verify-s0`（新 wheel，默认 + 带 manifest） | 3 / 3 | 定义行为：`S0 manifest not found` / `verify-s0 requires a source checkout` |
| 禁令串 grep（新脚本全文） | 1（零命中） | `urlopen/urlretrieve/os.system/shell=True/requests/httpx/urllib/http.client/socket` 全文零命中（本轮未新增脚本；两验证脚本未改动，复核通过） |

## 4. 禁令遵守证明

- 未改 `src/`、`tests/`、`schemas/`、fixture PNG、`tests/fixtures/s0/manifest.json`、S0 门槛、契约、规格文件、旧审查包与旧 T012 复制件：`git diff 1f02358 -- src tests schemas tests/fixtures/s0/manifest.json requirements.lock PROJECT_BOOK.md IMPLEMENTATION_PLAN.md PROJECT_BOOK.docx IMPLEMENTATION_PLAN.docx review/REVIEW_PACK_T014.md review/REVIEW_FINDINGS_T012.md review/REVIEW_INDEX_T012.md` 为空（0 行）。
- `tool_version` 仍 0.1.0（`src/textproof/core/report.py:100`；`verify_release.py --preflight` 核对通过）。
- 未加 ￥→¥ 映射：`src/*.py` 中无 `¥`；`￥` 命中仅为冻结文件原有内容（normalize.py 的不映射 docstring、fixture 定义、独立验证脚本的注释），均在 1f02358 已有，本轮零改动。
- 未缩小隐私扫描范围、未加白名单、未用 curl 绕过（全量 pytest 495 项通过，含 T010 静态门禁）。
- 字典零命中：`git ls-files | grep ppocrv6_dict` = 0；source.zip 清单 0；wheel 32 条目 0；wheelhouse 文件名 0；SHA256SUMS.txt 文本 0。
- 未新增脚本，故无新脚本禁令串问题；两验证脚本未改动（其哈希与 1f02358 一致，见清单）。
- README 复核：无已失效的限制描述。“Installing from the wheel”一节说明安装后使用（含字典重建与 verify-s0 exit 3）；“Known limitations”节为“(None currently recorded.)”，与 U-01 已修复状态一致。本轮未改 README。
- 未编造测试数据、截图或版本号；全部证据为真实运行输出（原始日志均在 `task_handoffs/T014/pkg/` 内；本轮冒烟脚本存于 `task_handoffs/T014/refresh/smoke_run.sh`）。

## 5. U-01 已修复的证据（新 wheel）

| 旧失败（T014，旧 wheel 939dbb57…） | 新结果（T014R2，新 wheel cffd5183…） |
|---|---|
| `check` exit 5，`generated report failed schema validation` | `check` exit 1，`MISMATCH` + `E001 MISSING_CHARACTER`，报告通过包内校验 |
| `serve` 启动崩溃 exit 1，`textproof/ui does not exist` | `serve` 启动成功，健康 200 + UI 200 |
| `verify-s0` 在 checkout 外找不到 runner/manifest（未定义行为） | 两次 exit 3，文案明确定义 |

清单 `resolved_items` 已记 U-01（修复 commit 717b813，合并进 1f02358，验证方式 verify_release.py 27/27 PASS）；`known_unresolved_items` 只剩 U-02、U-03（非阻断）。

## 6. 未完成项 / 未解决项

| ID | 级别 | 内容 |
|---|---|---|
| U-02 | 非阻断 | DOCX 正文漂移：`PROJECT_BOOK.md` 7 处 T013 文字澄清未进 DOCX（结构同步：标题 67/40、表格 14/4、同序、无缺节、无占位符）。由规格方决定是否重生成 DOCX。 |
| U-03 | 非阻断 | `omegaconf` 2.4.0 在已安装发行版元数据中无许可声明（SBOM 如实标注，未推断）。 |
| — | — | 无其他未完成项。本轮任务 9 项全部完成。 |

## 7. 风险

- **source.zip 内含旧 release 产物**：锚定 commit 1f02358 本身已包含 T014 的 `release/`（旧 source.zip + wheelhouse），`git archive` 忠实收录，故新 source.zip 达 263,808,324 B。这是重冻的预期结果（冻结树即如此），`verify_release.py` 的逐文件一致性检查通过；但终审方应知晓：source.zip 内嵌了一份旧 release 快照。下一轮若再重冻，体积会继续叠加——建议未来冻结 commit 不再把 `release/` 产物入库，或由协调员定夺。
- **干净目录验证改用 worktree 而非 clone**：/tmp tmpfs 仅剩 159M，`git clone` 写对象时磁盘满；改用持久磁盘上的 `git worktree add --detach 1f02358`（全新检出，等价干净目录）后 27/27 通过。验证用的临时 worktree 已删除（`git worktree remove --force`）。
- **pytest 运行产物**：全量 pytest 在 `tests/e2e/evidence/` 写出截图与 network_requests.json（测试自身行为）；已删除，未入库。`tmp/`（venv-offline、smoke 文件、pytest TMPDIR）亦已删除。
- **旧冒烟日志的残留**：`task_handoffs/T014/pkg/smoke_serve.log` 仍是 T014 的 U-01 serve 崩溃日志（历史证据，未动）；本次通过的 serve 运行记在 `smoke_serve2.log` + `smoke_serve_probe.txt`，`offline_smoke.txt` 头部已注明。`smoke_check_repo.log` / `smoke_check_wpp.log` 等诊断文件亦为 T014 旧物，未动。

## 8. 测试结果

- 全量 pytest：**495 passed、0 failed、exit 0**（176.27s；2 warnings；日志 `task_handoffs/T014/pkg/test_stdout.log`，副本见本目录 test_stdout.log）。
- `verify_review_pack.py`：PASS（389 行；688 文件全覆盖）。
- `verify_release.py`：工作树与干净目录均为 **27/27 PASS**。
- 离线冒烟（新 wheel）：安装 0、`--help` 0、`version` 0（0.1.0/1.0.0/1.0.0）、`check` exit 1 MISMATCH（E001）、`serve` 健康/UI 200、`verify-s0` 两次 exit 3。

## 9. 回退

- 回退 commit：`1f02358`。`git reset --hard 1f02358` 即回到 T014 集成线（含 U-01 修复的源码，但 release 产物回到修复前旧构建）；或 `git revert <本轮输出 commit>`。
