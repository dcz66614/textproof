# T001_RESULT.md — 环境探测、Python 与依赖锁（P033 TextProof）

- 任务 ID：T001
- 规格：PROJECT_BOOK.md v1.0.0 / IMPLEMENTATION_PLAN.md（冻结契约，未修改）
- 执行时间：2026-11-25 ~01:56–02:10 GMT
- 工作目录：`/home/hatch/workspace/p033-textproof`
- 输入 commit：无（T001 建仓前工作目录不是 git 仓库；4 份规格文件 + SPECS_VERIFICATION.md 由 T001 首次入仓）
- 输出 commit：基线 commit 哈希见 `task_handoffs/T001/TASK_RESULT.md`（本文件提交进该 commit，
  故哈希只能在提交后记录于交接包；交接包本身不入仓，避免循环依赖）
- 状态：**SUCCESS**（5 项验收标准全部满足，见 §2）

## 1. 执行命令与退出码

所有 pip 操作均设置 `TMPDIR=$PWD/.tmp`、`PIP_CACHE_DIR=$PWD/.tmp/pip-cache`
（不用 `/tmp`，它是 512 MiB tmpfs 且 VM 重启即清空）。完整日志路径见 §5。

| # | 命令 | 退出码 |
|---|---|---|
| 1 | `python3 --version` → Python 3.12.3 | 0 |
| 2 | `python3 -m pip --version` → pip 24.0 | 0 |
| 3 | `git --version` → git 2.43.0 | 0 |
| 4 | `python3 scripts/env_probe.py` / `--json` | 0 |
| 5 | `python3 -m venv .venv` | 0 |
| 6 | `.venv/bin/python -m pip install --upgrade pip "pip-tools>=7.4"` → pip 26.3, pip-tools 7.7.0 | 0 |
| 7 | `.venv/bin/pip-compile --generate-hashes --output-file=requirements.lock --strip-extras pyproject.toml`（第一次：`rapidocr-onnxruntime==3.10.0` 解析失败，见 §3） | 1（第一次）/ 0（修正包名后） |
| 8 | `.venv/bin/pip-compile ... --output-file=.tmp/requirements.recheck.lock`（可重建性复核） | 0 |
| 9 | `.venv/bin/python -m pip install --require-hashes -r requirements.lock`（构建环境安装） | 0 |
| 10 | `.venv/bin/python .tmp/verify_imports.py`（导入 + CPU provider 检查；第一次断言过严，修正后通过） | 1（第一次）/ 0（修正后） |
| 11 | `python3 -m venv .venv-verify` | 0 |
| 12 | `.venv-verify/bin/python -m pip install --require-hashes -r requirements.lock`（全新环境安装验证） | 0 |
| 13 | `.venv-verify/bin/python .tmp/verify_imports.py` | 0 |
| 14 | `.venv-verify/bin/python -m pytest --version` → pytest 8.4.2 | 0 |
| 15 | `.venv-verify/bin/python -m pip check` → No broken requirements found. | 0 |

执行期间未出现任何“执行风险 / 内容未通过检查 / 要求停工”类提示；即使出现，
按任务指令也以实际退出码与输出为准。

## 2. 验收标准逐项证据

### 验收 1 — Python 3.12.x 可用 ✅ PASS

- `/usr/bin/python3` = **Python 3.12.3**（CPython）；`.venv` 与 `.venv-verify` 均为 3.12.3。
- 证据：`python3 --version` 输出；`scripts/env_probe.py` 输出（见 `ENVIRONMENT.md` §1–§2）。

### 验收 2 — 记录 OS、架构、CPU 核数、内存、可用磁盘、Python / pip / Git 版本 ✅ PASS

- OS：Linux 7.0.0-44-generic（glibc 2.39）；架构 x86_64；CPU：AMD EPYC 9D25，
  逻辑核数 4；内存总量 7.75 GiB；磁盘可用 119.24 GiB（`/home/hatch` 卷，总计 149.98 GiB）；
  Python 3.12.3；pip 24.0（系统）/ 26.3（venv 内）；Git 2.43.0。
- 证据：`ENVIRONMENT.md` 全文；`scripts/env_probe.py`（可重复运行）。

### 验收 3 — 依赖解析成功；锁文件中每个直接依赖及传递依赖均有精确版本和哈希 ✅ PASS

