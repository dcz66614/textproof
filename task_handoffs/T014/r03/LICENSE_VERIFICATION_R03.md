# R-03 许可核实记录 — 识别字典 ppocrv6_dict.txt（T014）

- 任务：P033 T014，审查发现 R-03（T012，REVIEW_FINDINGS.md §R-03）
- 核实日期：2026-11-25（访问时间均为当日 12:25–12:26 GMT）
- 核实人：T014 施工员（本轮重新核实，非复述 T003 结论）
- 判定：**UNVERIFIED（维持）——未找到可明确、无歧义证明该字典文件可再分发的来源**，因此走合规打包方案（本地重建，见 `scripts/setup_dictionary.py` 与 `THIRD_PARTY_NOTICES.md` §4）。

## 核实对象

| 项 | 值 |
|---|---|
| 文件 | `assets/ocr/dictionaries/ppocrv6_dict.txt`（18,708 行，74,947 B） |
| SHA-256 | `b5f2bfe2bdd9448429e3e82b51c789775d9b42f2403d082b00662eb77e401c5d` |
| 上游 | https://github.com/PaddlePaddle/PaddleOCR/blob/main/ppocr/utils/dict/ppocrv6_dict.txt |
| 注册来源 | https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.10.0/paddle/PP-OCRv6/rec/PP-OCRv6_rec_small/ppocrv6_dict.txt |

内容一致性（T003 已证实，本轮重建时再次证实）：注册下载件、上游文件、模型内嵌 `character` 元数据三方字节一致；从模型元数据重建的文件与冻结文件逐字节相同（见 TASK_RESULT.md）。

## 查到的来源与结论

### S1 — RapidOCR 官方模型许可页（决定性：明确排除字典）

- URL：https://rapidai.github.io/RapidOCRDocs/latest/en/model_licenses/
- 访问：2026-11-25 12:25 GMT（页面抓取时间戳当日）
- 关键原文（§2 Scope of this notice）：
  > "The registry also records non-model resources, including recognition dictionaries (`dict_url`) and fonts (`fonts`). These resources are not model artifacts and are not covered by the Apache-2.0 declaration in this notice; they remain subject to their own applicable terms."
- 同页 §6 重申：
  > "The `dict_url` and `fonts` entries in the registry are resources, not models, and are excluded from this declaration."
- 结论：RapidOCR 的 Apache-2.0 声明**明确不覆盖**该字典。这是唯一一个针对字典本身发声的权威来源，而它的表态是否定的。不得凭模型许可推断字典许可。

### S2 — PaddleOCR 上游字典文件本身（无许可头）

- URL：https://github.com/PaddlePaddle/PaddleOCR/blob/main/ppocr/utils/dict/ppocrv6_dict.txt（raw 视图同日抓取）
- 访问：2026-11-25 12:26 GMT
- 所见：文件为纯字符表，首行 `!`，每行一个字符，共 18,708 行；**无任何许可头、版权声明或许可说明**。文件页标注 "18708 lines (18708 loc) · 73.2 KB"，与本地文件一致。
- 结论：文件本身不提供许可依据。

### S3 — PaddleOCR 仓库级 LICENSE（通用文本，未指明覆盖字典文件）

- URL：https://github.com/PaddlePaddle/PaddleOCR/blob/main/LICENSE
- 访问：2026-11-25 12:26 GMT
- 所见：标准 Apache License 2.0 全文，版权行 "Copyright (c) 2016 PaddlePaddle Authors"；"Work" 定义为 "the work of authorship, whether in Source or Object form, made available under the License, as indicated by a copyright notice"，附录要求 "attach the following boilerplate notice" 以将许可应用于具体作品——而字典文件无此种声明。
- 结论：仓库级存在 Apache-2.0 文本是事实，但它**没有明确、无歧义地说明覆盖 `ppocrv6_dict.txt` 这一数据文件**。在 S1 已明确把字典排除在下游 Apache-2.0 声明之外的情况下，仅凭仓库级 LICENSE 推断覆盖字典，不满足“明确、无歧义”的判定标准。**不采纳为核实依据。**

