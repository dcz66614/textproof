# T002 — 输入契约、图片解码与校验

- 任务 ID：T002
- 输入 commit：`394d507eee52f0fe822303cb0945aced660597f1`（T001 基线，master）
- 输出 commit（代码）：`c1c45ebef606551e119908efe685fb6487260d01`（分支 `t002-input-contracts`）
- 交接文件提交：与代码同分支（`t002-input-contracts`），本文件提交后的哈希见父代理的验收报告（`git log` 可核对；本文件记录代码输出 commit 以避免自指哈希）。
- 执行时间：2026-11-25 ~02:06–02:20 GMT
- 执行者：Muse 子代理（T002 构建者）
- 工作目录：`~/workspace/p033-textproof-t002`（git worktree，主工作目录 master 未动）
- 状态：**SUCCESS**（验收标准 6/6 满足，53 个测试全部通过）

## 实际改动文件

见 `changed_files.txt`（6 个文件，全部为新增，1041 行插入，0 删除）：

- `src/textproof/__init__.py`
- `src/textproof/contracts.py`
- `src/textproof/io/__init__.py`
- `src/textproof/io/image_loader.py`
- `tests/conftest.py`
- `tests/unit/test_image_loader.py`

交接文件（`task_handoffs/T002/`，同分支另提交）：`TASK_RESULT.md`、
`changed_files.txt`、`git_diff.patch`、`test_commands.txt`、
`test_stdout.log`、`test_stderr.log`、`exit_codes.txt`、`SHA256SUMS.txt`。

## 禁止文件未修改证明

- `git status --short` 在 worktree 内只出现 `src/`、`tests/`、`task_handoffs/` 三个新增目录，无任何修改（`M`）项。
- 四份规格文件（`PROJECT_BOOK.md` / `.docx`、`IMPLEMENTATION_PLAN.md` / `.docx`）未动：`git diff 394d507 HEAD -- PROJECT_BOOK.md PROJECT_BOOK.docx IMPLEMENTATION_PLAN.md IMPLEMENTATION_PLAN.docx` 为空。
- `requirements.lock`、`pyproject.toml` 未动（同上 diff 为空）；无新依赖、无版本升级、无联网安装。
- T003 文件（`src/textproof/ocr/`、`assets/ocr/`、`THIRD_PARTY_NOTICES.md`、`tests/integration/test_ocr_adapter.py`）不存在于本分支，未创建、未修改。
- 主工作目录 `~/workspace/p033-textproof/` 的 master 检出未动（全部工作在 worktree `~/workspace/p033-textproof-t002`）。

## 实现说明

### `src/textproof/contracts.py` — 冻结契约唯一来源

- 冻结上限（`PROJECT_BOOK.md` §4.2，一处定义，全项目 import 此处，不得另行定义）：`MAX_FILE_SIZE_BYTES = 25 MiB`、`MAX_DIMENSION_PX = 8192`、`MAX_PIXELS = 40,000,000`、`MAX_EXPECTED_CODEPOINTS = 5000`、`MAX_EXPECTED_LINES = 100`；`SCHEMA_ID = "textproof.report/v1"`、`COORDINATE_SYSTEM = "oriented_image_px_top_left"`（§5.1）。
- 统一错误码：所有输入错误均为 `InvalidInputError`（`ValueError` 子类），`.code` 恒为 `"INVALID_INPUT"`，`.reason` 为短 snake_case 原因（如 `file_too_large`、`animated_webp`、`expected_text_too_long`），错误文本不含路径、用户文本或 EXIF 内容。
- `ImageInput`（§5.1）：`data`（原始校验后字节，报告 `image.sha256` 的来源，永不重编码）、`mime`、`format`（`PNG`/`JPEG`/`WEBP`，报告 `image.format`）、`width`/`height`（**EXIF orientation 应用后**的尺寸）、`oriented`（orientation tag 2–8 时为真）、`pil_image`（解码后、已转正、已剥离元数据的 Pillow 图像，供 T003 直接消费像素，无需二次转正）。`data` 与 `pil_image` 不进 `repr`，日志无法泄漏图片字节。
- `ExpectedTextInput`（§5.1）：`raw`、`normalized_lines`（仅统一 `CRLF`/`CR` → `LF` 后按行切分）、`codepoint_count`、`line_count`。**§4.3 的完整规范化（NFC、全角映射、空白折叠）是 T004 `core/normalize.py` 的职责，本任务故意不在此做**，以保证 §4.3 只有一个所有者；`raw` 与 `normalized_lines` 不进 `repr`（§9：日志不得记录期望文本）。

### `src/textproof/io/image_loader.py` — 校验与解码

