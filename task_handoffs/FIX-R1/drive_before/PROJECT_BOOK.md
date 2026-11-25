# P033 字证 TextProof｜项目书

> **一句话定义：AI 负责画图，TextProof 负责逐字证明图里的文字是否符合用户原本提供的内容。**  
> 产品形态：本地离线 AI 图片文字确定性校验器  
> 规格版本：`1.0.0`  
> 项目编号：`P033`  
> 项目代号：`textproof`  
> 立项日期：`2026-11-25`  
> 规格状态：`SPEC_FROZEN / NOT_IMPLEMENTED`  
> 预算上限：`88h`  
> 参与者：`0`（全部测试数据为合成数据；不招募真人）  
> 许可证：`MIT`（TextProof 自有代码）  
> Owner 代理：Muse（负责调度、门禁、取证与归档；不编写业务代码或测试）

---

## 0. 文档控制与规范效力

### 0.1 权威文件

本文件是 TextProof 的唯一产品与算法契约。配套 `IMPLEMENTATION_PLAN.md` 负责施工任务、依赖、验收命令和交付证据。两份 Markdown 为内容源文件；对应 DOCX 必须由其生成，章节、表格、示例、约束和数值不得缺失。

### 0.2 冻结规则

以下内容为冻结契约：

1. 输入只支持静态 `PNG`、`JPEG`、`WebP` 图片；用户提供期望文本；处理语言范围为中文、英文和数字。
2. 输出必须为 `textproof.report/v1` JSON，包含错误类型、坐标、期望文本与 OCR 识别结果对照。
3. 核心机制为本地 OCR、字符级加权编辑距离、行级顺序对齐，以及将差异关联到 OCR 文本框坐标。
4. 产品运行离线、本地 CPU；不得使用 GPU、收费 API、远程模型服务或图片外传。
5. 测试只能使用程序生成的合成图片与合成期望文本；不得使用真实用户图片、公开图片数据集或真人参与者。
6. 预算总计 88 小时，不能通过删减验收门槛来掩盖超时。

施工期间不得擅自改变输入格式、字段名称、JSON schema、错误枚举、坐标系、算法阈值、S0 门槛或隐私边界。确需变更时，必须先提交 ADR，说明兼容影响、测试影响和迁移方式；提升 `SPEC_VERSION`，同步更新两份 Markdown 与 DOCX，取得项目 Owner 明确批准后才能实施。没有批准时继续按本版本执行。

### 0.3 状态边界

本文中的性能阈值、准确率和样例输出都是**验收目标或固定测试预言**，不是已经运行的成绩。当前尚无产品代码、实测数据、真实用户研究或发布版本。本规格完成不等于产品验收通过。

---

## 1. 产品定位：先解决真实的交付问题

### 1.1 目标用户

**主要用户：中文内容创作者与小型电商经营者。**  
他们在 Windows 或 Linux 电脑上使用 ComfyUI、Qwen-Image 或其他图像生成工具制作商品海报、促销图、课程封面、社交媒体配图。用户已经在提示词或设计稿中确定了商品名、金额、折扣、日期、活动文案；生成图片后，需要确认图片中实际出现的字是否与原文一致。

**次要用户：独立设计师、营销运营和课程内容制作者。**  
他们需要批量制作同一活动的多张图片，最担心的是品牌名、型号、金额、电话号码、优惠条件或日期被漏写、错写。TextProof 不是设计软件，也不替用户决定文案，只核对用户明确提供的期望文本。

### 1.2 具体使用场景

- 用户生成一张商品海报，输入期望文字“星河咖啡 限时优惠 ￥28.80”，图片上实际显示“星河咖啡 限时优 ￥28.00”；在发布前定位漏字和金额变化。
- 用户制作 6 张课程封面，期望每张都有“2026 秋季班”，检查某张是否漏掉“秋季”或把数字写错。
- 用户为同一产品生成不同风格图片，逐张导入并核对品牌名、规格和活动日期。
- 用户把生成图片交给同事前，导出 JSON 报告，留下可被脚本读取的差异记录。

频率与代价是规划假设，不是调查结论：高频创作者可能每周检查约 3–5 张图；单次放大图片、逐字核对或重生成约需 5–25 分钟。构思阶段没有访谈、真人试用、付费意愿或节省时间的实测，`USER_VALUE_NOT_MEASURED` 必须保留。

### 1.3 当前 workaround 及其不足

| 当前做法 | 具体不足 |
|---|---|
| 放大图片逐字检查 | 需要反复缩放与移动视图；小字、数字和相似字仍容易漏看；不能自动留下结构化证据 |
| 重新生成图片 | 可能改变构图、背景和其他文字；不能证明新图的字已经正确 |
| 使用图片编辑模型改字 | 编辑模型的目标是修改图像，不是独立判定最终图是否符合用户给出的原文 |
| 单独运行 OCR | 通常得到“识别出了什么”，但用户仍需手工对照原文；OCR 文本没有自动转成逐字符差异与图片坐标的完整报告 |
| 把图片发给在线视觉服务 | 与本项目的本地隐私约束冲突；网络服务也无法作为离线交付门禁 |

### 1.4 一句话价值与差异化

**AI 负责画图，TextProof 负责逐字证明图里的文字是否符合用户原本提供的内容。**

TextProof 是生成后的独立验证层：

- PaddleOCR / RapidOCR 解决文字检测与识别，提供文本及位置；TextProof 在其上增加“期望文本—识别文本”的确定性对账。
- AnyText、Qwen-Image、Qwen-Image-Edit 的方向是生成或编辑图像中的文字；TextProof 不生成、不修图、不调用这些模型。
- TextProof 将字符差异映射到 OCR 文本行的图片坐标，并输出固定 JSON schema；它不把 OCR 推断冒充视觉事实，也不声称每个错误坐标都是单字级精确框。

潜在传播路径：一张“原文 / 图片 / 错误框 / JSON”对照图即可解释价值；可独立运行，也可在后续版本做 ComfyUI 节点或本地 API 集成。潜在收购方只是一项商业假设，可能包括图片生成平台、设计工具和本地创作软件；目前没有收购意向或商业验证，不作保证。

---

## 2. 目标、非目标与产品边界

### 2.1 MVP 目标

