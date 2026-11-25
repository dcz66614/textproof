# P033 TextProof FIX-R1-02 验证报告 — 补齐当前版 R3 审查索引并证明冻结 commit 与归档的关系（修复终审 R1 的 P1-02）

- 执行时间：2026-11-25 ~20:00–20:15 GMT（Europe/London）
- 工作区：`~/workspace/p033-textproof/`，分支 `fix-r1`，HEAD `16a3ef5c1b5162f9dff6dfd63c85f10ae703ecbd`
- 冻结 commit：`93d1b7c65036bb16f596117f26a48f6ee62f99e1`
- Drive 冻结文件夹：`FREEZE_93d1b7c_T014_2026-11-25`，id `1UWRhmLOE66DbFDCizbQD8AIXzjkiPN_u`
- **结论：P1-02 已修复。根本原因链与任务描述一致（见 §1），另有一处编号纠正（见 §1.5）。当前版 R3 索引与 bundle 均已上传进 Drive 冻结文件夹并重新下载核对 SHA-256 一致；bundle 从克隆验证忠实反映冻结 commit。**

## 0. 执行摘要（数字总表）

| 项 | 值 |
|---|---|
| 当前版 R3 索引 `review/REVIEW_INDEX.md` | 72,796 B，SHA-256 `7ebbc997229cf1ef4ceb4600759f4d07580423a82966b30704f51da7b2529958` |
| manifest 登记的 `review/REVIEW_INDEX.md` | 72,796 B，SHA-256 `7ebbc997…9958`（与工作区当前文件完全一致） |
| 冻结 commit 内旧版索引 | 70,169 B，SHA-256 `fe0a307c9a7047a2c1ec40065ec9aed70b4115ec20a7a76a6a5cdea5bb98dd88`，git blob `5e10b5ec1aefface181ee47caea52a7a5dc41a6b` |
| `verify_review_pack.py` | **PASS**（400 行 / 锚定 commit 追踪文件 699 / 覆盖 699） |
| `source.zip`（本地 = Drive） | 512,109,756 B，SHA-256 `9c2305ed715e0e74e459e73348418a7011890a474af04cdc4de451a456d2c235`，与 manifest 登记一致 |
| bundle `task_handoffs/FIX-R1/TextProof-93d1b7c.bundle` | 457,701,056 B，SHA-256 `d4395c67a413db6b55ca12a8a36b0608ff34ee0883db9c67d09a431921705edb`，`git bundle verify` 通过，完整历史 |
| Drive 新文件 ① 索引 | `REVIEW_INDEX.md`，id `1IXwRD_eCua_o4_ksNoKSJTNYrn4bvGAK`，重新下载 SHA 与本地一致 |
| Drive 新文件 ② bundle | `TextProof-93d1b7c.bundle`，id `1MpHMtv2d7MFXn_LS00cAEdKBc5NjYcgX`，重新下载 SHA 与本地一致 |
| Drive 文件夹文件数 | 上传前 12 → 上传后 **14**（原 12 个文件 id 全部保留，未覆盖任何已有文件） |

## 1. 根本原因链（已逐项核实，与任务描述一致）

### 1.1 冻结 commit 93d1b7c 只改了 README，不含新索引

```
$ git show -s --format='%H %ci %s' 93d1b7c
93d1b7c65036bb16f596117f26a48f6ee62f99e1 2026-11-25 15:35:39 +0000 T014R3: fix stale U-01 limitation sentence in README (R14-01)

$ git show --stat --oneline 93d1b7c
93d1b7c T014R3: fix stale U-01 limitation sentence in README (R14-01)
 README.md | 7 ++++---
 1 file changed, 4 insertions(+), 3 deletions(-)
```

### 1.2 93d1b7c 内的 REVIEW_INDEX.md 是旧版（锚定 1f02358 的 R2 索引）

