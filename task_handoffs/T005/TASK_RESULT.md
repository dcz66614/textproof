# TASK_RESULT.md — T005 300 张合成 fixture 与固定预期（P033 TextProof）

- 任务 ID：T005
- 输入 commit：`c5511e1`（master：T001–T004 均已合入，全量 167 个测试通过）
- 输出 commit（代码与 fixture）：`6cfabb68fea0c56da080a0c54cebd4ddcb32e157`
- 分支：`t005-fixtures`（worktree `~/workspace/p033-textproof-t005`）
- 交接包 commit：见父代理的 git log（本文件包含在交接包 commit 中，故其哈希只能在提交后由外部读取；代码输出 commit 如上，不受交接包 commit 影响）
- 状态：**SUCCESS — 6 项验收标准全部满足**（逐项证据见 §2）
- 执行时间：2026-11-25 ~03:34–05:10 GMT
- 工作目录：`~/workspace/p033-textproof-t005`（`git worktree`，与主工作目录 master 检出隔离）

## 1. 实际改动文件（输出 commit 6cfabb6，308 个新增文件，0 修改）

| 文件 | 说明 |
|---|---|
| `scripts/generate_fixtures.py` | 新增：确定性生成器 + `--verify-manifest`（≈700 行） |
| `tests/fixtures/s0/*.png` | 新增：300 张 PNG（1200×480，白底黑字，见 §2） |
| `tests/fixtures/s0/manifest.json` | 新增：300 条记录（SHA-256 `cc9a0ea9ed75fda800882c226665fa61cfc8d7213682655d52358cf5c128f959`） |
| `tests/fixtures/s0/expected_output.json` | 新增：300 条固定预期报告（SHA-256 `a2e55725a2c8ffdbedc9dab7b7310db47c3bdb9311d4585fc3246ead6a9a641e`） |
| `tests/fixtures/s0/blind_subset.json` | 新增：60 条盲测清单（SHA-256 `a90fb851cd02e9f9315eeecb385392c29c71d07551163fdb6d87669a3a32e93c`） |
| `tests/fixtures/s0/fonts/NotoSansSC[wght].ttf` | 新增：随包字体，17,772,300 B（见 §3） |
| `tests/fixtures/s0/fonts/OFL.txt` | 新增：OFL-1.1 全文 |
| `tests/fixtures/s0/fonts/FONT_NOTICE.md` | 新增：字体来源、版本、SHA 记录 |
| `tests/unit/test_fixtures_s0.py` | 新增：7 个 fixture 测试（manifest、S0 四样本、T004 交叉核对、盲测、两次生成一致性） |

### 禁止文件未修改证明

- 提交前 `git status --porcelain` 只显示 3 个新增路径（`scripts/generate_fixtures.py`、`tests/fixtures/`、`tests/unit/test_fixtures_s0.py`），`git diff --name-only` 为空（0 个已跟踪文件修改）。
- `git diff --name-only c5511e1 -- PROJECT_BOOK.md PROJECT_BOOK.docx IMPLEMENTATION_PLAN.md IMPLEMENTATION_PLAN.docx requirements.lock pyproject.toml src/textproof/contracts.py src/textproof/io src/textproof/ocr tests/unit/test_image_loader.py tests/integration` 输出为空。
- 四份规格文件未修改；`requirements.lock`、`pyproject.toml` 未修改；未碰 T002/T003/T004 的文件；未新增任何依赖，未联网安装（字体下载是构建期一次官方来源下载，见 §3；生成与测试全程零外网）。

## 2. 验收标准逐项证据

### 验收 1 — 共 300 张唯一静态图片：100 clean、70 substitution、70 omission、60 numeric change ✅ PASS

