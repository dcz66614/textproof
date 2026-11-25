# P033 TextProof — 终审第 1 轮（GPT 回复归档）

- 终审对话：https://chatgpt.com/g/g-p-6ade5013e8ec8191b55dca46c27772e1-agent-project-automatic/c/6b072e69-b2ec-83ed-8848-22a0037a1125（新对话，标题“终审报告核验”）
- 发送：2026-11-25 18:52 GMT，模型 GPT-6.2 + Extra High（发送前手动核实：模型选择器显示 6.2，思考 Extra High，4 of 4，滑块最右；发送框显示 "6.2 Extra High"）
- 附件：Drive 插件 14 个芯片（冻结文件夹 FREEZE_93d1b7c_T014_2026-11-25 + 13 个单独文件）
- GPT 工作时长 56m 28s，回复完成约 2026-11-25 19:53 GMT
- 结论：FINAL_VERDICT: FAIL（P0 0 / P1 3 / P2 2 / P3 2）
- 冻结对象：commit 93d1b7c65036bb16f596117f26a48f6ee62f99e1，source.zip SHA-256 9c2305ed715e0e74e459e73348418a7011890a474af04cdc4de451a456d2c235，wheel SHA-256 9c880b88e401c618c91426c3009b3153c7da682fe461e42eb9802a55f33372a1

注意：本次浏览器任务中有两次误发（均作废，非本次提交）：约 17:34 GMT 误发不完整草稿（新对话 c/6b071c42-a308-83ed-a924-9d7a85e03310，GPT 思考后被点 Stop 停止）；约 17:41 GMT 误发仅含 §2 标题的消息（新对话 c/6b071dbf-a6c4-83ed-b2dc-93478ac67246，GPT 回复“请继续发送第 2 节的具体规格条目……”）。有效提交仅为上述 c/6b072e69 对话。

---

以下为 GPT 回复全文（按浏览器任务报告照录）：

P033 TextProof｜终审 R1

审查对象：FREEZE_93d1b7c_T014_2026-11-25

本轮以冻结 commit 93d1b7c65036bb16f596117f26a48f6ee62f99e1 为目标身份，不把 T014 施工方、两轮独立复审或主聊天此前的 PASS 当作本轮终审结论。

已实际定位并读取指定 Google Drive 冻结归档目录。目录中已找到：

source.zip

textproof-1.0.0-py3-none-any.whl

RELEASE_MANIFEST.json

SHA256SUMS.txt

SBOM_LICENSES.md

REVIEW_PACK_T014R3.md

两轮独立复审报告

S0 报告及主聊天裁决

T014 主聊天裁决

冻结归档说明

Drive 文件元数据显示，source.zip 为 512,109,756 字节，wheel 为 27,176,403 字节。这只是文件存在性及大小核对，尚不代表其 SHA-256 已经通过独立验证。

一、已独立完成的产物身份核验
SHA-256 核对通过

| 产物 | 独立计算结果 | 对照声明 |
| source.zip | 9c2305ed715e0e74e459e73348418a7011890a474af04cdc4de451a456d2c235 | 一致 |
| wheel | 9c880b88e401c618c91426c3009b3153c7da682fe461e42eb9802a55f33372a1 | 一致 |

另外核实：

source.zip：766 个 ZIP 条目，其中 699 个文件、67 个目录，无重复路径。

wheel：32 个条目，包含 3 个 ONNX 模型；没有识别字典文件。

wheelhouse：归档内确有 37 个 wheel。

RELEASE_MANIFEST.json、SHA256SUMS.txt、SBOM_LICENSES.md 的文件本身 SHA-256 均已独立计算。

以上证明冻结包和主要发布产物的身份数字真实吻合，但还不能证明其内部所有文件与清单一致。

二、发现一项规格版本对应关系问题
P1 候选阻断

我将 Drive 根目录实际下载的 PROJECT_BOOK.md 与 source.zip 内同名文件逐字节比较：