```
$ git ls-tree 93d1b7c -- review/
100644 blob bada75d40bcdad9020ae5277cb5f0c810dafc690  review/REVIEW_FINDINGS_T012.md
100644 blob 5e10b5ec1aefface181ee47caea52a7a5dc41a6b  review/REVIEW_INDEX.md
100644 blob 7384c399c17714fe0d599ef44ba404d15fa61519  review/REVIEW_INDEX_T012.md
100644 blob 6fdf276641b51611cfdad9cde0873562f1ca3a19  review/REVIEW_PACK_T014.md
100644 blob a0ae2055cce28914a4c054385132e0ee960159f2  review/REVIEW_PACK_T014R2.md

$ git show 93d1b7c:review/REVIEW_INDEX.md | wc -c
70169
$ git show 93d1b7c:review/REVIEW_INDEX.md | sha256sum
fe0a307c9a7047a2c1ec40065ec9aed70b4115ec20a7a76a6a5cdea5bb98dd88  -

$ git show 93d1b7c:review/REVIEW_INDEX.md | head -3
- 锚定 commit：`1f02358f1c44b4de4a7d6e0b80dd97bef633a5b6`（分支 `t014-refresh`；T014 重冻源码 commit…）
- 覆盖率：**全文列 388 / 锚定 commit 追踪文件总数 688**；…
```

旧版索引与 `~/workspace/p033-textproof-t014-review/review/REVIEW_INDEX.md` 相同：

```
$ ls -l ~/workspace/p033-textproof-t014-review/review/REVIEW_INDEX.md
-rw-rw---- 1 root root 70169 Nov 25 15:06 …/REVIEW_INDEX.md
$ sha256sum ~/workspace/p033-textproof-t014-review/review/REVIEW_INDEX.md
fe0a307c9a7047a2c1ec40065ec9aed70b4115ec20a7a76a6a5cdea5bb98dd88
```

**且 93d1b7c 的 review/ 树里没有 `REVIEW_PACK_T014R3.md`**（上列 `git ls-tree` 只有 5 个文件）。

### 1.3 新版 R3 索引是在冻结之后、由 9befbee 提交的

```
$ git show -s --format='%H %ci %s' 9befbee
9befbee756eb5f739121b0af5717b5d9e8a32518 2026-11-25 15:57:09 +0000 T014R3: rebuild release bundle from freeze commit 93d1b7c (R14-01 fixed)

$ git diff-tree --no-commit-id --name-status -r 9befbee | grep review/
M   review/REVIEW_INDEX.md
A   review/REVIEW_PACK_T014R3.md

$ git show --stat --oneline 9befbee | head -8
9befbee T014R3: rebuild release bundle from freeze commit 93d1b7c (R14-01 fixed)
 release/RELEASE_MANIFEST.json   | 32 ++++--
 release/SHA256SUMS.txt          |  4 +-
 release/source.zip              | Bin 263808324 -> 512109756 bytes
 release/textproof-1.0.0-py3-none-any.whl | Bin 27176403 -> 27176403 bytes
 review/REVIEW_INDEX.md          | 48 +++++----
 review/REVIEW_PACK_T014R3.md    | 118 +++++++++++++++++++++
```

随后随合并 `16a3ef5`（2026-11-25 16:38:48）进 master。当前工作区索引头：

```
- 锚定 commit：`93d1b7c65036bb16f596117f26a48f6ee62f99e1`（分支 `t014-r14fix`；T014R3 重冻源码 commit…）
- 覆盖率：**全文列 399 / 锚定 commit 追踪文件总数 699**；其余 300 张 fixture PNG 以一行聚合记录…
- 本索引本身与 `review/REVIEW_PACK_T014.md`、`review/REVIEW_PACK_T014R2.md`、`review/REVIEW_PACK_T014R3.md` 不在锚定 commit 内（它们是 T014 发布证据，在随后的 release 提交中入库）；其哈希见 `release/RELEASE_MANIFEST.json`。
```

### 1.4 source.zip 是从 93d1b7c 做 git archive 打的，所以里面是旧索引、缺 R3 包

manifest 自述（`release/RELEASE_MANIFEST.json`）：

```
"source_commit": "93d1b7c65036bb16f596117f26a48f6ee62f99e1",
"source_branch": "t014-r14fix",
"built_from": "git archive 93d1b7c65036bb16f596117f26a48f6ee62f99e1 (source.zip); …"
```

