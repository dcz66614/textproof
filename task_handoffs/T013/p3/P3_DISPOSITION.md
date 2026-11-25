# T013-FIX-06 — P3 批量处置记录（R-12…R-31；另 R-03 / R-13 / R-30 归属）

- 任务：T013-FIX-06（P3 批量）
- 基线：冻结候选 commit `ffe53ea`（分支 `t011-full-regression`）
- 工作分支：`t013-p3`（worktree `~/workspace/p033-textproof-t013-p3`）
- 审查来源：`~/workspace/p033-textproof-t011/review/REVIEW_FINDINGS.md`（T012 独立审查，2026-11-25）
- 处置原则：每项或修复或书面记录为非阻断并说明影响；无任何一项静默丢弃。
- 改动范围：仅 `PROJECT_BOOK.md`（文字澄清）、`THIRD_PARTY_NOTICES.md`（R-12）、`ENVIRONMENT.md`（R-31 数字）及本文件。未改任何 `.py` 文件、测试预期、fixture PNG、manifest、S0 门槛、输入输出契约、`tool_version`。
- §3 三条“非 finding”均未“修复”：`tool_version` 0.1.0 不是不一致、￥ 不映射正确、UI 数值写法 `393.0` vs `393` 不是分歧。

## 逐项处置

### R-12 — 已修复（THIRD_PARTY_NOTICES.md）

- 把 `tests/fixtures/s0/fonts/FONT_NOTICE.md` 的记录汇总进 `THIRD_PARTY_NOTICES.md` §6 新增小节“Fixture font — Noto Sans SC (T005, recorded here for completeness)”：版本 2.004-H2、SHA-256 `a3041811a78c361b1de50f953c805e0244951c21c5bd412f7232ef0d899af0da`、OFL-1.1、OFL.txt SHA-256 `1c05c68c34f9708415aada51f17e1b0092d2cea709bf4a94cd38114f9e73d7d9`、来源 URL、文件字节数 17,772,300、命名实例 Regular（wght 400）、仅用于渲染合成 S0 测试图、生成器每次运行校验哈希与字节数。
- 口径已写明：字体属 T005 交付物，不在该文件原自述的 T003 范围内；汇总于此是为使 §10.2 字体记录（OFL、来源、版本、哈希）在一处完整，权威记录仍为 `tests/fixtures/s0/fonts/FONT_NOTICE.md`；T014 在公开前复核。
- 另已具名 `tests/integration/test_ocr_adapter.py:38–39` 用的系统字体：Noto Sans CJK SC（`/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`）与 DejaVu Sans（`/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`），仅测试时渲染、从不随产品分发。
- 核对：两处 SHA-256 已在 worktree 内用 `sha256sum` 实测，与 FONT_NOTICE.md 一致。

### R-14 — 已修复（PROJECT_BOOK.md §5.5，仅加文字；退出码未改）

- 在 §5.5 退出码表后加注：`textproof verify-s0` 的退出码另有独立契约——0 表示 S0 门禁通过，1 表示 S0 门禁失败（原样透传 `scripts/verify_s0.py` 的通过 / 失败结果）；该 0/1 与上表 `check` 的退出码含义（0 = `MATCH`、1 = `MISMATCH`）无关，不得按上表解读 `verify-s0` 的退出码。
- 未改任何退出码（`verify_s0.py` 与 `cli.py` 均未动）。

### R-16 — 非阻断（记录；未改代码）

- API `GET /api/v1/version` 不含 `package_version`，而 CLI `version` 含之。两者均符合各自的文档形状（API_CONTRACT.md §2 的 version 示例本就不含 `package_version`），不是违规；仅为同一产品的两个版本端点字段集不对称，消费者横向比对时会缺一字段。
- 未改 `src/textproof/api/routes.py`（该文件属 R-04，不归本任务）。

### R-17 — 非阻断（记录；未改代码）

