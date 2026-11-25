# FIX-R1-01 验证报告：四份冻结规格统一权威版本（修复终审 R1 P1-01）

- 执行时间：2026-11-25 ~19:59–20:03 GMT
- 执行者：FIX-R1-01 子任务执行员
- 工作目录：`~/workspace/p033-textproof/`，分支 `fix-r1`，HEAD `16a3ef5`
- 结论：**PASS。4/4 文件工作区与 Drive 一致；PROJECT_BOOK.md/.docx 已同步为 T013 后新版，重新下载逐字节核对一致。**
- 未提交任何东西，未切换分支。唯一改动：`PROJECT_BOOK.docx`（重新生成）+ 新增生成脚本 `scripts/md_to_docx.py`（未追踪）。

## 1. 最终对照表（全部数字均为本次亲自实测）

| 文件 | 工作区大小 | 工作区 SHA-256 | Drive 大小 | Drive SHA-256（重新下载实测） | 一致 |
|---|---|---|---|---|---|
| PROJECT_BOOK.md | 46,114 B | `8a2b6e56…c496a` | 46,114 B | `8a2b6e56…c496a` | 是 |
| PROJECT_BOOK.docx | 62,512 B | `97706fc9…508464` | 62,512 B | `97706fc9…508464` | 是 |
| IMPLEMENTATION_PLAN.md | 35,772 B | `2d2ac3f3…113c2` | 35,772 B | `2d2ac3f3…113c2` | 是 |
| IMPLEMENTATION_PLAN.docx | 58,745 B | `c6d2b3a6…c385` | 58,745 B | `c6d2b3a6…c385` | 是 |

完整 SHA-256：

- PROJECT_BOOK.md：`8a2b6e565df88a2f6371879cdcfbb613500c8cc2ecee50376b8da95d7ecc496a`
- PROJECT_BOOK.docx：`97706fc9c542670245dbc28e31e174e3824f4c7164dfc8ca4251bba4e0508464`
- IMPLEMENTATION_PLAN.md：`2d2ac3f3b6eec92037ae43b76bfe91a925537b1563a73b0a987763d0deb113c2`
- IMPLEMENTATION_PLAN.docx：`c6d2b3a6d925e62ed18a976afc71b577b90248d41aa50d884f4036280c51c385`

## 2. 同步前 Drive 状态（2026-11-25 19:59 GMT 下载实测，`drive_before/`）

| 文件 | 同步前 Drive 大小 | 同步前 Drive SHA-256 | 与工作区关系 |
|---|---|---|---|
| PROJECT_BOOK.md | 44,552 B | `0fc4ef3bb59253267d16506350436dcf7b0c820bb7c530c9f5283b96ba077dfc` | **旧版，不一致**（R1 P1-01 所述旧版，缺 7 处 T013 澄清） |
| PROJECT_BOOK.docx | 64,339 B | `4b788b1c85d6066b5889163c4b8a03f5ef19ff902691aff5b1af75adde81aba7` | 旧版 DOCX，与工作区旧 DOCX 相同 |
| IMPLEMENTATION_PLAN.md | 35,772 B | `2d2ac3f3…113c2` | 与工作区一致，未动 |
| IMPLEMENTATION_PLAN.docx | 58,745 B | `c6d2b3a6…c385` | 与工作区一致，未动 |

- `diff`（Drive 旧 PROJECT_BOOK.md vs 工作区新版）恰好只差 7 处 T013 澄清（5 处替换行 + 2 处新增行），与 R1 描述一致，无其他差异。
- IMPLEMENTATION_PLAN 两份 Drive 副本与工作区逐字节一致，因此按任务要求未做任何同步。

## 3. DOCX 生成方法

- 工具：本机无 pandoc；用已装的 python-docx 1.1.0。生成脚本：`scripts/md_to_docx.py`（留作证据，可复跑：`python3 scripts/md_to_docx.py`）。
- 生成前先用 python-docx 反推旧 DOCX 的渲染约定（旧文件 358 段落、14 表），逐项复用：
  - `# ` → Title；`## ` → Heading 2；`### ` → Heading 3；标题纯文本。
  - `> ` 引用行 → Normal 段落，**不解析**行内标记（`**` 与反引号原文保留，与旧文件一致）。
  - 正文 / `- ` / `N. ` 行 → Normal / List Bullet / List Number，解析行内标记：`**粗体**` → 粗体 YaHei，`` `代码` `` → Consolas，其余 Microsoft YaHei（含东亚字体属性）。
  - `---` → 一个空 Normal 段落；每张表后跟一个空 Normal 段落（旧文件 32 个空段 = 18 个 `---` + 14 张表后空段，复核一致）。
  - 围栏代码块 → 单个 Normal 段落、整块以 `\n` 连接、单个 Consolas run。
  - 表格：跳过分隔行，首行为表头（粗体），样式 `Table Grid`，单元格同样解析行内标记。
  - 空行跳过；其余每行恰好一个段落；行尾空白剥离。