实测本地 `release/source.zip`：

```
$ ls -l release/source.zip; sha256sum release/source.zip
-rw-rw---- 1 root root 512109756 Nov 25 16:38 release/source.zip
9c2305ed715e0e74e459e73348418a7011890a474af04cdc4de451a456d2c235  release/source.zip

$ unzip -l release/source.zip | grep "review/"
        0  2026-11-25 15:35   review/
    53197  2026-11-25 15:35   review/REVIEW_FINDINGS_T012.md
    70169  2026-11-25 15:35   review/REVIEW_INDEX.md
    13375  2026-11-25 15:35   review/REVIEW_INDEX_T012.md
    14246  2026-11-25 15:35   review/REVIEW_PACK_T014.md
    14285  2026-11-25 15:35   review/REVIEW_PACK_T014R2.md
```

即：zip 内索引 70,169 B（旧版），**无 `REVIEW_PACK_T014R3.md`**。而 `git archive 93d1b7c` 的文件清单与 zip 内清单逐项相同（766 条，见 §5.2）。

### 1.5 manifest 登记的却是工作区当前文件 —— 缺口所在

```
$ grep -n "REVIEW_INDEX\|REVIEW_PACK_T014R3" release/RELEASE_MANIFEST.json
27:    "review/REVIEW_INDEX.md": {
28:      "sha256": "7ebbc997229cf1ef4ceb4600759f4d07580423a82966b30704f51da7b2529958",
29:      "size": 72796
47:    "review/REVIEW_PACK_T014R3.md": {
48:      "sha256": "ac5ee1de625575dd0e0208f5b6ca7c29ef72067f448bbedf8f86c7d79b418f08",
49:      "size": 15308

$ sha256sum review/REVIEW_INDEX.md review/REVIEW_PACK_T014R3.md
7ebbc997229cf1ef4ceb4600759f4d07580423a82966b30704f51da7b2529958  review/REVIEW_INDEX.md
ac5ee1de625575dd0e0208f5b6ca7c29ef72067f448bbedf8f86c7d79b418f08  review/REVIEW_PACK_T014R3.md
```

manifest 登记值与工作区当前文件一致，但与 `source.zip` 内容（旧索引 70,169 B / 无 R3 包）不一致。`verify_release.py` 当时只对了工作区，没对 `source.zip` 内容 —— 这就是缺口。**根本原因链成立。**

#### 编号纠正（任务描述的一处不准确）

任务描述称 93d1b7c 内旧索引的 "blob fe0a307c…"。实测：**`fe0a307c…` 是旧索引文件内容的 SHA-256，不是 git blob id**。该文件在 93d1b7c 中的 git blob id 是：

```
$ git rev-parse 93d1b7c:review/REVIEW_INDEX.md
5e10b5ec1aefface181ee47caea52a7a5dc41a6b
```

当前版 R3 索引的 git blob id 是 `aaf1691b4b0929bcce622893484a2aeea9c428c4`。其余数字（70,169 B、72,796 B、两版 SHA-256）全部核实无误。

## 2. 当前索引 SHA 与 manifest 对照

```
$ ls -l review/REVIEW_INDEX.md; sha256sum review/REVIEW_INDEX.md
-rw-rw---- 1 root root 72796 Nov 25 16:38 review/REVIEW_INDEX.md
7ebbc997229cf1ef4ceb4600759f4d07580423a82966b30704f51da7b2529958  review/REVIEW_INDEX.md

manifest review/REVIEW_INDEX.md: sha256 7ebbc997229cf1ef4ceb4600759f4d07580423a82966b30704f51da7b2529958, size 72796
→ 一致。
manifest review/REVIEW_PACK_T014R3.md: sha256 ac5ee1de…b418f08, size 15308 → 与工作区当前文件一致（上节）。
manifest release/source.zip: sha256 9c2305ed715e0e74e459e73348418a7011890a474af04cdc4de451a456d2c235, size 512109756
→ 与本地 release/source.zip 一致，也与 Drive 上的 source.zip 一致（见 §5.3）。
```

