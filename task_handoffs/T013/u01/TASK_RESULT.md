# T013-U01 修复轮次 — TASK_RESULT.md

- 任务 ID：T013-U01（T014 打包验证发现的阻断缺陷 U-01：已安装 wheel 无法独立运行）
- 分支：`t013-u01`；工作区：`~/workspace/p033-textproof-t013-u01`
- 输入 commit：`a08dcc0`（T014 集成线 HEAD = main + R-03 字典方案 + R-13 发布文件 + T014 打包）
- 输出 commit（修复）：`717b813`（源码修复 + 6 项新测试 + 文档）
- 输出 commit（证据）：`c209a2e`（冒烟证据 + pytest 日志 + 清单同步）
- 输出 commit（本交接）：（提交后填入）
- 回退 commit：`a08dcc0`（`git reset --hard a08dcc0` 即可回退；或 `git revert 717b813 c209a2e`）

## 1. 缺陷与根因（复核协调员的定位，全部属实）

| 症状（已安装 wheel，离线全新 venv） | 根因 |
|---|---|
| `check` exit 5：`generated report failed schema validation`（OCR 已跑完） | `cli.py::_validate_report()` 以 `parents[2]` 定位仓库根并 `from scripts.validate_report_schema import ...`；已安装布局下该路径是 `<venv>/lib/python3.12`，无 `scripts/`，导入失败 → fail-closed |
| `serve` 启动崩溃 exit 1：`Directory '.../site-packages/textproof/ui' does not exist` | `api/app.py:94` 挂载包内 `textproof/ui`，但 wheel 不含 `ui/*`（无 package-data 配置） |
| `verify-s0` 在 checkout 外找不到 `scripts/verify_s0.py` 与默认 manifest | 同根的仓库布局假设（`cli.py:285`、`REPO_ROOT`） |
| 无资产时 `check` exit 4（`FileNotFoundError`） | 适配器默认资产目录是 `parents[3]/assets/ocr`，已安装布局下无此内容；wheel 内本无模型 |

## 2. 设计决策（本轮定夺，写下来供终审/重冻核对）

### 2.1 资产边界（§11.2 / §11.3 第 2、3 项）

- **模型（Apache-2.0，可再分发）随 wheel 走**：`src/textproof/assets/ocr/models/` 是 `assets/ocr/models/` 的**逐字复制**（同一文件、同一 SHA-256），以 package-data 打进 wheel。`assets/ocr/models/` 仍是 canonical checkout 位置；两份复制的一致性由新测试 `test_packaged_model_copies_match_checkout` 锁定（SHA-256 逐个比对），适配器启动时也会对实际使用的那份验 SHA。wheel 因此从 52 KB 增大到约 27 MB。
- **字典（许可 UNVERIFIED）绝不进 wheel / source.zip / 任何公开产物**（R-03 裁决不变）：wheel 的 package-data glob 只匹配 `assets/ocr/models/*.onnx`，字典路径即使存在于构建机也不会被收录；`.gitignore` 新增 `src/textproof/assets/ocr/dictionaries/ppocrv6_dict.txt`；新 wheel 与 source.zip 的字典零命中已实测（见 §5）。
- **字典在已安装布局下由用户本地重建**：`python -m textproof.setup_dictionary`（逻辑已从 `scripts/setup_dictionary.py` 移进 `textproof.setup_dictionary` 包内模块；原脚本改为薄 wrapper，checkout 用法与退出码 0/2/3/4 不变）。重建读取 wheel 内模型的 embedded `character` 元数据，写到已安装包的 `textproof/assets/ocr/dictionaries/ppocrv6_dict.txt`，再按冻结 SHA `b5f2bfe2…` 与 18,708 行自验。
- **资产解析顺序**（`rapidocr_adapter.default_assets_dir()`，新增公开函数）：`TEXTPROOF_ASSETS_DIR`（显式覆盖）→ checkout `assets/ocr`（含三模型时优先，源码树行为**不变**）→ 打包的 `textproof/assets/ocr`（wheel 内）→ 否则回落到 checkout 路径（缺资产报错仍报熟悉的位置）。字典永远与模型取自同一目录。`TEXTPROOF_ASSETS_DIR` 也为 site-packages 不可写的环境留了出口（指向可写目录；模型需自行从 wheel 内取出——README 未展开该手工路径，见 §7 风险）。