1. 对一张静态图片进行本地 OCR，识别中文、英文和数字。
2. 接受用户提供的期望文本，并与 OCR 文本按阅读顺序进行行级和字符级对齐。
3. 用字符级加权编辑距离识别替换、缺失、额外字符和数字变化。
4. 把每个差异关联到包含它的 OCR 文本行坐标；没有对应 OCR 框时明确返回 `null`，不得伪造坐标。
5. 输出可机器读取、可校验的 `textproof.report/v1` JSON。
6. 提供本地浏览器 UI 与 CLI 两种入口。
7. 在断网、CPU-only、无真实图片、零真人参与条件下通过固定合成验收。

### 2.2 非目标

- 不生成、编辑、修复、重绘或润色图片。
- 不替用户改写期望文本，不用 LLM 判断语义是否正确。
- 不判断商品信息、法律文案或宣传承诺是否真实。
- 不保证 OCR 对艺术字、手写字、透视变形、弧形文字、竖排文字、复杂多栏排版或极小文字有效。
- 不做视频、GIF、PDF、SVG、TIFF、HEIC 或批量目录扫描。
- 不做字体版权检查、品牌色检查、对比度认证、无障碍认证或印刷预检。
- 不把 OCR 识别结果当作图片真值；低置信或歧义必须要求复核。
- 不上传图片、期望文本、OCR 结果、哈希或遥测数据到外部服务。
- 不提供账号、云端数据库、协作平台或在线 API。

### 2.3 支持范围与明确限制

| 维度 | MVP 支持 | 不承诺 |
|---|---|---|
| 图片 | 单张静态 PNG / JPEG / WebP | 动画 WebP、GIF、PDF、SVG、TIFF、HEIC |
| 文字 | 简体中文、英文、阿拉伯数字；常见标点可参与对比 | 所有语言、手写、复杂艺术字 |
| 阅读方向 | 以水平文字、从上到下、同一行从左到右为主 | 竖排、弧形、任意旋转、多栏复杂阅读顺序 |
| 期望文本 | 用户输入；换行表示期望的视觉文本行 | 自动从提示词、模型日志或设计源文件提取原文 |
| 坐标 | OCR 文本行的像素级外接框及四边形 | OCR 引擎未提供的真实单字精确边界 |
| 判定 | 文字差异提示与证据 | 对图像视觉内容的法律或事实认证 |

---

## 3. 用户流程与交互契约

### 3.1 主流程

1. 打开本机 `127.0.0.1` 上的 TextProof 页面。
2. 选择一张 PNG/JPEG/WebP 图片；页面在浏览器内显示本地预览。
3. 粘贴期望文本。每个换行代表一个期望视觉文本行；文字顺序应为从上到下、同一行从左到右。
4. 点击“开始核对”。浏览器将图片字节与期望文本发给本机服务；服务仅在内存中处理。
5. 页面展示 OCR 文本行、行框覆盖层、错误清单、差异片段和置信度提示。
6. 用户可修改期望文本后重新核对；也可下载 JSON 报告。
7. 点击“清除”后，页面撤销图片预览 URL 并清空输入、识别结果和报告；服务不保留跨请求会话数据。

### 3.2 UI 页面布局

- 顶部：产品名称、`离线 / 本机运行` 状态、版本号。
- 左栏：图片选择、图片信息、期望文本编辑框、开始核对按钮。
- 中央：图片预览画布；OCR 文本行用矩形框标记；选中错误时高亮对应文本行框。
- 右栏：总体 verdict、错误数量、错误类型、期望片段 / 识别片段、坐标和 OCR 置信度。
- 底部：下载 JSON、复制报告摘要、清除当前内容。
- 空状态：说明“先上传图片，再输入期望文本”；不展示虚构的检测结果。
- 低置信提示：明确写“识别结果不确定，需要人工查看原图片区域”，不自动把它标成确定错字。

### 3.3 用户可见措辞

界面使用“检测到差异 / 疑似不一致 / 需要复核”，不使用“已证明图片一定写错”。OCR 可能把正确图像识别错；TextProof 证明的是“期望文本与当前 OCR 输出存在差异”，不是无条件证明视觉事实。

---

## 4. 功能需求

### 4.1 功能需求表

| ID | 需求 | 验收要点 |
|---|---|---|
| FR-01 | 接受 PNG/JPEG/WebP 静态图片 | 文件魔数与格式一致；不接受扩展名伪装 |
| FR-02 | 接受用户期望文本 | 最多 5,000 个 Unicode 码点、最多 100 行；换行保留为行对齐提示 |
| FR-03 | 本地 OCR | RapidOCR CPU 推理；输出每行文本、置信度、bbox 与 quad |
| FR-04 | 规范化与对齐 | NFC、全角 ASCII 映射、空白规则固定；行序列动态规划；字符级加权编辑距离 |
| FR-05 | 差异分类 | `SUBSTITUTION`、`MISSING_CHARACTER`、`EXTRA_CHARACTER`、`NUMERIC_CHANGE`、`MISSING_LINE`、`EXTRA_LINE`、`AMBIGUOUS_ALIGNMENT` |
| FR-06 | 坐标关联 | 错误关联到 OCR 文本行 bbox；缺失整行或无框时坐标为 `null` |
| FR-07 | JSON 报告 | 输出 `textproof.report/v1`，字段完整并通过 JSON Schema 校验 |
| FR-08 | 本地 UI | 上传、预览、文本输入、运行、框选、错误清单、下载、清除 |
| FR-09 | CLI | `textproof check`、`textproof serve`、`textproof verify-s0` |
| FR-10 | 断网运行 | 启动、OCR、比较、UI、CLI、JSON 导出均不访问外网 |
| FR-11 | 数据清除 | 不持久化图片和文本；用户可清空当前 UI 内容；不写浏览器 localStorage |
| FR-12 | 可复现测试 | 固定 300 张合成图片、固定 manifest、固定预期输出、独立 Oracle |

### 4.2 输入约束

- 文件格式：PNG、JPEG/JPG、WebP；仅静态图片。
- 最大文件大小：25 MiB。
- 最大宽或高：8,192 px。
- 最大像素总数：40,000,000 px。
- 图片解码后应用 EXIF orientation；坐标以旋转后的显示图像为基准。
- 拒绝动画 WebP、损坏文件、格式与魔数不一致、超限图片和解压炸弹风险文件。
- 期望文本最多 5,000 Unicode 码点、最多 100 行；空白文本返回 `INVALID_INPUT`。
- 用户可输入中文、英文和数字；标点保留并参与对比。
- 不读取图片之外的 EXIF 用户备注或地理位置；报告不写入绝对路径。

