# T014 打包收尾 — TASK_RESULT.md（pkg）

- 任务 ID：T014（R-13 发布文件 + T014 打包 + R-30 + R-31 复核）
- 分支：`t014-pkg`；工作区：`~/workspace/p033-textproof-t014-pkg`
- 输入 commit：`c1694e3`（任务基线 = main `9cfaace` + 已合并的 R-03）
- 冻结源码 commit（C1）：`167594e0442090c057baba7c067c323dd88cf530`
  （含 R-13 发布文件与 R-30 审查脚本；`release/`、`review/` 生成物与本交接日志在其后的 release 提交中入库）
- 输出 commit（C2，release 提交）：`b3533fba0eb57b072f609cc58d78a6773eaaeb34`
- 交接记录 commit（C3）：（提交后填入）
- 回退 commit：`c1694e3`（删除本轮新增文件并 `git reset --hard c1694e3` 即可回退；冻结源码 commit 167594e 本身也是安全的回退点）

## 1. 改动文件（相对 c1694e3，见 changed_files.txt）

新增：`LICENSE`、`README.md`、`SECURITY.md`、`scripts/verify_release.py`、
`scripts/verify_review_pack.py`、`release/`（source.zip、wheel、wheelhouse/ 37 个 wheel、
SHA256SUMS.txt、RELEASE_MANIFEST.json、SBOM_LICENSES.md）、`review/`（REVIEW_INDEX.md、
REVIEW_PACK_T014.md、REVIEW_FINDINGS_T012.md、REVIEW_INDEX_T012.md）、
`task_handoffs/T014/pkg/`（本文件及全部证据日志）。
未修改：`src/`、`tests/`、`schemas/`、fixture PNG、`tests/fixtures/s0/manifest.json`、
S0 门槛、输入输出契约、`tool_version`（仍 0.1.0）、`requirements.lock`、`pyproject.toml`、
`PROJECT_BOOK.md`、`IMPLEMENTATION_PLAN.md`、两份 `.docx`（见 §5 未解决项 U-02）。

## 2. 逐项交付

### R-13 — LICENSE / README.md / SECURITY.md（全部新增，锚定 commit 内）

- `LICENSE`：MIT 全文；版权行 `Copyright (c) 2026 TextProof Contributors`。
  依据：PROJECT_BOOK.md §10.1/§11.3 只规定“自有代码采用 MIT”，未指定持有人写法；
  按任务指令采用项目名 + Contributors，不编造个人姓名或邮箱。
- `README.md`：项目简介；**最前写明全新检出先跑 `scripts/setup_dictionary.py` 再跑测试**；
  安装（源码 checkout 与离线 wheelhouse 两条路线）；CLI/API/UI 快速上手；版本身份说明
  （tool 0.1.0 / package 1.0.0 / spec 1.0.0 三维度，只解释、不“修复”）；
  离线-only 声明；许可与第三方声明指引（THIRD_PARTY_NOTICES.md）；安全指引（SECURITY.md）；
  另含“已知限制”一节，如实记录 U-01（已安装 wheel 的 check/serve/verify-s0 限制与变通办法）。
- `SECURITY.md`：报告渠道为仓库 GitHub Security Advisory（未编造任何邮箱地址）；
  支持范围（当前 release + main；仅自有代码）；不收集用户数据/不联网的声明与 §9 一致。

### T014 打包（IMPLEMENTATION_PLAN.md §T014 验收 1–9）

| 验收 | 结果 |
|---|---|
| 1. source.zip 与冻结 commit 逐文件一致 | PASS：596 文件，文件名集合 + 逐文件 SHA-256 全部一致（`verify_release.py` 核对 `git archive 167594e`） |
| 2. wheel 可安装；离线 wheelhouse 安装和运行 | 安装 PASS（全新 venv、`--no-index`，exit 0，37 包）；运行 **FAIL（U-01，阻断）**：`check` exit 5、`serve` 启动崩溃；`--help`/`version` 正常 |
| 3. 模型/字典/字体/依赖有来源、版本、SHA-256、许可记录 | PASS：THIRD_PARTY_NOTICES.md（模型/字典/字体）+ `release/SBOM_LICENSES.md`（37 依赖逐项；1 项元数据无许可声明，见 U-03） |
| 4. 300 fixture、manifest、盲测清单、S0 报告在交付物中 | PASS：均在 source.zip（锚定 commit 树）与 review 交付物中 |
| 5. SHA256SUMS.txt 覆盖全部发布文件；独立重算一致 | PASS：39 条（source.zip + wheel + 37 wheelhouse wheel），全部重算一致 |
| 6. DOCX 与 Markdown 同步 | 结构 PASS（标题 67/40、表格 14/4、同序、无缺节、无占位符）；正文漂移 7 行（U-02，未解决，未擅自重写 docx） |
| 7. REVIEW_INDEX / REVIEW_PACK 锚定最终冻结 commit；覆盖可追踪 | PASS：索引锚定 167594e，596 文件全覆盖；`verify_review_pack.py` PASS |
| 8. verify_release.py 从干净目录运行 PASS | **FAIL（仅 U-01 一项）**：工作树与干净目录（全新 clone + 复制产物）均为 26/27 通过 |
| 9. 版本身份一致（commit、source.zip、wheel、测试日志） | PASS（U-01 除外）：commit 167594e、source.zip、wheel 1.0.0、测试日志 489 passed 均一致 |