| 项目 | Drive 冻结规格 | source.zip 内 |
| 文件大小 | 44,552 B | 46,114 B |
| SHA-256 | 0fc4ef3b... | 8a2b6e56... |
| 字节一致 | 否 | 否 |

差异涉及七处 T013 文字澄清，包括：

尾随换行的行数计算规则。

OCR 文本框的纵向行聚合规则。

字符混淆对的具体集合。

保留警告码的触发边界。

verify-s0 的独立退出码说明。

歧义对齐及错误排序规则。

OCR_EMPTY 的 verdict 映射。

这里存在一个需要认真处理的问题：R3 审查包将 Markdown 描述为包含七处澄清、DOCX 未同步；但我直接读取的 Drive 根目录 Markdown 实际上也缺少这些澄清。

因此，当前不能简单地把 U-02 当成单纯的 DOCX 排版同步问题。必须明确哪份 Markdown 才是最终冻结契约，并确认源包与它一致。

三、算法、S0 与实际运行证据

这一部分我没有只接受报告中的 PASS，而是从 source.zip 中重新提取数据，独立计算了关键指标。

1. S0 指标独立复算
核心正确性指标复算通过

| 指标 | 独立复算结果 | 规格门槛 | 结果 |
| 注入字符检错召回率 | 201/201 = 100% | ≥95% | PASS |
| 替换召回率 | 100% | ≥90% | PASS |
| 缺失召回率 | 100% | ≥90% | PASS |
| 数字变化召回率 | 100% | ≥90% | PASS |
| Clean 误报 | 0/100 = 0% | ≤8% | PASS |
| JSON Schema | 300/300 | 100% | PASS |
| IoU 最小值 | 0.82868 | ≥0.80 | PASS |
| IoU 均值 | 0.93803 | ≥0.90 | PASS |
| Oracle parity | 300/300 | 100% | PASS |

具体独立操作：

对 300 个原始 PNG 重新计算 SHA-256，与 manifest 对比：300/300 一致。

对 300 条 live OCR 结果重新统计注入字符检测情况：201/201。

独立使用 JSON Schema Draft 2020-12 验证 300 份报告：300/300 合法。

实际执行 python scripts/parity_check.py --manifest tests/fixtures/s0/manifest.json：固定样本 300/300 parity，边缘案例 14/26。

因此，S0 的主要正确性指标不是单纯复述 Muse 的结果，而是得到我自己的计算支持。

2. 算法与独立 Oracle

实际检查了：

weighted_edit.py

align_lines.py

line_order.py

classify.py

report.py

report_schema.py

oracle/reference_compare.py

重点检查了：

加权编辑距离的替换、缺失、额外字符代价。

十进制精确比较与浮点边界问题。

多行单调对齐和并列最优处理。

第二优对齐及歧义判断。

差异类型与字符区间映射。

bbox 关联和报告字段完整性。

Oracle 与生产实现的代码路径隔离。

没有发现已检查算法模块中的 P0 级缺陷。T013 的 R-01 精确十进制修复在当前源码中确实存在。

3. 隐私与运行边界

检查了 FastAPI、CLI、OCR Adapter、图片加载器和 UI：

| 检查项 | 结论 |
| FastAPI loopback 限制 | 源码有明确限制 |
| ONNX Runtime provider | 明确使用 CPUExecutionProvider |
| UI 外部网络访问 | 未发现 |
| localStorage / IndexedDB 持久化 | 未发现 |
| 用户文本写入日志 | 已检查的路径未发现 |
| 图片持久化 | 未发现产品运行路径上的持久化 |
| 字典文件随发行包分发 | 没有 |
| 网络隔离运行 | 有 Muse 的 unshare -n 实际运行记录 |

另外实际查看了两张 UI 截图，确认不是静态设计稿，而是有真实差异高亮、缺字提示和报告面板的运行界面。

差异高亮演示参考
缺字检测演示参考

上面两张图片仅为视觉示意，不是本次读取的项目截图；实际验收依据是归档中的 ui_mismatch_highlight.png 和 ui_missing_line.png。