### 4.3 规范化规则

对期望文本和 OCR 文本分别应用同一套规范化：

1. Unicode NFC 规范化。
2. `CRLF` 与 `CR` 统一为 `LF`。
3. 全角 ASCII 字符映射为对应半角 ASCII；全角空格映射为普通空格。
4. 每行首尾空白去除；连续水平空白折叠为一个空格。
5. 英文字母大小写敏感；标点不删除；不做同义词替换或语义纠错。
6. 字符索引以规范化后的 Unicode 码点为准，区间采用左闭右开 `[start, end)`；报告仍保留用户原始期望文本和 OCR 原始识别文本。

该规则避免把全角 / 半角差异当成错误，但不会把不同数字、不同汉字、大小写或标点自动视为相同。

### 4.4 阅读顺序与行级对齐

- OCR 引擎返回文本行和四边形坐标。
- MVP 对主要水平文字按文本框垂直中心与纵向重叠聚合为行；同一视觉行内按 x 从小到大排序；行按 y 从小到大排序。
- 用户期望文本的换行顺序与上述阅读顺序对应。
- 期望行与 OCR 行使用序列动态规划对齐；配对代价为归一化加权编辑距离，插入 / 删除行使用固定 gap penalty。
- 若两个最优对齐路径代价差小于 `0.05`，标记 `AMBIGUOUS_ALIGNMENT`，总体 verdict 为 `REVIEW_REQUIRED`。
- 若行配对代价高于 `0.70`，优先作为缺失行与额外行处理，不强行制造逐字符配对。
- 平局顺序固定：匹配 / 替换优先，其次缺失期望行，最后额外 OCR 行。

### 4.5 字符级加权编辑距离

对每对已对齐文本行执行动态规划。代价固定如下：

| 操作 | 代价 |
|---|---:|
| 规范化后字符相同 | 0 |
| 常见视觉混淆对（如 `O/0`、`I/1/l`、`S/5`、`B/8`）替换 | 0.65 |
| 标点替换 | 0.50 |
| 数字替换（数字到数字） | 1.25 |
| 其他字符替换 | 1.00 |
| 缺失字符 / 额外字符 | 1.00 |

混淆对的较低代价只影响对齐选择，**只要字符不同仍必须产生差异记录**。数字替换优先分类为 `NUMERIC_CHANGE`。其他替换为 `SUBSTITUTION`；期望字符未在 OCR 结果中出现为 `MISSING_CHARACTER`；OCR 多出字符为 `EXTRA_CHARACTER`。

### 4.6 坐标定义与精度边界

- `bbox_xyxy = [x1, y1, x2, y2]`，单位为像素，原点位于经过 EXIF orientation 处理后的图像左上角。
- `quad` 是四个角点的像素坐标。
- 当前 OCR 结果只保证文本行级框；因此每个字符差异的 `bbox_xyxy` 是**包含该字符差异的 OCR 文本行框**，不是单字字形框。
- `MISSING_LINE` 没有 OCR 框，坐标为 `null`；不得把附近无关框冒充缺失字符位置。
- UI 高亮整行，并展示字符索引和差异片段；不绘制未经 OCR 提供的单字精确框。


---

## 5. 冻结的 JSON 输出契约

### 5.1 Schema 标识

- Schema：`textproof.report/v1`
- MIME：`application/json`
- 编码：UTF-8
- 字符索引：规范化文本的 Unicode 码点索引，左闭右开。
- 坐标系：`oriented_image_px_top_left`。

### 5.2 Verdict 枚举

| Verdict | 含义 |
|---|---|
| `MATCH` | 期望文本与 OCR 文本无差异，且无需复核警告 |
| `MISMATCH` | 检测到明确字符或行差异 |
| `REVIEW_REQUIRED` | 存在低置信度、对齐歧义或不支持的布局警告 |
| `OCR_FAILED` | OCR 未能产生可用识别结果或引擎失败 |

### 5.3 错误类型枚举

`SUBSTITUTION`、`MISSING_CHARACTER`、`EXTRA_CHARACTER`、`NUMERIC_CHANGE`、`MISSING_LINE`、`EXTRA_LINE`、`AMBIGUOUS_ALIGNMENT`。

警告枚举至少包括：`LOW_OCR_CONFIDENCE`、`POSSIBLE_MULTI_COLUMN`、`ROTATED_TEXT_NOT_SUPPORTED`、`OCR_EMPTY`。警告不冒充字符错误。

### 5.4 JSON 样例

以下是固定语义样例。实际 `sha256`、置信度与坐标由运行结果填入；样例中的坐标仅用于说明字段语义，不是实测 OCR 输出。

```json
{
  "schema": "textproof.report/v1",
  "tool_version": "0.1.0",
  "verdict": "MISMATCH",
  "image": {
    "sha256": "<runtime_sha256>",
    "format": "PNG",
    "width": 1200,
    "height": 480,
    "coordinate_system": "oriented_image_px_top_left"
  },
  "expected_text": "限时优惠",
  "recognized_text": "限时优",
  "ocr_lines": [
    {
      "line_index": 0,
      "text": "限时优",
      "confidence": 0.98,
      "bbox_xyxy": [120, 180, 520, 252],
      "quad": [[120, 180], [520, 180], [520, 252], [120, 252]]
    }
  ],
  "errors": [
    {
      "id": "E001",
      "type": "MISSING_CHARACTER",
      "expected_line_index": 0,
      "ocr_line_index": 0,
      "expected_text": "限时优惠",
      "recognized_text": "限时优",
      "expected_span": [3, 4],
      "recognized_span": [3, 3],
      "expected_fragment": "惠",
      "recognized_fragment": "",
      "bbox_xyxy": [120, 180, 520, 252],
      "bbox_scope": "ocr_line",
      "confidence": 0.98
    }
  ],
  "warnings": [],
  "summary": {
    "expected_lines": 1,
    "ocr_lines": 1,
    "error_count": 1,
    "warning_count": 0
  }
}
```

### 5.5 API 与 CLI 契约

本地 HTTP API：

