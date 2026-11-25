# P033 规格核对（Muse 独立核对，2026-11-25 ~01:51 GMT）

- 核对对象：~/workspace/p033-textproof/ 四份文件（从 ChatGPT 对话下载，SHA-256 与 GPT 声明一致；Drive 副本 MD5 与本地一致，见下）
- 规格版本：1.0.0，状态 SPEC_FROZEN / NOT_IMPLEMENTED
- **结论：PASS，冻结。进入施工（T001 门禁先行）。**

## 文件一致性（实测，非 GPT 自述）

| 文件 | 本地字节 | SHA-256（本地实测） | Drive 大小 | Drive MD5 | 一致 |
|---|---|---|---|---|---|
| PROJECT_BOOK.md | 44,552 | 0fc4ef3b…77dfc | 44,552 | 817ce3c9…1183 | 是 |
| PROJECT_BOOK.docx | 64,339 | 4b788b1c…1aba7 | 64,339 | d2d8e9b6…591f | 是 |
| IMPLEMENTATION_PLAN.md | 35,772 | 2d2ac3f3…13c2 | 35,772 | 8c1ea769…02d9 | 是 |
| IMPLEMENTATION_PLAN.docx | 58,745 | c6d2b3a6…385 | 58,745 | 3cbb7f0e…cb09 | 是 |

Drive 文件夹：P033-textproof（id 1ovRjSwX2eioP8XGzZa_I_arpauOsrRBr），四份文件 id 与 GPT 贴回的链接一致。

## DOCX ↔ MD 结构核对（实测）

- PROJECT_BOOK.docx：Title 1 + Heading 66 = 67 个样式段落；表格 14；章节标题与 MD 的 67 个 `#` 标题逐项同序（§0–§16）。
- IMPLEMENTATION_PLAN.docx：Title 1 + Heading 39 = 40 个样式段落；表格 4；章节标题与 MD 的 40 个 `#` 标题逐项同序（§0–§12，含 T001–T014）。
- GPT 回复称“标题 67 / 40”：计数含 Title 段落，与实测一致，无缺节。

## 规格内容核对（全文已读两份 MD）

- 冻结契约（书 §0.2）：输入 PNG/JPEG/WebP、输出 textproof.report/v1、本地 OCR + 加权编辑距离、离线 CPU-only、合成数据、88h 上限；变更须 ADR + 升版 + Owner 批准。
- S0 门禁（书 §8.4）：四固定样本（TP-S0-ZH-001/002、TP-S0-NUM-001、TP-S0-ZH-003）各有固定预期输出；独立 Oracle parity 100%；独立复核者从干净工作树重跑；网络 0、CPU-only；任一硬门失败即 S0_FAIL，T007–T014 停。验收标准逐条锚定章节号（计划 T006 逐项标注规格锚点）。
- 任务表（计划 §3）：**T001–T014，共 14 项**；工时 4+5+8+8+7+4+10+8+6+5+7+4+6+6 = **88h**。
- 证据核实（书 §15）：Star 数逐项重核并标注来源（ComfyUI 148,460 API、PPT Master 79,848 API、D3.js 113,996 标为第三方快照、Qwen-Image 8.5k 标为页面四舍五入）；Issue 逐项核实并给出来源与开启日期（PptxGenJS #1544/#1430/#1531、Docling #1203/#2204/#3198、Hermes Agent #91967 = NousResearch/hermes-agent）；明确写“无收购意向证据”“无真实用户频率/付费意愿证据”；USER_VALUE_NOT_MEASURED 保留。
- 诚实边界：性能阈值是验收目标不是实测成绩（书 §0.3）；OCR 准确率与检错召回率是两个指标（书 §8.3）；坐标只到 OCR 行级，不冒充单字框（书 §4.6、§7.5）。
- 零真人、MIT、离线、禁 GPU/收费 API/外传：书 §0.2、§2.2、§9 与计划 §0.2 一致。

## GPT 自述中的一处错误（已纠正，不影响冻结）

- GPT 第 2 条回复表格称实施计划为“T001–T025”；实际文件为 T001–T014，书 §8.4 与计划 §1/§3 均一致。**以文件内容为准。**已记录，后续终审不得引用 T001–T025。

## 施工记录

- T001 PASS（主聊天亲自核对 2026-11-25 ~02:04 GMT）：基线 commit 394d507（唯一 1 个 commit）；四份规格文件 SHA 与冻结值 4/4 一致，未动；requirements.lock 37 个包（构建者报告误写 33 个）、753 个 SHA-256 哈希；rapidocr==3.10.0、onnxruntime==1.32.0（CPU，providers 仅 Azure + CPU，无 CUDA/TensorRT）、Pillow 11.3.0、FastAPI 0.165.0、Uvicorn 0.54.0、Pydantic 2.14.4、pytest 8.4.2；无 onnxruntime-gpu。
- **包名澄清（非契约变更，不走 ADR）**：规格 §6.2 只写版本号 3.10.0、未写包名；实测 rapidocr-onnxruntime 最高仅 1.4.4，rapidocr 最新版即 3.10.0（2026-10-08，与规格 §15 一致）。用 rapidocr==3.10.0 满足冻结版本号，不是换产品、不改规格，记一笔即可。
- T002 + T003 已派（T002 输入契约、T003 RapidOCR CPU 适配，均只依赖 T001；T004 等两者接口冻结）。

- DOCX 未做逐页视觉审阅（只做了结构核对：标题、表格、章节顺序）。
- FACTORY_INDEX.md 登记 P033 为 SPEC_FROZEN / NOT_IMPLEMENTED（规格书 §10 要求；核对后执行，先拉 Drive 最新版再合并）。
- 施工：T001 门禁先行；S0 未通过则 T007–T014 全部 BLOCKED。
