# P033 TextProof — T013 集成线交接（供独立复审）

- 集成线：分支 `t013-fix`，HEAD `fd00def`（合并提交），基线冻结候选 `ffe53ea`（分支 `t011-full-regression`）
- 集成 worktree：`~/workspace/p033-textproof-t013`
- 6 个修复分支全部干净合并（无冲突）：t013-r01、t013-r02、t013-r04、t013-r05、t013-r09、t013-p3
- 协调员已亲自验证：全量 pytest **489 passed、0 failed、exit 0**（424.46s；436 基线通过 + 2 项 R-02 已修复 + 51 项新增）；S0 `--force-live`（300 张 live OCR）**exit 0、PASS**（召回 100%、clean FPR 0%、schema 100%、CER 0.0008、IoU 最小 0.829、parity 300/300、[3L] live NUM-001 PASS、CPU-only）

## 逐项处置表（31 项 findings，R-01…R-31）

| Finding | 级别 | 处置 | 修复 commit | 回归测试 |
|---|---|---|---|---|
| R-01 align_lines 浮点比较 | P1 | 已修：Fraction 精确算术（align_lines + weighted_edit 回溯 `==` 一并处理） | d26adcc8 | 4 项新增（A 案 40 字符行、B 案 0.05 边界、gap 求和、加权距离）；repro_f01.py 修复后 exit 1 |
| R-02 consistency_check 在扫描树内 | P1 | 已修：`git mv` scripts/ → tests/consistency_check.py；扫描门禁未动；T011 两处文档路径已更新 | 86fb673 | 16 项新增（tests/unit/test_consistency_check.py）；test_no_persistence.py 24 项全过 |
| R-03 字典许可 UNVERIFIED | P1 | T014 归属（公开再分发前必修）；T013 只确认归属与截止，未改许可声明 | —（P3_DISPOSITION.md 记录） | — |
| R-04 日志绝对路径 | P1 | 已修：(a) adapter 报错只用文件名；(b) run_check 内资产构造失败映射为 OCR_FAILED（500），只记类型名、不记消息/traceback | 09d101c | 1 项新增（test_missing_asset_logs_contain_no_absolute_path）；运行时探针复核：HTTP 500 OCR_FAILED，server.log 仅一行、无绝对路径 |
| R-05 校验器 expected_lines 公式 | P2 | 已修：校验器按“统一换行后再切分”计数（与 image_loader.py 同规则） | a5ebd27 | 21 项新增中的 R-05 部分；'a\rb' 修复后校验器与生产均为 2 |
| R-06 一致性证据留存不足 | P2 | 已修：每案独立文件名 api/cli/ui-\<case\>.json + 每份 SHA-256 记录；新证据在 task_handoffs/T013/consistency/ | 86fb673 | 同上 16 项；完整回环校验 exit 0，两案三路 IDENTICAL |
| R-07 helper 无回环约束 | P2 | 已修：`_require_loopback` 断言 base 以 http://127.0.0.1: 开头；轮询异常改为记录后重试 | 86fb673 | 同上 16 项（回环接受/拒绝 8 类 + 真实回环服务器 GET/POST） |
| R-08 写盘无清理 + 打印 fixture 文本 | P2 | 已修：finally 删除 scratch 三文件；stdout 只剩 case id 与 verdict；docstring 声明不得用于真实用户图片 | 86fb673 | 同上 16 项（清理保留证据、docstring 声明） |
| R-09 S0 VERDICT 未覆盖 §8.4 全部硬门 | P2 | 已修（选 a）：限定表述 `VERIFY_S0 ITEMS: PASS (script-checked items only)` + NOTE 重写；字面 `S0 VERDICT: PASS` 有意保留（tests/offline/test_offline_namespace.py:151 断言该字面串，禁改测试预期） | eca5440 | 9 项新增中的 R-09 部分 |
| R-10 gate_pass 无 timing 门槛 | P2 | 已修：未加 timing 判定（fixture 是 1200×480，非 §8.3 的 1920×1080）；gate_pass 加注释 + S0_REPORT.md 标注“由 T011 性能报告判定（P95 3.817s，PASS）” | eca5440 | 9 项新增中的 R-10 部分（P95=99.0 与 3.817 均通过 gate_pass） |
| R-11 live NUM-001 2 条错误 | P2 | 已修（选 b）：verify_s0.py 新增 check_live_num_001()（[3L] 项接入 all_pass）：恰好 1 条 NUMERIC_CHANGE + 至多 1 条已知 ￥→¥ SUBSTITUTION；固定记录路径不变 | eca5440 | 9 项新增中的 R-11 部分（合成 live 结果）；--force-live 实测 [3L] PASS；反向控制（3 条错误 → FAIL/exit 1） |
| R-12 字体记录未汇总 | P3 | 已修：THIRD_PARTY_NOTICES.md §6 汇总（2.004-H2、SHA a3041811…、OFL-1.1、OFL.txt SHA 1c05c68c…），口径写明 | 7540c4f | 文档核对（SHA 实测一致） |
| R-13 LICENSE/README/SECURITY 缺失 | P3 | T014 归属（发布打包），截止公开再分发前 | —（记录） | — |
| R-14 verify-s0 exit 1 同值异义 | P3 | 已修：PROJECT_BOOK.md §5.5 加注（verify-s0 0/1 与 check 退出码表无关；未改退出码） | 7540c4f | 文档核对 |
| R-15 存在侧行索引 null 可放行 | P3 | 已修：schema 三处 then 块 + 校验器三处分支均要求存在侧索引非空；300 fixture 期望输出新 schema 300/300 有效、新校验器 0 拒绝 | a5ebd27 | 21 项新增中的 R-15 部分；反例修复前后对比 |
| R-16 version 端点字段不对称 | P3 | 非阻断（两者均合规；未碰 routes.py） | —（记录） | — |
| R-17 验证脚本打印 fixture 文本 | P3 | 非阻断（合成 fixture、stdout 证据通道） | —（记录） | — |
| R-18 证据含本机绝对路径/主机名 | P3 | 非阻断（环境元数据、非用户内容） | —（记录） | — |
| R-19 UDP 仪器缺口 | P3 | 非阻断（全树 0 命中，仪器缺口而已） | —（记录） | — |
| R-20 快照监视范围边界 | P3 | 非阻断（监视范围有界；__pycache__ 为解释器产物） | —（记录） | — |
| R-21 Chrome profile 残留 | P3 | 非阻断（仅锁文件，无用户数据） | —（记录） | — |
| R-22 sys.path.insert(0) 遮蔽 | P3 | 非阻断（根目录无同名文件，仅纵深防御备注） | —（记录） | — |
| R-23 歧义按“路径”计 | P3 | 已修：§7.2 补“歧义按不同配对集合计” | 7540c4f | 文档核对 |
| R-24 混淆对“如”非穷尽 | P3 | 已修：§4.5“如”→“即以下集合”，冻结 6 对 | 7540c4f | 与 weighted_edit.py 逐对一致 |
| R-25 两警告码从未发出 | P3 | 已修：§5.3 注明为保留码、暂无检测器 | 7540c4f | 文档核对 |
| R-26 空识别区分未实现 | P3 | 已修：§7.6 冻结映射（引擎异常 → OCR_FAILED；空识别 → OCR_FAILED + OCR_EMPTY） | 7540c4f | 实现已是如此，未改代码 |
| R-27 错误顺序 extra-then-missing | P3 | 已修：§7.2 注明按对齐顺序编号、gap 段以回溯为准 | 7540c4f | 两处锁定测试未动 |
| R-28 尾随换行计行 | P3 | 已修：§4.2 注明尾随换行计入 100 行 | 7540c4f | 文档核对 |
| R-29 行聚合口径未冻结 | P3 | 已修：§4.4 冻结（只与最后一行比较、允许链式并入） | 7540c4f | 文档核对 |
| R-30 计划引用交付物缺失 | P3 | 记录：verify_review_pack.py 豁免（由 T012 REVIEW_INDEX.md 替代）；verify_release.py + release/ 属 T014 | —（记录） | — |
| R-31 锁文件“33 个包” | P3 | 已修：ENVIRONMENT.md §4 33 → 37（实测 37 包、753 哈希；lock SHA 不变） | 7540c4f | grep 实测 |