- `GET /api/v1/health`：健康状态，不包含用户数据。
- `GET /api/v1/version`：版本、schema 版本和 OCR 模型版本。
- `POST /api/v1/check`：接收 JSON 请求，字段为 `image_mime`、`image_base64`、`expected_text`；在内存解码并返回 `textproof.report/v1`。
- 服务只绑定 `127.0.0.1`；不启用公网监听、CORS 外域白名单或外部回调。

CLI：

```bash
textproof check --image ./poster.png --expected-file ./expected.txt --json ./report.json
textproof serve --host 127.0.0.1 --port 8765
textproof verify-s0 --manifest tests/fixtures/s0/manifest.json
textproof version
```

CLI 退出码：

| Exit code | 含义 |
|---:|---|
| 0 | `MATCH` |
| 1 | `MISMATCH` |
| 2 | `REVIEW_REQUIRED` |
| 3 | 输入无效 |
| 4 | OCR 失败 |
| 5 | 内部错误 |

CLI 与 HTTP API 必须使用同一套核心比较函数和同一 JSON schema；CLI 不得另造一套错误判定。

---

## 6. 技术架构与模块划分

### 6.1 冻结架构

TextProof 采用单进程 Python 本地应用：

1. 图片输入与校验层：Pillow 读取魔数、尺寸、EXIF orientation、静态帧和像素上限。
2. OCR 适配层：RapidOCR `3.10.0`，使用 ONNX Runtime CPU provider；默认小模型作为首选，模型文件与字典在安装包内本地可用。
3. 阅读顺序层：把 OCR 四边形归一化为文本行顺序。
4. 比较核心：规范化、行级动态规划、字符级加权编辑距离、错误分类。
5. 报告层：构建 `textproof.report/v1`，通过 JSON Schema 校验。
6. 服务层：FastAPI + Uvicorn，绑定 `127.0.0.1`。
7. UI 层：随包分发的本地 HTML/CSS/JavaScript；不使用 CDN、外链字体或远程脚本。
8. CLI 层：标准库 argparse；除非 T001 证明有明确必要，不引入额外 CLI 框架。

### 6.2 推荐技术栈与版本策略

| 组件 | 目标版本 / 选择 | 用途与边界 |
|---|---|---|
| Python | 3.12.x | 应用、CLI、API、OCR 与比较核心 |
| RapidOCR | `3.10.0` | OCR 适配；官方文档说明该版本默认模型路由为 PP-OCRv6 small 检测 / 识别及 PP-OCRv4 mobile 方向分类 |
| ONNX Runtime | CPU 版；精确版本由 T001 锁定 | 禁止安装 GPU 版；运行时确认 `CPUExecutionProvider` |
| Pillow | T001 锁定兼容版本 | 图片解码、EXIF orientation、尺寸与格式校验 |
| FastAPI / Uvicorn | T001 锁定兼容版本 | 本机 API 与静态 UI 服务 |
| Pydantic | T001 锁定兼容版本 | API 请求 / 响应模型 |
| pytest | T001 锁定兼容版本 | 单元、集成与 S0 测试 |
| Noto Sans SC | 固定字体文件及 SHA-256 在 T005 冻结 | 仅用于生成合成测试图片；字体许可为 OFL，不用于声称 OCR 模型精度 |

所有 Python 依赖必须生成带哈希的 `requirements.lock`。具体补丁版本以 T001 在实际虚拟机上的兼容性测试为准，不允许后续任务自行升级。打包时生成目标平台 wheelhouse；运行时不访问 PyPI、ModelScope、Hugging Face 或其他网络服务。

### 6.3 推荐工作区布局

```text
P033-textproof/
├── pyproject.toml
├── requirements.lock
├── LICENSE
├── README.md
├── THIRD_PARTY_NOTICES.md
├── SECURITY.md
├── src/textproof/
│   ├── cli.py
│   ├── contracts.py
│   ├── api/
│   │   ├── app.py
│   │   └── routes.py
│   ├── core/
│   │   ├── normalize.py
│   │   ├── line_order.py
│   │   ├── align_lines.py
│   │   ├── weighted_edit.py
│   │   ├── classify.py
│   │   └── report.py
│   ├── io/
│   │   └── image_loader.py
│   ├── ocr/
│   │   └── rapidocr_adapter.py
│   └── ui/
│       ├── index.html
│       ├── app.js
│       └── style.css
├── assets/ocr/
│   ├── models/
│   ├── dictionaries/
│   └── SHA256SUMS.txt
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── privacy/
│   ├── e2e/
│   └── fixtures/s0/
├── oracle/
│   └── reference_compare.py
├── scripts/
│   ├── generate_fixtures.py
│   ├── verify_s0.py
│   ├── independent_verify.py
│   └── verify_release.py
└── release/
    ├── wheelhouse/
    ├── source.zip
    ├── SHA256SUMS.txt
    ├── RELEASE_MANIFEST.json
    └── REVIEW_INDEX.md
```

---

## 7. 关键算法与数据假设

### 7.1 OCR 输出结构

每个 OCR 文本行至少包含：

- `line_index`：排序后的零基行索引。
- `text`：识别文本。
- `confidence`：OCR 置信度。
- `bbox_xyxy`：像素外接框。
- `quad`：四角点。
- `source_order`：OCR 原始输出顺序，便于审计。

OCR 引擎置信度是模型分数，不是字符正确概率的校准保证。

### 7.2 行序列对齐

设期望行序列为 `E = (e1 ... em)`，OCR 行序列为 `O = (o1 ... on)`。字符加权编辑距离为 `d_w(ei, oj)`，归一化配对代价：

\[
c(i,j)=\frac{d_w(e_i,o_j)}{\max(|e_i|,|o_j|,1)}
\]

使用全局序列动态规划，配对代价为 `c(i,j)`，插入 / 删除行 gap penalty 固定为 `0.35`。对齐结果按 §4.4 的平局规则确定。两个最优路径代价差小于 `0.05` 时，不输出确定性字符结论，而是 `REVIEW_REQUIRED`。

### 7.3 字符级动态规划

令 `D[i,j]` 为期望前 `i` 个字符与 OCR 前 `j` 个字符的最小代价：

\[
D[i,j]=\min
\begin{cases}
D[i-1,j]+1 & \text{缺失字符}\\
D[i,j-1]+1 & \text{额外字符}\\
D[i-1,j-1]+w(e_i,o_j) & \text{匹配或替换}
\end{cases}
\]

