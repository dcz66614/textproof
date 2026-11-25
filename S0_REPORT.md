# S0 报告 — P033 TextProof（字证）

> **S0 VERDICT: PASS**
>
> 9 项门禁逐项通过（见 §1）。本报告是 T006 的 S0 结论记录；最终 PASS
> 由主聊天复核后裁决。报告顶部先给结论，下面逐项给证据、给两项书面裁定、
> 给门禁范围之外的发现（§7），不把发现藏进附录。

- S0 run ID：`S0-20261125-run2`（权威证据轮次；run1 因门禁脚本自身的检查
  bug 退出 1，见 §8）
- 报告日期：2026-11-25（GMT；证据轮次 run2 完成 ~06:17 GMT）
- 输入 commit：`732f07e188770460ef4ba3551b03691987118dcc`（master：T001–T005
  与独立 Oracle 均已合入）
- 输出 commit：见 `task_handoffs/T006/TASK_RESULT.md`（本报告提交后由外部读取）
- 分支：`t006-s0-gate`（worktree `~/workspace/p033-textproof-t006`）
- 规格版本：`1.0.0`（PROJECT_BOOK.md / IMPLEMENTATION_PLAN.md 均未修改）

## 1. 门禁逐项结果（T006 任务卡 9 项）

| # | 门禁项（规格锚点） | 结果 | 证据位置 |
|---|---|---|---|
| 1 | Oracle 不 import 生产比较模块；独立会话、不同代码路径（§8.4） | **PASS** | §2；`parity_report.json`；Oracle 自测 43 通过 |
| 2 | 生产模块与 Oracle 在固定字符/行 fixture 上 100% parity（§8.4） | **PASS** | §3；`parity_report.json`：300/300 |
| 3 | 四个固定案例逐项核对 §8.1 类型、片段、span、bbox 规则、verdict（§8.1） | **PASS** | §4；`verify_s0.py` 输出 [3] 四行全 PASS |
| 4 | 300 样本检测召回率 ≥95%；替换/缺失/数字变化每类 ≥90%（§8.2–§8.3） | **PASS** | §5；召回率 **100.00%**，每类 100.00% |
| 5 | 100 张 clean 图片误报率 ≤8%（§8.2–§8.3） | **PASS** | §5；误报率 **0.00%**（0/100） |
| 6 | JSON schema 合法率 100%（§5.1–§5.3、§8.3）；OCR CER 独立报告，不替代检错召回率 | **PASS** | §5；合法率 **100%**（300/300）；CER **0.0008** 单独报告 |
| 7 | 网络访问 0；ONNX Runtime provider 仅 CPU（§6.1–§6.2、§8.3、§9） | **PASS** | §7；全程 `unshare -n` 下运行 exit 0；三模型均为 `CPUExecutionProvider` |
| 8 | `independent_verify.py` 从原始 PNG、manifest、expected output 独立复核 TP-S0-ZH-001；不只调用 `verify_s0.py`（§8.1、§8.4） | **PASS** | §6；ZH-001 / ZH-002 / ZH-003 / NUM-001 四案独立复核均 PASS |
| 9 | S0 报告记录环境、版本、commit、所有 SHA、命令、退出码、指标、未执行项（§8.4、§11.1） | **PASS** | 本报告全文；§8–§9 |

## 2. 环境、版本与哈希

### 2.1 运行环境

| 项目 | 值 |
|---|---|
| OS / 架构 | Linux 7.0.0-44-generic x86_64（glibc 2.39），4 CPU |
| Python | 3.12.3 |
| rapidocr | 3.10.0（冻结版本） |
| onnxruntime | 1.32.0（CPU 包；`onnxruntime-gpu` 未安装） |
| Pillow | 11.3.0 |
| pytest | 8.4.2 |
| fastapi / pydantic / uvicorn | 0.165.0 / 2.14.4 / 0.54.0（已锁，未使用） |
| 虚拟环境 | `/home/hatch/workspace/p033-textproof/.venv`（主工作目录已有环境；未升级、未联网装包） |
| 工作目录 | git worktree `~/workspace/p033-textproof-t006`，分支 `t006-s0-gate`，基线 `732f07e` |
| 网络隔离 | 全部 live OCR 与门禁运行在 `unshare -n`（无网络命名空间）下完成 |

### 2.2 冻结文件 SHA-256

| 文件 | SHA-256 |
|---|---|
| `tests/fixtures/s0/manifest.json` | `cc9a0ea9ed75fda800882c226665fa61cfc8d7213682655d52358cf5c128f959`（与 T005 记录一致） |
| `tests/fixtures/s0/expected_output.json` | `a2e55725a2c8ffdbedc9dab7b7310db47c3bdb9311d4585fc3246ead6a9a641e`（与 T005 记录一致） |
| `tests/fixtures/s0/blind_subset.json` | `a90fb851cd02e9f9315eeecb385392c29c71d07551163fdb6d87669a3a32e93c`（与 T005 记录一致） |
| `requirements.lock` | `8726d13cb20bb731b491a4119629c176b699f035b75d8547d853ca3585d1564d` |
| `pyproject.toml` | `5bcebcc11ab184e5449ed2fe0200198869aaa1a1d1a813015f54d5911a9d5511` |
| 字体 `NotoSansSC[wght].ttf` | `a3041811a78c361b1de50f953c805e0244951c21c5bd412f7232ef0d899af0da`（manifest 记录一致） |

