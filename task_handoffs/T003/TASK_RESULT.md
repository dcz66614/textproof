# TASK_RESULT.md — T003 RapidOCR CPU 适配与离线模型资产（P033 TextProof）

- 任务 ID：T003
- 输入 commit：`394d507`（T001 基线，master）
- 输出 commit（代码与资产）：`48e88da758f0729ee7bdfdafd5a6617ddf1d1a7b`
- 分支：`t003-rapidocr`（worktree `~/workspace/p033-textproof-t003`）
- 交接包 commit：见父代理的 git log（本文件包含在交接包 commit 中，故其哈希只能在提交后由外部读取；代码输出 commit 如上，不受交接包 commit 影响）
- 状态：**SUCCESS — 7 项验收标准全部满足**（逐项证据见 §2）
- 执行时间：2026-11-25 ~02:06–02:25 GMT
- 工作目录：`~/workspace/p033-textproof-t003`（`git worktree`，与主工作目录 master 检出隔离）

## 1. 实际改动文件（输出 commit 48e88da）

| 文件 | 说明 |
|---|---|
| `src/textproof/ocr/rapidocr_adapter.py` | 新增：CPU-only 离线适配器 + `OCRLine`（399 行） |
| `src/textproof/ocr/__init__.py` | 新增：包声明 |
| `src/textproof/__init__.py` | 新增：包声明（1 行 docstring） |
| `assets/ocr/models/PP-OCRv6_det_small.onnx` | 新增：9,929,594 B |
| `assets/ocr/models/PP-OCRv6_rec_small.onnx` | 新增：21,234,383 B |
| `assets/ocr/models/ch_ppocr_mobile_v2.0_cls_mobile.onnx` | 新增：585,532 B |
| `assets/ocr/dictionaries/ppocrv6_dict.txt` | 新增：18,708 行，74,947 B |
| `assets/ocr/SHA256SUMS.txt` | 新增：4 条哈希 |
| `THIRD_PARTY_NOTICES.md` | 新增：RapidOCR / 模型 / ONNX Runtime / 字典 / PaddleOCR 声明 |
| `tests/integration/test_ocr_adapter.py` | 新增：19 个测试（262 行） |
| `conftest.py` | 新增：把 `<root>/src` 加入 `sys.path`（venv 未安装 `textproof` 包） |
| `task_handoffs/T003/*` | 本交接包（随同提交，不在输出 commit 中） |

### 禁止文件未修改证明

- `git status` 在提交前只显示新增文件（`??`），无任何已跟踪文件修改；
  `git diff --stat 394d507`（提交后对照）仅含上述 11 个新增文件。
- 四份规格文件（`PROJECT_BOOK.md/.docx`、`IMPLEMENTATION_PLAN.md/.docx`）
  未修改；`requirements.lock`、`pyproject.toml` 未修改；未碰 T002 的文件
  （`src/textproof/contracts.py`、`src/textproof/io/`、
  `tests/unit/test_image_loader.py`——本 worktree 基于 394d507，T002 尚未合入，
  本任务未创建这些路径）。
- 注意（合并提示，非本任务问题）：T002 已合入 master（据 MEMORY.md 更新，
  T002 commit `c1c45eb`，合并 `2fb2e13`）。T002 很可能也创建了
  `src/textproof/__init__.py`；合并 `t003-rapidocr` 进 master 时若该文件冲突，
  以 T002 的版本为准再补本任务的 docstring，两者内容无功能冲突。

## 2. 验收标准逐项证据

### 验收 1 — RapidOCR 精确版本 3.10.0；依赖经 T001 锁文件固定 ✅ PASS

- `importlib.metadata.version("rapidocr") == "3.10.0"`；
  `onnxruntime == "1.32.0"`；`onnxruntime-gpu` 未安装（测试断言
  `PackageNotFoundError`）。
- 适配器启动时再次校验两个版本，不符即拒运行（`_check_versions`）。
- 证据：`test_rapidocr_exact_version`、`test_onnxruntime_exact_version_cpu_package`。

### 验收 2 — 默认模型路由按官方文档确认并冻结 ✅ PASS