`w` 依照 §4.5 的冻结权重。回溯生成操作序列；相同代价时按“对角替换 / 匹配 → 缺失 → 额外”的固定优先级，确保同一输入产生相同报告。

### 7.4 数字变化

当期望字符和 OCR 字符都属于 Unicode 十进制数字类别 `Nd`，且两者不同，分类为 `NUMERIC_CHANGE`。数字缺失仍为 `MISSING_CHARACTER`，数字额外仍为 `EXTRA_CHARACTER`，并在 `expected_fragment` / `recognized_fragment` 中保留完整片段。

### 7.5 坐标关联

替换和插入关联到包含 OCR 字符的文本行 bbox；缺失字符关联到匹配行 bbox；缺失整行没有 OCR 框，坐标必须为 `null`。任何情况下都不得按等宽假设把整行 bbox 伪装成真实单字框。

### 7.6 置信度与 verdict

OCR 行置信度低于 `0.65` 时添加 `LOW_OCR_CONFIDENCE` 警告。若差异所在行低于阈值，整体 verdict 至少为 `REVIEW_REQUIRED`；若无警告且存在差异，才为 `MISMATCH`；无差异且无警告为 `MATCH`。OCR 无可用文本时为 `OCR_FAILED` 或 `REVIEW_REQUIRED`，具体按引擎失败 / 空识别区分。


---

## 8. 可复现样本、S0 门禁与第一周验收

### 8.1 固定 S0 样本

样本图片必须由 `scripts/generate_fixtures.py` 用 Pillow 与随包 Noto Sans SC 字体生成。生成器、字体文件、参数、随机种子、PNG 字节哈希、期望文本和预期报告写入 `tests/fixtures/s0/manifest.json`。T005 完成后，manifest 中必须填入真实 SHA-256；不得把待生成哈希写成通过证据。

| Fixture ID | 固定输入图片内容 | 用户期望文本 | 固定预期输出 |
|---|---|---|---|
| `TP-S0-ZH-001` | 1200×480 PNG；白底黑字；绘制文本 `限时优` | `限时优惠` | 恰好 1 条 `MISSING_CHARACTER`；`expected_fragment=惠`；`recognized_fragment=""`；`expected_span=[3,4]`；bbox 指向该 OCR 文本行 |
| `TP-S0-ZH-002` | 1200×480 PNG；白底黑字；绘制文本 `新口上市` | `新品上市` | 恰好 1 条 `SUBSTITUTION`；`expected_fragment=品`；`recognized_fragment=口`；`expected_span=[1,2]`；bbox 指向该 OCR 文本行 |
| `TP-S0-NUM-001` | 1200×480 PNG；白底黑字；绘制文本 `￥28.00` | `￥28.80` | 恰好 1 条 `NUMERIC_CHANGE`；`expected_fragment=8`；`recognized_fragment=0`；`expected_span=[4,5]`；bbox 指向该 OCR 文本行 |
| `TP-S0-ZH-003` | 1200×480 PNG；白底黑字；绘制文本 `新客立减元` | `新客立减20元` | 至少 1 条 `MISSING_CHARACTER`；`expected_fragment=20`；`recognized_fragment=""`；bbox 指向匹配 OCR 文本行 |

坐标验收：生成器写入每个样本的预期文字区域 `target_region_xyxy`；OCR 返回 bbox 与该区域的 IoU 必须不低于 `0.80`，且不得越出图像边界。该区域只用于验证 OCR 行框定位，不冒充单字坐标。每个 fixture 的 `expected_output.json` 固定错误类型、文本片段、字符 span、verdict 和 bbox 范围规则。

### 8.2 300 张固定合成测试图片

第一周必须形成 300 张固定图片及 manifest：

- 100 张 clean：图片中的文字与期望文本一致，包含中文、英文、数字、标点和混排。
- 200 张 injected mismatch：70 张替换、70 张缺失、60 张数字变化。
- 所有图片由脚本生成；固定字体、画布尺寸、颜色、字号、布局、随机种子与生成器版本。
- 每张图片都有唯一 ID、图片 SHA-256、期望文本、注入操作、预期错误类型与预期坐标区域。
- 至少 60 张作为冻结盲测子集；在门禁前不得用盲测结果反复调参后再把它称作独立验收。盲测清单单独记录 SHA-256。

### 8.3 第一周验收指标

| 指标 | 定义 | 门槛 |
|---|---|---:|
| 固定合成样本数 | clean + injected 的唯一图片数 | 300 |
| 关键字符错误检测召回率 | 被正确检出的注入字符差异数 / 注入字符差异总数 | ≥95% |
| 单类召回率 | 替换、缺失、数字变化分别统计 | 每类 ≥90% |
| 清晰图片误报率 | 被判为 `MISMATCH` 的 clean 图片数 / clean 图片总数 | ≤8% |
| JSON schema 合法率 | 300 个报告均通过冻结 schema | 100% |
| OCR CER | `CER=(S+D+I)/N`，单独报告 | 记录值；不得替代检错召回率 |
| 外网访问 | 测试期间由 TextProof 发出的外部请求 | 0 |
| GPU provider | 实际 ONNX Runtime provider | 仅 CPU |
| 运行时间 | 1920×1080 合成图，预热后 30 次测量 P95 | ≤5s；记录 CPU / OS / 版本 |

OCR CER 与最终产品检错召回率是不同指标：OCR CER 衡量识别文本与图片真实文字的字符差异；检错召回率衡量 TextProof 是否发现用户输入期望文本与图片文字之间被注入的差异。不得用其中一个指标代替另一个。

### 8.4 S0 门禁定义与独立复核

S0 在 T001–T006 完成后执行。`verify_s0.py` 不能成为唯一证据。必须同时提供：

1. 固定图片、`manifest.json`、每张图片 SHA-256、期望文本和预期输出。
2. 生产比较模块的测试结果与独立 `oracle/reference_compare.py` 的逐案例 parity。
3. 独立复核者从干净工作树运行 `scripts/independent_verify.py --case TP-S0-ZH-001`，重新计算图片哈希、打开原始 PNG、读取期望文本、独立执行比较并逐字段核对输出；不得只运行 `verify_s0.py`。
4. 对四个固定样本分别核对错误类型、expected / recognized 片段、字符 span、bbox 范围和 verdict。
5. 300 样本指标报告、盲测子集哈希、测试日志、退出码、依赖锁哈希和 Git commit。
6. 网络封锁测试证据：OCR、API、UI 和 CLI 运行时均无外网访问；模型路径必须为本地文件。
7. 独立审查报告记录核查文件覆盖数、实际读取文件数、未读取文件和残余风险。