## 3. verify_review_pack 运行结果

```
$ ~/workspace/p033-textproof/.venv/bin/python scripts/verify_review_pack.py review/REVIEW_INDEX.md
anchor commit: 93d1b7c65036bb16f596117f26a48f6ee62f99e1
index rows:    400
tracked files at anchor: 699
files covered:           699
VERIFY_REVIEW_PACK: PASS
EXIT=0
```

**PASS。** 当前 R3 索引对锚定 commit 93d1b7c 的覆盖完整：400 行（含 300 张 S0 fixture PNG 的一行聚合），699 个追踪文件全部覆盖，无缺失、无多余。索引本身未发现覆盖不全问题。

## 4. Drive 上传记录

冻结文件夹 `1UWRhmLOE66DbFDCizbQD8AIXzjkiPN_u`，上传前 12 个文件（已逐一核对，见 §4.3）；两次上传均为**新文件**，未覆盖任何已有文件。

### 4.1 当前版 R3 索引

```
$ /opt/hatch/bin/hatch_gws_cli drive +upload /home/hatch/workspace/p033-textproof/review/REVIEW_INDEX.md \
    --parent 1UWRhmLOE66DbFDCizbQD8AIXzjkiPN_u --name 'REVIEW_INDEX.md'
{"id": "1IXwRD_eCua_o4_ksNoKSJTNYrn4bvGAK", "kind": "drive#file", "mimeType": "text/markdown", "name": "REVIEW_INDEX.md"}
UPLOAD_EXIT=0
```

重新下载核对：

```
$ drive files get --params '{"fileId":"1IXwRD_eCua_o4_ksNoKSJTNYrn4bvGAK","alt":"media"}' \
    --output task_handoffs/FIX-R1/tmp/drive-REVIEW_INDEX.md
bytes: 72796, status: success
$ sha256sum task_handoffs/FIX-R1/tmp/drive-REVIEW_INDEX.md review/REVIEW_INDEX.md
7ebbc997229cf1ef4ceb4600759f4d07580423a82966b30704f51da7b2529958  (两处相同)
$ cmp task_handoffs/FIX-R1/tmp/drive-REVIEW_INDEX.md review/REVIEW_INDEX.md
RE-DOWNLOAD_IDENTICAL
```

- Drive 文件 id：**`1IXwRD_eCua_o4_ksNoKSJTNYrn4bvGAK`**
- 大小 72,796 B，SHA-256 `7ebbc997229cf1ef4ceb4600759f4d07580423a82966b30704f51da7b2529958`，与本地及 manifest 一致。

### 4.2 Git bundle

```
$ /opt/hatch/bin/hatch_gws_cli drive +upload /home/hatch/workspace/p033-textproof/task_handoffs/FIX-R1/TextProof-93d1b7c.bundle \
    --parent 1UWRhmLOE66DbFDCizbQD8AIXzjkiPN_u --name 'TextProof-93d1b7c.bundle'
{"id": "1MpHMtv2d7MFXn_LS00cAEdKBc5NjYcgX", "kind": "drive#file", "mimeType": "application/octet-stream", "name": "TextProof-93d1b7c.bundle"}
UPLOAD_EXIT=0
```

重新下载核对：

```
$ drive files get --params '{"fileId":"1MpHMtv2d7MFXn_LS00cAEdKBc5NjYcgX","alt":"media"}' \
    --output task_handoffs/FIX-R1/tmp/drive-bundle.bundle
bytes: 457701056, status: success
$ sha256sum task_handoffs/FIX-R1/tmp/drive-bundle.bundle task_handoffs/FIX-R1/TextProof-93d1b7c.bundle
d4395c67a413db6b55ca12a8a36b0608ff34ee0883db9c67d09a431921705edb  (两处相同)
```

- Drive 文件 id：**`1MpHMtv2d7MFXn_LS00cAEdKBc5NjYcgX`**
- 大小 457,701,056 B，SHA-256 `d4395c67a413db6b55ca12a8a36b0608ff34ee0883db9c67d09a431921705edb`，与本地 bundle 一致。
- 重新下载的 bundle 副本也通过了 `git bundle verify`（见 §5.1）。

