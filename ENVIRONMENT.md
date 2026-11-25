# ENVIRONMENT.md — P033 TextProof 施工环境（T001 探测结果）

> 探测时间：2026-11-25 ~02:00 GMT（UTC）。探测工具：`scripts/env_probe.py`
> （`python3 scripts/env_probe.py` / `--json`）。本文件由 T001 生成并冻结为基线；
> 后续任务如在不同机器上施工，必须重新探测并更新本文件，不得沿用此处数值。

## 1. 操作系统与硬件

| 项目 | 值 |
|---|---|
| OS | Linux-7.0.0-44-generic-x86_64-with-glibc2.39 |
| 内核 | Linux 7.0.0-44-generic #1 SMP PREEMPT_DYNAMIC Fri Nov 6 01:23:31 UTC 2026 |
| 架构 | x86_64 |
| CPU 型号 | AMD EPYC 9D25 126-Core Processor（云端 VM 只分配 4 个逻辑核） |
| CPU 逻辑核数 | 4 |
| 内存总量 | 7.75 GiB（8,319,897,600 字节；`/proc/meminfo` MemTotal 8,124,900 KiB） |
| 磁盘（`/home/hatch` 所在卷） | 总计 149.98 GiB，已用 ~32 GiB，**可用 119.24 GiB**（探测时） |
| 主机名 | htch-runtime |
| 工作目录 | `/home/hatch/workspace/p033-textproof` |

> 注意：VM 内存总量 7.75 GiB，但探测时可用内存仅约 849 MiB（其余被运行环境占用），
> 且 VM 约每 2 小时重启一次。重型步骤（pip 安装、OCR 运行）应分段执行、及时落盘。

## 2. 工具链版本

| 工具 | 版本 | 备注 |
|---|---|---|
| Python（系统） | 3.12.3（`/usr/bin/python3`，CPython） | 满足 §6.2 的 Python 3.12.x |
| pip（系统） | 24.0 | 仅用于创建 venv；venv 内已升级到 26.3 |
| pip（`.venv` 内） | 26.3 | 由 T001 在 venv 内升级 |
| Git | 2.43.0 | |
| 虚拟环境 | `.venv`（构建）与 `.venv-verify`（全新验证），均为 Python 3.12.3 | 见 §3 |

## 3. 虚拟环境

```bash
# 构建环境（T001 使用，含 pip-tools，仅用于生成锁文件）
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip "pip-tools>=7.4"

# 锁文件生成（带哈希）
.venv/bin/pip-compile --generate-hashes \
    --output-file=requirements.lock --strip-extras pyproject.toml

# 全新环境验证（与构建环境隔离）
python3 -m venv .venv-verify
.venv-verify/bin/python -m pip install --require-hashes -r requirements.lock
```

pip 操作的临时目录与缓存均指向工作目录下的持久位置
（`TMPDIR=$PWD/.tmp`，`PIP_CACHE_DIR=$PWD/.tmp/pip-cache`），
不用 `/tmp`（512 MiB tmpfs，VM 重启即清空）。`.venv/`、`.venv-verify/`、
`.tmp/` 由 `.gitignore` 排除，不进 git。

## 4. 锁定的依赖（`requirements.lock`，共 37 个包，全部带精确版本与哈希）

直接依赖（`pyproject.toml` 声明）：

| 包 | 锁定版本 | 说明 |
|---|---|---|
| `rapidocr` | **3.10.0** | 冻结版本（PROJECT_BOOK.md §6.2 精确要求） |
| `onnxruntime` | 1.32.0 | **CPU 版**；锁文件中无 `onnxruntime-gpu` |
| `Pillow` | 11.3.0 | 图片解码 / EXIF / 校验 |
| `fastapi` | 0.165.0 | 本机 API |
| `uvicorn` | 0.54.0 | API 服务器（不含 `standard` extras） |
| `pydantic` | 2.14.4 | API 请求 / 响应模型 |
| `pytest` | 8.4.2 | 单元 / 集成 / S0 测试 |

传递依赖（由 pip-compile 解析，节选）：numpy 2.5.5、opencv-python-headless 5.1.0.95、
shapely 2.2.0、pyclipper 1.4.0、omegaconf 2.4.0、starlette 1.10.0、anyio 4.16.0、
requests 2.34.2。完整清单见 `requirements.lock`（858 行，753 个 SHA-256 哈希条目）。

锁文件 SHA-256：`8726d13cb20bb731b491a4119629c176b699f035b75d8547d853ca3585d1564d`

## 5. 与 PROJECT_BOOK.md §6.2 的一致性说明

- Python 3.12.x：一致（3.12.3）。
- RapidOCR 3.10.0：一致，但**包名有重要澄清**——见 `T001_RESULT.md` §3：
  3.10.0 属于当前包 `rapidocr`（PyPI 最新版即 3.10.0，2026-10-08 发布）；
  旧包 `rapidocr-onnxruntime` 最高只有 1.4.4，不存在 3.10.0。T001 按 `rapidocr==3.10.0`
  锁定，并显式安装 `onnxruntime` CPU 推理引擎（`rapidocr` 本身不声明 onnxruntime 依赖）。
- ONNX Runtime CPU 版：一致。`onnxruntime==1.32.0`，`ort.get_device() == "CPU"`；
  锁文件中无 `onnxruntime-gpu`，可用 provider 列表中无任何 CUDA / TensorRT / GPU provider。
  （注：标准 CPU wheel 的 provider 注册表里除 `CPUExecutionProvider` 外还列出
  `AzureExecutionProvider`，这是该 wheel 的内置注册项，不是 GPU provider，也不会被
  默认使用；T003 在创建 InferenceSession 时仍须显式限定 `CPUExecutionProvider`。）
- Pillow / FastAPI / Uvicorn / Pydantic / pytest：均锁定兼容版本（见 §4），无偏差。
- 锁文件可重建：重新运行 pip-compile 得到的锁文件与提交版逐字节一致，
  仅文件头自指的命令输出文件名不同（见 `T001_RESULT.md` §4）。

## 6. 已知限制

- 本机在 T001 时段 pip 可访问 PyPI；运行时的离线要求（不访问 PyPI / ModelScope /
  Hugging Face）由 T003（模型资产本地化）与 T010（离线测试）负责，不属于 T001。
- RapidOCR 模型文件的下载与本地化属于 T003；T001 只验证依赖可安装、可导入、
  ONNX Runtime 为 CPU 版，未实例化 `RapidOCR()`、未触发任何模型下载。
- `pip check` 在全新验证环境中报告 "No broken requirements found."。

## 7. T014/R-03 补充：识别字典须本地重建（2026-11-25）

- 识别字典 `assets/ocr/dictionaries/ppocrv6_dict.txt` 许可仍为 UNVERIFIED
  （见 `THIRD_PARTY_NOTICES.md` §4 与
  `task_handoffs/T014/r03/LICENSE_VERIFICATION_R03.md`），自 T014/R-03
  提交起不再进入 git 树与公开快照。
- 全新检出后、跑测试前，必须先重建字典（本地操作，不联网）：

```bash
.venv/bin/python scripts/setup_dictionary.py
```

- 脚本从本机已随包分发的 `PP-OCRv6_rec_small.onnx` 内嵌 `character`
  元数据提取字符表，校验 SHA-256 `b5f2bfe2…` 与 18,708 行后写出；
  重建产物与冻结文件逐字节一致。未重建时
  `test_model_assets_present_locally` 等断言字典存在的测试会失败，
  属预期的顺序依赖，不得为此改测试。