**S0 PASS 条件：** §8.3 全部硬门通过；四个固定样本满足 §8.1；独立 Oracle parity 100%；独立复核样本通过；网络访问 0；CPU-only；无真实图片、真人参与或外传。任何一项失败即 `S0_FAIL`，停止 T007–T014，不得降低阈值、删除失败 fixture 或把失败案例改为非阻断。修复后须提升 S0 run ID 并完整重跑。

---

## 9. 隐私、安全与数据生命周期

- 图片、期望文本、OCR 结果只在本机进程和浏览器内存中处理。
- 不写数据库、不写 `localStorage`、不上传日志、不调用遥测、不发外部 HTTP 请求。
- API 仅绑定 `127.0.0.1`；拒绝公网监听参数，或启动时强制校验 loopback。
- 浏览器预览使用 object URL；清除时调用 revoke 并清空输入、预览和报告。
- 服务端 stateless；每个请求结束后不保留跨请求图片或报告对象。
- 日志只记录请求状态、耗时、错误码和软件版本；不得记录图片字节、OCR 全文、期望文本、绝对路径或用户目录。
- JSON 导出由用户显式触发；导出文件会包含期望文本与 OCR 结果，UI 必须提示其可能包含敏感文字。
- 不保证操作系统 swap、崩溃转储或浏览器进程内存被安全擦除；清除功能只承诺应用不再持有可访问引用，不宣称密码学级内存擦除。
- 图片输入进行魔数、尺寸、像素数、解码异常和动画检查；不得信任文件扩展名。
- 禁止 shell 拼接、任意文件路径写入、外部 URL 图片加载或自动打开用户提供的 URL。

---

## 10. 许可证与第三方合规

### 10.1 项目许可证

TextProof 自有源码采用 MIT。仓库必须包含 `LICENSE`、`THIRD_PARTY_NOTICES.md`、依赖清单和模型资产清单。MIT 仅适用于 TextProof 自有代码，不自动覆盖依赖、OCR 模型、字典或字体。

### 10.2 已核实的第三方许可边界

| 资产 | 当前核实结果 | 使用边界 |
|---|---|---|
| RapidOCR 源码 | Apache-2.0 | 保留版权和许可证声明 |
| RapidOCR registry 中的 PP-OCR 模型 | RapidOCR 官方模型许可说明声明为 Apache-2.0；每个实际使用文件须对照 registry 与 SHA-256 | 记录模型名、来源 URL、哈希和许可证；不得把模型版权写成 TextProof 所有 |
| ONNX Runtime | MIT | 保留第三方声明 |
| PaddleOCR 上游项目 | Apache-2.0 | 只作为 RapidOCR 模型来源和技术先例 |
| Noto Sans SC | SIL Open Font License（OFL） | 仅用于合成测试图片；保留 OFL 与字体来源；记录字体版本和哈希 |
| FastAPI / Pydantic / Pillow / Uvicorn | 以发布时各自 LICENSE 文件为准 | T014 生成 SBOM / license report，逐项复核 |

模型 registry 也列出字典和字体等非模型资源；RapidOCR 模型许可声明明确这些资源不自动落入其模型 Apache-2.0 声明范围。T003 必须单独确认字典来源与许可证，不允许仅凭模型许可推断字典许可。

### 10.3 禁止复制的内容

不复制 ComfyUI、AnyText、Qwen-Image 或 Qwen-Image-Edit 的生成模型、工作流代码、权重、训练数据或 UI。只使用 RapidOCR / ONNX Runtime 作为 OCR 运行时，并按许可证要求保留声明。项目自己的比较算法、JSON schema、界面与合成样本由本项目独立实现。


---

## 11. 验证指标与最终验收

### 11.1 质量指标

- S0 300 样本门槛：见 §8.3。
- OCR CER：独立报告，不替代最终检错召回率。
- 字符错误检测召回率：≥95%；替换、缺失、数字变化每类 ≥90%。
- clean 图片误报率：≤8%。
- JSON schema 合法率：100%。
- 生产比较模块与独立 Oracle parity：100%。
- 离线网络访问：0。
- CPU provider：100%。
- 1920×1080 图片预热后 P95：≤5 秒。
- API/UI/CLI 对同一输入的 JSON 语义结果一致。

### 11.2 产品可用性验收

- 用户可在本机启动 UI，不需要注册、API key、云服务或 GPU。
- 输入格式、文本长度、文件大小和像素边界提示明确。
- 图片预览与 OCR 行框对齐；点击错误项可定位对应行框。
- 用户可修改期望文本后重跑。
- JSON 可下载并通过 schema 校验。
- 清除操作后 UI 不保留图片预览、输入文本和报告。
- CLI 可在无浏览器环境运行并输出相同 schema。
- 断网后应用仍能完成 OCR 与报告导出。

### 11.3 最终交付物

1. 完整源码及 `source.zip`。
2. 可安装 wheel 与目标虚拟机平台的离线 wheelhouse。
3. OCR 模型 / 字典资产、SHA-256 清单、许可证和来源说明。
4. `README.md`、`LICENSE`、`THIRD_PARTY_NOTICES.md`、`SECURITY.md`。
5. `requirements.lock`、Python 版本、环境探测日志和离线安装指南。
6. 300 张合成 fixture、manifest、expected outputs、盲测子集清单。
7. 单元 / 集成 / E2E / 隐私 / 离线测试日志。
8. S0 报告、独立 Oracle、独立复核报告。
9. UI 截图或演示录屏（只包含合成图片）。
10. `REVIEW_INDEX.md`、`REVIEW_PACK_XX.md`、文件覆盖清单、SHA-256 清单、Git bundle / 冻结 commit。
11. `RELEASE_MANIFEST.json`、`verify_release.py` 及其真实运行日志。

---

## 12. 样例输入与输出

### 12.1 输入

```text
image: fixtures/s0/TP-S0-ZH-001.png
expected_text: 限时优惠
```