- 只接受 `bytes`（`bytearray`/`memoryview` 转 bytes）：**没有任何路径参数**，因此不存在任意路径读/写面（§9）。格式判定只看魔数（PNG `89 50 4E 47 0D 0A 1A 0A`、JPEG `FF D8 FF`、WebP `RIFF....WEBP`），不依赖扩展名；魔数与 Pillow 解出的 `format` 不一致即拒绝（扩展名伪装 / 魔数伪造）。
- 尺寸与像素上限先在**图片头**检查、再在完整解码后复查，超限文件不触发大分配（解压炸弹防御）；另设 `Image.MAX_IMAGE_PIXELS = 40_000_000` 作纵深防御。
- 动画 WebP 双重检查：原始字节的 VP8X chunk 动画位（`0x02`）+ 解码器 `n_frames`/`is_animated`；任一命中即拒绝。
- 损坏/截断文件、解码异常一律 fail-closed 转 `INVALID_INPUT`（不透传 Pillow 异常）。
- EXIF：只读 orientation tag（274）一个值；`ImageOps.exif_transpose` 应用转正；返回的 `pil_image` 经 `_strip_private_metadata` 剥离全部 EXIF blob（UserComment 0x9286、GPS 0x8825 等）与 PNG 文本块，仅保留 `icc_profile`/`dpi`；像素不变。
- `validate_expected_text`：非字符串、空白（空或纯空白字符）、>5000 码点、>100 行、孤立代理项（lone surrogate）均拒绝；行数按统一换行后的 `LF` 分段计。

### `tests/conftest.py`

- 把 worktree 的 `src/` 加入 `sys.path`，使验收命令在未安装包的情况下直接跑源码（`.venv` 未安装 `textproof`，且不得向共享 venv 做指向 worktree 的 editable 安装）。该文件随仓库提交，干净检出同样可用。

## 接口定义（供 T004 消费，计划 §5.1）

```python
from textproof.contracts import ImageInput, ExpectedTextInput, InvalidInputError
from textproof.io.image_loader import load_image, validate_expected_text

image: ImageInput = load_image(image_bytes)          # raises InvalidInputError(code="INVALID_INPUT")
expected: ExpectedTextInput = validate_expected_text(text)
```

接口样例 JSON（字段含义，非真实报告）：

```json
{
  "image_input": {
    "mime": "image/png",
    "format": "PNG",
    "width": 1200,
    "height": 480,
    "oriented": false,
    "sha256_hex": "<sha256 of the original input bytes>",
    "image_report_fields": {
      "format": "PNG",
      "width": 1200,
      "height": 480,
      "coordinate_system": "oriented_image_px_top_left"
    }
  },
  "expected_text_input": {
    "codepoint_count": 4,
    "line_count": 1,
    "normalized_lines": ["限时优惠"]
  },
  "error_shape": {
    "code": "INVALID_INPUT",
    "reason": "file_too_large"
  }
}
```

T004 约定：`image.pil_image` 为已转正图像，直接取像素做 OCR 输入，不要二次 `exif_transpose`；`expected.normalized_lines` 仍需过 T004 的 §4.3 规范化；报告 `image.sha256` 取 `image.sha256_hex()`。

## 验收标准逐项核对

1. 只接受 PNG/JPEG/WebP，魔数检查，不依赖扩展名 —— 满足。`test_png_accepted` / `test_jpeg_accepted` / `test_webp_accepted`（含无损与 RGBA WebP）；`test_magic_detection_ignores_would_be_extension`；GIF/随机字节/纯文本拒绝；加载器无文件名入参（`test_loader_takes_bytes_only` 断言签名仅为 `data`）。
2. 25 MiB、8192 px、40MP 三项边界分别有正反测试 —— 满足。25 MiB：恰好 `25*1024*1024` 字节的填充 PNG 通过，+1 字节拒绝；8192 px：`8192x1` 与 `1x8192` 通过，`8193x1` 与 `1x8193` 拒绝；40MP：`8000x5000 = 40,000,000`（L 模式）通过，`8000x5001 = 40,008,000` 拒绝（原因 `too_many_pixels`）。
3. 动画 WebP、损坏文件、扩展名伪装、超像素和解码异常均 fail-closed —— 满足。动画 WebP（2 帧 `save_all`）拒绝；单帧 WebP 置 VP8X 动画位也被原始字节检查拒绝；截断 PNG/JPEG/WebP 拒绝；PNG 魔数 + JPEG 内容、JPEG 魔数 + PNG 内容拒绝；超像素拒绝；全部以 `INVALID_INPUT` 收敛（`test_all_rejections_share_the_unified_code`）。
4. 正确应用 EXIF orientation，输出宽高和坐标基准符合 §5 —— 满足。JPEG orientation 6/8：`100x50` → `50x100` 且 `oriented=True`；orientation 3：尺寸不变但 `oriented=True`；orientation 1 / 无 EXIF：`oriented=False`；PNG eXIf orientation 6 同样转正；`image_report_fields()` 返回 `coordinate_system: oriented_image_px_top_left` 与转正后宽高。
5. 期望文本 5,000 码点 / 100 行边界通过测试；空白输入拒绝 —— 满足。恰好 5000 码点（中英混排）通过，5001 拒绝；恰好 100 行通过，101 行拒绝；`""`、`"   "`、`"\n\n"`、`"\t \r\n  "`、全角空格拒绝；`CRLF`/`CR` 统一计行；非字符串与孤立代理项拒绝。
6. 不把绝对路径、EXIF 用户备注或地理位置写入报告 —— 满足。含 UserComment + GPS IFD（25°N/121°E）的 JPEG：加载成功，但 `repr`、报告字段、剥离后图像的 EXIF（空）与 `info` 均不含备注/GPS；含 `Comment` 文本块的 PNG 同样剥离；错误文本不含 `/` 路径与用户文本；`ImageInput`/`ExpectedTextInput` 的 `repr` 排除用户内容。