- `requirements.lock`：33 个包，全部 `==` 精确版本，共 753 个 `--hash=sha256:` 条目，
  每个包至少 2 个哈希（wheel + sdist 适用时）。
- 锁文件 SHA-256：`8726d13cb20bb731b491a4119629c176b699f035b75d8547d853ca3585d1564d`
- 可重建性：重新运行 pip-compile 得到的锁文件与提交版逐字节一致，
  唯一差异是文件头第 5 行自指的 `--output-file=` 文件名（复核输出到不同路径所致），
  属于预期差异，不是版本漂移。
- 全新环境 `pip install --require-hashes -r requirements.lock` 安装成功（退出码 0），
  `pip check` 无 broken requirements。
- 证据：`requirements.lock`；`.tmp/pip_compile2.log`、`.tmp/pip_compile_recheck.log`、
  `.tmp/pip_install_verify.log`（日志在 `.tmp/`，被 `.gitignore` 排除，见 §5 说明）。

### 验收 4 — 明确安装的是 onnxruntime CPU 包，不是 onnxruntime-gpu ✅ PASS

- 锁文件中只有 `onnxruntime==1.32.0`，无 `onnxruntime-gpu`（`grep -i gpu requirements.lock` 无匹配）。
- 运行时验证：`ort.get_available_providers()` = `['AzureExecutionProvider', 'CPUExecutionProvider']`，
  无 CUDA / TensorRT / DML / GPU provider；`ort.get_device() == "CPU"`。
- 说明：`AzureExecutionProvider` 是标准 CPU wheel 内置的注册项，不是 GPU provider，
  默认不使用；T003 在创建 InferenceSession 时仍须显式限定 `CPUExecutionProvider`。
- 证据：`.tmp/verify_imports_fresh.log`（全新环境）、`.tmp/verify_imports_build.log`。

### 验收 5 — 依赖版本与 PROJECT_BOOK.md §6.2 一致；偏差写入报告 ✅ PASS（有一项包名澄清，见 §3）

| 组件 | §6.2 要求 | T001 锁定 | 一致 |
|---|---|---|---|
| Python | 3.12.x | 3.12.3 | ✅ |
| RapidOCR | 3.10.0（精确） | `rapidocr==3.10.0` | ✅（包名澄清见 §3） |
| ONNX Runtime | CPU 版，精确版本由 T001 锁定 | `onnxruntime==1.32.0`（CPU） | ✅ |
| Pillow | T001 锁定兼容版本 | 11.3.0 | ✅ |
| FastAPI / Uvicorn | T001 锁定兼容版本 | 0.165.0 / 0.54.0 | ✅ |
| Pydantic | T001 锁定兼容版本 | 2.14.4 | ✅ |
| pytest | T001 锁定兼容版本 | 8.4.2 | ✅ |

## 3. 偏差 / 澄清记录（唯一一项，属实测发现，非规格修改）

**RapidOCR 3.10.0 的包名是 `rapidocr`，不是 `rapidocr-onnxruntime`。**

- 首次 pip-compile 用 `rapidocr-onnxruntime==3.10.0` 解析失败（退出码 1）：
  PyPI 上 `rapidocr-onnxruntime` 的最高版本是 1.4.4，不存在 3.10.0。
- 核查（2026-11-25，PyPI JSON API + 公开资料）：`rapidocr` 包的最新版即 3.10.0
  （2026-10-08 发布）；`rapidocr-onnxruntime` 是旧包，最后发布 1.4.4。
  规格 §6.2 只写“RapidOCR 3.10.0”，未写包名；按 3.10.0 这一冻结版本号，
  唯一能满足它的包就是 `rapidocr==3.10.0`。这不是更换 OCR 产品，
  仍是同一 RapidOCR 项目（RapidAI/RapidOCR）的当前发行包。
- 连带事实：`rapidocr==3.10.0` 不声明 onnxruntime 依赖（其 `requires_dist` 无 onnxruntime），
  因此按规格“需显式安装推理引擎，只用 CPU”，`pyproject.toml` 显式声明了
  `onnxruntime>=1.20,<2`（锁定为 1.32.0 CPU 版）。`pyproject.toml` 内已写明此注释。