- `manifest.json` counts：`{total: 300, clean: 100, substitution: 70, omission: 70, numeric_change: 60, blind_subset: 60}`。
- 唯一性：300 个唯一 ID、300 个唯一 SHA-256、300 个唯一 expected_text、300 个唯一 drawn_text（`--verify-manifest` 与 `test_manifest_counts_and_uniqueness` 双重断言）。
- 全部 1200×480 PNG，白底黑字；PNG 总字节 3,476,554；每张均在 T002 输入约束内（25 MiB / 8192 px / 40 MP）。
- 类别构成（含 4 个固定 S0 样本）：clean 100（TP-CLN-001–100）；substitution 70（TP-S0-ZH-002 + TP-SUB-001–069）；omission 70（TP-S0-ZH-001、TP-S0-ZH-003 + TP-OMI-001–068）；numeric change 60（TP-S0-NUM-001 + TP-NMC-001–059）。

### 验收 2 — 固定生成器、固定参数、固定字体、固定 seed ✅ PASS

- 生成器 `scripts/generate_fixtures.py` v1.0.0；seed 20261125（盲测抽样用独立 seed 20261126）；画布 1200×480 PNG；字号 64 px；字体 Noto Sans SC Regular（wght 400）；黑字白底；单行居中布局。
- 全部随机选择来自 `random.Random(20261125)` 的固定调用顺序；Pillow PNG 编码字节确定。
- 字体见 §3。生成与验证均不访问网络（字体文件已随包，生成器校验其 SHA-256 与字节数后才工作）。

### 验收 3 — 每张图片有唯一 ID、SHA-256、expected text、mutation label、target region 和 expected report ✅ PASS

- manifest 每条记录含：`id`、`filename`、`sha256`、`bytes`、`width`/`height`/`format`、`category`、`mutation{kind, position, expected_char, drawn_char}`、`expected_text`、`drawn_text`、`ink_bbox_xyxy`、`target_region_xyxy`、`expected_verdict`、`expected_errors[]`（每条错误含 type、expected/recognized fragment、span、`bbox_scope: ocr_line` 与 bbox 规则）。
- `expected_output.json` 与 manifest 逐字段一致（`--verify-manifest` 核对全部 300 条；`test_expected_output_mirrors_manifest`）。
- `target_region_xyxy` 定义见 §4；每张的 region 均在画布内，且等于按墨迹框重算的校准规则值（verify 在重渲染时逐张核对）。

### 验收 4 — 四个 TP-S0-* 固定案例完全符合 PROJECT_BOOK.md §8.1 ✅ PASS

| 样本 | 期望 / 图绘 | 预期报告（manifest 与 expected_output.json 一致） | PNG SHA-256 |
|---|---|---|---|
| TP-S0-ZH-001 | `限时优惠` / `限时优` | 恰好 1 条 `MISSING_CHARACTER`，fragment `惠`/`""`，span `[3,4]`/`[3,3]`，verdict `MISMATCH` | `7d3a5c0b…ec660` |
| TP-S0-ZH-002 | `新品上市` / `新口上市` | 恰好 1 条 `SUBSTITUTION`，fragment `品`/`口`，span `[1,2]`/`[1,2]` | `d980c561…48e7f` |
| TP-S0-NUM-001 | `￥28.80` / `￥28.00` | 恰好 1 条 `NUMERIC_CHANGE`，fragment `8`/`0`，span `[4,5]`/`[4,5]` | `1b373beb…6a3a` |
| TP-S0-ZH-003 | `新客立减20元` / `新客立减元` | 恰好 1 条 `MISSING_CHARACTER`，fragment `20`/`""`，span `[4,6]`/`[4,4]`（相邻缺失合并一条，与 T004 golden 一致） | `1951e5d0…7887` |

- 上表由 `--verify-manifest` 的 S0 专段逐字断言（另见 `test_s0_four_samples_exact`）。
- 全部 1200×480 PNG，白底黑字；`bbox_scope` 均为 `ocr_line`，bbox 规则为“bbox_xyxy 等于包含该错误的 OCR 行框；IoU(ocr_bbox, target_region_xyxy) ≥ 0.80”。
- 与 T004 compare 的交叉核对：300 个 fixture 全部通过——把图绘文本当作固定 OCR 行记录喂给 T004 `compare`，其 verdict 与错误（类型/片段/span）与 manifest 记录逐条一致（`test_expected_reports_match_t004_compare`）。此核对不依赖 OCR 引擎。