## 禁令遵守（复审请抽查）

- 未改 tool_version（仍 0.1.0）；未缩小 T010 隐私扫描范围、未加白名单、未用 curl；未加 ￥→¥ 映射；未改测试预期、fixture PNG、manifest、S0 门槛、输入输出契约。
- 各修复分支文件集互不重叠，6 次合并无冲突。改动文件清单见 `git diff --name-only ffe53ea fd00def`。

## 协调员注意到的变化（非门禁项，供复审判断）

- 边缘电池（诊断性质，非门禁）：S0 裁决时 13/26，本次 --force-live 为 **14/26**（多一项匹配；差异列表见 S0 输出）。属诊断电池，不影响 S0 判定；可能与 R-01 精确算术修正了某一边缘 case 有关。
- S0 --force-live 在本集成树上重写了 task_handoffs/T006/live_ocr_results.jsonl 与 s0_metrics.json（工作树内未提交的证据输出）；复审重跑时会再次更新，以复审自己的运行为准。
- R-09 保留字面 `S0 VERDICT: PASS` 的决定：因 tests/offline/test_offline_namespace.py:151 断言该字面串，且任务禁改测试预期；限定词与原串同行。复审若认为应彻底改名，须指出该测试需同步更新（属测试预期改动，需另行裁决）。

## 各修复交接文件

- task_handoffs/T013/r01/TASK_RESULT.md、r02/TASK_RESULT.md（含 full_pytest.log）、r04/TASK_RESULT.md、r05/TASK_RESULT.md、r09/TASK_RESULT.md、p3/P3_DISPOSITION.md
- T012 审查报告：~/workspace/p033-textproof-t011/review/REVIEW_FINDINGS.md（31 项原文）