- `scripts/independent_verify.py`、`compute_s0_metrics.py`、`parity_check.py`、`verify_s0.py`、`benchmark_perf.py` 把 fixture 文本打印到 stdout。全部是已提交的合成 fixture 文本、走 stdout 证据通道，非产品运行时日志；与 R-08 同属“验证脚本不受产品日志口径约束但字面冲突”的模式。
- 影响：无用户数据外泄；若日后任一脚本被复用于真实用户图片，应先去除文本打印。

### R-18 — 非阻断（记录；未改代码）

- 证据输出含本机绝对路径与主机名（`benchmark_perf.py` 的模型绝对路径、`env_probe.py` 的 `disk_path` / `python_executable` / `hostname`、`verify_s0.py` 打印的绝对 `out_dir`）。内容是环境元数据、非用户内容；但与 §9“日志不得记录绝对路径”的字面口径有张力（产品日志口径 vs 证据报告）。
- 影响：无用户数据外泄；如需收紧，可在 summary 中把模型路径记为相对路径或只记文件名 + SHA-256。

### R-19 — 非阻断（记录；未改代码）

- 网络拦截仪器有 UDP 覆盖缺口：`SocketRecorder` 只拦截 `connect` / `connect_ex` / `getaddrinfo`，不拦截 `sendto` / `sendmsg`；strace 只 trace `openat,connect`。但全树 grep `sendto|sendmsg|recvfrom|SOCK_DGRAM|datagram` 为 0 命中，且 `src/` 内唯一 socket 使用在 R-02 的脚本中，因此残余风险只是仪器缺口，不是已发现的通道。
- 另 `_is_loopback_host` 把 `""`、`None`、`"localhost"` 判为回环放行，与产品 `validate_bind_host` 的严格精确比对口径不同，但这是测试仪器的分类器，不是产品行为。

### R-20 — 非阻断（记录；未改代码）

- 文件快照监视范围有边界：`take_snapshot` 只扫 `src`、`tests`、`assets`、`scripts`、`schemas`（另加 `TMPDIR`），不能证明 `task_handoffs/`、`tmp/`、`~/.cache` 等位置无写入；`test_check_writes_no_files` 的结论以其监视范围为限（ORT 遥测 outbox 由独立测试覆盖，不在此项内）。
- `__pycache__` / `*.pyc` 遍布全树 16 个目录，是解释器产物，测试明确排除，不含用户数据。

### R-21 — 非阻断（记录；未改代码）

- Chrome profile 临时目录清理不可靠，有残留：`tmp/` 下实测残留 `tmp/textproof-chrome-fvtgk8vn/`（无 Chrome 进程在跑），其内仅有一个锁文件，无浏览数据；另有 `tmp/org.chromium.Chromium.*` 单例目录残留。`shutil.rmtree(..., ignore_errors=True)` 使清理失败静默。
- 影响：残留物不含用户数据；如需收紧，可在 `stop()` 后断言 profile 目录已消失。

### R-22 — 非阻断（记录；未改代码）

- `sys.path.insert(0, REPO_ROOT)` 的标准库遮蔽 footgun：`src/textproof/cli.py:86–88`（产品运行时，每次 `check` 的 `_validate_report` 都执行）及多份脚本与 `tests/conftest.py` 均把仓库根目录插到 `sys.path` 首位。当前根目录无与标准库同名文件，故无实际遮蔽，仅为纵深防御备注；若日后根目录出现 `json.py` 之类文件会被优先导入。

### R-23 — 已修复（PROJECT_BOOK.md §7.2，仅加文字；不改代码）

- 在 §7.2 补一句：“歧义按不同配对集合计：仅当存在代价差小于 `0.05` 的另一组不同配对集合时才判歧义；同一配对集合内 gap 顺序不同（先缺失后额外与先额外后缺失）不计为不同对齐。”
- 实现已有穷举测试背书（`tests/unit/test_core/test_align_lines.py:155–194` 按配对集合比较），本改动只把该解释冻结成文。

### R-24 — 已修复（PROJECT_BOOK.md §4.5，仅改文字；冻结现有 6 对；不改代码）

