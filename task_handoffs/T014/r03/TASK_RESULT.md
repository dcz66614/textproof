# TASK_RESULT — P033 T014 / R-03：识别字典许可

- 任务 ID：T014-R03（审查发现 R-03，T012 REVIEW_FINDINGS.md §R-03，P1）
- 输入 commit：9cfaace（T011+T013 已合并；T013 主聊天裁决 PASS，全量 489 passed，S0 PASS）
- 输出 commit：e38b6d7（实施提交；本交接包文件另见本分支其后提交）
- 工作区：`~/workspace/p033-textproof-t014-r03`，分支 `t014-r03`
- 日期：2026-11-25

## 结论（先说结果）

1. **许可核实：UNVERIFIED（维持，不改判）。** 本轮重新核实（非复述 T003）未找到任何能明确、无歧义证明 `ppocrv6_dict.txt` 可再分发的来源；唯一针对字典本身发声的权威来源——RapidOCR 官方模型许可页——明确将其排除在 Apache-2.0 声明之外。完整来源记录见 `LICENSE_VERIFICATION_R03.md`（本目录）。
2. **合规打包方案已实施并验证：** 公开产物不再含字典单独文件；用户侧用新脚本 `scripts/setup_dictionary.py` 从本机已随包分发的 Apache-2.0 模型文件内嵌元数据本地重建字典，重建产物与冻结文件逐字节一致；适配器启动校验照常通过；全量 pytest **489 passed，0 failed**。
3. R-03 以“许可仍未核实 + 以本地重建替代公开再分发”的方式关闭；字典许可栏继续写 UNVERIFIED，**没有**在任何文件中把字典写成 Apache-2.0。

## 改动文件（相对 9cfaace）

| 文件 | 变动 | 说明 |
|---|---|---|
| `scripts/setup_dictionary.py` | 新增 | 本地重建脚本（见下） |
| `assets/ocr/dictionaries/ppocrv6_dict.txt` | 从 git 追踪中删除（D） | 磁盘文件保留（已重建，哈希正确）；`.gitignore` 已排除，不再进入快照 |
| `.gitignore` | 修改 | 增加字典路径 + 注释 |
| `THIRD_PARTY_NOTICES.md` | 修改（§4） | 许可仍 UNVERIFIED + T014 再核实记录 + 重建步骤 + 打包排除清单 |
| `ENVIRONMENT.md` | 修改（新增 §7） | 全新检出后先跑重建脚本的步骤 |
| `task_handoffs/T014/r03/` | 新增 | 本交接包：`TASK_RESULT.md`、`LICENSE_VERIFICATION_R03.md`、`changed_files.txt`、`test_commands.txt`、`test_stdout.log`、`test_stderr.log`、`exit_codes.txt` |

## 新脚本：scripts/setup_dictionary.py

- 做法：校验本机 `assets/ocr/models/PP-OCRv6_rec_small.onnx` 的 SHA-256（冻结值 `6f3272…`）→ 用 ONNX Runtime 读其内嵌 `character` 元数据（18,708 行）→ 以 `"\n".join + "\n"` 写出 `assets/ocr/dictionaries/ppocrv6_dict.txt` → 重读校验 SHA-256 `b5f2bfe2…` 与 18,708 行，失败则删部分文件并报 exit 4。
- 本地文件 only：不联网、不下载、不读任何远程来源；只 import `argparse/hashlib/os/sys/pathlib` + 惰性 `onnxruntime`（先置 `ORT_DISABLE_TELEMETRY=1`，与适配器一致）。
- 幂等：已存在且校验通过时直接报 verified，exit 0；已存在但内容不符时默认拒绝（exit 3，文件原样保留），须显式 `--force` 才替换；`--check` 只校验不写盘；`--root` 可指定仓库根。
- 禁用串检查：`grep -E "urlopen|urlretrieve|os\.system|shell=True|requests|httpx|urllib|http\.client|socket|tempfile|sqlite3|telemetry|sentry|UploadFile|multipart|create_connection|getaddrinfo|NamedTemporaryFile|mkstemp|TemporaryFile|subprocess" scripts/setup_dictionary.py` → 无命中（grep exit 1）。脚本全文不含上述任一字面串（含注释与 docstring）。

## 证明（真实跑出，命令见 test_commands.txt）

1. **重建与冻结值一致**：干净状态（删字典后）跑脚本，exit 0；`sha256sum` = `b5f2bfe2bdd9448429e3e82b51c789775d9b42f2403d082b00662eb77e401c5d`，`wc -l` = 18708，`cmp` 与备份的冻结原文件逐字节相同。预先在 /tmp 探针中验证过 `"\n".join(embedded) + "\n"` 与原文件逐字节相同（74,947 B）。
2. **失败路径**：字典被改动一行后，不带 `--force` 跑脚本 exit 3（文件保留），`--check` exit 3；`--force` 后 exit 0 且哈希恢复。模型缺失/哈希不符时 exit 2（代码路径，未实测改模型——改模型文件属禁令外的高危操作，未做）。
3. **适配器能启动 + 真实 OCR smoke**：`tests/integration/test_ocr_adapter.py` + `tests/privacy/test_local_assets.py` + `tests/offline/test_offline_static.py` 共 29 passed；CLI 真实检查 `TP-S0-ZH-001.png`（期望“限时优惠”）返回 verdict MISMATCH、错误 MISSING_CHARACTER（期望片段“惠”）、识别文本“限时优”——与该 omission 样本的预期完全一致（MISMATCH 的 CLI exit 1 属 verdict 退出码，非故障）。
4. **全量 pytest**：`TMPDIR=$PWD/tmp <venv>/bin/python -m pytest -q -p no:cacheprovider` → **489 passed, 2 warnings, 131.58s，exit 0**（日志见 `test_stdout.log` / `test_stderr.log`，退出码见 `exit_codes.txt` = 0）。
5. **快照排除证明**：`git archive e38b6d7 | tar -t | grep -F "dictionaries/ppocrv6_dict.txt"` 无命中（exit 1）；`git ls-files | grep dict` 无命中；`git archive` 清单中 `dictionaries/` 条目数为 0。
6. **全新检出端到端证明**（`~/workspace/r03-fresh-clone`，已清理）：clone 出的树里字典不存在；重建前 `test_model_assets_present_locally` 与 `test_model_files_are_local_with_frozen_hashes` 均 FAILED（exit 1）；跑脚本后 exit 0、SHA 与行数正确；随后 21 项测试（2 项字典断言 + 19 项适配器集成）全部通过。