300 张 PNG 的 SHA-256 已由 `verify_s0.py` [0] 步逐张重算并与 manifest
比对：300/300 一致，无缺失、无字节数不符。

### 2.3 OCR 模型与字典（T003 冻结，启动时逐文件验 SHA）

| 资产 | SHA-256 |
|---|---|
| `PP-OCRv6_det_small.onnx` | `090f04abcd9d9a7498bc4ebf677e4cb9bdce1fe4197ddb7e529f1ef44e1ff94f` |
| `PP-OCRv6_rec_small.onnx` | `6f327246b50388f3c176ae304bd95767ea6dc0c9ae92153ef8cbe210b3c14884` |
| `ch_ppocr_mobile_v2.0_cls_mobile.onnx` | `e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c` |
| `ppocrv6_dict.txt`（18,708 行） | `b5f2bfe2bdd9448429e3e82b51c789775d9b42f2403d082b00662eb77e401c5d` |

## 3. Parity：生产模块 vs 独立 Oracle（门禁项 2）

### 3.1 门禁范围内的结果：300/300，100% PASS

方法（`scripts/parity_check.py`）：对 manifest 的每一张 fixture，把
`drawn_text` 作为单条固定 OCR 行记录（bbox = manifest
`target_region_xyxy`，confidence 0.99）同时喂给生产 `build_report`
与 Oracle `compare`，逐案例比对 verdict、错误类型、expected /
recognized 片段、expected / recognized span、bbox、warning codes、
summary。结果：**300/300 一致，0 差异**。四案 §8.1 样本的固定路径
核对同时由 `verify_s0.py` [3] 步对两个实现各做一次：全部 PASS。

Oracle 独立性（门禁项 1）：`oracle/reference_compare.py` 经 AST
检查只导入标准库（`re`、`unicodedata`、`fractions`、`typing`），
无任何 `textproof` 导入；同一断言在 Oracle 自测
（`tests/oracle/test_reference_compare.py`，43 通过）中以全新子进程
复核。Oracle 由独立会话（T006-oracle）仅按项目书实现，未读生产
核心代码（见其 TASK_RESULT.md）。

### 3.2 T004 与 Oracle 的三处字面解读：三处全部一致

| 字面解读 | 生产（T004） | Oracle | 本轮核对 |
|---|---|---|---|
| 混淆对集合（§4.5“如 O/0、I/1/l、S/5、B/8”） | 仅字面列出的 6 对；小写 `o/0` 不算 | 相同 | 边缘电池 `confusion_lower_o`：两侧错误类型一致 |
| 标点替换 0.50（§4.5） | 要求两侧均为 Unicode 类别 P | 相同 | `punct_sub` / `punct_vs_letter`：两侧错误类型一致 |
| gap 顺序（§4.4 平局规则） | 回溯表现为 trailing 缺失+额外按“额外在前、缺失在后” | 相同配对集合与错误顺序 | `high_cost_pair` / `multi_sub_mixed_types`：两侧错误顺序一致 |

### 3.3 门禁范围之外的诊断：26 项边缘电池（14/26 一致）

`parity_check.py` 另跑 26 项手造边缘案例（空输入、低置信、缺失/额外行、
高代价配对、混淆对、标点、全角字符、尾换行、CRLF、阅读顺序排列、重复字符），
**不属于冻结门禁范围**，结果 14 项一致、12 项有差异。差异逐项列出并裁定如下；
完整逐字段 diff 见 `task_handoffs/T006/parity_report.json` 的
`edge_battery.differences`（该文件是 T006 裁决时 13/26 的原始记录；
当前代码实测 14/26，见 §8 补充命令行；翻转的一案为 `confusion_upper_O`，
见 V2）。

**R 组 — 规格未写明的表示字段（10 项）**：缺失侧 span 取 `null`（生产）
vs `[0, 0]`（Oracle）；`MISSING_LINE` / `AMBIGUOUS_ALIGNMENT` 的
`bbox_scope` 取 `null`（生产）vs `"none"`（Oracle）；警告对象报文文本不同，
Oracle 多一个 `confidence` 字段。涉及案例：`empty_expected_one_ocr`、
`missing_line`、`extra_line`、`high_cost_pair`、`confusion_lower_o`、
`trailing_newline`、`multi_sub_mixed_types`、`same_row_two_boxes_x_order`
（仅 `bbox_scope`）、`low_conf_match`、`low_conf_diff`（仅警告对象形态）。
裁定：§5.4 样例只规定了字符错误的字段形态，**未规定**行级错误的缺失侧
span 取值、未规定 `bbox_scope` 除 `"ocr_line"` 外的取值、§5.3 只规定了
警告码枚举而未规定警告对象形态。两处取值均无项目书原文可依，**无法按原文
裁定孰对孰错**。这些字段在 300 张固定 fixture 中一次未出现（无
`MISSING_LINE` / `EXTRA_LINE` / `AMBIGUOUS_ALIGNMENT`，无警告），
对 S0 指标零影响。记为发现 F-03：需 T009 在冻结 JSON schema 时统一口径，
终审前不得各行其是。