固定样本图片中实际绘制的文字为 `限时优`。这是合成测试图片，不是真实用户图片。

### 12.2 预期结果

```text
verdict: MISMATCH
error_count: 1
error[0].type: MISSING_CHARACTER
error[0].expected_fragment: 惠
error[0].recognized_fragment: ""
error[0].expected_span: [3, 4]
error[0].bbox_scope: ocr_line
```

若 OCR 置信度低于 0.65，则该案例还必须带 `LOW_OCR_CONFIDENCE`，总体 verdict 改为 `REVIEW_REQUIRED`；不得为了让样例通过而忽略低置信度。

---

## 13. 关键风险与最大反对意见

| 风险 / 反对意见 | 影响 | 缓解与诚实边界 |
|---|---|---|
| OCR 把正确图像识别错 | 产生假阳性差异 | 报告称“期望文本与 OCR 输出差异”；显示置信度和原图行框；低置信时 `REVIEW_REQUIRED` |
| OCR 漏掉整行 | 可能误报整行缺失 | 记录 `MISSING_LINE`，坐标为 null；不伪造框 |
| 用户输入的换行与图片视觉行不同 | 行级对齐歧义 | UI 明示一行对应一个视觉行；提供 `AMBIGUOUS_ALIGNMENT` |
| 艺术字、低对比、纹理背景 | OCR 失败或误读 | 明确 MVP 边界；不承诺复杂艺术字和所有风格 |
| 多栏、旋转、竖排文字 | 阅读顺序不稳定 | 返回警告或要求复核；不强行给出确定性判定 |
| 模型权重、字典和字体许可不同 | 重新分发风险 | 分别记录模型 registry、字典来源、字体 OFL、SHA 和 NOTICE |
| “检测到差异”被误读为“图片一定写错” | 过度信任 | UI、README 和 JSON 明确 OCR 假设边界；不提供自动修图按钮 |
| 300 张合成样本无法代表真实图片 | 真实场景价值未知 | 只报告合成集结果；`USER_VALUE_NOT_MEASURED`；不宣称真实场景准确率 |

**最大反对意见：** “OCR 已经能读出图片文字，用户自己看一眼就够了。”  
TextProof 的回答不是再做 OCR，而是把用户已知的原文与图片实际识别结果逐项对账，自动给出差异类型、字符 span、图片行框和 JSON 证据。是否足以让真实用户长期使用仍未验证；本项目先验证算法、离线能力、误报和可复现性，不把合成测试包装成市场证明。

---

## 14. GitHub 传播与产品化边界

README 首屏演示建议固定为：

1. 左侧图片中实际显示 `限时优`。
2. 右侧期望文本为 `限时优惠`。
3. 一条红色差异卡显示缺失字符“惠”，并高亮对应 OCR 行框。
4. 展示 `textproof.report/v1` JSON。
5. 一条命令本地运行，不需要 API key。

可传播的价值是“生成之后自动核对图片里的字”，而不是宣称通用视觉理解。未来可评估 ComfyUI custom node、本地 REST API 和设计工具插件，但不属于本轮 MVP。任何集成不得破坏本地离线和不外传边界。

---

## 15. 构思报告来源核实记录（2026-11-25）

### 15.1 Star 数核实

Star 数仅表示 GitHub 生态关注度，**不代表实际使用量、付费需求、用户满意度或收购意向**。下列数字是检索时页面 / API 的近似快照，会随时间变化。

| 构思报告项目 | 本次核实值 | 来源与核实边界 |
|---|---:|---|
| ComfyUI | 148,460 | GitHub REST API `https://api.github.com/repos/Comfy-Org/ComfyUI`，2026-11-25 检索；许可证字段为 GPL-3.0 |
| Qwen-Image | 约 8.5k | GitHub 仓库页 `https://github.com/QwenLM/Qwen-Image`，页面显示 8.5k；精确 API 本轮未成功读取 |
| PPT Master | 79,848 | GitHub REST API `https://api.github.com/repos/hugohe3/ppt-master`，2026-11-25 检索 |
| OpenDesign | 约 109k | GitHub 仓库页 `https://github.com/nexu-io/open-design`，页面显示 109k |
| Docling | 约 71k | GitHub 仓库页 `https://github.com/docling-project/docling`，页面显示 71k |
| D3.js | 113,996 | 第三方 OSS Tanbou `https://oss-tanbou.dev/en/oss/d3-d3`，页面标注仓库数据截至 2026-11-23；本轮未从 GitHub API 独立读取，故标为第三方快照 |
| PaddleOCR | 93,139 | GitHub REST API `https://api.github.com/repos/PaddlePaddle/PaddleOCR`，2026-11-25 检索 |
| RapidOCR | 约 8.6k | GitHub 仓库页 `https://github.com/RapidAI/RapidOCR`，页面显示 8.6k |
| AnyText | 约 4.9k | GitHub 仓库页 `https://github.com/tyxsspa/AnyText`，页面显示 4.9k |

这些数字不用于证明 TextProof 需求，只说明图片生成、设计、文档与可视化生态具有社区关注。

### 15.2 构思报告 Issue 编号逐项核实

| 来源 | 本次核实结果 | 与 TextProof 的关系 |
|---|---|---|
| PptxGenJS #1544 | 已核实：`lang=en-US` 默认值会影响 PowerPoint 日文 kinsoku 换行，表格单元格未继承 table-level lang；Issue 于 2026-10-25 开启 | 支持 CJK 排版候选，不是图片文字检测证据 |
| PptxGenJS #1430 | 已核实：编辑 PPTX 图表嵌入工作簿后，货币 / 百分比格式丢失、零值显示为空；Issue 于 2025-11-21 开启 | 支持 ChartSync 候选，不是 TextProof 证据 |
| PptxGenJS #1531 | 已核实：category chart 嵌入 workbook 的 `table1.xml` `ref` 末尾出现多余 apostrophe，Keynote / Preview 可能丢弃图表；Issue 于 2026-08-25 开启 | 支持 ChartSync 候选，不是 TextProof 证据 |
| Docling #1203 | 已核实：多栏 PDF 阅读顺序混乱；Issue 于 2025-03-19 开启 | 支持 PDF 解析风险判断，不是 TextProof 证据 |
| Docling #2204 | 已核实：标准双栏 PDF 阅读顺序错误；Issue 于 2025-09-04 开启 | 同上 |
| Docling #3198 | 已核实：多栏 / 缩进 PDF 文本顺序反转、跨栏合并；Issue 于 2026-03-27 开启 | 同上 |
| Hermes Agent #91967 | 已核实：PowerPoint 默认正文占位框溢出导致渲染后文字被裁切；Issue 于 2026-08-22 开启 | 支持 PPTX 渲染验收候选，不是 TextProof 证据 |