- 路由（与规格 §6.2 一致）：
  - 检测：PP-OCRv6 `small`（`multi_PP-OCRv6_det_small`）
  - 识别：PP-OCRv6 `small`（`multi_PP-OCRv6_rec_small`）
  - 方向分类：PP-OCRv4 `mobile`（`ch_ppocr_mobile_v2.0_cls_mobile`）
- 确认依据（三处交叉印证）：
  1. 已安装 `rapidocr` 3.10.0 的 `config.yaml` 默认值：`Det: PP-OCRv6/small`、
     `Rec: PP-OCRv6/small`、`Cls: PP-OCRv4/mobile`；
  2. `default_models.yaml` 路由表（`model_routes`）把 `ch` 映射到上述三个
     `model_key`；
  3. 官方模型许可页 §6 表格把恰好这三个文件列为“RapidOCR 默认 ONNX Runtime
     配置的分发物”（https://rapidai.github.io/RapidOCRDocs/latest/en/model_licenses/，
     2026-11-25 读取）。
- 模型名、来源 URL、版本已记入 `THIRD_PARTY_NOTICES.md` §2 与本报告 §4，
  并以常量冻结在适配器（`DET_MODEL` / `REC_MODEL` / `CLS_MODEL`）。
- 证据：`test_frozen_model_route_recorded`。

### 验收 3 — 模型、字典全部位于本地资产路径；记录来源 URL、许可证、版本、SHA-256 ✅ PASS

- 全部 4 个文件在 `assets/ocr/`（`models/` 3 个 + `dictionaries/` 1 个），
  哈希见 `assets/ocr/SHA256SUMS.txt` 与 §4 清单。
- 每个文件的来源 URL、许可证、版本、SHA-256 记入 `THIRD_PARTY_NOTICES.md`
  和 §4。

### 验收 4 — 启动时不得触发模型下载；断网后仍可完成 OCR ✅ PASS（已实测）

- 机制：适配器在构造 RapidOCR **之前**校验全部资产的存在与 SHA-256，
  缺失/篡改直接抛 `FileNotFoundError` / `ValueError`；随后以显式
  `model_path` 构造引擎——RapidOCR 的 `OrtInferSession` 仅在 `model_path`
  为 `None` 时才走下载分支，因此运行时不存在下载路径。
  `Global.model_root_dir` 也指向本地 `assets/ocr/models`。
- 断网实测（方法与结果）：
  - 方法：`unshare -n bash -c '...'` 新建网络命名空间（本机 root 身份，
    无需额外工具）；先在命名空间内 `curl https://www.modelscope.cn/`
    验证外网确实不通（`curl: (7) Failed to connect to hatch-egress-proxy
    port 3128`，HTTP 000），再在同一命名空间内跑完整验收测试。
  - 结果：`19 passed in 24.73s`，exit 0。日志：
    `task_handoffs/T003/offline_test.log`（含 curl 失败行与 pytest 输出）。
- 另有 fail-closed 测试：删除任一模型、篡改模型字节、删除字典，适配器
  均在引擎构造前抛错（`test_missing_model_asset_fails_closed_without_download`、
  `test_tampered_model_asset_fails_closed`、`test_missing_dictionary_fails_closed`）。

### 验收 5 — ONNX Runtime 实际 provider 仅 CPUExecutionProvider ✅ PASS

- 适配器启动时对 det/cls/rec 三个 session 各自断言
  `get_providers() == ["CPUExecutionProvider"]`，否则拒运行；
  `EngineConfig.onnxruntime` 的 `use_cuda/use_dml/use_cann/use_coreml`
  全部显式置 `False`。
- 证据：`test_onnx_providers_are_cpu_only`、`test_no_gpu_provider_available_in_runtime`
 （`ort.get_device() == "CPU"`，`CUDAExecutionProvider` 不在可用列表）。
- 说明：`get_available_providers()` 另列的 `AzureExecutionProvider` 是标准
  CPU wheel 的内置注册项，不是 GPU provider，从未被选中。

### 验收 6 — 返回结构至少包含文本、置信度、bbox、quad 和原始顺序 ✅ PASS

- `OCRLine`（计划 §5.1 / 项目书 §7.1）：`line_index`、`text`、
  `confidence`、`bbox_xyxy`（另有 `bbox` 别名属性）、`quad`（4 个
  `(x, y)` 点）、`source_order`。