**V1 — 空期望 + 空 OCR 的 verdict（1 项）**：生产 `OCR_FAILED` +
`OCR_EMPTY` 警告；Oracle `MATCH`。裁定：§7.6 原文“OCR 无可用文本时为
`OCR_FAILED` 或 `REVIEW_REQUIRED`，具体按引擎失败 / 空识别区分”直接
覆盖“OCR 无可用文本”的情形，生产取值有原文支持；Oracle 的空期望 carve-out
在项目书中无依据。且该情形在产品内不可达：T002 对空白期望文本返回
`INVALID_INPUT`（§4.2）。记为发现 F-04（Oracle 的 carve-out 与 §7.6
字面不符；产品行为以生产为准）。

**V2 — 单字符混淆替换 `O` → `0` 的歧义判定（1 项，生产缺陷）**：生产
`REVIEW_REQUIRED` + 单条 `AMBIGUOUS_ALIGNMENT`；Oracle `MISMATCH` +
`SUBSTITUTION`。裁定：§4.4 原文“两个最优对齐路径代价差小于 `0.05`”——
精确十进制算术下次优（缺失+额外行，0.35+0.35=0.70）与最优（配对，混淆代价
0.65）之差恰好为 0.05，**不小于 0.05，不应判歧义**；Oracle（`Fraction`
精确计算）正确。生产用二进制浮点：`0.7 - 0.65 == 0.04999999999999993
< 0.05`，误判歧义。这是**已证实的生产缺陷**，记为发现 F-01。影响面：
仅当最优与次优代价差在十进制下恰好为 0.05 时触发；300 张 fixture 中
0 次触发（固定 parity 300/300 即证），S0 指标零影响。**修复状态（终审 R1
前更新）：T013 R-01 已修复**——`align_lines` / `weighted_edit` 的内部代价
比较与歧义判定改用精确 `Fraction` 算术（commit `d26adcc`，随 T013 合并
`9cfaace`；见 `task_handoffs/T013/r01/TASK_RESULT.md`）。修复后本案生产与
Oracle 一致（`MISMATCH` + `SUBSTITUTION`），边缘电池由 13/26 变为 14/26。
本案翻转的原因是该确定性代码修复：边缘电池用固定合成记录
（`scripts/parity_check.py` 内 `confusion_upper_O`：期望 `O`、OCR 行 `0`），
不经过 live OCR，与 OCR 读法抖动无关。

**V3 — 同行多框、中心高度不同的阅读顺序（1 项，Oracle 偏差）**：两框
纵向重叠（同一视觉行），`AB` 框 `[0,0,100,52]`、`CD` 框 `[200,2,300,48]`；
生产按 x 排为 `AB`、`CD`；Oracle 按中心 y 排为 `CD`、`AB`。裁定：§4.4
原文“按文本框垂直中心与纵向重叠聚合为行；**同一视觉行内按 x 从小到大
排序**”——两框纵向重叠属同一视觉行，行内应按 x 排序，生产正确；
Oracle 的纯中心排序违反该句。记为发现 F-02（Oracle 阅读顺序与 §4.4
字面不符；无 fixture 影响——全部 fixture 为单行图，live OCR 每图只返回
1 行）。其余阅读顺序案例（行交换、重叠行）两侧一致。

**范围声明（重要）：** 门禁项 2 的冻结范围是“manifest 的固定 OCR 行记录”
（任务卡原文），该范围 parity 为 100% PASS。若终审将“Oracle parity 100%”
理解为**全输入域** 100%，则 F-03（规格未写明的表示字段）使 parity 在该理解下
不成立，S0 应为 FAIL（F-01 生产浮点缺陷已由 T013 R-01 修复，当前实测
14/26，见 V2；其余 12 项差异均为 R 组 / V1 / V3 类表示与口径分歧）。
本报告按任务卡字面范围给 PASS，同时把该分歧点写明，供主聊天复核时裁决是否推翻。

## 4. 四个固定案例 §8.1 逐项核对（门禁项 3）

固定 OCR 行记录路径（`drawn_text` + `target_region_xyxy`），生产与 Oracle
双实现逐字核对 `expected_output.json`：

| 样本 | 期望 / 图绘 | 核对结果（双实现一致） |
|---|---|---|
| TP-S0-ZH-001 | `限时优惠` / `限时优` | 恰好 1 条 `MISSING_CHARACTER`，fragment `惠`/`""`，span `[3,4]`/`[3,3]`，bbox = OCR 行框，verdict `MISMATCH` ✅ |
| TP-S0-ZH-002 | `新品上市` / `新口上市` | 恰好 1 条 `SUBSTITUTION`，fragment `品`/`口`，span `[1,2]`/`[1,2]`，bbox = OCR 行框，verdict `MISMATCH` ✅ |
| TP-S0-NUM-001 | `￥28.80` / `￥28.00` | 恰好 1 条 `NUMERIC_CHANGE`，fragment `8`/`0`，span `[4,5]`/`[4,5]`，bbox = OCR 行框，verdict `MISMATCH` ✅（固定路径；live 路径见 §6(a)） |
| TP-S0-ZH-003 | `新客立减20元` / `新客立减元` | 恰好 1 条 `MISSING_CHARACTER`，fragment `20`/`""`，span `[4,6]`/`[4,4]`，bbox = OCR 行框，verdict `MISMATCH` ✅ |

