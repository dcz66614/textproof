# T013-FIX-04 — TASK_RESULT

- **TASK_ID**: T013-FIX-04 (T012 findings R-05 P2 + R-15 P3)
- **Worktree**: `~/workspace/p033-textproof-t013-r05`, branch `t013-r05`
- **Baseline**: `ffe53ea1fb7e1d31f536abd732c258ffc50aae56` (branch `t011-full-regression`)
- **Fix commit**: `7e3703d2076f0f214f2d928a0c61948fead63552` (branch `t013-r05`)
- **Date**: 2026-11-25 ~11:05–11:25 GMT

## R-05 (P2) — 根因

手写校验器 `scripts/validate_report_schema.py` 用
`report["expected_text"].count("\n") + 1` 算 `summary.expected_lines`，
生产（`src/textproof/core/report.py:248,272,345`，均用
`len(expected_norm)`）先把 `\r\n`/`\r` 统一为 `\n` 再切分
（`src/textproof/io/image_loader.py:292–293`）。
期望文本含孤立 CR 时两公式分歧：`'a\rb'` 与 `'a\r'` 校验器算 1、
生产算 2；CRLF/LF 一致。于是 `textproof check` 对此类合法输入产出
合法报告，却在自检（`cli.py:236–241`）中被判违规 → exit 5。
基线复现（修复前）：生产 2、校验器要求 1，`$.summary.expected_lines:
must be 1, got 2 (§5.4)`。

## R-05 — 修复

校验器新增 `_unified_lines()`，与生产同规则（`\r\n`→`\n`、
`\r`→`\n` 再 `split("\n")`），`summary.expected_lines` 改用
`len(_unified_lines(report["expected_text"]))`。只改
`scripts/validate_report_schema.py`；生产代码、fixture、manifest、
S0 门槛、契约、tool_version 均未动。

## R-15 (P3) — 根因

Schema（`schemas/textproof.report.v1.schema.json` 的 MISSING_LINE
条件块 :45–72、EXTRA_LINE 块 :74–98、字符错误块 :130–163）与手写
校验器（`:265–270` 只要求行索引“null 或 ≥0 整数”，`:292–341`
只校验缺失侧为 null + 存在侧 span 非空）jointly 放行“存在侧行索引
为 null”的错误对象。手工构造的 MISSING_LINE 且
`expected_line_index: null` 可同时通过两者。生产从不产出此类对象
（`classify.py:234–252` 的 `missing_line_difference` 必填
`expected_line_index`；`:255–276` 的 `extra_line_difference` 必填
`ocr_line_index`；字符错误双索引由 `report.py:338–347` 的对齐对保证），
故为纵深防御缺口而非实际缺陷。基线复现（修复前）：三类反例
（MISSING_LINE / EXTRA_LINE / SUBSTITUTION 存在侧索引 null）在手写
校验器与系统 jsonschema 4.10.3 下均判 VALID。

## R-15 — 修复（已完成，未记录为非阻断）

- Schema：MISSING_LINE `then` 块要求 `expected_line_index` 为
  integer ≥ 0；EXTRA_LINE `then` 块要求 `ocr_line_index` 为
  integer ≥ 0；字符错误 `then` 块要求双索引均为 integer ≥ 0
  （三处描述文字同步注明 T013 R-15）。
- 校验器：MISSING_LINE 分支要求 `expected_line_index` 非空；
  EXTRA_LINE 分支要求 `ocr_line_index` 非空；字符错误分支要求双
  索引非空。AMBIGUOUS_ALIGNMENT（双索引必须为 null）未动；缺失侧
  仍必须为 null（有反向守卫测试锁定）。
- 回退风险检查（修复后，未发现回退，故未停下）：全部 300 张
  fixture 的固定路径生产报告（`load_image` + `build_report` +
  `parity_check.fixed_ocr_line`，与 `verify_s0.py` / `test_s0_gate.py`
  同法）经新手写校验器 0 拒绝、经系统 jsonschema 对新 schema
  300/300 有效；verdict 与错误类型与 `expected_output.json` 0 不符。
  （脚本为一次性检查，未提交：`/tmp/check_300.py`、
  `/tmp/reports300.json`。）

## 新增回归测试

`tests/unit/test_validate_report_schema.py`（新建，21 项，全部通过）：

| 测试 | 内容 |
|---|---|
| `test_expected_lines_lone_cr_matches_production[a\rb / a\r]` | 孤立 CR：生产 2 行，校验器接受 expected_lines=2 |
| `test_expected_lines_crlf_and_lf_unchanged`（3 参数） | CRLF/LF 计数不变（2/2/3 行） |
| `test_expected_lines_lone_cr_undercount_is_rejected` | `'a\rb'` 宣称 1 行被拒（旧公式答案） |
| `test_missing_line_null_expected_line_index_rejected` | R-15 反例：MISSING_LINE 存在侧 null 被拒；合法形式通过 |
| `test_extra_line_null_ocr_line_index_rejected` | R-15 反例：EXTRA_LINE 存在侧 null 被拒；合法形式通过 |
| `test_character_error_null_line_index_rejected`（4 类型 × 2 字段 = 8） | 字符错误任一索引 null 被拒 |
| `test_character_error_both_indices_present_accepted`（4 类型） | 字符错误双索引合法形式通过 |
| `test_absent_side_index_must_still_be_null` | 反向守卫：缺失侧仍必须为 null |

新测试单独运行：`21 passed in 1.42s`。

## 验证结果

- R-05 算术复核（修复后）：`'a\rb'` 与 `'a\r'` 校验器与生产均为 2，
  无违规；`'a\r\nb'` / `'a\nb'` 仍为 2。
- R-15 反例报告修复前后对比：修复前三类反例（MISSING_LINE /
  EXTRA_LINE / SUBSTITUTION 存在侧 null）校验器与 schema 均放行；
  修复后校验器与 schema（系统 jsonschema 4.10.3）均拒绝
  （schema 报错 `None is not of type 'integer'`）。
- 300 fixture 期望输出：固定路径生产报告 300/300 通过新手写校验器，
  300/300 通过新 schema；verdict/错误类型与 `expected_output.json`
  0 不符。
- 全量 pytest（`TMPDIR=$PWD/tmp .venv/bin/python -m pytest -q
  -p no:cacheprovider`）：**2 failed, 457 passed, 2 warnings,
  922.29s (0:15:22)**。两项失败均为基线已知、属另一修复员
  （T013-R02）范围的 R-02 项：
  `tests/privacy/test_no_persistence.py::test_forbidden_token_absent_from_sources[urlopen]`
  与 `::test_no_network_client_import_in_sources`
  （`scripts/consistency_check.py` 的 urlopen/socket，本分支未碰）。
  T012 基线为 2 failed、436 passed；457 = 436 + 本任务新增 21 项，
  无新增失败。耗时远超基线 227s 的原因是三路 T013 全量套件
  （r01、r05、r09）同期并行，VM 内存紧张（跑时仅 ~366 MB 空闲、
  swap 在用）；非本分支引入的缓慢。

## 改动文件（仅以下）

- `scripts/validate_report_schema.py`（R-05 公式 + R-15 三分支检查 + docstring）
- `schemas/textproof.report.v1.schema.json`（R-15 三处 `then` 块 + 描述）
- `tests/unit/test_validate_report_schema.py`（新增 21 项回归测试）
- `task_handoffs/T013/r05/TASK_RESULT.md`（本文件）

未改：测试预期、fixture PNG、manifest、S0 门槛、输入输出契约、
tool_version、其他 finding 的文件。未合并到 master 或
`t011-full-regression`。