### 2.2 校验器与 UI 随包可用

- 校验器实现**移进包内** `src/textproof/core/report_schema.py`（原文照搬，只改了 docstring 头）；`scripts/validate_report_schema.py` 改为薄 wrapper（re-export `validate_report`/`main`，直接运行时自动补 `src/` 到 `sys.path`）。`from scripts.validate_report_schema import validate_report` 的既有导入（测试、verify_s0、compute_s0_metrics）继续可用；CLI 的 `_validate_report()` 改为直接调用包内实现，**fail-closed 语义不变**（无效报告仍 exit 5）。
- UI（`ui/*`）与模型同以 `[tool.setuptools.package-data]` 打进 wheel；`api/app.py` 的挂载代码**未动**（包内相对路径在两种布局下都成立）。未加 `MANIFEST.in`：sdist 不是发布物（source.zip 走 `git archive`），不引入字典误收风险。

### 2.3 `verify-s0` 的已安装行为（明确定义，非含糊崩溃）

- **已安装布局下 `verify-s0` 不运行、不声称任何 S0 结论**：S0 门禁依赖 checkout 的 300 张 fixture、manifest 与 `scripts/` 助手脚本，这些不进 wheel。行为定义：默认 manifest 不存在 → exit 3 `S0 manifest not found`（与原来一致）；manifest 存在但 runner 不存在 → exit 3 `verify-s0 requires a source checkout: the S0 runner is not shipped in the wheel.`。两种都是明确拒绝，**绝不静默通过**。源码树内行为不变（仍 subprocess 委托，`cmd[1]` 仍以 `scripts/verify_s0.py` 结尾，既有测试未动）。
- `REPO_ROOT` / `DEFAULT_MANIFEST` 的定义未改（源码树内仍指向 `tests/fixtures/s0/manifest.json`，既有 `test_parser_defaults` 断言未动）。

## 3. 改动文件（相对 a08dcc0，见 changed_files.txt / git_diff.patch）

新增：`src/textproof/core/report_schema.py`（校验器实现，原文搬移）、
`src/textproof/setup_dictionary.py`（字典重建实现）、
`src/textproof/assets/__init__.py` + `src/textproof/assets/ocr/models/` 下 3 个模型复制、
`tests/integration/test_installed_wheel.py`（6 项新测试）、
`task_handoffs/T014/pkg/setup_dictionary_install.log`、
`task_handoffs/T014/pkg/smoke_report_standalone.json`、
本交接目录 `task_handoffs/T013/u01/`。

修改：`src/textproof/cli.py`（校验器直连包内实现；verify-s0 缺 runner 时 exit 3）、
`src/textproof/ocr/rapidocr_adapter.py`（资产解析顺序 + `default_assets_dir()`）、
`scripts/validate_report_schema.py`（薄 wrapper）、
`scripts/setup_dictionary.py`（薄 wrapper）、
`pyproject.toml`（package-data：`ui/*` + `assets/ocr/models/*.onnx`）、
`.gitignore`（包内字典路径）、
`README.md`（U-01 已知限制节改为“Installing from the wheel”使用说明）、
`THIRD_PARTY_NOTICES.md`（§2 wheel 模型复制说明；§4 安装布局重建路径 + 包内字典排除；**许可 UNVERIFIED 判定原文未动**）、
`scripts/verify_release.py`（期望 pytest 数 489 → 495；其余逻辑未动）、
`release/RELEASE_MANIFEST.json`（仅 `scripts/verify_release.py` 的哈希/大小条目与 `test_evidence.pytest` 字符串；见 §6 注意）、
`task_handoffs/T014/pkg/` 下冒烟与 pytest 证据（见 §5）。

## 4. 禁令遵守证明