live OCR 路径的四案核对（`independent_verify.py` 逐案实测，见 §6）：

| 样本 | live OCR 逐字文本（置信度） | live IoU | live 结论 |
|---|---|---|---|
| TP-S0-ZH-001 | `限时优`（0.99929） | 0.964 | 恰好 1 条 `MISSING_CHARACTER`（惠，[3,4]），verdict `MISMATCH` ✅ |
| TP-S0-ZH-002 | `新口上市`（0.99978） | 0.955 | 恰好 1 条 `SUBSTITUTION`（品/口，[1,2]），verdict `MISMATCH` ✅ |
| TP-S0-NUM-001 | `¥28.00`（0.93004） | 0.875 | 1 条 `NUMERIC_CHANGE`（8/0，[4,5]）+ 1 条额外 `SUBSTITUTION`（￥→¥，[0,1]），verdict `MISMATCH`（见 §6(a) 裁定） |
| TP-S0-ZH-003 | `新客立减元`（0.94255） | 0.924 | 恰好 1 条 `MISSING_CHARACTER`（20，[4,6]），verdict `MISMATCH` ✅ |

## 5. 300 样本 live 指标（门禁项 4、5、6）

live 全流程：T002 加载 → T003 RapidOCR（CPU）→ T004 比较 → §5 报告，
300 张逐张实测（`scripts/compute_s0_metrics.py`，结果
`task_handoffs/T006/s0_metrics.json` + `live_ocr_results.jsonl`）。
300 张全部返回单行 OCR，无零行、无多行；最低置信度 0.91432（> 0.65，
故无 `LOW_OCR_CONFIDENCE` 警告）；全部 300 张无警告。

| 指标（§8.3） | 门槛 | 实测 | 结论 |
|---|---|---|---|
| 检测召回率（注入字符差异数计） | ≥95% | **100.00%（201/201）** | PASS |
| 替换类召回率 | ≥90% | **100.00%（70/70）** | PASS |
| 缺失类召回率 | ≥90% | **100.00%（71/71）** | PASS |
| 数字变化类召回率 | ≥90% | **100.00%（60/60）** | PASS |
| clean 误报率（verdict `MISMATCH` 计） | ≤8% | **0.00%（0/100）** | PASS |
| clean 非 `MATCH` 率（补充口径） | —（仅报告） | 0.00%（0/100） | — |
| JSON schema 合法率（300 份 live 报告） | 100% | **100%（300/300 有效，0 违规）** | PASS |
| OCR CER（独立报告，不替代召回率） | 记录值 | **0.0008**（S=1，D=1，I=0，N=2496） | 仅记录 |
| IoU（live bbox vs target_region） | 每张 ≥0.80 | 最小 **0.829**，均值 0.938，低于 0.80 的 **0 张** | PASS |

召回率计分规则（`compute_s0_metrics.py` 有载）：注入字符总数按 manifest
计——替换 70×1、缺失 68×1 + ZH-001 1 + ZH-003 2（`"20"`）= 71、数字变化
60×1，合计 201；某注入差异计为检出，当且仅当 live 报告含同类型错误，
其 `expected_span` 覆盖注入 span 且 `expected_fragment` 包含注入片段
（覆盖而非精确相等：live OCR 若同时误读相邻字符会展宽报告 run，
但注入差异本身必须仍在其中）。漏检 0 项。

CER 说明：CER 的两个字符差异即 live OCR 与图绘文本的全部差异——
TP-S0-NUM-001 的 `￥`→`¥`（S=1）与 TP-SUB-055 的 `TOP 当季上馈` →
`TOP当季上馈`（空格丢失，D=1）。其余 298 张 OCR 文本与图绘文本逐字一致。
CER 与检错召回率是不同指标（§8.3 原文），此处分开报告；SUB-055 的注入
替换本身仍被检出（召回率不受影响）。

`verdict` 分布：`MATCH` 100 张（恰为 100 张 clean），`MISMATCH` 200 张
（恰为 200 张 injected），`REVIEW_REQUIRED` / `OCR_FAILED` 各 0 张。