### 验收 5 — 盲测子集不少于 60 张，单独保存 ID 列表与 SHA-256 ✅ PASS

- `tests/fixtures/s0/blind_subset.json`：60 张，分层抽样（clean 20、substitution 14、omission 14、numeric_change 12），独立 seed 20261126，每条含 id + SHA-256，与 manifest 逐条核对（`--verify-manifest` 与 `test_blind_subset`）。
- 盲测纪律：target_region 的校准只用了 240 张非盲测图片的实测 OCR 框（见 §4）；盲测 60 张在拟合中一次未用，只在最后做了一次整体测量（结果见 §5）；生成器本身不区分盲测/非盲测。

### 验收 6 — 测试样本中不得混入网络图片、用户图片、真实人物照片或真人标注 ✅ PASS

- 全部 300 张均由 `scripts/generate_fixtures.py` 用 Pillow 程序渲染；文本来自生成器内置词表组合（中文促销短语、英文、价格、混排），无任何外部图片、用户图片、真实照片或人工标注。生成器不读取除随包字体外的任何外部文件。

### 验收命令

```bash
/home/hatch/workspace/p033-textproof/.venv/bin/python scripts/generate_fixtures.py --verify-manifest tests/fixtures/s0/manifest.json
```

- 退出码 **0**，输出：`VERIFY OK: 300 fixtures, counts={...}, font=Noto Sans SC 2.004-H2 sha256=a3041811a78c361b...`（完整输出见 `test_stdout.log` CMD1）。
- `--verify-manifest` 不只是读 manifest：它逐张重渲染并比对 PNG 字节与 SHA、核对 target_region、核对 expected_output.json 与盲测清单、逐字核对四个 S0 样本。

## 3. 字体：Noto Sans SC（OFL，仅用于合成测试图片）

| 项目 | 值 |
|---|---|
| 文件 | `tests/fixtures/s0/fonts/NotoSansSC[wght].ttf`（17,772,300 B，随包） |
| 官方来源 | https://github.com/google/fonts/raw/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf（Google Fonts 仓库 `ofl/notosanssc`） |
| 版本（name 表 ID 5） | 2.004-H2（`Version 2.004-H2;hotconv 1.0.118;makeotfexe 2.5.65603`） |
| SHA-256 | `a3041811a78c361b1de50f953c805e0244951c21c5bd412f7232ef0d899af0da` |
| 许可 | SIL Open Font License 1.1（全文随包 `fonts/OFL.txt`，SHA-256 `1c05c68c34f9708415aada51f17e1b0092d2cea709bf4a94cd38114f9e73d7d9`） |
| 渲染档位 | 可变字体命名实例 `Regular`（wght 400，64 px）；字体默认实例为 Thin（wght 100），生成器显式 `set_variation_by_name("Regular")` 并断言 |
| 下载 | 2026-11-25 构建期一次下载（HTTP 200）；生成与测试零外网 |

- 记录位置：`manifest.json` 的 `font` 段、`tests/fixtures/s0/fonts/FONT_NOTICE.md`、生成器内嵌常量（生成/验证时逐字节核对 SHA 与大小）。
- `THIRD_PARTY_NOTICES.md` 未改动（不属于 T005 文件所有权；字体许可复核留给 T014 的 SBOM/license report，本任务已在 FONT_NOTICE.md 与 manifest 中完整记录）。

## 4. 关键设计判断（写在生成器 docstring 中，此处摘要）