- 未改现有测试预期、fixture PNG、`tests/fixtures/s0/manifest.json`、S0 门槛、输入输出契约：`git diff a08dcc0 HEAD -- tests/fixtures/s0/manifest.json schemas requirements.lock src/textproof/core/report.py PROJECT_BOOK.md IMPLEMENTATION_PLAN.md PROJECT_BOOK.docx IMPLEMENTATION_PLAN.docx` 全部为空（0 行）。
- `tool_version` 仍 `0.1.0`（`src/textproof/core/report.py:100`；`textproof version` 实测三版本 0.1.0 / 1.0.0 / 1.0.0）。
- 未加 ￥→¥ 映射；未缩小隐私扫描范围、未加白名单、未用 curl 绕过（全量 pytest 495 项通过，含 T010 静态门禁）。
- 未把字典重新加回 git 追踪、wheel 或任何公开产物：`git ls-files | grep ppocrv6_dict` = 0；新 wheel 内字典零命中；`release/source.zip`（654 条目，含目录项）字典零命中；THIRD_PARTY_NOTICES.md §4 许可仍为 **UNVERIFIED**（3 处原文保留）。
- 新脚本禁用串 grep：`urlopen / urlretrieve / os.system / shell=True / requests / httpx / urllib / http.client / socket` 在 `scripts/` 新 wrapper 与全部新增/改动的 `src/` 文件中**零命中**。唯一命中在新增**测试**文件 `tests/integration/test_installed_wheel.py`（`urllib`/`socket` 仅用于 127.0.0.1 的 serve 健康探针，与既有 `tests/integration/test_cli.py` 的同款写法一致；T010 静态扫描范围是 `src/**/*.py` + `scripts/*.py`，测试文件不在其中）。

## 5. 执行命令与退出码（全部真实跑出）

| 命令 | 退出码 | 结果 |
|---|---|---|
| `python scripts/setup_dictionary.py`（worktree，主树 venv） | 0 | 字典重建；SHA `b5f2bfe2…`；18,708 行 |
| 全量 pytest（`mkdir -p tmp; TMPDIR=$PWD/tmp .venv/bin/python -m pytest -q -p no:cacheprovider`，HEAD `717b813` 上） | 0 | **495 passed、0 failed**（194.46s；2 warnings，与 T014 相同的 DecompressionBomb warnings） |
| 新测试单跑 `tests/integration/test_installed_wheel.py`（6 项，含端到端冒烟） | 0 | 6 passed（35.27s） |
| `python scripts/verify_release.py --preflight` | 0 | PASS（12/12） |
| `python scripts/verify_release.py`（worktree） | 0 | **PASS（27/27）**，此前唯一失败的离线冒烟项通过 |
| `python scripts/verify_release.py --root <干净目录>`（detached worktree，commit `c209a2e`） | 0 | **PASS（27/27）**，日志见 `verify_release_clean_dir.log` |
| `python scripts/verify_review_pack.py review/REVIEW_INDEX.md` | 0 | PASS（596 文件全覆盖） |
| 手动离线冒烟（脚本 `task_handoffs/T013/u01/smoke_run.sh`；wheel 由修复 commit `717b813` 构建，SHA `6d2d45f13a3647f908a955492138f4c7104065736d38f9fda7f95bb62042b7ca`，32 条目） | 0 | 全新 venv；`pip install --no-index --find-links release/wheelhouse` exit 0；`--help` 0；`version` 0（0.1.0/1.0.0/1.0.0，rapidocr 3.10.0，onnxruntime 1.32.0，仅 CPUExecutionProvider）；`python -m textproof.setup_dictionary` exit 0（SHA `b5f2bfe2…`，18,708 行）；`check` TP-S0-ZH-001 + “限时优惠” **exit 1，MISMATCH，E001 MISSING_CHARACTER，报告通过包内校验、无路径泄漏**；`serve` 健康 200（`status ok`）+ UI 200（含 TextProof 与“可能包含敏感文字”）；`verify-s0` 默认 exit 3、带 manifest exit 3（定义见 §2.3） |
| 禁令串 grep（§4） | 1（零命中） | `src/` + `scripts/` 新/改文件零命中；命中仅在新测试文件的 loopback 探针 |

## 6. 未完成项与重冻注意事项（重要，请协调员不要漏掉）