计时（1200×480 fixture，单 warmed adapter，OCR+比较每图；权威轮次 run2）：
P50 2.1235s、P95 2.7147s、max 3.2683s——由 `task_handoffs/T006/live_ocr_results.jsonl`
300 行的 `seconds` 字段重算（P50 为中位数，P95 按 `scripts/compute_s0_metrics.py`
的 `_percentile` 线性插值），与同目录 `task_handoffs/T006/s0_metrics.json` 的
`timing_seconds`（P50 2.1235、P95 2.714725、max 3.2683）逐数一致。
本报告初版（commit `0ad56d6`）所写的 P50 1.33s / P95 1.77s / max 3.13s 在磁盘上
无对应运行记录可考：T006 交接包只保留了 run2 的逐图计时，run1 的逐图计时未保留，
且 T006 交接记录的 run1/run2“逐数一致”只覆盖召回率、FPR、CER、IoU 最小值四项，
不含计时；T009 重跑（P50 1.4198s / P95 2.2830s / max 5.2882s）与 T011 重跑
（P50 2.2322s / P95 2.9777s / max 3.5225s）的计时也各不相同（同机不同时段的
CPU 争用所致，各轮 `live_ocr_results.jsonl` 与 `s0_metrics.json` 自洽）。
故 1.33/1.77/3.13 不得再作为任一轮次的计时引用；本节以 run2 实测为准。
§8.3 的运行时间门槛针对 1920×1080 预热后
P95 ≤5s，**本次未测量**（冻结 fixture 为 1200×480），记为 NOT_MEASURED，
归 T011 性能报告。T011 性能报告实测：1920×1080 预热后 P95 3.817s ≤ 5s，
PASS（见 PERFORMANCE_REPORT.md）；§8.3 运行时间门槛由 T011 性能报告判定，
不属于 verify_s0.py。

## 6. 两项必须书面裁定的问题

### 6(a) TP-S0-NUM-001 的 live-OCR ￥→¥ 问题 — 裁定：样本仍满足 §8.1

**逐字贴出的 live 运行实际输出**（`independent_verify.py --case
TP-S0-NUM-001`，RapidOCR 3.10.0，CPU，置信度 0.93004；同一输出在
`scripts/verify_s0.py` 的 300 张 live 运行与 `tests/s0/test_s0_gate.py`
的锁定测试中复现一致）：

```text
live OCR line: text='¥28.00' confidence=0.93004 bbox=[478.0, 188.0, 729.0, 291.0]
expected_text: '￥28.80'   drawn_text: '￥28.00'
verdict: MISMATCH
errors:
  E001 SUBSTITUTION      expected_fragment='￥' recognized_fragment='¥'
       expected_span=[0, 1] recognized_span=[0, 1]
  E002 NUMERIC_CHANGE    expected_fragment='8' recognized_fragment='0'
       expected_span=[4, 5] recognized_span=[4, 5]
```

即：live 路径下该样本有 2 条错误，其中 `NUMERIC_CHANGE` 恰好 1 条，
其 fragment（`8`/`0`）与 span（`[4,5]`）与 §8.1 逐字一致；多出的一条是
`SUBSTITUTION`（`￥` U+FFE5 → `¥` U+00A5），来自 OCR 引擎把图绘的全角
`￥` 读作半角 `¥`。

**裁定：按项目书原文，“恰好 1 条 `NUMERIC_CHANGE`”只约束
`NUMERIC_CHANGE` 的条数；多出的一条 `SUBSTITUTION` 作为 OCR 行为如实记录，
样本仍算满足 §8.1。** 理由（均引项目书原文）：

1. §8.1 表格原文是“恰好 1 条 `NUMERIC_CHANGE`；`expected_fragment=8`；
   `recognized_fragment=0`；`expected_span=[4,5]`；bbox 指向该 OCR 文本行”。
   计数修饰的是带类型的错误（`NUMERIC_CHANGE`），不是错误总数；若指总数，
   自然写法应如 §12.2 对 ZH-001 所写的 `error_count: 1`。本样本 live 路径的
   `NUMERIC_CHANGE` 条数恰好为 1，fragment 与 span 逐字符合。
2. 同表 ZH-003 一栏写的是“**至少** 1 条 `MISSING_CHARACTER`”，证明该栏的
   计数约束是按错误类型计的下限/精确数，而非对错误总数的封顶；按类型计是
   表格一贯的写法。
3. §8.1 的“固定预期输出”是定义在**固定样本**（图绘文本为 ground truth）
   上的期望；在固定 OCR 行记录路径下，本样本恰好只有 1 条错误（即该条
   `NUMERIC_CHANGE`），两种读法在该路径下都通过。live OCR 的识别文本
   （`¥28.00`）与图绘文本（`￥28.00`）不同，live 路径的输入本身已偏离
   固定样本定义；其额外错误是 OCR 识别差异（§8.3 的 CER 口径正在度量
   此类差异：本轮 CER 的 S=1 即此一例），不是比较算法漏报或多报。
4. §4.3 规范化原文只把 U+FF01–U+FF5E 的全角 ASCII 映射为半角；
   `￥`（U+FFE5）不在该范围内，**不得**映射——T004 与 T005 均已按此锁定。
   因此比较核心如实报告 `￥`→`¥` 为差异是正确的；把它删掉或把 `￥`/`¥`
   视为相同，都需要 ADR 与 Owner 批准，本任务无权做。

**未做的处理（明示）：** 未删除多出的 `SUBSTITUTION` 错误，未改 fixture
（图绘 `￥28.00` 仍为冻结值），未改 manifest，未提交 ADR，未用任何变通
绕过。`--strict-live`（要求 live 报告与固定预期逐字相等）下
`independent_verify.py --case TP-S0-NUM-001` 退出 1，正是该额外错误的
如实记录；默认（子集）模式退出 0。本裁定若被复核推翻（即采用“总错误数
恰好为 1”的读法），则该样本不满足 §8.1，S0 应为 FAIL——此分歧点已写明，
供主聊天裁决。