- 把混淆对的“如”改为“即以下集合”，并完整列出冻结的 6 对：`O/0`、`I/1`、`I/l`、`1/l`、`S/5`、`B/8`（与 `src/textproof/core/weighted_edit.py:95–107` 的 `CONFUSION_PAIRS` 逐对一致；原表述 `I/1/l` 为三对 `I/1`、`I/l`、`1/l` 的简写，现展开写明）。
- 未冻结更大的集合；`o/0`、`D/0`、`Z/2` 等未列出的视觉混淆对仍按 1.00 计费。

### R-25 — 已修复（PROJECT_BOOK.md §5.3，仅加文字；未发明检测器）

- 在 §5.3 警告枚举后注明：`POSSIBLE_MULTI_COLUMN` 与 `ROTATED_TEXT_NOT_SUPPORTED` 为保留码，本版本无对应检测器、从不发出；触发条件未冻结，待检测规则冻结后再实现，不得凭空发明检测器。

### R-26 — 已修复（PROJECT_BOOK.md §7.6，仅加文字；实现已是如此，不改代码）

- 把 §7.6 原句“OCR 无可用文本时为 `OCR_FAILED` 或 `REVIEW_REQUIRED`，具体按引擎失败 / 空识别区分”改为冻结映射：引擎异常 → `OCR_FAILED`；空识别（引擎正常返回但无可用文本）→ `OCR_FAILED` 并附 `OCR_EMPTY` 警告；空识别不判 `REVIEW_REQUIRED`。

### R-27 — 已修复（PROJECT_BOOK.md §7.2，仅加文字；不改输出顺序，不改两处锁定测试）

- 在 §7.2 末补一句：“错误按对齐顺序编号（`E001`、`E002`、……）；同一 gap 连续段内错误的顺序以回溯实现为准（当前实现为先额外行、后缺失行），不保证按直觉的先缺失后额外顺序。”
- 两处锁定测试（`tests/unit/test_core/test_align_lines.py:71–80`、`tests/unit/test_core/test_report.py:253–260`）未动。

### R-28 — 已修复（PROJECT_BOOK.md §4.2，仅加文字；不改代码）

- 在 §4.2“期望文本最多 5,000 Unicode 码点、最多 100 行”后注明：行数按统一换行后以 `\n` 切分计数，尾随换行计入行数（即 `"a\n"` 计 2 行）；100 行文本加一个尾随换行计 101 行，予以拒绝。

### R-29 — 已修复（PROJECT_BOOK.md §4.4，仅加文字；不改代码）

- 在 §4.4 行聚合句后冻结口径：新文本框只与当前最后一行的纵向区间比较重叠（重叠条件为 `y1 <= hi and y2 >= lo`），重叠则并入该行并取区间并集，否则开新行；允许链式并入（区间可通过逐个重叠的文本框依次延伸）。

### R-31 — 已修复（ENVIRONMENT.md §4，仅改数字）

- “共 33 个包”改为“共 37 个包”（实测：`grep -cE '^[a-z0-9_.-]+==[0-9]' requirements.lock` = 37；`grep -c 'sha256:'` = 753；lock SHA-256 `8726d13c…` 不变，与 ENVIRONMENT.md 记录一致）。

## 不由本任务修复的归属（R-03 / R-13 / R-30）

### R-03 — 归属 T014 发布打包（字典许可 UNVERIFIED）

- 字典 `ppocrv6_dict.txt` 内容已核实（SHA `b5f2bfe2…` 三方一致），但许可仍为 UNVERIFIED（`THIRD_PARTY_NOTICES.md` §4）。按 PROJECT_BOOK.md §10.2 与 T003 验收标准 7，在许可解决前不得把字典作为单独文件随公开版本再分发。
- 截止点：公开再分发前，T014 必须复核字典许可并更新 `THIRD_PARTY_NOTICES.md` §4。本任务不作任何许可断言。

### R-13 — 归属 T014 发布打包（LICENSE / README.md / SECURITY.md 缺失）