1. **`release/` 产物仍是修复前构建，必须重冻重建**：`release/textproof-1.0.0-py3-none-any.whl`、`source.zip`、`SHA256SUMS.txt` 仍是 T014 的旧构建（旧 wheel 仍有 U-01 缺陷）。本轮的 `verify_release.py` PASS 依赖的是**新证据**——由修复 commit 构建的 wheel 的冒烟结果（`task_handoffs/T014/pkg/offline_smoke.txt` 头部已写明 wheel 来源 commit 与 SHA）——不是 `release/` 里的旧 wheel。重冻时须：从新 HEAD 重新 `git archive` 出 source.zip、重新 `python -m build --wheel`、重算 SHA256SUMS、重生成 RELEASE_MANIFEST（新 `source_commit`、新产物哈希、**从 `known_unresolved_items` 移除 U-01**）。
2. **`RELEASE_MANIFEST.json` 仍列 U-01 为 BLOCKING**：有意保留——该清单描述的是冻结的 `release/` 产物（仍为旧构建），不是修复后的源码。`verify_release.py` 因此仍在末尾打印 U-01 BLOCKING，但 27 项检查全部通过；重冻重生成清单时移除。
3. **`review/REVIEW_PACK_T014.md` 未动**：它记录的是 T014 冻结时的旧 wheel 哈希与 U-01 失败；改它会破坏清单哈希且属于审查证据，不由本修复轮次改写。重冻须出新审查包（或由审查轮次更新）。
4. **Wheel 体积**：27 MB（含 32 MB 模型文件，压缩后）；wheelhouse 不变。
5. **冒烟证据的 wheel 不是 `release/` 的 wheel**：`task_handoffs/T014/pkg/` 下的 `offline_install.log` 等安装的是 `tmp/smoke/dist/` 的修复版 wheel（`tmp/` 为 scratch，未提交；wheel 本身可由 `717b813` 重新构建复现，SHA 见 §5）。

## 7. 风险

- **模型双份漂移**：`src/textproof/assets/ocr/models/` 与 `assets/ocr/models/` 两份复制可能随时间漂移。缓解：新测试逐文件比对 SHA-256；适配器启动时对实际使用的那份验 SHA（漂移会 fail-closed 报错而非静默用错文件）。若将来升级模型，两处须同步更新（建议重冻检查单上加一项）。
- **字典重建写入 site-packages**：需要安装位置可写；系统级只读安装下须用 `TEXTPROOF_ASSETS_DIR` 指向可写目录并自行把模型复制过去，README 未展开该手工路径。常规用户 venv 不受影响。
- **新测试的端到端冒烟较慢**：全量套件从 142s 增至约 194s，主要来自新测试的 venv 创建 + 离线安装 + 真实 OCR（单跑约 35–40s）。这是有意的回归覆盖，不得为提速而 stub 引擎或把 checkout 放上路径。
- **e2e 测试构建 wheel 时的 worktree 污染**：初版测试误以 worktree 为构建源目录，留下 `build/` 与 `*.egg-info/`；已修复为在 pytest 临时目录的 scratch 副本内构建（提交前已清理；`git status` 干净）。

## 8. 测试结果

- 全量 pytest：**495 passed、0 failed、exit 0**（194.46s；2 warnings；日志 `test_stdout.log` / `test_stderr.log`）。
- 新增 6 项（`tests/integration/test_installed_wheel.py`）：包内校验器与脚本 wrapper 一致、checkout 资产优先、打包模型复制与 checkout 字节一致、verify-s0 两种 exit-3 拒绝、端到端离线冒烟（check exit 1 MISMATCH + serve 健康/UI + verify-s0 exit 3）。
- `verify_release.py`：工作树与干净目录均为 **27/27 PASS**。
- `verify_review_pack.py`：PASS。

## 9. 回退

- 回退 commit：`a08dcc0`。`git reset --hard a08dcc0`（或 `git revert 717b813 c209a2e`）即回到 T014 集成线；U-01 随之恢复为已知阻断项（`verify_release.py` 回到 26/27 FAIL）。