### 6(b) target_region 校准方法 — 裁定：方法合法，盲测验证成立

**独立重跑结果（本任务实测，非引用 T005）：** 对全部 300 张 fixture 跑
live OCR（与 §5 同一次运行，同一 adapter、同一模型），逐张算
IoU（live OCR bbox，manifest `target_region_xyxy`）：

| 子集 | 张数 | 最小 IoU | 均值 IoU | < 0.80 的张数 |
|---|---:|---:|---:|---:|
| 全部 300 张 | 300 | **0.829** | 0.938 | **0** |
| 非盲测 240 张（校准集） | 240 | 0.829 | 0.938 | 0 |
| 盲测 60 张（未参与拟合） | 60 | **0.835** | 0.940 | **0** |

与 T005 报告值（全部最小 0.829、盲测最小 0.835）逐数一致，独立复现成立。

**方法合法性评估：**

1. 规则本身是绘图几何的确定性函数：`target_region_for(ink_bbox)` 只用
   墨迹框几何（`height = 70 + 0.7*ink_height - 0.05*ink_width`；
   `width = ink_width + 40 - 0.02*ink_width`，以墨迹框中心为中心），
   不用任何一张图片自己的 OCR 输出。本任务逐张重算验证：该规则从
   `ink_bbox_xyxy` 复现 manifest 的 `target_region_xyxy`，**300/300
   一致**。规则定义见 manifest `generator.target_region` 段与
   `scripts/generate_fixtures.py`。
2. 盲测验证成立：规则按 240 张非盲测的实测 OCR 框拟合，60 张盲测在拟合中
   一次未用；盲测最小 IoU 0.835 ≥ 0.80，与校准集（0.829）同一水平，
   无过拟合迹象。本任务在看到 S0 结果后**没有**重拟合规则；盲测 60 张
   未用于任何调参（本次工作只读 manifest 与 live OCR 输出，未改生成器、
   未改 manifest、未改任何 fixture）。
3. 边界说明：该规则是按冻结的 PP-OCRv6 检测框几何校准的经验规则；
   若更换 OCR 引擎/版本或字号，对应关系需重测（T005 已登记）。本轮
   S0 的结论只在冻结模型路线下成立。

**结论：target_region 校准方法合法；盲测验证成立；无一张 IoU < 0.80，
无 S0 发现。**

## 7. 离线与 CPU-only 证据（门禁项 7）

- **网络访问 0（实测方式）：** 两轮完整门禁运行（run1、run2）均在
  `unshare -n`（新建的空网络命名空间，无任何接口、无回环以外的网络）
  下执行，`verify_s0.py` 全程 exit 0（run2）且 300 张 live OCR 全部完成；
  若运行中任何一步需要外网（模型下载、遥测、远程 OCR），在该命名空间内
  必失败。`verify_s0.py`、`compute_s0_metrics.py`、`parity_check.py`、
  `independent_verify.py` 均不打开 socket（代码内无网络调用；RapidOCR
  适配器在构造时验模型 SHA 并传显式本地 `model_path`，从不走下载分支，
  见 T003）。另：T003 已验证删除外网后仍可完成 OCR；本轮未重复该实验，
  以 `unshare -n` 全程运行为本次证据。
- **ONNX Runtime provider 仅 CPU：** 启动时 adapter 对 det / cls / rec
  三个 session 逐一断言 `get_providers() == ["CPUExecutionProvider"]`
 （不满足即拒跑）；实测三模型均为 `["CPUExecutionProvider"]`，
  `test_onnx_providers_cpu_only` 亦通过。`onnxruntime-gpu` 不在锁文件中。

## 8. 执行命令与退出码（权威证据轮次 run2）

验收命令（任务卡原文；Python 为主工作目录已锁 venv）：

| # | 命令 | 退出码 | 结果 |
|---|---|---|---|
| 1 | `/home/hatch/workspace/p033-textproof/.venv/bin/python -m pytest -q` | **0** | **229 passed**，2 warnings（均为 T002 既有的 Pillow `DecompressionBombWarning`，与 T006 无关），179.62s |
| 2 | `unshare -n /home/hatch/workspace/p033-textproof/.venv/bin/python scripts/verify_s0.py --manifest tests/fixtures/s0/manifest.json`（`--force-live`） | **0** | S0 VERDICT: PASS（见 §1；stderr 为空） |
| 3 | `/home/hatch/workspace/p033-textproof/.venv/bin/python scripts/independent_verify.py --case TP-S0-ZH-001` | **0** | INDEPENDENT VERIFICATION: PASS（IoU 0.964） |

补充命令（均 exit 0，除注明外）：

