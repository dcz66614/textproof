# P033 TextProof — S0 门禁：主聊天复核裁决 S0 PASS

- 裁决时间：2026-11-25 ~07:20 GMT；裁决人：主聊天（Muse）
- 冻结依据：项目书 §8.4 + IMPLEMENTATION_PLAN.md T006 任务卡
- 构建者提交：T006 commit `0ad56d6`（分支 t006-s0-gate），合并 `4ae03dd`；Oracle 任务 `8f89548`，合并 `732f07e`；报告 `S0_REPORT.md`

## 我亲自重跑的证据（非只信报告）

- `scripts/verify_s0.py --manifest tests/fixtures/s0/manifest.json --force-live`（本机 .venv，300 张 live OCR，11 分钟，exit 0）：**S0 VERDICT: PASS**
  - [1] Oracle 独立性 PASS；[0] manifest 300 PNG SHA-256 PASS
  - [3] 四个 §8.1 固定案例全 PASS（生产与 Oracle 各 error_count 1，verdict MISMATCH 一致）
  - [2] parity 固定记录 300/300 PASS；边缘电池 13/26（诊断性质，与构建者一致）
  - [4] 召回率 100.00%（201/201；替换 70/70、缺失 71/71、数字 60/60）≥95%/每类≥90% PASS
  - [5] clean 误报率 0.00%（0/100）≤8% PASS
  - [6] JSON schema 合法率 100%（300/300）；CER 0.0008（S=1、D=1，单独报告）
  - [I] IoU 最小 0.829、均值 0.938，盲测 60 张最小 0.835，0 张 < 0.80 PASS
  - [7] ONNX provider 全部 CPUExecutionProvider PASS
- `scripts/independent_verify.py --case <四案>` 逐案重跑：四案全部 **INDEPENDENT VERIFICATION: PASS**（ZH-001 IoU 0.964、ZH-002 0.955、ZH-003 0.924）
- NUM-001 `--strict-live` exit 1，与报告所述一致（额外错误如实记录，见下）

## 裁定 (a)：NUM-001 live-OCR 多出一条 SUBSTITUTION（￥→¥）——采纳构建者的按类型计数读法，样本仍满足 §8.1

我自己的 live 运行逐字复现了该记录：expected `￥28.80`，drawn `￥28.00`，OCR 读作 `¥28.00`（置信度 0.93004），E001 SUBSTITUTION（￥→¥，[0,1]）+ E002 NUMERIC_CHANGE（8→0，[4,5]）。采纳理由：

1. §8.1 原文“恰好 1 条 NUMERIC_CHANGE”计数修饰的是带类型的错误；同表 ZH-003 写“至少 1 条 MISSING_CHARACTER”，证明该栏按类型计数；§12.2 对 ZH-001 写 `error_count: 1`，证明规格在指总数时会明确写总数。
2. 固定 OCR 记录路径下该样本恰好只有 1 条错误（即该条 NUMERIC_CHANGE），两种读法在冻结的门禁范围内都通过；门禁项 [3] 我重跑即为此路径，error_count 1。
3. 多出的 SUBSTITUTION 是 OCR 引擎行为（全角 ￥ 读作半角 ¥），如实记录、未删除；CER 的 S=1 正在度量此类差异。§4.3 只映射 U+FF01–U+FF5E，￥（U+FFE5）不在其内，删掉该错误或视为相同都需要 ADR，本任务无权做。
4. 若终审采用“总错误数恰好为 1”的读法，该样本在 live 路径下不满足——此分歧点已在 S0_REPORT.md §6(a) 写明，供终审裁决；本裁决不掩盖它。

## 裁定 (b)：target_region 校准方法合法，盲测验证成立

规则是墨迹几何的确定性函数（只用 ink_bbox）；构建者核对 manifest region 300/300 复现；盲测 60 张未参与拟合；我重跑 IoU 数值与 T005 一致。

## 范围声明（门禁定义本身，终审可见）

- 门禁项 2 的冻结范围是“manifest 的固定 OCR 行记录”，该范围内 parity 100% PASS；边缘电池 13/26 为诊断性质，不在冻结范围内。
- F-01（P1，真实生产缺陷：`align_lines` 浮点比较，`0.7-0.65 = 0.04999999999999993 < 0.05`，单字符 O→0 混淆时生产判 AMBIGUOUS 而 Oracle 判 MISMATCH 正确；300 fixture 零触发）**不在冻结 parity 范围内、对 S0 指标零影响**，按工厂纪律记为 **T013 的 P1 必修项**，不是 S0 失败。
- F-03（P1，规格澄清：行级错误缺失侧 span、`bbox_scope`、警告对象形态——规格未写明）记为 **T009 的 schema 统一口径项**。
- F-02（低，Oracle 阅读顺序与 §4.4 字面不符，生产正确）与 F-04（低，空期望 + 空 OCR 的 verdict，产品内不可达）如实记录。
- 未测项：1920×1080 P95 ≤5s 运行时间 NOT_MEASURED（冻结 fixture 为 1200×480），归 T011；正式 `.schema.json` 是 T009 的交付物。

## 裁决

**S0 VERDICT: PASS。解锁 T007–T014。** 构建者报告与我独立重跑的证据一致；两项分歧点与四项发现均已书面记录并分派，无一被掩盖。