- `LICENSE`、`README.md`、`SECURITY.md` 在冻结候选内均不存在；`THIRD_PARTY_NOTICES.md:3` 首句“TextProof's own source code is MIT (see `LICENSE`…)”当前指向不存在的文件。要求来源：PROJECT_BOOK.md §10.1、§6.3、§11.3。
- 截止点：公开前由 T014 补齐（`THIRD_PARTY_NOTICES.md:3–4` 自述亦称 `LICENSE`“to be added by T014 if not yet present”）。模型/字典资产清单与依赖清单（`SHA256SUMS.txt`、`requirements.lock`）齐全，不阻塞 T013。

### R-30 — verify_review_pack.py 豁免；verify_release.py 与 release/ 属 T014

- `scripts/verify_review_pack.py`：豁免。T012 已以新建的 `review/REVIEW_INDEX.md`（格式按 IMPLEMENTATION_PLAN.md §13/§14 要求：每文件路径、字节数、SHA-256、行数、读取状态）作为覆盖证据替代；本任务不再新建该脚本。
- `scripts/verify_release.py` 与 `release/` 目录：属 T014。按 IMPLEMENTATION_PLAN.md §1，T014 以 `verify_release.py` PASS 收尾；T014 补齐二者。

## PROJECT_BOOK.md 改动位置一览

| Finding | 位置 | 改动 |
|---|---|---|
| R-14 | §5.5，退出码表后新增注（:340） | `verify-s0` 的 0/1 通过/失败契约与 §5.5 的 `check` 退出码表无关 |
| R-23 | §7.2，歧义判定句后（:455） | 歧义按不同配对集合计，gap 顺序不同不计为不同对齐 |
| R-24 | §4.5，代价表混淆对行（:211） | “如”改为“即以下集合”，展开列出冻结的 6 对 |
| R-25 | §5.3，警告枚举句后（:253） | `POSSIBLE_MULTI_COLUMN` 与 `ROTATED_TEXT_NOT_SUPPORTED` 为保留码、暂无检测器 |
| R-26 | §7.6，末句（:484） | 冻结映射：引擎异常 → `OCR_FAILED`；空识别 → `OCR_FAILED` 并附 `OCR_EMPTY` |
| R-27 | §7.2，末尾新增段（:457） | 错误按对齐顺序编号、gap 段顺序以回溯实现为准 |
| R-28 | §4.2，行数上限句后（:177） | 尾随换行计入 100 行（即 `"a\n"` 计 2 行） |
| R-29 | §4.4，行聚合句后（:197） | 冻结行聚合口径（与最后一行区间比较、允许链式并入） |

其他文件改动位置：

| Finding | 文件 | 位置 |
|---|---|---|
| R-12 | THIRD_PARTY_NOTICES.md | §6：系统字体具名（:137–141）；新增小节“Fixture font — Noto Sans SC”（:143–166），含版本 / SHA / OFL-1.1 / OFL.txt SHA 与 T005 口径说明 |
| R-31 | ENVIRONMENT.md | §4 标题（:55）：“共 33 个包”→“共 37 个包” |

## 验证

- 改动处与 REVIEW_FINDINGS.md 逐字核对：字体版本 / SHA、6 对混淆对集合、37 包 / 753 哈希、lock SHA 均与审查报告及实测一致。
- 全量 pytest（`TMPDIR=$PWD/tmp ~/workspace/p033-textproof/.venv/bin/python -m pytest -q -p no:cacheprovider`，worktree 内运行，耗时 701.70s）：**2 failed, 436 passed, 2 warnings**——与 T012 协调员在冻结候选上的重跑（2 failed, 436 passed, 226.79s）完全一致。两项失败均为已知的 R-02（`tests/privacy/test_no_persistence.py`：`test_forbidden_token_absent_from_sources[urlopen]` 与 `test_no_network_client_import_in_sources`，源头 `scripts/consistency_check.py` 的 `urlopen`/`socket`/`urllib` import），属基线已有问题，不由本任务修复（R-02 归其他 T013 修复员：脚本移入 `tests/`）。本任务只改文档，未引入任何新失败；436 项通过与基线相同。注：本次耗时 701.70s 明显长于 T012 重跑的 226.79s，系 VM 共享 CPU/内存紧张所致，非测试内容变化。