## 执行命令与退出码

见 `test_commands.txt` / `exit_codes.txt`。验收命令：

```bash
/home/hatch/workspace/p033-textproof/.venv/bin/python -m pytest tests/unit/test_image_loader.py -q
```

- 退出码：**0**（`test_stdout.log` / `test_stderr.log` 为该次运行的原始日志）。
- 结果：**53 passed, 2 warnings in 1.51s**。
- 2 条 warnings 是预期的 Pillow `DecompressionBombWarning`（`test_pixels_over_40m_rejected` 与 `test_all_rejections_share_the_unified_code` 中 40,008,000 px 图片在 `Image.open` 时触发，因 `Image.MAX_IMAGE_PIXELS` 已设为冻结值 40,000,000；加载器随后以 `INVALID_INPUT` / `too_many_pixels` 拒绝，非失败）。

## 测试结果

- 验收命令：53 passed，0 failed，exit 0。
- 测试图片全部由 Pillow 在内存中合成生成；零真人图片、零网上图片、零网络访问；无收费 API / LLM / 云服务调用。

## 未完成项

- 无。本任务卡的输出文件（`contracts.py`、`io/image_loader.py`、`tests/unit/test_image_loader.py`）与 6 项验收标准全部完成。

## 风险

1. **25 MiB 精确边界用尾部填充 PNG 测得**：精确到字节的 25 MiB 真实图片难以用 Pillow 自然生成，测试用小 PNG 后补 `\x00` 至恰好上限（Pillow 容忍 IEND 后尾部字节）。尺寸检查以 `len(data)` 为准，与填充方式无关，边界结论成立；但若未来 Pillow 版本收紧尾部字节容忍，该正向用例可能失效，届时应改用自然大图逼近边界重测。
2. **`Image.MAX_IMAGE_PIXELS` 是进程级全局设置**：本模块将其设为冻结值 40,000,000，同一进程内的 T003/T005 若打开超限图片也会收到 Pillow 警告/拒绝——这与 §4.2 一致，是有意为之的纵深防御，不是副作用；但若后续任务确需在同一进程内处理超限图片（如负向测试之外的用途），须显式说明，不得悄悄调高。
3. **EXIF 读取失败时按无 orientation 处理**：EXIF 段损坏但像素可解的图片会被当作无转正继续处理（`getexif` 异常分支）。Pillow 的 `exif_transpose` 同样容忍此情况；坐标错误的残余风险极低，且 fail-open 仅影响显示元数据、不影响像素校验。T010 隐私审查可复核此分支。
4. **40MP 正向用例内存占用**：`8000x5000` L 模式图约 40 MB，加上 PNG 编解码缓冲，峰值约 100 MB。当前 VM 可用内存约 849 MB（T001 探测），实测通过；内存更紧张时可改用 `1` 模式（位图）重测同一边界。
5. **WebP 动画检测依赖 VP8X 位置假设**：原始字节检查在前 32 字节内找 `VP8X`（标准 RIFF 布局中 VP8X 紧跟 12 字节 RIFF 头）。解码器的 `n_frames`/`is_animated` 检查是第二道防线；两者任一命中即拒绝，单点失效不导致放行。

## 回退

- 回退 commit：`394d507eee52f0fe822303cb0945aced660597f1`（T001 基线）。本分支只新增 6 个文件，未修改任何已有文件，回退即删除本分支（`git branch -D t002-input-contracts`）或将 worktree 移除，不影响 master。
- 失败回退策略（按任务卡）：不放宽输入上限；不支持的格式返回明确 `INVALID_INPUT`。本实现未放宽任何上限。