4. 我实际执行的测试范围
216 passed

独立运行：

Bash
PYTHONPATH=src python -m pytest -q \
  tests/unit/test_core \
  tests/unit/test_image_loader.py \
  tests/unit/test_validate_report_schema.py \
  tests/oracle/test_reference_compare.py

结果：216 passed。

完整 495 项 pytest，我没有在自己的执行环境重新运行。原因是当前容器为 Python 3.13，而项目锁定环境为 Python 3.12.3，且当前容器没有对应的 ONNX Runtime 环境。

因此，495 passed 是我读取到的 Muse/独立审查日志证据，不冒充 GPT 自己重新运行的结果。

四、P2 与 P3 非阻断发现
P2：S0 报告与当前证据没有完全同步

有三处需要修正。

第一，边缘案例数量。

S0_REPORT.md 记录：13/26。

当前源码实际执行 parity_check.py：14/26。

T013 的交接记录也采用 14/26。

这不是硬门禁失败，但 S0 报告应与最终代码同步。

第二，1200×480 计时数据。

S0_REPORT.md 记录：

P50：1.33s

P95：1.77s

Max：3.13s

但我从 live_ocr_results.jsonl 重新计算，并与 s0_metrics.json 对照，得到：

P50：2.1235s

P95：2.7147s

Max：3.2683s

需要明确这两组数据分别对应什么运行记录，不能同时作为同一轮结果。

第三，T014 第二轮是否重跑 S0。

R1 报告确实记录了 verify_s0.py --force-live 重跑。

但 R2 报告明确表示本轮没有重跑 S0，因为 R3 相对上一版本只改了 README。

所以用户消息中"两轮独立复审均重跑 S0"的描述不准确。由于功能代码没有变化，这一点本身不阻断交付。

P2：多行中文海报的端到端覆盖不足

我独立统计了 300 个 live OCR 结果：

300 张均为单行 OCR

虽然生产代码支持多行对齐，合成行对齐测试也通过，但 300 张 S0 图片没有覆盖真实多行 OCR 输出。

另一个证据是 1920×1080 四行性能样本：OCR 将两个空格省略，并将「减」识别成「減」，最终产生 MISMATCH。

此外，NUM-001 出现了：

￥（U+FFE5）→ ¥（U+00A5）

从字符级精确比较角度，保留该差异是合理的；但对电商价格海报用户，它会形成额外误报。

这些不是冻结规格明确规定的阻断门槛，但建议下一版本增加多行 clean 样本和货币符号样本。

P3：已披露的许可证与归档问题

RapidOCR 字典：

官方资料明确区分模型许可和字典许可。字典不自动包含在 Apache-2.0 授权范围内。
RapidOCR Documentation

本项目没有把字典文件放入发行包，采用从本地 ONNX 元数据重建的方式，并明确保留 UNVERIFIED 状态。这个处理是诚实的，暂不阻断发行。

OmegaConf 2.4.0：

wheel 的 METADATA 没有许可字段，但上游 PyPI 将该版本列为 BSD-3-Clause。
PyPI

建议补充 SBOM 记录，不属于当前阻断问题。

512MB source.zip：

嵌套历史 release 文件导致体积较大。归档说明已经披露，文件完整性没有因此失效。未来干净快照应排除历史 release/ 嵌套。

五、正式验收结果

| 验收维度 | 结论 |
| 产品核心算法 | 已检查部分通过 |
| S0 正确性指标 | 独立复算通过 |
| JSON Schema | 通过 |
| Oracle parity | 通过 |
| OCR 模型与 CPU 限制 | 通过 |
| 隐私和离线边界 | 代码检查及归档日志支持通过 |
| CLI / API / UI | 关键路径及截图证据通过 |
| wheel 与源码一致性 | 通过 |
| wheelhouse 与锁文件 | 通过 |
| 开源许可证 | 主体合规，两个已披露事项非阻断 |
| 四份冻结规格一致性 | 不通过 |
| 最终源码审查索引 | 证据缺失 |
| 最终版本性能门槛 | 证据不足 |