- `line_index` 在本层等于 `source_order`（RapidOCR 输出顺序，检测器已按
  y 稳定排序）；阅读顺序重排是 T004（`core/line_order.py`）的职责，
  本层不做（见适配器 docstring）。
- 证据：`test_recognize_english_and_digits`（精确识别 `Hello World 123`，
  置信度 > 0.9）、`test_recognize_two_lines_keeps_source_order`、
  `test_recognize_chinese`（精确识别 `限时优惠`）、
  `test_recognize_numeric_price`（`￥28.80` 中数字 `28.80` 被识别；
  注：模型输出半角 `¥`（U+00A5）而非全角 `￥`（U+FFE5），全角归一化是
  T004 的职责，项目书 §4.3）、`test_blank_image_returns_no_lines`、
  `test_repeat_recognition_is_deterministic`。

### 验收 7 — 字典许可单独核实；不因模型 Apache-2.0 推断字典许可 ✅ PASS（诚实记录：未核实）

- 字典文件：`ppocrv6_dict.txt`，18,708 行。已证实三处来源字节一致
  （同一 SHA-256 `b5f2bfe2…`）：
  1. registry `dict_url`（ModelScope RapidAI/RapidOCR v3.10.0）；
  2. PaddleOCR 上游 `ppocr/utils/dict/ppocrv6_dict.txt`（main 分支）；
  3. `PP-OCRv6_rec_small.onnx` 元数据内嵌的 `character` 列表
     （ONNX Runtime `get_modelmeta().custom_metadata_map` 读取）。
  适配器每次启动都把本地字典与模型内嵌列表逐行比对，不一致拒运行。
  注意：它**不是**旧的 `ppocr_keys_v1.txt`（6,623 行），后者与内嵌列表
  不符，未使用。
- 许可结论：**未核实（UNVERIFIED）**。依据：
  - RapidOCR 官方模型许可页 §2 明确排除字典：“registry 记录的非模型资源，
    包括识别字典（`dict_url`）和字体……不受本声明的 Apache-2.0 覆盖，
    适用其各自条款”（§6 重申）；
  - 字典文件本身无任何许可头或许可声明；
  - 仅有的相关事实是它随 Apache-2.0 的 PaddleOCR 仓库分发，但未找到针对该
    字典文件的专门许可声明。
  - 因此按项目书 §10.2 与任务卡要求，记为**未核实**，不硬写 Apache-2.0。
  - 已写入 `THIRD_PARTY_NOTICES.md` §4（逐项来源 + 未核实状态 + 后续要求：
    T014 的 SBOM/许可证报告在公开重分发前必须复核）。
- 风险见 §5。

## 3. 执行命令与退出码

| # | 命令（cwd `~/workspace/p033-textproof-t003`，除非注明） | 退出码 |
|---|---|---|
| 1 | `git worktree add ~/workspace/p033-textproof-t003 -b t003-rapidocr 394d507` | 0 |
| 2 | 模型 registry / 字典核查（venv python 读取 `default_models.yaml`、SHA-256 比对） | 0 |
| 3 | 官方许可页读取（browser.open `model_licenses/`，2026-11-25） | 0 |
| 4 | 字典三方比对：curl ModelScope `dict_url` + PaddleOCR GitHub raw + ONNX 元数据提取 | 0（字节一致） |
| 5 | 探针：`/home/hatch/workspace/p033-textproof/.venv/bin/python /tmp/t003probe/probe.py`（5 个合成用例全部精确识别；三模型 provider 均为 CPU） | 0 |
| 6 | 验收：`/home/hatch/workspace/p033-textproof/.venv/bin/python -m pytest tests/integration/test_ocr_adapter.py -q` | 0（19 passed，跑过 3 次：19.84s / 22.66s / 19.12s 全套） |
| 7 | 全套：`/home/hatch/workspace/p033-textproof/.venv/bin/python -m pytest -q` | 0（19 passed；本 worktree 只有集成测试） |
| 8 | 断网实测：`unshare -n bash -c 'curl …; pytest tests/integration/test_ocr_adapter.py -q'` | 0（curl 失败如预期；19 passed in 24.73s） |
| 9 | `git commit` 代码（48e88da） | 0 |