### 4.3 上传后文件夹现状（14 个文件）

上传后重新列出文件夹，原 12 个文件 id 全部保留：

| 文件 | id |
|---|---|
| TextProof-93d1b7c.bundle（新增） | 1MpHMtv2d7MFXn_LS00cAEdKBc5NjYcgX |
| REVIEW_INDEX.md（新增） | 1IXwRD_eCua_o4_ksNoKSJTNYrn4bvGAK |
| FREEZE_ARCHIVE_NOTE.md | 10FR9liKXF0roqYZKW2eN6ThguXOeiEUM |
| source.zip | 1IWsa7zPflkPbFq_PKhO8wC964NwbZ3EW |
| textproof-1.0.0-py3-none-any.whl | 1saaVScWA6gTP7HOidIkK4pnZ97Oa_47v |
| S0_MAINCHAT_VERDICT.md | 1eQCybptd49K2pp335BJHd1NT_3P7KtQA |
| S0_REPORT.md | 1GOrWfqRu5FZq4ZtBvl5co0_MTtRDZzs7 |
| T014_MAINCHAT_VERDICT.md | 1ngvtJHXLbL4lgFBRvOJeerlyadrdug78 |
| REVIEW_REPORT_T014_R2.md | 1C3-xUkBrxIWA4zmyqeqUWIIuLPC8AYSc |
| REVIEW_REPORT_T014_R1.md | 1jfRseMAIwnKd60BmwpSX7-y2Jk-8Zi_N |
| REVIEW_PACK_T014R3.md | 19IhdjgU82wSpN2TthlX8q7d7lSfd_Xpv |
| SBOM_LICENSES.md | 16sEK8-6D7Eyj_tzfBhbFf2zaxb-pA_F- |
| SHA256SUMS.txt | 1dhm_WcUZClee7S3c0-5whQEubrQcFWAE |
| RELEASE_MANIFEST.json | 1zg6ERxs-lS4O0F1UwFaaDRuK7dUHnYjH |

## 5. Bundle 验证记录

### 5.1 生成 —— 对任务字面命令的一处必要偏离

任务字面命令 `git bundle create task_handoffs/FIX-R1/TextProof-93d1b7c.bundle 93d1b7c` 在本机 git 2.43.0 上失败：

```
$ git bundle create task_handoffs/FIX-R1/TextProof-93d1b7c.bundle 93d1b7c
fatal: Refusing to create empty bundle.
EXIT=128
```

原因：`git bundle create` 要求 rev-list 参数至少产生一个可写入 bundle 头的 ref；裸 SHA-1 不产生 ref，故被拒为空 bundle（仓库非 shallow，`git rev-list --count 93d1b7c` = 61）。改用临时轻量标签提供 ref：

```
$ git tag freeze-93d1b7c 93d1b7c
$ git bundle create task_handoffs/FIX-R1/TextProof-93d1b7c.bundle freeze-93d1b7c
-rw-rw---- 1 root root 457701056 Nov 25 20:01 task_handoffs/FIX-R1/TextProof-93d1b7c.bundle
d4395c67a413db6b55ca12a8a36b0608ff34ee0883db9c67d09a431921705edb  task_handoffs/FIX-R1/TextProof-93d1b7c.bundle
$ git bundle verify task_handoffs/FIX-R1/TextProof-93d1b7c.bundle
The bundle contains this ref:
93d1b7c65036bb16f596117f26a48f6ee62f99e1 refs/tags/freeze-93d1b7c
The bundle records a complete history.
The bundle uses this hash algorithm: sha1
VERIFY_EXIT=0
$ git bundle list-heads task_handoffs/FIX-R1/TextProof-93d1b7c.bundle
93d1b7c65036bb16f596117f26a48f6ee62f99e1 refs/tags/freeze-93d1b7c
```

bundle 包含 93d1b7c 及其完整历史（61 个 commit）。随后立即删除临时标签（`git tag -d freeze-93d1b7c`，`git tag -l 'freeze-*'` 为空）；bundle 自身保留该 ref，不受影响。**未提交任何东西，未切换分支。**