1. **target_region 的校准规则。** 第一版定义（墨迹框横向扩 16 px、纵向固定 100 px）下，实测 RapidOCR 框的 IoU 有 58/300 低于 0.80。原因：检测框高度随文本宽度系统性变化（实测：墨迹宽 100–199 px 的行 OCR 框高均值 ~101 px，600–699 px 的行 ~80 px），且随墨迹高度变化（中文墨迹 ~60 px，拉丁大写墨迹 ~49 px）；固定高度的 region 无法同时贴合短行与长行。改用墨迹几何的线性规则（以墨迹框中心为中心）：`height = 70 + 0.7*ink_height - 0.05*ink_width`，`width = ink_width + 40 - 0.02*ink_width`。该规则只用 240 张非盲测图片的实测 OCR 框拟合，是墨迹几何的光滑函数，不用任何一张图片自己的 OCR 输出；盲测 60 张未参与拟合。`unclip` 公式（`d = k·w·h/(2(w+h))`）实测不成立（dx/u 均值 0.51±0.20，dy/u 0.71±0.28），故未采用。
2. **生成期发现的两个真实问题并修复。** (a) 漏字变异若删空格相邻字符，图绘文本出现双空格，§4.3 规范化将其折叠后 T004 compare 会把缺失片段报成 `" 1"`（空格+字符）而非单个字符——生成器现跳过空格相邻位置（由 `test_expected_reports_match_t004_compare` 抓出 TP-OMI-046 后修复并重生成）。(b) 漏字变异跳过与邻字符重复的位置，避免缺失 span 对齐歧义。
3. **文本池的规范化不变量。** 全部池文本均为 NFC、半角 ASCII、无全角空格，生成器逐条断言（否则 span 索引会与 §4.3 规范化后文本错位）。货币符号只用 U+00A5 `¥`（RapidOCR 原样返回）；全角 `￥`（U+FFE5）只出现在 §8.1 冻结的 TP-S0-NUM-001，verify 对此强制断言。
4. **变异规则。** substitution 只换同类非数字字符（中文→中文、拉丁大/小写→同 case 字母），避免数字替换被 T004 判为 `NUMERIC_CHANGE`；omission 删 1 个字符（S0-ZH-003 删相邻 2 个字符 `20`，合并为一条错误，与 T004 一致）；numeric change 只换 1 位数字。全部 expected_errors 由构造（期望文本 + 图绘文本 + 变异记录）直接算出，不跑 OCR、不调 compare。

## 5. 实测证据（单次 OCR 测量 pass，非调参）

2026-11-25 用 T003 的 RapidOCR 适配器（CPU-only）对 300 张 fixture 各跑一次 OCR（`/tmp/t005_ocr_probe.py`，结果 `/tmp/t005_ocr_probe.jsonl`；该脚本不在交付物内，仅为测量探针）：

| 指标 | 结果 |
|---|---|
| 单行 OCR | 300/300（无多行、无零行） |
| OCR 文本与图绘文本完全一致 | 298/300 |
| OCR 置信度 | 最小 0.914，均值 0.991；低于 0.65 的 0 行 |
| IoU(ocr_bbox, target_region) | 全部 300 张：最小 **0.829**，均值 0.938，低于 0.80 的 **0 张** |
| IoU — 非盲测 240 张（校准集） | 最小 0.829，均值 0.938，低于 0.80 的 0 张 |
| IoU — 盲测 60 张（未参与拟合） | 最小 **0.835**，均值 0.940，低于 0.80 的 **0 张**（校准规则泛化成立） |
| 四个 S0 样本 IoU | ZH-001 **0.964**、ZH-002 **0.955**、NUM-001 **0.875**、ZH-003 **0.924** |

### 已知 live-OCR 差异（2 项，T006 / S0 需注意，非 fixture 错误）