- 新 DOCX：62,512 B（旧 64,339 B；差值来自生成器模板部件差异，内容经下述逐项核对无缺失）。

## 4. DOCX 结构核对（复用 SPECS_VERIFICATION.md §DOCX ↔ MD 结构核对方法）

对新 DOCX（python-docx 读回）实测：

- **Title 1 + Heading 66 = 67 个样式段落**；表格 **14**；67 个章节标题与 MD 的 67 个 `#` 标题**逐项同序**（§0–§16）。
- 段落总数 360（旧 358，+2 = T013 新增的 2 行：§5.5 注 + §7.2 错误排序行）；List Bullet 98、List Number 81、Normal 114（含 32 个空段），与 MD 行类型普查一致。
- 14 张表行列尺寸与旧 DOCX 逐表相同：(6,2)、(7,3)、(13,3)、(7,2)、(5,2)、(7,2)、(9,3)、(5,4)、(10,3)、(7,3)、(9,3)、(10,3)、(8,3)、(11,3)。
- 新旧 DOCX 段落级 diff：**除 7 处 T013 澄清外零差异**（5 处替换 + 1 处插入 + 1 处 1 段变 2 段，见 §5）。
- 全量 MD→DOCX 保真检查：MD 全部 177 行正文/引用行、98 条 bullet、81 条编号、14 张表全部单元格、5 个代码块内容，经行内标记还原后在新 DOCX 提取文本中**零缺失**。
- 未做逐页视觉审阅（与 SPECS_VERIFICATION.md 原核对口径相同，只做结构核对）。

## 5. 7 处 T013 澄清逐项定位（MD 行号 → 新 DOCX 验证）

定位方法：先 `diff` Drive 旧 MD 与工作区新 MD 确认 7 处，再用 python-docx 读回新 DOCX，在段落/表格提取文本中按锚定字符串检索；同时抽查行内代码段的 Consolas 字体。

| # | 澄清 | MD 位置 | DOCX 位置与锚定字符串 | 验证 |
|---|---|---|---|---|
| C1 | 尾随换行行数规则 | §4.2，MD L177（bullet 行） | 段落 102（List Bullet）：`尾随换行计入行数（即 "a\n" 计 2 行）；100 行文本加一个尾随换行计 101 行，予以拒绝`；`` `\n` `` / `"a\n"` 为 Consolas run | FOUND |
| C2 | OCR 文本框纵向行聚合规则 | §4.4，MD L197（bullet 行） | 段落 116（List Bullet）：`行聚合口径冻结为：新文本框只与当前最后一行的纵向区间比较重叠（重叠条件为 y1 <= hi and y2 >= lo）`；`y1 <= hi and y2 >= lo` 为 Consolas run | FOUND |
| C3 | 字符混淆对集合 | §4.5，MD L211（表 3 第 2 行第 0 列） | 表格 3（index 3）r2 c0：`常见视觉混淆对（即以下集合：O/0、I/1、I/l、1/l、S/5、B/8）替换`；6 个混淆对各为 Consolas run | FOUND |
| C4 | 保留警告码触发边界 | §5.2，MD L253 | 段落 144（Normal）：`其中 POSSIBLE_MULTI_COLUMN 与 ROTATED_TEXT_NOT_SUPPORTED 为保留码：本版本无对应检测器，从不发出；其触发条件未冻结，待检测规则冻结后再实现，不得凭空发明检测器` | FOUND |
| C5 | verify-s0 独立退出码说明 | §5.5，MD L340（新增行） | 段落 159（Normal，新增）：`注：textproof verify-s0 的退出码另有独立契约——0 表示 S0 门禁通过，1 表示 S0 门禁失败（原样透传 scripts/verify_s0.py 的通过 / 失败结果）；该 0/1 与上表 check 的退出码含义（0 = MATCH、1 = MISMATCH）无关`；`textproof verify-s0` / `scripts/verify_s0.py` / `check` / `MATCH` / `MISMATCH` 为 Consolas run | FOUND |
| C6a | 歧义对齐规则 | §7.2，MD L455 | 段落 193（Normal）：`歧义按不同配对集合计：仅当存在代价差小于 0.05 的另一组不同配对集合时才判歧义；同一配对集合内 gap 顺序不同（先缺失后额外与先额外后缺失）不计为不同对齐` | FOUND |
| C6b | 错误排序规则 | §7.2，MD L457（新增行） | 段落 194（Normal，新增）：`错误按对齐顺序编号（E001、E002、……）；同一 gap 连续段内错误的顺序以回溯实现为准（当前实现为先额外行、后缺失行），不保证按直觉的先缺失后额外顺序`；`E001` / `E002` 为 Consolas run | FOUND |
| C7 | OCR_EMPTY 的 verdict 映射 | §7.6，MD L484 | 段落 211（Normal）：`OCR 无可用文本时按以下冻结映射判定：引擎异常 → OCR_FAILED；空识别（引擎正常返回但无可用文本）→ OCR_FAILED 并附 OCR_EMPTY 警告。空识别不判 REVIEW_REQUIRED` | FOUND |