### 5.2 从 bundle 克隆验证 —— 忠实反映冻结 commit

第一次在 `/tmp` 克隆时遇到磁盘事故：`/tmp` 是 512 MB tmpfs，检出 93d1b7c（内含 512 MB source.zip 及 wheelhouse）写满导致 `Out of diskspace`，检出失败（对象库本身无损：`git rev-parse 93d1b7c`、`git log` 均已通过）。按既往教训改用持久磁盘重做：

```
$ git clone -q --no-checkout task_handoffs/FIX-R1/TextProof-93d1b7c.bundle task_handoffs/FIX-R1/tmp-bundle-clone
CLONE_EXIT=0
$ git rev-parse 93d1b7c65036bb16f596117f26a48f6ee62f99e1
93d1b7c65036bb16f596117f26a48f6ee62f99e1
$ git cat-file -t 93d1b7c
commit
$ git log --oneline -1 93d1b7c
93d1b7c T014R3: fix stale U-01 limitation sentence in README (R14-01)
$ git show 93d1b7c:review/REVIEW_INDEX.md | wc -c
70169
$ git show 93d1b7c:review/REVIEW_INDEX.md | sha256sum
fe0a307c9a7047a2c1ec40065ec9aed70b4115ec20a7a76a6a5cdea5bb98dd88  -
$ git ls-tree 93d1b7c -- review/
100644 blob bada75d40bcdad9020ae5277cb5f0c810dafc690  review/REVIEW_FINDINGS_T012.md
100644 blob 5e10b5ec1aefface181ee47caea52a7a5dc41a6b  review/REVIEW_INDEX.md
100644 blob 7384c399c17714fe0d599ef44ba404d15fa61519  review/REVIEW_INDEX_T012.md
100644 blob 6fdf276641b51611cfdad9cde0873562f1ca3a19  review/REVIEW_PACK_T014.md
100644 blob a0ae2055cce28914a4c054385132e0ee960159f2  review/REVIEW_PACK_T014R2.md
$ git checkout 93d1b7c -- review/REVIEW_INDEX.md
-rw-rw---- 1 root root 70169 Nov 25 20:02 review/REVIEW_INDEX.md
fe0a307c9a7047a2c1ec40065ec9aed70b4115ec20a7a76a6a5cdea5bb98dd88  review/REVIEW_INDEX.md
```

结论：从 bundle 克隆出的 93d1b7c 与源仓库完全一致；其 `review/REVIEW_INDEX.md` 为旧版（70,169 B，SHA-256 `fe0a307c…`，blob `5e10b5ec…`），且树中无 `REVIEW_PACK_T014R3.md` —— bundle 忠实反映冻结 commit。

（注：bundle 只含 tag ref、无分支，故 `git clone` 时提示 `remote HEAD refers to nonexistent ref, unable to checkout`；属预期现象，对象库完整，用 `git checkout 93d1b7c` / `--no-checkout` + `git show` 验证即可。）

### 5.3 git archive 对照与 Drive source.zip 的关系

```
$ git archive 93d1b7c | tar -t | sort  → 766 条
$ unzip -l release/source.zip（去表头） → 766 条
$ diff → 无差异：FILE_LISTS_IDENTICAL (766 entries)
```

抽查 4 个文件的内容哈希（zip 内解出 vs `git show 93d1b7c:`），全部一致：

| 文件 | SHA-256 |
|---|---|
| review/REVIEW_INDEX.md | fe0a307c9a7047a2c1ec40065ec9aed70b4115ec20a7a76a6a5cdea5bb98dd88 |
| review/REVIEW_PACK_T014R2.md | 0b781edb37d127efde3f7e4105dbcf4016df5028935c96256aa126f870c70808 |
| README.md | 136b28776f603731fe79abcf11247dda1786316313e03632582e193fd3c1eebf |
| PROJECT_BOOK.md | 8a2b6e565df88a2f6371879cdcfbb613500c8cc2ecee50376b8da95d7ecc496a |

