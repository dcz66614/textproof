# P033 TextProof — T014 主聊天裁决：PASS

裁决时间：2026-11-25 ~16:40 GMT。协调员 c177b280 汇报 T014 完成，两轮独立复审均为 FINAL_VERDICT: PASS。本裁决为主聊天亲自核实后的结论。

## 主聊天亲自核实

1. **全量 pytest：495 passed，exit 0**（主聊天在集成树 t014-fix HEAD a9eb45f 上亲自跑，196.89s，2 warnings）。
   - 第一遍跑出 28 failed + 10 errors（457 passed），与协调员的 495-passed  claim 不符。查因：主工作区缺字典文件 `assets/ocr/dictionaries/ppocrv6_dict.txt`——T014/R-03 把它移出 git 追踪后，本工作区从未重建；所有失败均为 `FileNotFoundError`（adapter `_verify_assets` 拒绝运行时下载），属环境缺件，不是产品缺陷。
   - 按新流程 `scripts/setup_dictionary.py` 本地重建：SHA-256 `b5f2bfe2bdd9448429e3e82b51c789775d9b42f2403d082b00662eb77e401c5d`、18,708 行，与协调员声称的逐字节一致值相符；重跑后 495 passed。
   - 教训：R-03 之后任何新 checkout/工作区跑全量测试前必须先重建字典；T014 的验收流程应把这一步写进前置条件。
2. **verify_release.py：27/27 PASS，exit 0**（主聊天亲自跑），与协调员 claim 一致。未解决非阻断项 U-02（DOCX 正文漂移）、U-03（omegaconf 2.4.0 SBOM 无许可声明）如实列出。
3. **字典不在 git 追踪中**：`git ls-files` 中 `ppocrv6_dict.txt` 零命中（仅 setup 脚本与裁决文件含 "dict" 字样）；`.gitignore` 已列 `assets/ocr/dictionaries/ppocrv6_dict.txt` 与包内路径。R-03 合规方案成立：UNVERIFIED 维持（RapidOCR 许可页 §2/§6 明确排除 dict_url 字典；PaddleOCR 仓库级 LICENSE 未指明覆盖该数据文件；文件本身无许可头），字典本地重建、不联网。
4. **两轮独立复审报告均含 FINAL_VERDICT: PASS**：首轮 `~/workspace/p033-textproof-t014-review/task_handoffs/T014/review/REVIEW_REPORT.md`（t014-review commit 51880ad，行 214）；增量复审 `~/workspace/p033-textproof-t014-review2/task_handoffs/T014/review2/REVIEW_REPORT.md`（t014-review2 commit 59bf0df，行 192）。
5. **冻结 commit 存在**：`93d1b7c`（T014R3，R14-01 修复）。集成线 `t014-fix` HEAD `a9eb45f`。合并前 master 为 `9cfaace`（未动）。

## 结论

**T014 PASS。** R-03 字典许可、R-13 发布文件与打包、U-01（已安装 wheel 无法独立运行 check/serve）均已修好并经两轮独立复审 + 主聊天重跑验证。未解决项均为非阻断：U-02、U-03，以及 R14-02/R14R-03 指出的 source.zip 体积叠加（现 512MB，因冻结 commit 本身入库了 `release/` 旧产物嵌套）——后者须在 GitHub 快照准备时处理（快照策略：排除嵌套旧产物；未来冻结不再把 `release/` 产物入库）。

## 合并

`t014-fix`（a9eb45f）合并进 master（见合并提交）。下一步：Drive 归档 → 终审（新对话，GPT-6.2 + Extra High）→ PASS 后公开上传 GitHub（快照须排除字典文件与 512MB 嵌套旧产物）。