## 禁令文件未修改证明

`git diff --name-status 9cfaace..e38b6d7` 仅有上述 5 项（3 改 + 1 删 + 1 增）；`src/` 下零改动（`rapidocr_adapter.py` 一字未动）；`tests/`、S0 fixture、manifest、S0 门槛、输入输出契约、tool_version 均未碰；未加 ￥→¥ 映射；未缩小隐私扫描范围、未加白名单、未用 curl 绕过。

## 书面取舍与依赖（重要，请协调员转达后续任务）

1. **测试顺序依赖（有意为之）**：全新检出后必须先跑 `scripts/setup_dictionary.py` 再跑测试，否则 `test_model_assets_present_locally`（offline）与 `test_model_files_are_local_with_frozen_hashes`（privacy）会失败。这是文档化、实测过的依赖（全新检出证明第 6 项），不是测试缺陷——**不要为此改测试**。已写入 `THIRD_PARTY_NOTICES.md` §4 与 `ENVIRONMENT.md` §7。
2. **source.zip / wheel 打包**：git 树已排除字典，但从工作副本组装档案时必须显式排除 `assets/ocr/dictionaries/ppocrv6_dict.txt`（工作副本里有本地重建的文件）。已写入 `THIRD_PARTY_NOTICES.md` §4 的排除清单。`assets/ocr/SHA256SUMS.txt` 仍保留字典哈希行——它是本地重建文件的校验参照，不是“随包分发”的主张。
3. **合规依据**：重建不分发字典文件——它是在用户本机上对已合法持有的模型文件（Apache-2.0 覆盖，含内嵌字符表）做机械格式转换（元数据 → 文本文件），模型文件本身的再分发在许可范围内；转换结果不进入任何公开产物。脚本不联网、不下载。
4. **残留风险**：字符表作为数据是否独立享有版权、以及从模型元数据提取在所有法域是否无争议，未获法律意见；本方案消除的是“公开再分发未核实许可文件”这一已确认风险，而非法律定论。若上游日后给出字典文件的明确许可声明，应重新核实并更新 §4（届时可恢复 git 追踪）。
5. **S0 影响**：无。S0 门禁、固定记录、300 张 fixture 均未动；全量 489 passed 与 S0 基线一致（本次未重跑 S0 --force-live——字典重建产物与冻结文件逐字节相同，适配器校验路径未变；如协调员要求，可在合并后重跑一次 S0 以确认）。

## 执行命令（摘要；完整清单见 test_commands.txt）

- `grep -n -E <禁用串> scripts/setup_dictionary.py` → 无命中
- `rm assets/ocr/dictionaries/ppocrv6_dict.txt && <venv>/bin/python scripts/setup_dictionary.py` → exit 0
- `sha256sum` / `wc -l` / `cmp` → 与冻结值一致
- `TMPDIR=$PWD/tmp <venv>/bin/python -m pytest tests/integration/test_ocr_adapter.py tests/privacy/test_local_assets.py tests/offline/test_offline_static.py -q` → 29 passed
- CLI smoke：`PYTHONPATH=$PWD/src <venv>/bin/python -m textproof.cli check --image tests/fixtures/s0/TP-S0-ZH-001.png --expected-file <期望文本文件> --json <out>` → verdict MISMATCH（符合预期）
- 全量：`TMPDIR=$PWD/tmp <venv>/bin/python -m pytest -q -p no:cacheprovider` → 489 passed，exit 0
- `git archive e38b6d7 | tar -t | grep -F dictionaries/ppocrv6_dict.txt` → 无命中
- 全新检出：clone → 2 项字典测试 FAILED → setup → 21 passed

## 未完成项

- 无。本任务两步（核实 + 方案实施）均已完成并验证。
- 建议（非阻塞）：合并后由协调员重跑一次 S0 `--force-live` 作最终确认（见“取舍”第 5 项）；GitHub 快照打包时按 §4 排除清单复核 `source.zip` 内容。

## 风险

- 若未来有人把字典文件重新 `git add` 进树，排除即失效——`.gitignore` 是唯一机械屏障；快照打包时应以 `git archive` 清单复核（本次已证明清单干净）。
- 若上游更换 rec 模型版本，内嵌字符表可能变化——脚本校验模型 SHA 与字典 SHA 双冻结值，模型变了会直接 exit 2 拒绝重建，不会静默产出错误字典。

## 回退 commit

- 回退到 9cfaace 即可恢复字典进 git 树（同时恢复未核实许可文件的公开再分发风险——回退前须重新评估）。
- 实施提交 e38b6d7；输入基线 9cfaace。