完整日志：`task_handoffs/T003/test_stdout.log`（在线验收 + 全套）、
`task_handoffs/T003/test_stderr.log`、`task_handoffs/T003/offline_test.log`
（断网实测）、`task_handoffs/T003/exit_codes.txt`。

注：执行期间两次出现运行时“审批超时未完成”的提示（02:1x 两次 pytest
exec 调用），但两次命令实际均已执行并返回了完整输出（19 passed，
exit 0，日志已落盘）。按任务指令以实际退出码和输出为准，未因此停工，
也未重复执行未获批的部分；此事如实记录，供父代理知悉。

## 4. 模型资产清单

| 文件 | 来源 URL | SHA-256 | 许可证 |
|---|---|---|---|
| `assets/ocr/models/PP-OCRv6_det_small.onnx` | https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.10.0/onnx/PP-OCRv6/det/PP-OCRv6_det_small.onnx | `090f04abcd9d9a7498bc4ebf677e4cb9bdce1fe4197ddb7e529f1ef44e1ff94f` | Apache-2.0（模型；版权 Baidu / PaddleOCR 权利人） |
| `assets/ocr/models/PP-OCRv6_rec_small.onnx` | https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.10.0/onnx/PP-OCRv6/rec/PP-OCRv6_rec_small.onnx | `6f327246b50388f3c176ae304bd95767ea6dc0c9ae92153ef8cbe210b3c14884` | Apache-2.0（模型；版权 Baidu / PaddleOCR 权利人） |
| `assets/ocr/models/ch_ppocr_mobile_v2.0_cls_mobile.onnx` | https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.10.0/onnx/PP-OCRv4/cls/ch_ppocr_mobile_v2.0_cls_mobile.onnx | `e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c` | Apache-2.0（模型；版权 Baidu / PaddleOCR 权利人） |
| `assets/ocr/dictionaries/ppocrv6_dict.txt` | https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.10.0/paddle/PP-OCRv6/rec/PP-OCRv6_rec_small/ppocrv6_dict.txt（另见 PaddleOCR 上游 `ppocr/utils/dict/ppocrv6_dict.txt`） | `b5f2bfe2bdd9448429e3e82b51c789775d9b42f2403d082b00662eb77e401c5d` | **未核实**（见 §2 验收 7） |

模型文件来源说明：三份 `.onnx` 是 T001 环境验证时由 RapidOCR 按 registry
自动下载到 venv `site-packages/rapidocr/models/` 的文件；T003 逐字节校验
其 SHA-256 与 registry 及官方许可页 §6 表格完全一致后，才复制进
`assets/ocr/models/`（未重新下载，避免来源漂移；哈希即身份证明）。

## 5. 未完成项与风险

1. **字典许可未核实（已知、已记录）**：`ppocrv6_dict.txt` 无专门许可声明，
   RapidOCR 模型 Apache-2.0 声明明确不覆盖字典。T014 的 SBOM / 许可证报告
   必须在公开重分发前复核；在此之前不得把字典描述为 Apache-2.0。
   不影响 T003 本地使用与 S0（模型本身许可已确认）。
2. **合并注意**：`src/textproof/__init__.py` 可能与 T002 的同名文件冲突
   （见 §1）；合并时以 T002 版本为准，无功能影响。
3. **适配器依赖 RapidOCR 3.10.0 内部加载方法**（`_load_det_model` 等，
   用于启动时 eager 加载与 provider 断言）。版本已冻结（3.10.0），升级
   RapidOCR 时须复核；这不是运行时行为风险。
4. **数字 `￥` 识别为半角 `¥`**：模型行为，全角归一化属 T004 职责，
   本任务不处理（见 §2 验收 6）。
5. 无其他未完成项。未调用任何收费 API / LLM / 云 OCR；测试图片全部为
   Pillow 合成图（零真人）；未复制 ComfyUI / AnyText / Qwen-Image 的
   代码或权重。

## 6. 回退

- 回退 commit：`394d507`（删除 `t003-rapidocr` 分支与 worktree 即可，
  主工作目录 master 未动）。
- 若后续发现模型资产不可用：适配器 fail-closed（启动即报错，绝不下载），
  按任务卡 T003 FAIL 处理，停止 S0。