| 命令 | 退出码 | 结果 |
|---|---|---|
| `python scripts/parity_check.py --manifest tests/fixtures/s0/manifest.json` | 0 | 固定 300/300；边缘电池 14/26（见 §3.3；T006 裁决时为 13/26，T013 R-01 修复 F-01 后翻转为 14/26） |
| `python scripts/independent_verify.py --case TP-S0-ZH-002` | 0 | PASS（IoU 0.955） |
| `python scripts/independent_verify.py --case TP-S0-ZH-003` | 0 | PASS（IoU 0.924） |
| `python scripts/independent_verify.py --case TP-S0-NUM-001` | 0 | PASS（子集模式；额外 `SUBSTITUTION` 逐字记录，见 §6(a)） |
| `python scripts/independent_verify.py --case TP-S0-NUM-001 --strict-live` | **1** | FAIL（by design：额外 `SUBSTITUTION` 使严格相等不成立；见 §6(a)） |
| `python scripts/validate_report_schema.py`（对 300 份 live 报告，门禁内调用） | 0 | 300/300 VALID（`schema_validation.log`） |
| `python scripts/generate_fixtures.py --verify-manifest tests/fixtures/s0/manifest.json`（T005 命令，pytest 内已跑） | 0 | 全量 pytest 通过即含该验证（`test_fixtures_s0.py` 7 通过） |

run1 说明：第一轮完整门禁运行（同样 `unshare -n` + `--force-live`）
除门禁项 1 外全部通过，退出 1 的唯一原因是 `verify_s0.py` 自身的
独立性检查 bug——它用子串 `"textproof" in source` 误判了 Oracle 文档
字符串中的冻结 schema 名 `"textproof.report/v1"`。修复为 AST 导入检查后
（只改本任务的 `scripts/verify_s0.py`，未动 Oracle 与生产代码），run2
全项通过、退出 0。run1 的指标数与 run2 逐数一致（召回率 100%、FPR 0%、
CER 0.0008、IoU 最小 0.829），run2 为权威轮次。

执行中的两则运行时提示（据实记录）：两次较长 exec 调用返回了
“审批超时”提示，但命令实际已执行并返回完整输出与退出码（以实际退出码
与日志为准，未重复执行；按任务指示向父代理报告此提示）。

## 9. 交付物、未执行项与已知事项

### 9.1 本任务交付物（worktree `t006-s0-gate`，均新增、零修改已跟踪文件）

| 文件 | 说明 |
|---|---|
| `S0_REPORT.md` | 本报告（仓库根目录） |
| `scripts/verify_s0.py` | S0 门禁总控（9 项逐项判定，exit 0 当且仅当全过） |
| `scripts/independent_verify.py` | 独立复核（不调用 `verify_s0.py`；逐字段核对 + live 逐字输出） |
| `scripts/parity_check.py` | 固定 300 parity + 26 项边缘电池 + 裁定分组 |
| `scripts/compute_s0_metrics.py` | 300 张 live OCR 指标（召回率/FPR/CER/IoU/schema/计时） |
| `scripts/validate_report_schema.py` | §5 手工 schema 校验器（stdlib only；无 `jsonschema` 依赖可用） |
| `tests/s0/test_s0_gate.py` | 12 个 S0 pytest（四样本双实现、300 parity、Oracle 独立性、CPU provider、schema、NUM-001 live 锁定） |
| `task_handoffs/T006/` | 交接包：TASK_RESULT.md、changed_files.txt、git_diff.patch、test_commands.txt、test_stdout.log、test_stderr.log、exit_codes.txt、SHA256SUMS.txt 及运行证据（`s0_metrics.json`、`parity_report.json`、`live_ocr_results.jsonl`、`schema_validation.log`） |

禁止文件未修改证明：`git status` 只显示新增文件（5 个 scripts、1 个
tests/s0/、S0_REPORT.md、task_handoffs/T006/）；`git diff --name-only
732f07e` 对 PROJECT_BOOK.md / .docx、IMPLEMENTATION_PLAN.md / .docx、
requirements.lock、pyproject.toml 输出为空；未碰 T002–T005 与 Oracle 的文件；
未新增依赖、未联网安装。

### 9.2 未执行项

| 未执行项 | 原因 |
|---|---|
| §8.3 运行时间：1920×1080 预热后 30 次测量 P95 ≤5s | 冻结 fixture 为 1200×480；记为 NOT_MEASURED，归 T011 性能报告（§5 计时段） |
| 正式的 `.schema.json` 文件 | 是 T009 的交付物；本任务以 `validate_report_schema.py` 按 §5 逐字段校验并留日志，校验方法与依据的 §5 条款见该脚本 docstring |
| API / UI / CLI 一致性、隐私与离线全量测试 | 属 T007–T014（待 S0 解锁后）；本任务只覆盖 S0 门禁范围 |
| 1920×1080 图片的 OCR 实测 | 同运行时间项；未用非 fixture 图片 |

### 9.3 已登记、不改的事项（转述，不处理）

- `tool_version` 取 `"0.1.0"` 与 `pyproject.toml` 的 `1.0.0` 不一致：
  已登记事项（T004 风险 1），本任务不改，留给 T009/终审统一口径。
  §5 schema 校验只要求 `tool_version` 为非空字符串，不绑定具体值。
- 字典许可：T003 已核实字典无单独许可声明、不在模型 Apache-2.0 声明内；
  与 S0 门禁无关，转述。
- TP-SUB-055 的 live-OCR 空格丢失（`TOP 当季上馈` → `TOP当季上馈`，
  置信度 1.000，IoU 0.979）：OCR 引擎的混排空格行为，fixture 不改；
  注入替换本身仍被检出，召回率计分按“注入差异是否检出”而非“错误数相等”
  （见 §5 计分规则）。