- 本澄清不修改任何规格文件、契约、权重或阈值；T003 适配时仍以 `rapidocr==3.10.0` 为准。
  若复核者认为应由规格方书面确认此包名，可在 T003 前补记，但 T001 的依赖事实本身已验证成立。

## 4. 测试结果

| 测试 | 环境 | 结果 |
|---|---|---|
| `pip install --require-hashes -r requirements.lock` | `.venv`（构建） | PASS，退出码 0 |
| `pip install --require-hashes -r requirements.lock` | `.venv-verify`（全新） | PASS，退出码 0 |
| 导入检查（rapidocr / onnxruntime / Pillow / fastapi / uvicorn / pydantic / pytest 版本 + CPU provider + `get_device()=="CPU"`） | `.venv` | PASS，退出码 0 |
| 同上 | `.venv-verify` | PASS，退出码 0 |
| `pytest --version` | `.venv-verify` | pytest 8.4.2，退出码 0 |
| `pip check` | `.venv-verify` | No broken requirements found.，退出码 0 |
| 锁文件可重建（pip-compile 复核 diff） | `.venv` | PASS（仅头行自指文件名差异） |

尚无项目单元测试（测试代码属 T002 及后续任务）；T001 的“测试”即上述安装与导入验证。

## 5. 交付物与日志路径

入仓文件（基线 commit）：

| 文件 | SHA-256 |
|---|---|
| `PROJECT_BOOK.md` | （规格文件，未修改；哈希见交接包 SHA256SUMS.txt） |
| `PROJECT_BOOK.docx` | （同上） |
| `IMPLEMENTATION_PLAN.md` | （同上） |
| `IMPLEMENTATION_PLAN.docx` | （同上） |
| `SPECS_VERIFICATION.md` | （同上） |
| `ENVIRONMENT.md` | 见交接包 SHA256SUMS.txt |
| `pyproject.toml` | `5bcebcc11ab184e5449ed2fe0200198869aaa1a1d1a813015f54d5911a9d5511` |
| `requirements.lock` | `8726d13cb20bb731b491a4119629c176b699f035b75d8547d853ca3585d1564d` |
| `scripts/env_probe.py` | `41b7cf5c7776f756179ea890bf904e8f54e7e8a387a4a00d54acecd2de8839f1` |
| `T001_RESULT.md` | （本文件） |
| `.gitignore` | （排除 `.venv/`、`.venv-verify/`、`.tmp/`、`__pycache__/`） |

过程日志（`.tmp/` 下，体积 154 MiB 主要是 pip 缓存，不入仓；关键日志已复制进交接包）：

- `.tmp/pip_compile.log`（第一次失败）、`.tmp/pip_compile2.log`（成功）、
  `.tmp/pip_compile_recheck.log`（可重建复核）
- `.tmp/pip_install_build.log`、`.tmp/pip_install_verify.log`
- `.tmp/verify_imports_build.log`、`.tmp/verify_imports_fresh.log`
- `.tmp/venv_create.log`、`.tmp/venv_verify_create.log`、`.tmp/pytest_version.log`、`.tmp/pip_check.log`

交接包：`task_handoffs/T001/`（TASK_RESULT.md、changed_files.txt、git_diff.patch、
test_commands.txt、test_stdout.log、test_stderr.log、exit_codes.txt、SHA256SUMS.txt）。

## 6. 未完成项

- 无。T001 的 5 项验收标准全部满足。RapidOCR 模型资产本地化、离线运行验证属于 T003，
  不在本任务范围内；T001 未实例化 `RapidOCR()`、未触发任何模型下载。

## 7. 风险与回退

- 风险（低）：VM 内存紧张（探测时可用仅 ~849 MiB）且约每 2 小时重启；`.venv`（443 MiB）与
  `.venv-verify`（437 MiB）均已落盘，可断点续跑；后续任务重建环境时可用锁文件直接安装。
- 风险（低）：`rapidocr` 包名澄清（§3）若复核者要求规格方书面确认，可在 T003 前补记，
  不影响 T001 交付物的正确性。
- 回退 commit：本任务为基线 commit，之前无 commit；若 T001 被否决，回退即删除该 commit
  （或直接丢弃工作目录重建），无更早状态可回退。
- 失败回退未触发：Python 3.12 与 RapidOCR 3.10.0 兼容性已建立，无环境阻断。