另从 Drive 重新下载 `source.zip`（id `1IWsa7zPflkPbFq_PKhO8wC964NwbZ3EW`）核对：

```
bytes: 512109756, status: success
$ sha256sum <Drive 下载的 source.zip>
9c2305ed715e0e74e459e73348418a7011890a474af04cdc4de451a456d2c235
```

与本地 `release/source.zip` 及 manifest 登记值完全一致。**因此：Drive 上的 source.zip 就是 `git archive 93d1b7c` 的产物；bundle + Drive source.zip + manifest 三者对 93d1b7c 的关系现已可独立证明。**

## 6. 遗留说明与注意事项

1. **P1-02 本身已闭合，但 source.zip 内的旧索引并未被改写。** 这是符合冻结语义的：source.zip 是 93d1b7c 的归档产物，改写它等于篡改归档。本次修复的正确形态是“冻结文件夹里同时有旧归档（source.zip，内含旧索引）+ 当前版 R3 索引（新上传的 REVIEW_INDEX.md，7ebbc997…）+ 证明 commit 的 bundle”，三者关系由本报告与 manifest 共同说明。终审 R2 递交时应明确指出这一点，避免评审员把“zip 内索引仍是旧版”再次当作新问题。
2. **manifest 仍登记工作区当前文件而非 zip 内容。** manifest 的 `files` 条目对 `review/REVIEW_INDEX.md` 与 `review/REVIEW_PACK_T014R3.md` 登记的是 9befbee 提交后的工作区文件；它们不在 93d1b7c 内、也不在 source.zip 内，索引头已声明这一点（“其哈希见 release/RELEASE_MANIFEST.json”）。建议 R2 递交材料中附一句话说明该登记口径，否则同一歧义会反复出现。是否改 manifest 本身不在本子任务范围内，未动。
3. **bundle 偏离字面命令已在 §5.1 说明**：裸 SHA 无法建 bundle，改用临时标签（已删）。bundle 头 ref 为 `refs/tags/freeze-93d1b7c`。
4. **工作区状态**：执行期间未提交、未切换分支（仍在 `fix-r1`，HEAD `16a3ef5`）。`git status` 显示的 `M PERFORMANCE_REPORT.md / PROJECT_BOOK.docx / S0_REPORT.md` 及新增未追踪文件（`scripts/md_to_docx.py`、`tests/fixtures/performance/` 等）不是本子任务产生的——任务开始时 status 只有 5 项未追踪（`FINAL_REVIEW_R1_MESSAGE.md`、`P033_FINAL_REVIEW_R1.md`、`task_handoffs/T001/`、`tests/e2e/evidence/`、`tmp/`），其余变化来自并行的 FIX-R1 兄弟子任务；本子任务只在 `task_handoffs/FIX-R1/` 内新增了 bundle、本报告及 `tmp/` 校验中间文件。
5. **中间文件**：`task_handoffs/FIX-R1/tmp/` 保留 `clone-archive-list.txt`、`sourcezip-list.txt`、`sourcezip-list-clean.txt`、`list-diff.txt`、`drive-REVIEW_INDEX.md`（72,796 B，Drive 回下载副本）；体积大的验证副本（Drive 回下载的 source.zip 512 MB、bundle 457 MB）及 `tmp-bundle-clone/` 已在核对 SHA 后删除，哈希均已记录在本报告中。

## 7. 交付物

- 本报告：`task_handoffs/FIX-R1/fix-r1-02-verification.md`
- bundle：`task_handoffs/FIX-R1/TextProof-93d1b7c.bundle`（457,701,056 B，SHA-256 `d4395c67a413db6b55ca12a8a36b0608ff34ee0883db9c67d09a431921705edb`）
- Drive 新文件：`REVIEW_INDEX.md`（id `1IXwRD_eCua_o4_ksNoKSJTNYrn4bvGAK`）、`TextProof-93d1b7c.bundle`（id `1MpHMtv2d7MFXn_LS00cAEdKBc5NjYcgX`），均在文件夹 `1UWRhmLOE66DbFDCizbQD8AIXzjkiPN_u` 内