### 9.4 门禁范围外的发现（汇总；详见 §3.3）

| 编号 | 发现 | 严重度 | 处置建议 |
|---|---|---|---|
| F-01 | 生产 `align_lines` 浮点比较误判歧义（单字符混淆替换 `O`→`0`：0.7−0.65 在浮点下 < 0.05） | P1（生产缺陷；S0 零影响） | T013 修复：以精确十进制/分数比较代替浮点比较 + 回归测试；终审前关闭 |
| F-02 | Oracle 阅读顺序与 §4.4 字面不符（同行多框按中心而非按 x 排） | 低（Oracle 偏差；无 fixture 影响） | Oracle 跟进修正或在 Oracle docstring 中登记为已知偏差 |
| F-03 | 行级错误缺失侧 span（null vs [0,0]）、`bbox_scope`（null vs "none"）、警告对象形态：规格未写明，两侧取值均无原文可依 | P1（规格澄清） | T009 冻结 JSON schema 时统一口径；终审前不得各行其是 |
| F-04 | 空期望 + 空 OCR 的 verdict：生产 `OCR_FAILED`（有 §7.6 原文支持），Oracle `MATCH`（无原文依据的 carve-out） | 低（产品内不可达，T002 拒空白期望） | Oracle 跟进对齐 §7.6；或由规格方明确空期望语义 |

### 9.5 回退

- 回退 commit：`732f07e`（输入 commit；本任务只新增文件，删除分支
  `t006-s0-gate` 与 worktree `~/workspace/p033-textproof-t006` 即完整回退）。
- 任一硬门失败即 `S0_FAIL`、T007–T014 BLOCKED 的纪律未被触发：9 项全部通过。
- 失败回退条款未动用：未降低指标、未删除 fixture、未修改分母（召回率分母
  201、clean 分母 100 均为 manifest 原值）。

## 10. 已知限制（非门禁）

以下两项是终审 R1（P2）指出的已知限制。它们**不是冻结规格的门槛**（§8.3
的 S0 PASS 条件未列多行 clean 样本，也未列货币符号等价要求），**不改变
S0 VERDICT: PASS**；本节只作如实记录，供下一版本改进。本轮不扩大 S0 样本集、
不改动冻结门禁。

### 10(a) 多行中文海报的端到端覆盖不足

- 300 张 S0 fixture 的 live OCR 每图只返回 1 行：`task_handoffs/T006/live_ocr_results.jsonl`
  与 `task_handoffs/T011/s0/live_ocr_results.jsonl` 的 `ocr_line_count` 分布均为
  `{1: 300}`。生产代码支持多行对齐（`src/textproof/core/align_lines.py`），
  合成行对齐测试 `tests/unit/test_core/test_align_lines.py::test_align_multi_line_mixed_case`
  通过，但 300 张图没有覆盖真实多行 OCR 输出。
- 唯一的多行实测是 T011 的 1920×1080 四行性能样本
  （`task_handoffs/T011/perf_image_1920x1080.png`，4 行：`限时优惠 全场5折` /
  `新品上市 会员专享` / `新客立减20元` / `SALE 50% OFF ￥28.80`）：
  30 次测量的 verdict 均为 `MISMATCH`——OCR 漏读两处中文词间空格
  （`限时优惠 全场5折` → `限时优惠全场5折`等，2 条 `MISSING_CHARACTER`），
  并把第 3 行的「减」读成「減」（1 条 `SUBSTITUTION`）
  （见 `task_handoffs/T011/PERFORMANCE_REPORT.md` §4）。该样本只用于 §8.3
  计时门槛（P95 3.817s ≤ 5s），判读结果不计入门禁。
- 下一版本：增加多行 clean 样本（终审 R1 P2 建议）。

### 10(b) ￥/¥ 混淆：字符级应保留，电商场景属误报

- 按字符级精确比较，`￥`（U+FFE5）→ `¥`（U+00A5）的差异应保留：§4.3 规范化
  只把 U+FF01–U+FF5E 的全角 ASCII 映射为半角，`￥` 不在该范围内，**不得**映射
  （见 §6(a)；`src/textproof/core/normalize.py` 亦如是；T013 裁决确认“无 ￥→¥ 映射”）。
  把两者视为相同需要 ADR 与 Owner 批准，本报告无权改动。
- 但对电商价格海报用户，live OCR 把图绘的 `￥` 读作 `¥` 会形成额外误报：
  TP-S0-NUM-001 的 live 路径因此多出 1 条 `SUBSTITUTION`（§6(a) 已裁定样本仍满足
  §8.1）；300 张 CER 的 S=1 即此一例。单行样本里另有一例同类 OCR 空格行为：
  TP-SUB-055 的 `TOP 当季上馈` → `TOP当季上馈`（空格丢失，D=1；见 §5 CER 说明与
  §9.3），注入替换本身仍被检出。
- 下一版本：增加货币符号样本与口径说明（终审 R1 P2 建议），评估电商场景的误报
  影响；是否引入任何等价映射须另行 ADR。