### R-30 — verify_review_pack.py（补齐，取代 T013 的豁免记录）

`scripts/verify_review_pack.py` 已新建：按 `REVIEW_INDEX.md` 的锚定 commit（`git archive`
取数）逐行核对路径、字节数、SHA-256、行数（`wc -l` 口径），并核对覆盖完整性（含 300 张
PNG 的聚合行：字节合计 + 按路径排序的逐文件 SHA 行的 SHA-256）。实测
`python scripts/verify_review_pack.py review/REVIEW_INDEX.md` → **PASS**
（297 行；596 文件全覆盖）。T013 交接中的豁免记录就此作废。

### R-31 — 锁文件“33 个包”（已由 T013 处置，T014 独立复核）

T013 已修复（commit `7540c4f`）：`ENVIRONMENT.md` §4 现为“共 37 个包”。
T014 复核：`grep -cE '^[a-z0-9_.-]+==[0-9]' requirements.lock` = 37；
`grep -c 'sha256:'` = 753；lock SHA-256 `8726d13c…` 与 ENVIRONMENT.md 记录一致。
无文件改动。

## 3. 执行命令与退出码（全部真实跑出，见 test_commands.txt 与各日志）

| 命令 | 退出码 | 结果 |
|---|---|---|
| `python scripts/setup_dictionary.py`（主树 venv） | 0 | 字典重建；SHA `b5f2bfe2…`；18,708 行 |
| 全量 pytest（`TMPDIR=$PWD/tmp … -m pytest -q -p no:cacheprovider`） | 0 | **489 passed、0 failed**（142.19s；2 warnings） |
| `python scripts/verify_release.py --preflight` | 0 | PASS（12/12） |
| `python scripts/verify_release.py`（工作树） | 1 | 26/27；仅 U-01 冒烟 FAIL |
| `python scripts/verify_release.py --root /tmp/t014-clean`（全新 clone + 复制产物） | 1 | 26/27；仅 U-01 冒烟 FAIL |
| `python scripts/verify_review_pack.py review/REVIEW_INDEX.md` | 0 | PASS |
| wheelhouse 下载 `pip download --no-deps -r requirements.lock` | 0 | 37 个 wheel |
| 离线安装（全新 venv，`--no-index --find-links release/wheelhouse`） | 0 | 37 包全部安装 |
| `textproof --help`（已安装 wheel） | 0 | 正常 |
| `textproof version`（已安装 wheel） | 0 | tool 0.1.0 / package 1.0.0 / spec 1.0.0 / CPU-only |
| `textproof check` 冒烟（已安装 wheel，standalone） | 5 | **FAIL（U-01）**；无报告产出；两次独立运行复现 |
| `textproof serve`（已安装 wheel） | 1 | **启动崩溃（U-01）**；`RuntimeError: .../site-packages/textproof/ui does not exist` |
| 同一 check，主树源码（`PYTHONPATH=src`） | 1 | 正确：`MISMATCH` + `MISSING_CHARACTER`（对照） |
| 同一 check，已安装 wheel + `PYTHONPATH=<checkout>` | 1 | 正确：`MISMATCH`（诊断用，证明唯一故障点是校验器导入路径） |
| T010 静态门禁（新脚本在内） | 0 | 17 passed |
| 禁令串 grep（新脚本全文） | 1（零命中） | `urlopen/urlretrieve/os.system/shell=True/requests/httpx/urllib/http.client/socket` 全文零命中 |

注：首次全量 pytest 被 VM 重启打断（SIGTERM，环境事故）；重启后完整重跑通过。
最终重跑中途又遇 27 个收集错误——原因是 `tmp/wheelbuild/`（本人为构建 wheel 解压的
临时全树副本）被 pytest 收集导致 import-file mismatch；删除该临时目录后重跑通过。
属本人操作污染，非产品问题；教训已记入 §7。

## 4. 禁令遵守证明

- 未改 `src/`、`tests/`、`schemas/`、fixture PNG、manifest、S0 门槛、契约：
  `git diff c1694e3 HEAD -- src tests schemas` 为空（C1 冻结 commit 内）；`git status`
  在 C2 提交前除新增文件外无任何修改。