8 个锚定字符串全部在新 DOCX 提取文本中命中（C6 拆为 a/b 两项）。

## 6. Drive 操作记录

Drive 连接状态：`connected`（操作前核查）。文件夹：P033-textproof（`1ovRjSwX2eioP8XGzZa_I_arpauOsrRBr`）。

| 操作 | 文件 ID | 时间（GMT） | 结果 |
|---|---|---|---|
| 下载 PROJECT_BOOK.md（同步前） | `1wFI_OAfye3_ft_ktiRt5dgTsTsGa1I_g` | 2026-11-25 19:59:14 | 44,552 B，SHA `0fc4ef3b…77dfc`（旧版） |
| 下载 PROJECT_BOOK.docx（同步前） | `1Pprli78AucDctlpNacNLMbafTMfx8J86` | 2026-11-25 19:59:15 | 64,339 B，SHA `4b788b1c…1aba7`（旧版） |
| 下载 IMPLEMENTATION_PLAN.md（同步前） | `1-_xCz6jUrhDsOliUCiV_vHvEi_OfeMzJ` | 2026-11-25 19:59:16 | 35,772 B，SHA `2d2ac3f3…13c2`（与工作区一致） |
| 下载 IMPLEMENTATION_PLAN.docx（同步前） | `11ocoNski5C8y3QYP9LifDMcKoeE9uZdl` | 2026-11-25 19:59:17 | 58,745 B，SHA `c6d2b3a6…c385`（与工作区一致） |
| `files update` 替换 PROJECT_BOOK.md | `1wFI_OAfye3_ft_ktiRt5dgTsTsGa1I_g` | 2026-11-25 ~20:03 | 成功，ID 不变 |
| `files update` 替换 PROJECT_BOOK.docx | `1Pprli78AucDctlpNacNLMbafTMfx8J86` | 2026-11-25 ~20:03 | 成功，ID 不变 |
| 重新下载 PROJECT_BOOK.md 核对 | `1wFI_OAfye3_ft_ktiRt5dgTsTsGa1I_g` | 2026-11-25 20:03:29 | 46,114 B，SHA `8a2b6e56…c496a`，`cmp` 逐字节一致 |
| 重新下载 PROJECT_BOOK.docx 核对 | `1Pprli78AucDctlpNacNLMbafTMfx8J86` | 2026-11-25 20:03:29 | 62,512 B，SHA `97706fc9…508464`，`cmp` 逐字节一致 |

- IMPLEMENTATION_PLAN 两份文件 Drive 副本与工作区一致，**未做任何替换**。
- 证据副本：同步前下载存于 `task_handoffs/FIX-R1/drive_before/`（含工作区旧 DOCX 备份 `PROJECT_BOOK.docx.worktree-old`）；同步后重新下载存于 `task_handoffs/FIX-R1/drive_after/`。
- Drive 命令口径按 `/opt/hatch/connectors/google_drive/CONNECTOR.md`：下载用 `files get --params '{"fileId":"<id>","alt":"media"}' --output <path>`，替换用 `files update --params '{"fileId":"<id>"}' --upload <absolute_path>`。

## 7. 残留说明

- 无未解决困难。DOCX 生成无结构难题：表格、代码块、行内标记均按旧文件约定复现并通过逐项核对。
- 注意：新 DOCX 比旧 DOCX 小 1,827 B（62,512 vs 64,339），系生成器模板部件差异；段落/表格/标题/全部正文内容已逐项核对无缺失（§4）。
- R1 P1-02（REVIEW_INDEX.md 缺失）与 P1-03（§8.3 性能重测）不在本子任务范围内，未处理。