六、终审裁决

项目：P033 TextProof

发现统计：

| 级别 | 数量 | 是否阻断 |
| P0 | 0 | — |
| P1 | 3 | 是 |
| P2 | 2 | 否 |
| P3 | 2 | 否 |

RELEASE VERDICT

PROJECT_ID: P033-TextProof

RELEASE_SHA256_OR_COMMIT:

source.zip SHA-256：9c2305ed715e0e74e459e73348418a7011890a474af04cdc4de451a456d2c235

wheel SHA-256：9c880b88e401c618c91426c3009b3153c7da682fe461e42eb9802a55f33372a1

声明的冻结 commit：93d1b7c65036bb16f596117f26a48f6ee62f99e1

commit 声明已读取，但由于缺少可用 Git 对象库或 Git bundle，未能独立重新证明该 commit 与归档之间的关系。

COVERAGE:

699 个 source.zip 文件已枚举并通过 ZIP CRC 检查。

300/300 S0 PNG 文件 SHA-256 独立核对。

26 个关键源码、配置和验证文件直接检查。

当前 R3 REVIEW_INDEX 未取得，不能证明最终 699 个文件均有对应审查记录。

BLOCKERS:

P1-01： 冻结 PROJECT_BOOK.md 的 Drive 根目录版本与 source.zip 内版本不一致，七处规范澄清未进入根目录 Markdown 和 DOCX。必须统一四份规格的权威版本。

P1-02： R3 REVIEW_INDEX.md 缺失。manifest 期待的 SHA-256 为 7ebbc997...，source.zip 中实际是旧版索引。必须提供当前索引并证明其覆盖最终 commit 的全部文件。

P1-03： §8.3 的 1920×1080、30 次运行、P95 ≤5s 是冻结规格硬门槛。现有 3.817s 性能报告来自 T013 核心算法修改之前，必须在最终版本重新测量。

NON_BLOCKING:

P2：S0 报告中的诊断计时与当前保存的 metrics 不一致。

P2：多行 OCR 端到端覆盖不足，以及 ￥/¥ 的 OCR 混淆。

P3：source.zip 历史 release 嵌套。

P3：OmegaConf SBOM 许可字段缺失；RapidOCR 字典许可继续明确标注 UNVERIFIED。

Windows 实机未测试；当前交付只证明 Linux 环境。

ACCEPTANCE_EVIDENCE:

source.zip 和 wheel 的声明 SHA-256 独立核对一致。

SHA256SUMS 39/39 项通过。

wheelhouse 37/37 与锁文件版本及哈希对应。

wheel 中 26 个产品文件与源码对应内容一致。

S0 检错召回率、clean 误报率、JSON Schema、IoU、Oracle parity 均独立复算通过。

216 项独立纯核心测试通过。

Muse 归档的完整 pytest 495 passed 日志已读取，但未在本容器独立重跑。

REQUIRED_NEXT_ACTIONS:

以 source.zip 中包含七处 T013 澄清的 Markdown 为建议权威版本，同步 Drive 根目录 PROJECT_BOOK.md 和 DOCX，并重新核对四份文件。

将当前 R3 REVIEW_INDEX.md 实际文件上传到 FREEZE_93d1b7c_T014_2026-11-25，确认其 SHA-256、699 文件覆盖和 commit 锚点；同时提供 Git bundle 或可读取的 Git 仓库对象。

在最终冻结代码上重新执行：

Bash
python scripts/benchmark_perf.py \
  --out task_handoffs/T011/perf_measurements.json \
  --summary PERFORMANCE_REPORT.md \
  --image-out tests/fixtures/performance/perf_1920x1080.png

确认 30 次预热后测量的 P95 ≤5s，并归档原始结果。
4. 修订 S0 报告中的诊断计时和 14/26 边缘案例数据，明确哪些记录属于历史轮次。

最终裁决：当前不能交付。

FINAL_VERDICT: FAIL