### S4 — 字典文件的 git 历史（无许可相关提交）

- URL：https://github.com/PaddlePaddle/PaddleOCR/commits/main/ppocr/utils/dict/ppocrv6_dict.txt
- 访问：2026-11-25 12:26 GMT
- 所见：仅有一条提交记录："[Feat] Support PP-OCRv6 (#18104)"（commit b03f464）；无任何许可、版权相关的提交说明。
- 结论：历史中无许可依据。

### S5 — 第三方转述（不采纳：非权威来源）

- 检索 "`ppocrv6_dict` license redistribution character dictionary"（2026-11-25）得到若干第三方页面把字典标为 Apache-2.0，例如：
  - `onnxocr-ppocrv6` PyPI 页（"Models are licensed under Apache-2.0"，轮子内含字典）；
  - DeepWiki 生成的 `ftcvictory/local-OCR` 与 `hl540/ocr` 许可页（把字典列为 Apache 2.0 (PaddleOCR)）。
- 结论：**均不采纳**。这些是第三方再分发者或自动生成的文档自己的断言，不是权利人或上游项目针对该字典文件的许可声明；它们本身正是“凭仓库级许可推断”的做法，不能作为推断成立的证据。采纳它们等于循环论证。

### S6 — 模型卡片许可（覆盖对象是模型权重，不是字典）

- 检索确认：PaddlePaddle 在 Hugging Face 的 PP-OCRv6 模型卡片（如 `PP-OCRv6_small_rec`）许可字段为 `apache-2.0`；RapidOCR 许可页 §3 同样引用这些卡片为模型权重的证据。
- 结论：覆盖对象是模型权重/ONNX 表征，未提及字典文件；不能外推到字典。

## 最终判定

**字典许可仍为 UNVERIFIED。** 没有任何来源明确、无歧义地证明 `ppocrv6_dict.txt` 可作为单独文件再分发；唯一针对字典发声的权威来源（S1）明确将其排除在 Apache-2.0 声明之外。

因此：

1. `THIRD_PARTY_NOTICES.md` §4 的许可栏**继续写 UNVERIFIED**，不得写成 Apache-2.0。
2. 公开分发的产物（GitHub 快照树、source.zip、wheel）**不得包含** `assets/ocr/dictionaries/ppocrv6_dict.txt` 这个单独文件。
3. 用户侧改用本地重建：`scripts/setup_dictionary.py` 仅从本机已随包分发的、Apache-2.0 覆盖的 `PP-OCRv6_rec_small.onnx` 模型文件内嵌 `character` 元数据中提取字符表，在本地重建字典并校验 SHA-256 与行数。重建产物与冻结文件逐字节一致（本轮实测），适配器的启动交叉校验照常通过。
4. 合规依据（书面）：重建行为本身不分发字典文件——它是在用户本机上对已合法持有的模型文件（Apache-2.0 覆盖，含内嵌字符表）做机械格式转换（元数据 → 文本文件），且模型文件的再分发本身在许可范围内；转换结果不进入任何公开产物。脚本不联网、不下载、不接触任何远程来源。
5. 残留风险（诚实记录）：该字符表作为数据是否独立享有版权、以及从模型元数据提取是否在所有法域都无争议，未获法律意见；本方案消除的是“公开再分发未核实许可文件”这一已确认风险，而非给出法律定论。若将来上游给出字典文件的明确许可声明，应重新核实并更新 §4。

## 判定标准（供复核者）

按任务书第 1 步：只有来源能“明确、无歧义地证明该字典可再分发”（例如仓库级 Apache-2.0 明确覆盖全部文件、或字典文件本身带许可声明）时，方可改为已核实。本轮查到的最强反向证据是 S1 的明确排除；最强正向证据只是仓库级 LICENSE 的存在——它未指明覆盖范围，且被 S1 的排除声明所抵消。故不满足改判标准。