- `tool_version` 仍 0.1.0（`verify_release.py --preflight` 核对通过）。
- 未加 ￥→¥ 映射；未缩小隐私扫描范围、未加白名单、未用 curl 绕过。
- 字典未重新进入 git 追踪或任何公开产物：`git ls-files` 无字典路径；
  `git archive` 清单与 `source.zip` 清单中字典路径零命中；wheel 23 条目零命中；
  wheelhouse 文件名零命中（`verify_release.py` 逐项核对通过）。
- 新脚本禁用串全文 grep 零命中（见 §3 末行；注：禁令串列表本身以片段拼接方式
  写在 `verify_release.py` 内，避免字面串出现在文件里）。
- 未编造联系方式、测试数据或截图；全部证据为真实运行输出（原始日志均在
  `task_handoffs/T014/pkg/` 内）。

## 5. 未完成项 / 未解决项

| ID | 级别 | 内容 |
|---|---|---|
| U-01 | **阻断** | 已安装 wheel 无法 standalone 运行 `check`（exit 5）与 `serve`（启动崩溃）；`verify-s0` 同根。根因：`cli.py` `_validate_report` 与 `REPO_ROOT` 的仓库布局假设（`scripts/` 未打包）；`app.py:94` 挂载的 `ui/` 未打包进 wheel（无 package-data 配置）；API check 还需安装位置的 `assets/ocr`。修复需源码改动 + wheel 内容决策，属 T013 修复轮次（计划 T014：“如发现代码问题回到 T013”）。T014 不擅自以打包变通掩盖（见 REVIEW_PACK §3 第 5 点）。`verify_release.py` 因此为 FAIL；终审不得在 U-01 解决前通过。 |
| U-02 | 非阻断 | DOCX 正文漂移：`PROJECT_BOOK.md` 7 处 T013 文字澄清未进 DOCX（结构同步：标题 67/40、表格 14/4、同序、无缺节、无占位符；`IMPLEMENTATION_PLAN.md` 零漂移）。由规格方决定是否重生成 DOCX。 |
| U-03 | 非阻断 | `omegaconf` 2.4.0 在已安装发行版元数据中无许可声明（SBOM 如实标注，未推断）。 |

## 6. 风险

- U-01 之外最大的残余风险是“wheel 从未被安装运行过”这一事实本身：全部 489 项测试
  均在源码树内运行；T014 的离线冒烟是第一次执行安装后路径。除 U-01 外未再发现
  安装后问题（`--help`/`version` 正常；诊断运行证明 OCR 核心正常），但 `serve` 的
  API/UI 路径在安装后未做端到端验证（服务无法启动，故无从验证）——修复轮次重跑冒烟时应补。
- VM 约每 2 小时重启：长步骤（pytest、wheelhouse 下载、离线安装）须分段落盘；
  本轮两次被重启打断（一次 pytest、一次无影响的后台任务），均已重跑。
- `tmp/` 下的全树副本会被 pytest 收集：构建 wheel 的解压目录不得留在 `tmp/` 内
  （已删除；后人注意）。

## 7. 经验（供后续任务）

- `git archive` 构建 source.zip 前，先确认锚定 commit 已包含全部冻结文件；
  每 amend 一次冻结 commit 就要重生成索引 + source.zip + 清单（本轮共 amend 三次，
  每次都重生成并重跑了两项验证脚本）。
- 新脚本若内含禁令串列表，必须用片段拼接写法，否则列表本身会触发 T010 静态门禁；
  而 T010 的 token 列表本身绝不能拼写进新脚本（字面量即命中）——T014 因此不在
  `verify_release.py` 内复现 T010 门禁，只复用其已提交的 pytest 证据。
- wheel 构建用 `python -m build --wheel --no-isolation`（主树 venv 自带 setuptools；
  全新 venv 无 setuptools，`--no-build-isolation` 在全新 venv 内失败）。
- `pip download -r requirements.lock` 会严格按锁文件版本与哈希下载；37 个 wheel
  共约 145MB，`TMPDIR` 与 `PIP_CACHE_DIR` 须指向工作区内持久目录。

## 8. 证据文件（task_handoffs/T014/pkg/）

- `TASK_RESULT.md`（本文件）、`changed_files.txt`、`test_commands.txt`、
  `test_stdout.log`、`test_stderr.log`、`exit_codes.txt`
- `verify_release.log`（工作树全量运行）、`verify_release_clean_dir.log`（干净目录运行）
- `offline_install.log`、`offline_smoke.txt`、`smoke_help.log`、`smoke_help2.log`、
  `smoke_version.json`、`smoke_version.err`、`smoke_check.log`、
  `smoke_check_standalone.log`、`standalone_check_exit.txt`、
  `smoke_check_wpp.log`、`smoke_report_wpp.json`（诊断：PYTHONPATH 变通）、
  `smoke_check_repo.log`、`smoke_report_repo.json`（对照：主树源码）、
  `smoke_serve.log`、`smoke_serve2.log`、`smoke_api_check.json`、`smoke_api_err.log`、
  `editable_install.log`（可编辑安装失败：全新 venv 无 setuptools，仅作记录）