### 15.3 与 TextProof 直接相关的公开先例

| 来源 | 已核实内容 | 借鉴与边界 |
|---|---|---|
| AnyText 论文 | `https://arxiv.org/abs/2311.03054`；研究多语言视觉文字生成与编辑，并讨论生成图像文字准确性挑战 | 证明生成图像文字是独立研究问题；TextProof 不复制扩散生成模型 |
| AnyText 仓库 | `https://github.com/tyxsspa/AnyText`；官方实现，Apache-2.0，页面显示约 4.9k stars | 借鉴文字框 / OCR 先验概念；不复制代码、权重或数据集 |
| Qwen-Image 技术报告 | `https://arxiv.org/abs/2508.02324`；报告复杂文字渲染与图像编辑训练流程 | 说明生成模型持续改善文字渲染；不意味着生成结果无需独立核对 |
| Qwen-Image 仓库 | `https://github.com/QwenLM/Qwen-Image`；Apache-2.0；仓库含 Qwen-Image-Edit 相关资料 | 作为生成 / 编辑先例；TextProof 不调用其模型 |
| Qwen-Image-Edit 模型卡 | `https://huggingface.co/Qwen/Qwen-Image-Edit`；官方模型卡标记 Apache-2.0，并说明支持中英文图片文字编辑 | 是生成后编辑方案，不是独立校验器；TextProof 不调用或打包该模型 |
| PaddleOCR | `https://github.com/PaddlePaddle/PaddleOCR`；Apache-2.0；2026-11-25 API 返回 93,139 stars | OCR 先例；TextProof 使用其生态衍生的 RapidOCR 模型路线，不复制完整文档解析平台 |
| RapidOCR | `https://github.com/RapidAI/RapidOCR`；官方文档支持中文 / 英文和离线部署；v3.10.0 发布于 2026-10-08 | 选为 OCR 适配器；固定模型、字典和 SHA；运行时禁用网络 |
| RapidOCR 安装文档 | `https://rapidai.github.io/RapidOCRDocs/main/en/install_usage/rapidocr/install/` | `rapidocr` 与 `onnxruntime` 安装；3.10.0 需显式安装推理引擎；本项目只用 CPU |
| RapidOCR 模型许可 | `https://rapidai.github.io/RapidOCRDocs/latest/en/model_licenses/` | registry 中模型声明 Apache-2.0；字典和字体不自动纳入模型许可，必须单独核验 |
| Noto Sans SC | `https://github.com/google/fonts/tree/main/ofl/notosanssc` | Google Fonts 元数据标记 OFL；只用于合成测试图片，需保留 OFL |

### 15.4 未核实与不作扩张

- 构思报告中的 Star 数均是时间敏感快照，不将其作为用户需求证据。
- Qwen-Image 的精确 Star 数本轮只核实到 GitHub 页面四舍五入的 `8.5k`，未成功读取其 GitHub REST API 精确计数。
- D3.js 的 `113,996` 来自第三方数据页面，不是本轮 GitHub API 直接读取值。
- 没有证据证明上述 Issue 在当前最新发布版仍未修复；本书只把它们作为特定时间的公开故障报告。
- 没有找到能证明 TextProof 真实用户频率、真实图片检错率或付费意愿的研究；这些仍是待验证假设。
- 没有核实任何企业的收购意向。

---

## 16. 参考网址清单

1. RapidOCR：<https://github.com/RapidAI/RapidOCR>
2. RapidOCR 安装：<https://rapidai.github.io/RapidOCRDocs/main/en/install_usage/rapidocr/install/>
3. RapidOCR 使用：<https://rapidai.github.io/RapidOCRDocs/main/en/install_usage/rapidocr/usage/>
4. RapidOCR 模型许可：<https://rapidai.github.io/RapidOCRDocs/latest/en/model_licenses/>
5. PaddleOCR：<https://github.com/PaddlePaddle/PaddleOCR>
6. PaddleOCR Quick Start：<https://www.paddleocr.ai/main/en/quick_start.html>
7. AnyText 论文：<https://arxiv.org/abs/2311.03054>
8. AnyText 仓库：<https://github.com/tyxsspa/AnyText>
9. Qwen-Image 技术报告：<https://arxiv.org/abs/2508.02324>
10. Qwen-Image 仓库：<https://github.com/QwenLM/Qwen-Image>
11. Qwen-Image-Edit 模型卡：<https://huggingface.co/Qwen/Qwen-Image-Edit>
12. ComfyUI：<https://github.com/Comfy-Org/ComfyUI>
13. PPT Master：<https://github.com/hugohe3/ppt-master>
14. OpenDesign：<https://github.com/nexu-io/open-design>
15. Docling：<https://github.com/docling-project/docling>
16. D3.js：<https://github.com/d3/d3>
17. PptxGenJS #1430：<https://github.com/gitbrent/PptxGenJS/issues/1430>
18. PptxGenJS #1531：<https://github.com/gitbrent/PptxGenJS/issues/1531>
19. PptxGenJS #1544：<https://github.com/gitbrent/PptxGenJS/issues/1544>
20. Docling #1203：<https://github.com/docling-project/docling/issues/1203>
21. Docling #2204：<https://github.com/docling-project/docling/issues/2204>
22. Docling #3198：<https://github.com/docling-project/docling/issues/3198>
23. Hermes Agent #91967：<https://github.com/NousResearch/hermes-agent/issues/91967>
24. Noto Sans SC：<https://github.com/google/fonts/tree/main/ofl/notosanssc>

---

**项目书结论：** TextProof 的产品边界、输入输出契约、核心算法、S0 样本和验收门槛已冻结为 `1.0.0`。当前状态为 `SPEC_FROZEN / NOT_IMPLEMENTED`。只有四份规格文件归档、Muse 完成技能盘点并按实施计划派工后，才能进入施工；产品最终是否接受仍以独立终审和真实证据为准。