1. **TP-S0-NUM-001 的 `￥`→`¥`。** 图绘 `￥28.00` 被实测 OCR 读作 `¥28.00`（U+FFE5 → U+00A5，置信度 0.93）。T004 compare 对此会多报一条 `SUBSTITUTION ￥→¥ [0,1]`，即 live-OCR 路径下该样本为 2 条错误而非 §8.1 固定的恰好 1 条 `NUMERIC_CHANGE`。fixture 本身按 §8.1 冻结（图绘 `￥28.00` 不可改）；T006 的 S0 live-OCR 核对需为此定一条书面规则（例如：固定 OCR 行记录路径保持恰好 1 条；live 路径核对“预期的 NUMERIC_CHANGE 存在”并记录该额外替换），或由规格方裁定是否在 compare 中规范化 `￥`/`¥`（需 ADR 与 Owner 批准，T005 无权改）。
2. **TP-SUB-055 的空格丢失。** 图绘 `TOP 当季上馈` 被读作 `TOP当季上馈`（拉丁与中文之间的空格丢失，置信度 1.000，IoU 0.979）。live-OCR 路径下该样本会多出一条空格缺失；注入的 substitution 本身仍被检出。属 OCR 引擎的混排空格行为，fixture 不改。

## 6. 测试结果

| 命令 | 退出码 | 结果 |
|---|---|---|
| `python scripts/generate_fixtures.py --verify-manifest tests/fixtures/s0/manifest.json` | 0 | VERIFY OK（300 张） |
| `python -m pytest tests/unit/test_fixtures_s0.py -q` | 0 | 7 passed（21.13s） |
| `python -m pytest -q`（全量） | 0 | **174 passed**，2 warnings（均为 T002 既有的 Pillow DecompressionBombWarning，与本任务无关） |
| 独立重生成到 `/tmp/t005-regen3` 并比对 SHA 清单 | 0 | 300/300 一致 |

- 全量 174 = 既有 167 + 新增 7；既有测试零回归。
- 完成定义（连续两次生成 SHA 清单完全一致）：除上表 CMD4 外，`test_two_generations_are_byte_identical` 在 pytest 内另做两次重生成并与 manifest 比对，同样通过；此前 `/tmp/t005-regen2` 的一次独立重生成亦 300/300 一致。

## 7. 未完成项与风险

- **未完成项：无。** T005 任务卡的 3 个输出文件组与 6 项验收标准全部完成；验收命令 exit 0；全量测试 174 通过。
- **风险 1（需 T006 裁定）：TP-S0-NUM-001 的 live-OCR `￥`→`¥`额外替换（见 §5.1）。** 若 S0 对该样本做“恰好 1 条错误”的 live-OCR 断言会失败；T004 的固定 OCR 行记录路径不受影响。建议 T006 在 `S0_REPORT.md` 中书面记录处理规则，不得为通过而改 fixture 或删样本。
- **风险 2（已缓释）：target_region 规则是按 PP-OCRv6 实测框校准的经验规则。** 若 T006 换 OCR 引擎/版本或改字号，region 与实测框的对应关系需重测；规则与校准数据（240 张非盲测）已完整记录在生成器 docstring、manifest 与本报告 §4，复现路径明确。
- **风险 3（记录）：`tool_version` 0.1.0 与 `pyproject.toml` 1.0.0 不一致**（T004 已登记，本任务未改禁改文件；与 T005 无关，仅转述）。
- **风险 4（记录）：TP-SUB-055 的 live-OCR 空格丢失（见 §5.2）。** 仅影响 live-OCR 路径下该样本的额外误差，不影响注入检出；S0 召回统计时应按“注入差异是否检出”计分，而非按“报告错误数恰好等于注入数”计分（后者在 live-OCR 下会被 OCR 自身误差污染）。

## 8. 回退

- 回退 commit：`c5511e1`（T005 之前的状态；本任务只新增文件，无任何修改，`git revert 6cfabb6` 或直接删除分支即可完整回退）。
- 失败回退（按计划）：fixture 不可复现则 S0 不得启动；本次两次独立重生成 SHA 清单 300/300 一致，复现性已证实，无需回退。
