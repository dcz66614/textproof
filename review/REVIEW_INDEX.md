# P033 TextProof — T014 发布审查索引（REVIEW_INDEX.md)

- 锚定 commit：`93d1b7c65036bb16f596117f26a48f6ee62f99e1`（分支 `t014-r14fix`；T014R3 重冻源码 commit，含 R-13 发布文件、R-30 审查脚本、T013-U01 修复与 R14-01 README 修正）
- 审查报告：`review/REVIEW_PACK_T014R3.md`（本次重冻的定稿说明；旧包 `review/REVIEW_PACK_T014.md` 记录 U-01 失败证据、`review/REVIEW_PACK_T014R2.md` 记录 R2 重冻，原文保留）；T012 原始审查报告见 `review/REVIEW_FINDINGS_T012.md`（自 T011 审查工作树逐字复制，见 §6）
- 本表每行的字节数、SHA-256、行数均取自锚定 commit 本身（`git archive <commit>`），不受工作树脏文件影响；行数按 `wc -l` 口径（换行符个数）。
- 覆盖率：**全文列 399 / 锚定 commit 追踪文件总数 699**；其余 300 张 fixture PNG 以一行聚合记录（逐文件 SHA 见 `tests/fixtures/s0/manifest.json`，由 `scripts/verify_s0.py` 全量重算验证）。
- 校验命令：`python scripts/verify_review_pack.py review/REVIEW_INDEX.md`（逐行核对路径、字节数、SHA-256、行数，并核对覆盖完整性）。
- 本索引本身与 `review/REVIEW_PACK_T014.md`、`review/REVIEW_PACK_T014R2.md`、`review/REVIEW_PACK_T014R3.md` 不在锚定 commit 内（它们是 T014 发布证据，在随后的 release 提交中入库）；其哈希见 `release/RELEASE_MANIFEST.json`。
- 字典 `assets/ocr/dictionaries/ppocrv6_dict.txt` 不在锚定 commit 内（T014/R-03 起不再追踪，见 `THIRD_PARTY_NOTICES.md` §4），故本表无此行；它是唯一被排除的源文件。

## 1. 覆盖表

| 文件 | 字节数 | SHA-256 | 行数 | 读取状态 | 备注 |
|---|---:|---|---|---|---|
| `.gitignore` | 470 | `be229dc86c2a8ee818f99c0385d43a164414ec4739028463ccec13c7b1207bae` | 13 | 已列 | 冻结源码 commit 文件 |
| `API_CONTRACT.md` | 8218 | `32209a2cb1c2dbef3a6f04af4ddd59601bcfd2c571e04e8b339ee7ec1d513ce2` | 177 | 已列 | 冻结源码 commit 文件 |
| `ENVIRONMENT.md` | 6002 | `3635a7d56f4e9cd983b55165df664537e9a0731a818f91ffa9113f5f5806e056` | 115 | 已列 | 冻结源码 commit 文件 |
| `FULL_TEST_REPORT.md` | 7439 | `4016d03f6fdfa83bb3694c41744fbd5858005f7737daba3fc1ea322cb55b34be` | 139 | 已列 | 冻结源码 commit 文件 |
| `IMPLEMENTATION_PLAN.docx` | 58745 | `c6d2b3a6d925e62ed18a976afc71b577b90248d41aa50d884f4036280c51c385` | 225 | 已列 | 冻结源码 commit 文件 |
| `IMPLEMENTATION_PLAN.md` | 35772 | `2d2ac3f3b6eec92037ae43b76bfe91a925537b1563a73b0a987763d0deb113c2` | 632 | 已列 | 冻结源码 commit 文件 |
| `LICENSE` | 1079 | `9aba15d7108d16139cdeb618c30dda7345318a114802c8cec97181422671f3d6` | 21 | 已列 | 冻结源码 commit 文件 |
| `METRICS_REPORT.json` | 4398 | `0b7f9e481e03c347eae858b918cb88217934ccaab0b20e37794afa7c01222391` | 0 | 已列 | 冻结源码 commit 文件 |
| `PERFORMANCE_REPORT.md` | 5225 | `12fc24d91f08bf230d1da9b8056a3f50be70d4b5a06231ee1c246926eaac1622` | 116 | 已列 | 冻结源码 commit 文件 |
| `PRIVACY_TEST_REPORT.md` | 15760 | `230459a168b15b162e61460909339903888274e69bcb27c84e125a49ed71e820` | 139 | 已列 | 冻结源码 commit 文件 |
| `PROJECT_BOOK.docx` | 64339 | `4b788b1c85d6066b5889163c4b8a03f5ef19ff902691aff5b1af75adde81aba7` | 250 | 已列 | 冻结源码 commit 文件 |
| `PROJECT_BOOK.md` | 46114 | `8a2b6e565df88a2f6371879cdcfbb613500c8cc2ecee50376b8da95d7ecc496a` | 775 | 已列 | 冻结源码 commit 文件 |
| `README.md` | 10469 | `136b28776f603731fe79abcf11247dda1786316313e03632582e193fd3c1eebf` | 247 | 已列 | 冻结源码 commit 文件 |
| `S0_MAINCHAT_VERDICT.md` | 4308 | `ec75cf85faca9c8e79d9c1e499c894dc01b8a735a64b725e78c2997c5ca9cf9a` | 44 | 已列 | 冻结源码 commit 文件 |
| `S0_REPORT.md` | 29600 | `add1f385e6423b0686843dbbca11e617195459c58eeab0381350772b862c0e21` | 419 | 已列 | 冻结源码 commit 文件 |
| `SECURITY.md` | 3606 | `a8c7221936dbf8c466a4e39405f7cb3fe6ca2269b519d449543f3f9675f03a10` | 74 | 已列 | 冻结源码 commit 文件 |
| `SPECS_VERIFICATION.md` | 4497 | `653a480c2b6bb9ebb486caa5b07e611bbaf2f447349dba1db8df65b8de70d794` | 45 | 已列 | 冻结源码 commit 文件 |
| `T001_RESULT.md` | 10157 | `d448c1375be7a9ff01d6e178bdcdcd3dcdf880598fa3e1116d63307412206c8f` | 159 | 已列 | 冻结源码 commit 文件 |
| `T011_MAINCHAT_VERDICT.md` | 3697 | `376b8c7686bedf239005e26568ab32c040e4a30d689d16cdd8621c3ca88df1b1` | 54 | 已列 | 冻结源码 commit 文件 |
| `T013_MAINCHAT_VERDICT.md` | 3137 | `994a768e163e9f7289aec9e29cc758cdf18ed8865d292ffc3436de0cf243cd45` | 32 | 已列 | 冻结源码 commit 文件 |
| `THIRD_PARTY_NOTICES.md` | 13668 | `abc16ca0d469c5d6d4f2e76be104477ba4ccbd1d40baaed524c7227a8a57ff6e` | 231 | 已列 | 冻结源码 commit 文件 |
| `assets/ocr/SHA256SUMS.txt` | 400 | `8a815bc577f4b6b60f2675eee8c3b6e329f88a8df21caaf1d185f35059cece9e` | 4 | 已列 | 冻结源码 commit 文件 |
| `assets/ocr/models/PP-OCRv6_det_small.onnx` | 9929594 | `090f04abcd9d9a7498bc4ebf677e4cb9bdce1fe4197ddb7e529f1ef44e1ff94f` | 33550 | 已列 | 冻结源码 commit 文件 |
| `assets/ocr/models/PP-OCRv6_rec_small.onnx` | 21234383 | `6f327246b50388f3c176ae304bd95767ea6dc0c9ae92153ef8cbe210b3c14884` | 97095 | 已列 | 冻结源码 commit 文件 |
| `assets/ocr/models/ch_ppocr_mobile_v2.0_cls_mobile.onnx` | 585532 | `e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c` | 3622 | 已列 | 冻结源码 commit 文件 |
| `conftest.py` | 463 | `ba310c9260e597cf3356a3757d99cb3f20983b907f07c946438c9b55eeb44d21` | 12 | 已列 | 冻结源码 commit 文件 |
| `oracle/__init__.py` | 146 | `a2613c46c556b794eb72e502e284144c6e5c5d8c8e993376c081da8b97d67b72` | 5 | 已列 | 冻结源码 commit 文件 |
| `oracle/reference_compare.py` | 29172 | `afb372da91ac762e7ab159245eac2678dcab7426acc4d23f55f1b4eab8231520` | 751 | 已列 | 冻结源码 commit 文件 |
| `pyproject.toml` | 1825 | `23080e18ca755f3575d7e284b3086e180bfcb52118e046816fa197d08a107712` | 52 | 已列 | 冻结源码 commit 文件 |
| `release/RELEASE_MANIFEST.json` | 10850 | `9fe64bd6617651a3b4bb4a236edd53645769c9ae26eaf0d516efc4b1f371505b` | 269 | 已列 | 冻结源码 commit 文件 |
| `release/SBOM_LICENSES.md` | 2766 | `362c3bd8dcae783ea550819a9d1def4840b3c6314eb4850160705daba1ee2cd2` | 55 | 已列 | 冻结源码 commit 文件 |
| `release/SHA256SUMS.txt` | 4680 | `b62cf635a680181f80295b2370d62d24af62cb04270bbfd2ddb1acfb3be6f8df` | 39 | 已列 | 冻结源码 commit 文件 |
| `release/source.zip` | 263808324 | `9fb6ca9747177aebf5f932054b509439f245020054f75441e954f5ae78465bab` | 981527 | 已列 | 冻结源码 commit 文件 |
| `release/textproof-1.0.0-py3-none-any.whl` | 27176403 | `cffd51836449a83efeeb9d407582b26c358526ba374d685cdb925e2f7dd17c0c` | 100843 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/annotated_doc-0.0.7-py3-none-any.whl` | 5286 | `6bc31bbbec6dfaaedc1676dbc11dbda96fe22a2b5c400e9ebad113fec44a9dc6` | 31 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/annotated_types-0.8.0-py3-none-any.whl` | 13427 | `f072f4d804ea359e4eaf198b1af7a8b0943881a87f31bb764f8bf219bb9419e0` | 47 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/anyio-4.16.0-py3-none-any.whl` | 134521 | `c66ae634e0b8228396b801741beb3294326d4b6102f7bba4041c0dfb58c29026` | 531 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/certifi-2026.11.20-py3-none-any.whl` | 127913 | `7422df25243767b9877031a2248cb14d09ddac9beee846f4cef3d5c9191d488f` | 476 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/charset_normalizer-3.5.3-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl` | 257134 | `e5e4785d8a0adeadfbdf75f4efc357911842674651cbafd7e97f69b11ec3cbc6` | 899 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/click-8.5.1-py3-none-any.whl` | 126163 | `8bb5376d2006950386f8c6427613334a2acadc5f559cb80e638d00b4df957e37` | 497 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/colorlog-6.12.0-py3-none-any.whl` | 12239 | `30d392604e9110045a2c2aeefc27d7a017abbab63f3a8aee594eac0801df784e` | 34 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/fastapi-0.165.0-py3-none-any.whl` | 159475 | `896f48462042bb4f162147eb8fac7e858753dc1f486765709baf105d70e4fc5b` | 594 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/flatbuffers-25.12.19-py2.py3-none-any.whl` | 26661 | `7634f50c427838bb021c2d66a3d1168e9d199b0607e6329399f04846d42e20b4` | 120 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/h11-0.16.0-py3-none-any.whl` | 37515 | `63cf8bbe7522de3bf65932fda1d9c2772064ffb3dae62d55932da54b31cb6c86` | 137 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/idna-3.20-py3-none-any.whl` | 69583 | `ab7ae7122974553370f0bdb919e1a960b2cd1bc1ef0276416d896db81c14582c` | 226 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/iniconfig-2.3.1-py3-none-any.whl` | 7552 | `9121e2c1fdb355232495be3194c8dfe87ccc2d5dee45947b78e68f499790d7a7` | 26 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/numpy-2.5.5-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl` | 15720599 | `704d819265e5d1064d932968e9ee85fff2103ccc78c05b878c06943ba27b8507` | 56271 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/omegaconf-2.4.0-py3-none-any.whl` | 254152 | `f141a664c777582405e3cc6e0545ecc79429e79f844995b1a6e71c35946a025c` | 992 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/onnxruntime-1.32.0-cp312-cp312-manylinux_2_28_x86_64.whl` | 27780211 | `99e1074c4b2197accd5073052a465361be17b89c093b8ffb6e6bd8f986c52df8` | 99201 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/opencv_python_headless-5.1.0.95-cp37-abi3-manylinux_2_28_x86_64.whl` | 63704594 | `7d387d4a64abe0c737440d38b5a90822f9bbcc10c8ce06a35904d6ecf7a2fb30` | 225580 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/opentelemetry_api-1.45.2-py3-none-any.whl` | 60335 | `2cbd737377e710ee740d261c94e93fa0f08e6d037c18f17513cc0a2d94479a34` | 219 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/packaging-26.4-py3-none-any.whl` | 140049 | `81383611a09c1bc0b08b76e0fd5829d7c6824c65b27a6aee339da133f4233ea2` | 516 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/pillow-11.3.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl` | 6645236 | `676b2815362456b5b3216b4fd5bd89d362100dc6f4945154ff172e206a22c024` | 24351 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/pluggy-1.7.0-py3-none-any.whl` | 27082 | `7dd7b0d8832ba3cb632c306926ded123429211b83641b35dc5c41ad2d34f9bec` | 100 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/protobuf-7.36.2-cp310-abi3-manylinux2014_x86_64.whl` | 343223 | `89f23aa53c24553a2416fd4fd1ec06f74fa42b14b546d8883128813f775bbfd2` | 1204 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/pyclipper-1.4.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | 978235 | `d1f807e2b4760a8e5c6d6b4e8c1d71ef52b7fe1946ff088f4fa41e16a881a5ca` | 3659 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/pydantic-2.14.4-py3-none-any.whl` | 494865 | `653a2ad9f6d8858529c77c72717d0ea991d6c6837fe683246b2f4b2bbfc3fadc` | 1937 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/pydantic_core-2.50.5-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | 2264846 | `470bbc2495367f60d3ca849a8039e4c164701d10637e7743f4427d92651bdb6d` | 8556 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/pygments-2.21.0-py3-none-any.whl` | 1250147 | `2363c69b61c4a97c838da3b130dcd6468f4848992b21a82f2a63ec34377137d9` | 4881 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/pytest-8.4.2-py3-none-any.whl` | 365750 | `872f880de3fc3a5bdc88a11b39c9710c3497a547cfa9320bc3c5e62fbf272e79` | 1408 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/pyyaml-6.0.4-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl` | 849249 | `93bfb2459195406a518e2f487a9bbf01df240175f31e06f5a252ac6734c7bbf0` | 3138 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/rapidocr-3.10.0-py3-none-any.whl` | 27288134 | `2fc34e26cd0f48514804a94f8832283039c7334076bff60768b1fed9ad068050` | 101217 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/requests-2.34.2-py3-none-any.whl` | 73075 | `2a0d60c172f83ac6ab31e4554906c0f3b3588d37b5cb939b1c061f4907e278e0` | 236 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/shapely-2.2.0-cp312-cp312-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl` | 2300970 | `650a5f4d8a8e3c96982079d8c99b6ddbe6602bbd1e34c75c2b95dbc0d28ac997` | 7553 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/six-1.17.0-py2.py3-none-any.whl` | 11050 | `4721f391ed90541fddacab5acf947aa0d3dc7d27b2e1e8eda2be8970586c3274` | 47 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/starlette-1.10.0-py3-none-any.whl` | 80571 | `478c0ab3b4ced6e82719849c118fa406f0278a3499c1a898cd15cd31bdc38ce4` | 310 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/tqdm-4.70.1-py3-none-any.whl` | 80199 | `c293e525e6fef9c20e8728fd4612df02a0aa31bb5fe91ecd93e123b1b7bffa73` | 311 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/typing_extensions-4.16.0-py3-none-any.whl` | 45571 | `481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8` | 161 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/typing_inspection-0.4.5-py3-none-any.whl` | 14874 | `bc210535442b39e1bf2805e0c7a17dfd6a4ace760c84c7f7d16245d23a6b1c39` | 48 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/urllib3-2.8.0-py3-none-any.whl` | 135717 | `0cf3cae568d36aa9576b28dfb35f11328f1cb974ca7647d9475ebb86c75ac6e3` | 509 | 已列 | 冻结源码 commit 文件 |
| `release/wheelhouse/uvicorn-0.54.0-py3-none-any.whl` | 87427 | `505bdb0f318731d45f1f712071fc781a8981f6847a31c902c9f5e652d4f67faf` | 300 | 已列 | 冻结源码 commit 文件 |
| `requirements.lock` | 66057 | `8726d13cb20bb731b491a4119629c176b699f035b75d8547d853ca3585d1564d` | 858 | 已列 | 冻结源码 commit 文件 |
| `review/REVIEW_FINDINGS_T012.md` | 53197 | `35b2260d2d79ac375cd4499f54084dc03744b8c44d6f0174bec6b75e0c30f3c9` | 374 | 已列 | 冻结源码 commit 文件 |
| `review/REVIEW_INDEX.md` | 70169 | `fe0a307c9a7047a2c1ec40065ec9aed70b4115ec20a7a76a6a5cdea5bb98dd88` | 441 | 已列 | 冻结源码 commit 文件 |
| `review/REVIEW_INDEX_T012.md` | 13375 | `f91dd1a022fd00f8abcd91a643eac78744745287905b78cb525ecf921f89715a` | 126 | 已列 | 冻结源码 commit 文件 |
| `review/REVIEW_PACK_T014.md` | 14246 | `1f8393a567a0a1f481b4a89585389757854b1eca4374947dc2350332f2890a7a` | 116 | 已列 | 冻结源码 commit 文件 |
| `review/REVIEW_PACK_T014R2.md` | 14285 | `0b781edb37d127efde3f7e4105dbcf4016df5028935c96256aa126f870c70808` | 118 | 已列 | 冻结源码 commit 文件 |
| `schemas/textproof.report.v1.schema.json` | 15422 | `6b65f6a4c52a4c8b2cf802e2c6ef53d2a0f1c9b458404d9b2e1abf9c0d37a8c1` | 481 | 已列 | 冻结源码 commit 文件 |
| `scripts/benchmark_perf.py` | 11178 | `f0f1d3d5564b8def9e07e1eb1e4860d8796be1efc9360d4f606e859e14192a0b` | 296 | 已列 | 冻结源码 commit 文件 |
| `scripts/compute_s0_metrics.py` | 20228 | `8fa687f198682f9a20a28a11bf9d8b00742437c5be309b1d7c94ee64e05ff15d` | 470 | 已列 | 冻结源码 commit 文件 |
| `scripts/env_probe.py` | 3594 | `41b7cf5c7776f756179ea890bf904e8f54e7e8a387a4a00d54acecd2de8839f1` | 113 | 已列 | 冻结源码 commit 文件 |
| `scripts/generate_fixtures.py` | 40131 | `261e4b12193323e9394f1163a34d9ccbfae1aefb503f0deaaf211754e411ee5f` | 888 | 已列 | 冻结源码 commit 文件 |
| `scripts/independent_verify.py` | 13865 | `48c112e88dd827081eb3fdf22d15b085c7f1d8a8e91024fc9880e929a3f763fe` | 303 | 已列 | 冻结源码 commit 文件 |
| `scripts/parity_check.py` | 18327 | `82309bd4f744d857314e62c0b19d567d43b4a8250c873a39a57bee81ec3aeb20` | 397 | 已列 | 冻结源码 commit 文件 |
| `scripts/setup_dictionary.py` | 3395 | `e1d358dea47afd466fc3e018811025e213bbe86ccb6a9f80d4027d136330cc12` | 89 | 已列 | 冻结源码 commit 文件 |
| `scripts/validate_report_schema.py` | 1922 | `7ec85c0cc553f007141d345bf3fa71206a411cca1f15b205da3401fe0f050a1d` | 66 | 已列 | 冻结源码 commit 文件 |
| `scripts/verify_release.py` | 24915 | `00a57db5e11dee6e9624d6981b249db9fa47040a7228e106160cc17324b468f0` | 618 | 已列 | 冻结源码 commit 文件 |
| `scripts/verify_review_pack.py` | 7931 | `35dc4b79edc4d5b1962342833b79145311b9e173274cc491991e60f695791379` | 228 | 已列 | 冻结源码 commit 文件 |
| `scripts/verify_s0.py` | 22224 | `2ec805c7ed927ef8d7e1faccb04a494f48113cb528ab39f444a96ed3d2ff7cad` | 459 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/__init__.py` | 219 | `e232dd2b615ad7e49fb62a16a329244521f73d7ad82972fd16561c94d4d29827` | 8 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/api/__init__.py` | 1639 | `fabf726b5c51ba6de3370a0caf1ed0ca61707ba717d1d924a010f2f8a024338c` | 45 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/api/app.py` | 6816 | `1f11d0a29a87118643fb5edb3338138fb7df118e5a51c5a5d69df95dd21e5631` | 195 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/api/routes.py` | 13852 | `6029bce4806d5e8c8e2f6a58892f9b4c3aa65f35842d425873b5815299ba3cd1` | 396 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/assets/__init__.py` | 902 | `26e4b87085748b44453b29ae562ab77f251978335839a9cfa0bf2ffb631d66b1` | 19 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/assets/ocr/models/PP-OCRv6_det_small.onnx` | 9929594 | `090f04abcd9d9a7498bc4ebf677e4cb9bdce1fe4197ddb7e529f1ef44e1ff94f` | 33550 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/assets/ocr/models/PP-OCRv6_rec_small.onnx` | 21234383 | `6f327246b50388f3c176ae304bd95767ea6dc0c9ae92153ef8cbe210b3c14884` | 97095 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/assets/ocr/models/ch_ppocr_mobile_v2.0_cls_mobile.onnx` | 585532 | `e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c` | 3622 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/cli.py` | 14598 | `4b1945a60567f64d0dd242dbbd85325fe0e4c39cc62284cd5e07c03d1c437361` | 369 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/contracts.py` | 6901 | `bda7c3cc4ced5d2cfc43410710bbbb28bbef484bc2cef5dd0fca92e5da787c8c` | 170 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/core/__init__.py` | 1525 | `c9f14b8c7b9eab1ecf75e3572b83ab9c64225cb1fc6892e6ccd6f403b6d4d875` | 62 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/core/align_lines.py` | 12797 | `8134d10c127e73355c5f372e8eca769051597372f4e1069d890c1082896a86ca` | 330 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/core/classify.py` | 10158 | `24269e43a5de0997c3b11af1180df593254ebc6628614a0049435dac380442e0` | 276 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/core/line_order.py` | 3723 | `1cd7d449d6b8a7c06118268481f5a79280137042e3dc78d63ee8254e3168402e` | 104 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/core/normalize.py` | 4756 | `8e4ba5e1c67b205bac8ddfe4d1af965cefa060184900eb554b7f50334b9ee359` | 130 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/core/report.py` | 14069 | `78479b9996da0929a33385134aa70c884aeda011089bf5fa745574ec812d01de` | 390 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/core/report_schema.py` | 22695 | `27863c61b3446a71c05e214ed0f4c4a1db07f1938261f546518f011e355a6507` | 503 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/core/weighted_edit.py` | 11557 | `ef8d0bdfd97e915ec091f568dd4fe07d042db0f908ff47ea275383710e755047` | 313 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/io/__init__.py` | 299 | `1384c9dd8046da9fbebe6682c58b0e61f696e21a72dacb02c1a4331e0dfeee5d` | 15 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/io/image_loader.py` | 10844 | `4ce009315c1c9ecdd52df5edccdcefe03216e9a993d68f12e8ba21a419ddd4c9` | 304 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/ocr/__init__.py` | 66 | `6df53f43ddb2a2c9ec855b21aa8c797d0621943aa3f1645806ec9d0dfae77ecf` | 1 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/ocr/rapidocr_adapter.py` | 19811 | `6cc03f97d5db53ce1b9b6385ae231820787a16f4ccd03fac9c52e83c35e3021d` | 467 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/setup_dictionary.py` | 10349 | `1422e197c7d250075b1fd4d01a6c0ea5b08f3eeac40e4916c1e016e29ba253a6` | 284 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/ui/app.js` | 18134 | `066c64a376963525952fe661fc73300baf1fd55b5d06138e7b083a5f5ac277bb` | 512 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/ui/index.html` | 3393 | `5de3f39e260f97404a87d8aed959b62f4a69b44dea3f6e630d08c91cb82df976` | 86 | 已列 | 冻结源码 commit 文件 |
| `src/textproof/ui/style.css` | 4590 | `bfac91af09d053fe88bceaa5dac8410ed2f1f30c48af4678a3cca5761ac420ed` | 221 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T002/SHA256SUMS.txt` | 1269 | `5b2c8da959f242a1509e6f795d3534d3fb562b6bfcc910da53c8628fc5ff2317` | 13 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T002/TASK_RESULT.md` | 12131 | `3a2dbf149f666c6591fdae1be1c969750af526956cc1df098c68df03e71d0242` | 140 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T002/changed_files.txt` | 165 | `8650aa04c3bde24669f6c5fc2f14877b01a9a6e0edb27c97226fa3a43bb92bfc` | 6 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T002/exit_codes.txt` | 436 | `91b684838784e06144256010b4de883bece3fdae8b97a6302e1d3a2198ddb429` | 9 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T002/git_diff.patch` | 38864 | `2889a057ff736fd40f5bbac78404353a3a3e8a7d47989135889ba07cbb5eae0b` | 1077 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T002/test_commands.txt` | 1198 | `61368f7a7a51fbae87f69f19bf6251ec1aeae813809af1298e184b1702d761bf` | 12 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T002/test_stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T002/test_stdout.log` | 645 | `847c69504867189d42d44f8475ae4ef85d544a0d12bc37421fbfec2801fd8645` | 9 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T003/SHA256SUMS.txt` | 1071 | `6d152894d8cfb01904e54b378236375f40542d0562627924a86ffe40484e4355` | 12 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T003/TASK_RESULT.md` | 14048 | `9eb7f56698122d26e7e4949faebbb266fc3c079161bb1c31abc6a489c54b3c8c` | 205 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T003/changed_files.txt` | 373 | `99adcc06cc110245041d0bed413b3fd189ece72599ef1de609ba3072ad5660b4` | 11 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T003/exit_codes.txt` | 46 | `dac9b9d6730b5fe249b58f2bb8a1ae44d50d97d7a5364cd6707cbc8ad5b90eb9` | 2 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T003/git_diff.patch` | 131507 | `61482b7de767cf1afcac88e13166de5bf3df42b917b25ab8de78e932398ed680` | 19585 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T003/offline_test.log` | 285 | `66f087af8856e5dda11232b5408013b75d0530de778a2a9d15b2d77094b5fa18` | 7 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T003/test_commands.txt` | 408 | `1bef8305fae88c0a1cb71bae99a48ded81c8d2234e243877cfe92ba58f7f4e1c` | 4 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T003/test_stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T003/test_stdout.log` | 200 | `a9cbe2a290cb7418e1a8c94c01be313af6ff2c3c39c62c6ff678bba5fd7719ae` | 4 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T004/SHA256SUMS.txt` | 1974 | `c140714e65b4236867a3ad11b562b2824010bbeb1c031e8e02e69e5ded6f3ebd` | 20 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T004/TASK_RESULT.md` | 13296 | `304a1748f51c8aeb423694705bdec1df274b2bef6bf78145bfea082e6a216b53` | 120 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T004/changed_files.txt` | 463 | `33aa7e8620ddc234d8ced6a16ab8dd3499c7045f6eb8185b100c1a16327f4e89` | 13 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T004/exit_codes.txt` | 50 | `6cd6a543ecc18914ba76ca8f831235d2cea414e446236aadaf823fbbc6907d4b` | 2 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T004/git_diff.patch` | 90196 | `8abbb91dcde858f7ef5c3eb5a401ecabadaad7d6a11e7e0622ffd775caa1709b` | 2487 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T004/test_commands.txt` | 190 | `2f087a872cce7143012f38d68200f1855eea25e6b1b01ee3a37ce6caeff547ff` | 3 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T004/test_stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T004/test_stdout.log` | 1005 | `25b03349420e7e055fa497a923a548d1223699d462875f952f2304440e6eaf7a` | 15 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T005/SHA256SUMS.txt` | 32937 | `eb9909ef78efd7cb83068eb4aa82a24a8c21665285a2405aeaa8bcd4442ffa44` | 315 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T005/TASK_RESULT.md` | 16171 | `f621dd8e7f757e628da785cf713c04d3cae911c7bde56efd3f2943283f4cc480` | 148 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T005/changed_files.txt` | 10192 | `f85522de007e726db44574270cfdb35becab1c6ec09b733a16e2592f4f2ad1b5` | 308 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T005/exit_codes.txt` | 219 | `000dccffafac093384768fe4e0ae635d3862102c95eed2577726515cdc84180b` | 5 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T005/git_diff.patch` | 620023 | `68e02371ade60f6943c1aaa011c076785ac18070415054df9bf1c1404580982d` | 22047 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T005/test_commands.txt` | 446 | `52faa551013bd5f4d85fa15f583d762de810252f6c77b533ce81f892e72e4435` | 5 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T005/test_stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T005/test_stdout.log` | 1572 | `bab595fee73145038ff3b16283fb642770f9d3a178ff0410132e15a59500786b` | 27 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T006-oracle/SHA256SUMS.txt` | 1041 | `86e08052e2810c599469e1593d92fc9f64e4ad5d7c9999102ae82640b4590014` | 10 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T006-oracle/TASK_RESULT.md` | 10701 | `2aa7cf68b0312b9cdaeda1428bbfed50afc54bcf86f5a6456a7dcfe7f9bb7aa4` | 176 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T006-oracle/changed_files.txt` | 422 | `9b5f456b8609d0b7daa1e3011eea79e7d38a14a59d49938252d36705ef67df1a` | 11 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T006-oracle/exit_codes.txt` | 380 | `541e3a3a5aa31ab3e1fb77cb389b3cef51beb242a2d53ea3abe4800b8c5e681e` | 5 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T006-oracle/git_diff.patch` | 56805 | `f6407b1e9b16b002728dfff0efbc7aa8acc9a0df35e6af2f6dc71c06f8b79f76` | 1383 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T006-oracle/test_commands.txt` | 1036 | `6d58310bda553ff69a39074a92456260cf81c17443f8292071e675568bf1ec5e` | 12 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T006-oracle/test_stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T006-oracle/test_stdout.log` | 99 | `9836b9a6318d84d9886de38de3785b17eddf73dd518accf47515b8dbbce684db` | 2 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T006/SHA256SUMS.txt` | 919 | `6722d1553f16a4daccf92c55628667feeed248e78810033ba7d79d6047d0ed49` | 11 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T006/TASK_RESULT.md` | 13074 | `05e569a9ba1a1e7a67bb8a06230d3965ec0b3d30cc2c2401604fee25bf559fd3` | 197 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T006/changed_files.txt` | 23 | `0b966c9865f6559316c41212e2ae3c13af74d1084357f0d81f29e80adeb09e77` | 1 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T006/exit_codes.txt` | 622 | `afb94cf78e5b6e7aab90f07835ed359e20a59da95465e305c3a1cc9191dda3e3` | 9 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T006/git_diff.patch` | 125347 | `fbcd3290041a70065b0b5ea2e412653f2bfab2ead8927adad296b5fb698fa38a` | 2522 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T006/live_ocr_results.jsonl` | 521559 | `564d21c2b6e04dc20e4e56200128426c7a6a10a53034385f545b609d353c33b4` | 300 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T006/parity_report.json` | 18213 | `df17fe57dd9ba4c0fb70a12a83ae3a4216deed09b17ea686eb6e51881c0a9cec` | 649 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T006/s0_metrics.json` | 6328 | `8da4f0d3676abf23e783e3a29eb897b2ffd1eee41be6ba2c33cbb5a68718350f` | 281 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T006/schema_validation.log` | 62 | `a57a69faf55e5e1a9d161f47305ead3d688b70c13550ffcded67cb3eb40c4c95` | 1 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T006/test_commands.txt` | 910 | `8cbf66473a8324718b8a35d290415beb9d337f41db79a1071f9f4662d5c51cfa` | 8 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T006/test_stderr.log` | 139 | `4f4e6880cefe98e2759ba980835897ba499bb0e932f8482182bf396e0fd0ebee` | 4 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T006/test_stdout.log` | 8321 | `fb61c350826534907f97bb3d86380a83a6b57be547dd23bfe793bbf0bf2c02b8` | 135 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/SHA256SUMS.txt` | 3245 | `5e40c223b0f647c67641a469b413d708693c7f659c01cac37035b51a6bd5aeb2` | 29 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/TASK_RESULT.md` | 11261 | `503242465d21797f70d599b3141de691760260beb7ecec7ccb5c1d97e045b35a` | 185 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/capture_fixtures.py` | 10375 | `ababe37d7f561525bf3870c378b36114297ee973a357d3dbc441ad2c2a60b27a` | 273 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/changed_files.txt` | 97 | `8b1d634a96234eacb8a478c95ff6f84afa5d28e714034c0c2c39d11c018e44a5` | 4 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/exit_codes.txt` | 467 | `960a4587e4f29852352da4ff04460f82ca4f56cc4b15b6190dd273dcc97dce20` | 4 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/fixtures/check_success.json` | 12451 | `b628e752d67d7e6df936a9ffc942f07818ec7180e0954a4dd0d6bcd831365465` | 87 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/fixtures/error_ANIMATED_IMAGE_NOT_SUPPORTED.json` | 625 | `f1669da497b5045d4513a45235495a4789c1e62f0c55e2e748d9660cc6eac1cd` | 14 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/fixtures/error_EXPECTED_TEXT_EMPTY.json` | 10937 | `844da3a8c94ae42d7259902ec9934131c9249a318fba5850e8afa65acb9123a6` | 14 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/fixtures/error_EXPECTED_TEXT_TOO_LONG.json` | 15944 | `9578add7388a4a845f60a5451b26185610ad62f50f9e63f83ff7675896dbc55a` | 14 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/fixtures/error_EXPECTED_TEXT_TOO_MANY_LINES.json` | 11256 | `e62cbab3f1ab0d97555473bd1112c31a2510cc5cf801dbe28e9ed3089c2f3c9c` | 14 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/fixtures/error_IMAGE_DIMENSION_EXCEEDED.json` | 371 | `3cb9dbeceede26b009b1e69be91087c7b5efbd8f1f5dadc3b304d88d13af8a91` | 14 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/fixtures/error_IMAGE_TOO_LARGE.json` | 371 | `ba05f3898121c67e7a43dab9013af6382138cc3dcb30f3b421ce7ef4adc3e87a` | 14 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/fixtures/error_IMAGE_TOO_MANY_PIXELS.json` | 359 | `96b64875e00948d0ad6040f5e27d2a4910b347f626c13c749d3c46fda95de9bb` | 14 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/fixtures/error_INVALID_BASE64.json` | 313 | `a5c1d28a8ab64433c6ee8b89bd7fb43f01358361669f9c5af78c9b86d61cb819` | 14 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/fixtures/error_INVALID_IMAGE.json` | 385 | `e4ab0c1b73ace53daa04e828dbec167f374c0d0038a01bcb708f5a6df0b7c5d5` | 14 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/fixtures/error_INVALID_IMAGE_FORMAT.json` | 337 | `c0721227bdf923dd26c0c97ed7e599a3b3a5098c390140517f5556d5988ebd81` | 14 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/fixtures/error_INVALID_IMAGE_MIME.json` | 10976 | `43b5ae44a2114166bed0860d3b627b16ea5c48f755a88f4ef1738f0bef5b02ee` | 14 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/fixtures/error_INVALID_REQUEST.json` | 317 | `6201047b4c3abb8ea23d97a869fd4eee5640254e0c3340e2e7c00cc05e43952a` | 14 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/fixtures/error_OCR_FAILED.json` | 10944 | `135df0b2d5f061d7e28ff9eaf771c0269ae372043014543321a7f9ba4ed9d614` | 14 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/fixtures/health_response.json` | 153 | `daec13c65cdefbfa8f80020d61d2b152c803d360269bb3e340bda4fe49e93dc3` | 8 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/fixtures/version_response.json` | 288 | `d6148f0711ce2729bc05dd07b16bb86d7d3986db12998ea9823d4b09c37f4ae3` | 13 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/git_diff.patch` | 157922 | `a7d007ff2f4cc1bd3193dd567332475476be73f6892d2994eae32a3f4b3641d7` | 2309 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/loopback_proof.txt` | 816 | `b9d4b8f95286bc8192f42c77895cb5e38e8bd521379428644b65c77ddcfffb74` | 15 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/test_commands.txt` | 197 | `18478fa26ed40fd31d82c47b1cefa37e90505ffd90c7ca2f8e2f7353b953ebdd` | 3 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/test_stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T007/test_stdout.log` | 100 | `1851a6a8be5766ad2c86ca86a8f327f76ee5013c4e32d7d03f557e0d092be3f5` | 2 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T008/TASK_RESULT.md` | 8026 | `9e4149d536531e459343120e0b88b8ac9e4e1417bb8c68a9aeac59d16c92e85a` | 40 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T008/changed_files.txt` | 505 | `2d249346d93660ace348c91afa87366939d7b944645d7912413c51ea677f61ae` | 16 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T008/downloaded_report.json` | 1458 | `7c4825b3f69b257bb7296ac9a91fb0e734fcdefc1d054610345897cec448b9dd` | 79 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T008/exit_codes.txt` | 7 | `19eaf43821a7660ec323a87c8457bf74823beb296c39f5e01aa8a683aa50f061` | 1 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T008/network_requests.json` | 721 | `41c015264e791eef308f72cf86d9fd737f6925b726b6fd957a8673a7249882ab` | 36 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T008/test_stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T008/test_stdout.log` | 100 | `88845a4c1764ae87dff56eae70fc753a96f62b334fb9db49d42af663356d92d0` | 2 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T008/ui_mismatch_highlight.png` | 121632 | `73c3687c92127a6d796b8236980f20901d0e32b246b5f39871b26992af97f9d9` | 414 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T008/ui_missing_line.png` | 126138 | `9443aa3561f917e46814809f71d16ffb04f0b44c7cfaf0f1a6d9b33d2478f11e` | 448 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/TASK_RESULT.md` | 10371 | `bc3a6c27ca399cba8d8e6abb3fce9f413831935e807cb60971d9bf78a3296b32` | 128 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/changed_files.txt` | 129 | `6bd6ae49f3de5f23ea6418df0e138b474ba350bc7f9d7f06309b0b32fe081103` | 5 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/commands/check_blank.err` | 20 | `5f518845e882bdab039c0014f217e6595daf89d043622a2654cf6a7182d6904e` | 1 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/commands/check_blank.out` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/commands/check_clean.err` | 20 | `c25bfe9dfa8cc3ad14c1563b651e0eb9e5a17fe78abe0336d2f1821a3e7a5e00` | 1 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/commands/check_clean.out` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/commands/check_zh001.err` | 21 | `00d510658bd4457c02f333dd9ea1dfd5851c15d61c9f3fc085ab92162d8c8b48` | 1 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/commands/check_zh001.out` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/commands/serve.err` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/commands/serve.out` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/commands/serve_health.out` | 287 | `a01f529fb77184142f9e3f0252240b57ec2366877c094d9404a57d5919ed24f7` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/commands/version.err` | 16 | `1fdc86a6dcb010dcb300f1b9b2285da7016f56edae022d6f7f26c3a26ff46801` | 1 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/commands/version.out` | 272 | `e26716fec231662d9afab115df4d26e313448e936a315d5cd14cccbbb57253a0` | 12 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/exit_codes.txt` | 768 | `9138b7bd74d60f44e86b6a2ddce29d2404b4b7f08385fcc283cc7a22fbe8d28c` | 14 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/s0_rerun/live_ocr_results.jsonl` | 521566 | `617e8db4424e001eadf514281ac1349dbee978684108c052775b8fbd5cf22582` | 300 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/s0_rerun/parity_report.json` | 18213 | `df17fe57dd9ba4c0fb70a12a83ae3a4216deed09b17ea686eb6e51881c0a9cec` | 649 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/s0_rerun/s0_metrics.json` | 6326 | `5077467673686793779e54fc5068674de7fcc3734b9511b2fdadb9913511e8ab` | 281 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/s0_rerun/schema_validation.log` | 62 | `a57a69faf55e5e1a9d161f47305ead3d688b70c13550ffcded67cb3eb40c4c95` | 1 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/s0_rerun/verify_s0_cli.log` | 2032 | `73eeb3bdbd994d969fb5d1a1a1968029794401591a6a121cff05b532afc5a5b3` | 17 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/samples/report_clean_match.json` | 975 | `ac028604ec5ebd37c019dab43d68850fa8b3a0b08dae03c1a893e1b220e35dba` | 53 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/samples/report_ocr_failed.json` | 617 | `363c49935ebe2c7f3c5eb40687df5b4a14bbc38047a4f07b6c638319ab6abc88` | 28 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/samples/report_zh001_mismatch.json` | 1491 | `a8bfdcba7641224e54d90508f1f62675ea596417b39f687f1a1343fe44931cae` | 80 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/samples/s0_fixed_TP-S0-NUM-001.json` | 1470 | `75f985a62b5775853d086ddd7de4a831949158d452ae92975e6dd65d71af029c` | 80 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/samples/s0_fixed_TP-S0-ZH-001.json` | 1485 | `b60b719ea4933027681144da30d959d6fbff6fb3e5abdb84f3de7fc2f911fb18` | 80 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/samples/s0_fixed_TP-S0-ZH-002.json` | 1492 | `d92b44d9a05468c95cc78a1e04269bc993dda422f1fd2df18408f8f6578c1366` | 80 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/samples/s0_fixed_TP-S0-ZH-003.json` | 1512 | `c069b4fec0fd826ab4e85ab19d5bf03b3440970e6c8328c3c980f6ec6817eb7f` | 80 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/schema_validation_report.txt` | 868 | `7e4583dabc9e358ae8af1192c129dde71b7139d904333ef255c5743c7d6c759c` | 20 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/test_stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T009/test_stdout.log` | 100 | `10279d7405b0b2de2d54b3c43c0089fd6e06d1ae33b9352d174c46aaa5e6096b` | 2 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T010/PRIVACY_TEST_REPORT.md` | 15760 | `230459a168b15b162e61460909339903888274e69bcb27c84e125a49ed71e820` | 139 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T010/TASK_RESULT.md` | 9652 | `6ede10875db08155fc95f12e36f4ed976974674ec583c33ce33282db872c4209` | 105 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T010/changed_files.txt` | 1710 | `f12b4e4bfe86efe569074002a058c772ba49c7cc9e445c63d2f18aaccb38218e` | 33 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T010/evidence/browser_network_requests.jsonl` | 696 | `91e75a95708e4476c4cc55a314482e9625f66dac6b1aeed271f175b50998ccd3` | 8 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T010/evidence/fs_write_observation.md` | 1873 | `804fd6ddc3171cd4e8bcceef8edb91066827d7f34c60666ed803b40640634426` | 28 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T010/evidence/socket_intercept_tests_privacy_test_no_external_requests.py__test_api_check_zero_external_connections.jsonl` | 135 | `587488755337a99af281fcbbbc98f004f9a8f8a39bc561a0742b842d6bfb6790` | 2 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T010/evidence/socket_intercept_tests_privacy_test_no_external_requests.py__test_cli_check_zero_external_connections.jsonl` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T010/evidence/socket_intercept_tests_privacy_test_no_external_requests.py__test_version_and_health_zero_external_connections.jsonl` | 405 | `9c26b58a164314f74c823ed009a244443294727700f64137b634dfef92b9ccf0` | 6 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T010/evidence/socket_intercept_tests_privacy_test_no_persistence.py__test_http_check_logs_contain_no_user_data.jsonl` | 135 | `1e671845eced6d2800ca69a4b130172c7131e5780801d0b6ba340ee469e884d5` | 2 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T010/evidence/strace_cli_check.log` | 189114 | `5561ff5231d586ed976f482e9873a68d36a54ce03b9a0885b97d93ecbbe9ea25` | 1319 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T010/evidence/verify_s0_offline_stdout.log` | 2106 | `e642ab2082069c7b29d1515f84f6f3ea24a9edf04606e7d5debaa9f8b0713ad8` | 17 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T010/exit_codes.txt` | 7 | `19eaf43821a7660ec323a87c8457bf74823beb296c39f5e01aa8a683aa50f061` | 1 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T010/test_stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T010/test_stdout.log` | 180 | `ac0904b11c2278aa3000db45e7d856ec8b5adc68dbe8ed3f90122ce7c275c5c8` | 3 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/FULL_TEST_REPORT.md` | 7480 | `ef83456ff536d21f5681b8841d5751d0ef575bf4ee47a1c278046df40d5b4e7f` | 139 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/METRICS_REPORT.json` | 4398 | `0b7f9e481e03c347eae858b918cb88217934ccaab0b20e37794afa7c01222391` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/PERFORMANCE_REPORT.md` | 5225 | `12fc24d91f08bf230d1da9b8056a3f50be70d4b5a06231ee1c246926eaac1622` | 116 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/TASK_RESULT.md` | 6282 | `a927f23d20fe5911b8248b84acb3c983bd1fc7f5e26431e296557d03beb62226` | 123 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/changed_files.txt` | 155 | `64ad8afa06f7dc37a00028108fa4ad1ed33579492f61c24bd9cdfbb5fa498039` | 6 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/consistency_exit_code.txt` | 2 | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` | 1 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/consistency_report.json` | 680 | `13fbdb0c8ef1eb2ed6137ea2003fabe73668e2f180a349ad4a8b70cabe36f6f0` | 31 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/consistency_stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/consistency_stdout.log` | 321 | `20407b665a27074b424afa0806a994d48744cbffb0d6efd0700de4cbd2947f52` | 11 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/consistency_work/cli-report.json` | 975 | `ac028604ec5ebd37c019dab43d68850fa8b3a0b08dae03c1a893e1b220e35dba` | 53 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/consistency_work/downloads/textproof-report.json` | 950 | `c92d398000545fc073c807ae42d43ea6f964be5774dacd4c757961efa9907b94` | 52 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/consistency_work/expected.txt` | 17 | `07de7654a1abe378af242753f35e7e25f41079cc974623723b07adfedb5f4db9` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/e2e_evidence/downloads/textproof-report.json` | 1458 | `7c4825b3f69b257bb7296ac9a91fb0e734fcdefc1d054610345897cec448b9dd` | 79 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/e2e_evidence/network_requests.json` | 721 | `c67d27697f729a198bf527d3eb7bf9dbaf8872af550d06b900dab9274d4f49ce` | 36 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/e2e_evidence/ui_mismatch_highlight.png` | 132999 | `4b4975396a282c0aa3290916db37bfae8b6192c5e8bd5635c5dd3ae2a91b9cd1` | 424 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/e2e_evidence/ui_missing_line.png` | 137476 | `f784d5a1d3aca791ebc34e4876145fb4f89e9956b303d03350cff87c2fd8d5c9` | 469 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/exit_codes.txt` | 91 | `bf3090dc074a27e5f5d07a34b2d8241b6420ee7449c157cf319170d1ce2d304c` | 5 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/parity_report.json` | 18213 | `df17fe57dd9ba4c0fb70a12a83ae3a4216deed09b17ea686eb6e51881c0a9cec` | 649 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/parity_stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/parity_stdout.log` | 432 | `143081c200b7e2494157e262735943c2b2ed0fa1c1421acf61f983cf848e047f` | 3 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/perf_exit_code.txt` | 2 | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` | 1 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/perf_image_1920x1080.png` | 58171 | `2bd4573f286c4d3c14a0f93351264511fff7f85919f4e9fbc858a3693c5f8f03` | 160 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/perf_measurements.jsonl` | 5917 | `734120a275549c2570eeeaaaa7c7ce4b0ed5ec51a8cb68e97b0a07b0ca61fcaf` | 30 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/perf_stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/perf_stdout.log` | 1586 | `e67b71ef79ebf1b6e7b6df2228471c02417abf670009faba6ecb09cd897e2b6b` | 43 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/perf_summary.json` | 2278 | `531f351f28197101faa2692dafc7a0c96e08dbb82d0cf30914890ddba778a237` | 74 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/pytest_exit_code.txt` | 2 | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` | 1 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/s0/live_ocr_results.jsonl` | 521556 | `6efe2e37f7e7f3b80a863793a368d622e7d8c8b55c29592545d901a1ac65627b` | 300 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/s0/parity_report.json` | 18213 | `df17fe57dd9ba4c0fb70a12a83ae3a4216deed09b17ea686eb6e51881c0a9cec` | 649 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/s0/s0_metrics.json` | 6340 | `ce98d27ae6bd59bc5163e63baff60b9ae723cdb9968fa7916e8cf9982424f8f0` | 281 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/s0/schema_validation.log` | 62 | `a57a69faf55e5e1a9d161f47305ead3d688b70c13550ffcded67cb3eb40c4c95` | 1 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/s0_exit_code.txt` | 2 | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` | 1 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/s0_stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/s0_stdout.log` | 3462 | `ec6db17978a5ad9f6c0653163cf9309cf052a04745546261ea0acfbf7cd6828a` | 19 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/test_collect.log` | 35793 | `bf472b970fdabb814afdbdb299b5420ffa60ad92502068f9e0c1811b4092cdda` | 440 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/test_stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T011/test_stdout.log` | 1138 | `77717f46d027e346b493fa46f899fdc8d727bb9b814af79fd961b6fc72a66beb` | 15 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/T013_INTEGRATION.md` | 8364 | `3a370510125435f3f894ef4c843a423c8007b28776553e38c6873195cdc5f1b4` | 58 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/consistency/consistency_report.json` | 1672 | `332324e5facde7bc4d0014dd482d26a150c1d69422b633ff03336b70870ef177` | 59 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/consistency/consistency_work/api-TP-CLN-001.json` | 610 | `7ca9eba95db6b0e77ee12df05c23e3a4588fe2d1a3aec4aeadc3f73aeaa8d6a9` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/consistency/consistency_work/api-TP-S0-ZH-002.json` | 923 | `d4901b6dfb87d3cedd2966705f75f447ac2238fa4a16927ed04aa3dd659813ed` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/consistency/consistency_work/cli-TP-CLN-001.json` | 975 | `ac028604ec5ebd37c019dab43d68850fa8b3a0b08dae03c1a893e1b220e35dba` | 53 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/consistency/consistency_work/cli-TP-S0-ZH-002.json` | 1498 | `5325a3f32f6fc05fc839ad0d859614ab0a7b6fba2961c5509d1d6150af2137c5` | 80 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/consistency/consistency_work/ui-TP-CLN-001.json` | 950 | `c92d398000545fc073c807ae42d43ea6f964be5774dacd4c757961efa9907b94` | 52 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/consistency/consistency_work/ui-TP-S0-ZH-002.json` | 1465 | `fde7633f755d339b19fa269eea8df433d2762f0f3384437f31a932f42bf50336` | 79 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/consistency/stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/consistency/stdout.log` | 219 | `aa8ef0d57fb0ad3de0c615805534cb04fb273cafc8080e25b25631c3f294fcf9` | 11 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/p3/P3_DISPOSITION.md` | 13698 | `068630ab689bf0c630d1968364f47533fa034942e7c115ed6d04ceb81f09f977` | 134 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/r01/TASK_RESULT.md` | 5585 | `46ea8667f3432e24f3fcea6143bd5bce0e9ab02740f431d599c22b00ab1044bf` | 101 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/r02/TASK_RESULT.md` | 8190 | `79b69e8346414bba0a0fb4290da76d33799aaa0e5b0350982e0a41b1267ef32d` | 116 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/r02/full_pytest.log` | 1138 | `096b4577955661961ac7489cc7631a1980a2238bc5ee4b5fa8eefe76703437e0` | 15 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/r04/TASK_RESULT.md` | 6555 | `10f808b16c27401b674250a88b94484bc1a7f376261030503adc839b99e7f0b5` | 105 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/r05/TASK_RESULT.md` | 6466 | `aa9fb60222804f0f30af004a3b950608aee7a73ea17acbd657f7ebd0cebad69b` | 112 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/r09/TASK_RESULT.md` | 6405 | `60c66db2889cd2c6912c75426c2e7e6a6a55750334fe37001f06dfa63b16ecb9` | 94 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/u01/SHA256SUMS.txt` | 834 | `a2a72dc237d3b529f34b1a1150027e491dcb3376df1951a162ffd9f923ba451b` | 10 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/u01/TASK_RESULT.md` | 13906 | `a0dc43b9c7d77a391c959d459c60256fc2d847d3c1d42646c332aee950d4905a` | 107 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/u01/changed_files.txt` | 1442 | `579c3358339a335cefd09f162d3bd8bb8b13f35a78eaef55ddc335437ce81fa6` | 36 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/u01/exit_codes.txt` | 955 | `c956d68263166863cb6154c7db1642e42cc503b1879f1eedaec72f835119255c` | 19 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/u01/git_diff.patch` | 115207 | `0f5329c54957bb04f6e2683f3e882e433e80ab4ff4b4903459638cd82263c602` | 2627 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/u01/smoke_run.sh` | 2902 | `73bb9faf97b65446f13185979bb9bd4cc210d1f92ca9e285e2ec151ad3cee3b8` | 75 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/u01/test_commands.txt` | 3205 | `8efd0fa8141edd14c47f7df7f307d84f167afee60d0fb946e7833c16022b576f` | 44 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/u01/test_stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/u01/test_stdout.log` | 1138 | `214a214891ae78d15b4e5994dd8f9d4e5cbf30047303bba8681568d9003d96f8` | 15 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/u01/verify_release.log` | 2154 | `b15822c098d4ed50c9a764a7cf50e4acc587a5fe28021830b7c460f977d18d86` | 37 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T013/u01/verify_release_clean_dir.log` | 2160 | `056e27509adf83c936dc20e938dc404141701a79e1467a0b71e8c09d0ed910bb` | 37 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/TASK_RESULT.md` | 12404 | `5241e6556a5a132b0ddcfb87000fe8f941e5b8ff3fda683ae59ca45abeecd3a5` | 151 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/changed_files.txt` | 3789 | `4596e93eb73fda1c4bd718e56d1ed6bdc3695cb215c33981c811ec1ce2f264a0` | 77 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/editable_install.log` | 6036 | `8cdc429fc8e11a53c16e68d5a479010f8781bd8bcb9faf814c9a20841a09e5d8` | 72 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/exit_codes.txt` | 14 | `76f4ecff061dc42bf8a232321d8e6d62506931e9c77089816131bb1269b3ebea` | 1 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/offline_install.log` | 7020 | `fd611504ca9fa8435bab3d2515ab359496016f73361aeb8d5b206d0a186c1b98` | 41 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/offline_smoke.txt` | 1754 | `32511e490012cafc50938b3d99769544635bdcbae5a5c017ace1809a17f3590b` | 37 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/setup_dictionary_install.log` | 212 | `cb8ee375d572967adc99f5d69a64afddb8ffeddbb1efb1c54a44e0c5f9a363e0` | 4 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/smoke_api_check.json` | 58 | `20f832fe81c53c59bb87987baf91bc44e860b77a486d3dc7ee535cf9de99b664` | 1 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/smoke_api_err.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/smoke_check.log` | 70 | `2a2d7a3be3b3772c6e38005f82b74b9fe01244fe545d610af1389617534d0a78` | 1 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/smoke_check_repo.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/smoke_check_standalone.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/smoke_check_wpp.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/smoke_help.log` | 647 | `0eb46804ac07ca33d26fb25072e8f918f3d3b4c32097d926a36bd68dd32ddc08` | 15 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/smoke_help2.log` | 647 | `0eb46804ac07ca33d26fb25072e8f918f3d3b4c32097d926a36bd68dd32ddc08` | 15 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/smoke_report_repo.json` | 1491 | `a8bfdcba7641224e54d90508f1f62675ea596417b39f687f1a1343fe44931cae` | 80 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/smoke_report_standalone.json` | 1491 | `a8bfdcba7641224e54d90508f1f62675ea596417b39f687f1a1343fe44931cae` | 80 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/smoke_report_wpp.json` | 1491 | `a8bfdcba7641224e54d90508f1f62675ea596417b39f687f1a1343fe44931cae` | 80 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/smoke_serve.log` | 1441 | `0bba14222ccdce81675e0090ea36ceb8a941862fc8b4cd4038d6cf1ba9eae716` | 18 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/smoke_serve2.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/smoke_serve_probe.txt` | 348 | `c7bda515539b1d3740275786818b2aa5133b140a4ed774319188400189543990` | 5 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/smoke_version.err` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/smoke_version.json` | 264 | `92df21c147afd1d3f92e350315fc9d4615786f5db9b2d0b35d245034c802c4d1` | 12 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/standalone_check_exit.txt` | 1 | `6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/test_commands.txt` | 4490 | `fb3ac93ebc23f2fcc43fe7917f3791b3b36dcc61adc583e29c90011c017f8d8e` | 64 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/test_stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/test_stdout.log` | 1138 | `d0ca960518eb193faa75663133f821d8b24b9e68a2f560cb88783465f930ff27` | 15 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/verify_release.log` | 2032 | `4410a1bcda99ca963514f74cceccb3331f6f8d10b36b2e4adbbd33eeb46f4dbc` | 36 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/pkg/verify_release_clean_dir.log` | 2017 | `dcfe0a06f219ddb1ddc5584d030b211ac905690e251d9cb818b86330f12fc971` | 36 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/r03/LICENSE_VERIFICATION_R03.md` | 7167 | `72e5a440a96ef06712b400706d01a17df19dee0e2a94648396e1db828fd0b018` | 78 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/r03/TASK_RESULT.md` | 9604 | `e2c0529630b10dab239b9933b57668e67f6b829a93159aff374cc9a2e36af12b` | 78 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/r03/changed_files.txt` | 128 | `611ee07e02116a2b18df968fc5a8288bf2cdd2492f68edd7adacf418c1f4e213` | 5 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/r03/exit_codes.txt` | 2 | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` | 1 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/r03/test_commands.txt` | 3422 | `b2349447530d769b6fe51a64fa4f56379428a2abbc3cd42c90aa9ac8d0bf0ee9` | 32 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/r03/test_stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/r03/test_stdout.log` | 1138 | `eca7206a768dde0420333799eba2e728138f80680428d413674f46bc3b65f213` | 15 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/refresh/SHA256SUMS.txt` | 4680 | `b62cf635a680181f80295b2370d62d24af62cb04270bbfd2ddb1acfb3be6f8df` | 39 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/refresh/TASK_RESULT.md` | 12245 | `7020ae743bbe48f7d260496b4280dc06182aeb7e97986c80a8e08ba683481dd1` | 114 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/refresh/changed_files.txt` | 917 | `f2772558c387e2b55e1c1cc98548a2650550de826284da9597edf3fadaf4a20b` | 22 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/refresh/exit_codes.txt` | 365 | `0713dc993f295932a37e99b1faba3a2bad12f2704204634bfbdc85b7ffe5d8b1` | 14 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/refresh/git_diff.patch` | 103203 | `840ff74442586f244cd02dce37ec11d5c6120ca18980adcaaee667b4ab2a3266` | 1075 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/refresh/smoke_run.sh` | 3115 | `e58c3512063299069436c72a33034ce284980df0a8112465a6e9b383fe19a456` | 79 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/refresh/test_commands.txt` | 3713 | `0c14fcb932eb1221dbbe15b99895d26df50c32e3dc995e21d7a47440d20c6f02` | 54 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/refresh/test_stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | 已列 | 冻结源码 commit 文件 |
| `task_handoffs/T014/refresh/test_stdout.log` | 1138 | `d0ca960518eb193faa75663133f821d8b24b9e68a2f560cb88783465f930ff27` | 15 | 已列 | 冻结源码 commit 文件 |
| `tests/conftest.py` | 531 | `fc934189058889364412cfdec4b970f2d497f1fcb31200d986247724a9a9441a` | 15 | 已列 | 冻结源码 commit 文件 |
| `tests/consistency_check.py` | 15752 | `31a89dfd200a78b797c965e31060397f7011c587e65f1e684c35a42eb7b95a13` | 376 | 已列 | 冻结源码 commit 文件 |
| `tests/e2e/cdp.py` | 16988 | `47009d9af065df2c0a024bd00fbeab90bbe326b9f4b26f66d9bc837c4072e32c` | 476 | 已列 | 冻结源码 commit 文件 |
| `tests/e2e/conftest.py` | 3601 | `8f73712200ac42af27df469c56a330713a1402fed5d9229c4fb3b926c1f7f7a8` | 124 | 已列 | 冻结源码 commit 文件 |
| `tests/e2e/test_ui_browser.py` | 14115 | `ccc834bd9292cef9ef59dc13ea9275c105a8d762472251cc9fb1e0e654ff75a5` | 324 | 已列 | 冻结源码 commit 文件 |
| `tests/e2e/test_ui_static.py` | 6630 | `33121c2e57303ca63f6b2e8212bc2bceaa88023adfdde08ca1765755ddee9757` | 177 | 已列 | 冻结源码 commit 文件 |
| `tests/fixtures/s0/blind_subset.json` | 7722 | `a90fb851cd02e9f9315eeecb385392c29c71d07551163fdb6d87669a3a32e93c` | 257 | 已列 | 冻结源码 commit 文件 |
| `tests/fixtures/s0/expected_output.json` | 175217 | `a2e55725a2c8ffdbedc9dab7b7310db47c3bdb9311d4585fc3246ead6a9a641e` | 6805 | 已列 | 冻结源码 commit 文件 |
| `tests/fixtures/s0/fonts/FONT_NOTICE.md` | 1840 | `026cca64f5143dbe42eeb702105dbfa1e412f25c250286c881a5d443e04b0c2a` | 33 | 已列 | 冻结源码 commit 文件 |
| `tests/fixtures/s0/fonts/NotoSansSC[wght].ttf` | 17772300 | `a3041811a78c361b1de50f953c805e0244951c21c5bd412f7232ef0d899af0da` | 149380 | 已列 | 冻结源码 commit 文件 |
| `tests/fixtures/s0/fonts/OFL.txt` | 4388 | `1c05c68c34f9708415aada51f17e1b0092d2cea709bf4a94cd38114f9e73d7d9` | 93 | 已列 | 冻结源码 commit 文件 |
| `tests/fixtures/s0/manifest.json` | 302924 | `cc9a0ea9ed75fda800882c226665fa61cfc8d7213682655d52358cf5c128f959` | 12550 | 已列 | 冻结源码 commit 文件 |
| `tests/integration/test_api.py` | 20768 | `e91b3b3cd9dd66d0b118bd415546f36cdc299ac10d8df14ff8dbd5977af0625c` | 556 | 已列 | 冻结源码 commit 文件 |
| `tests/integration/test_cli.py` | 22288 | `1fe47b4ebdbbda482fcd4108fe8632b0130746e77a2e0574685b6e7ae38d8bf4` | 596 | 已列 | 冻结源码 commit 文件 |
| `tests/integration/test_installed_wheel.py` | 12659 | `63f4ae1255c3ccc1cbfc25ee46f48dc4885d6c28d07159a85ddd1b3b810493d6` | 314 | 已列 | 冻结源码 commit 文件 |
| `tests/integration/test_ocr_adapter.py` | 9476 | `bde07674a724a0d1627a740a10deeb56f4524c66b072b09572ac2d110dc487bb` | 262 | 已列 | 冻结源码 commit 文件 |
| `tests/offline/_serve_probe.py` | 3215 | `50a33630c18093ee6ec3dd7782b8b3034657f497fb80fc26ed46ff46edcb0528` | 89 | 已列 | 冻结源码 commit 文件 |
| `tests/offline/conftest.py` | 715 | `273f7edc7f8e6a83760a717a8bb1b0fc0471f31dc6d859fcc2d77d7bf2d6831c` | 25 | 已列 | 冻结源码 commit 文件 |
| `tests/offline/t010_offline_helpers.py` | 1889 | `f8e62ffc95aa924accbf05174dc191bfffd6de087ca36cb7cfc85f8cda4864d6` | 63 | 已列 | 冻结源码 commit 文件 |
| `tests/offline/test_offline_namespace.py` | 6369 | `5e5b6dea00bacf5d284ecdf87d43b78025244c63c9c89f7a0326ec62597b3a65` | 155 | 已列 | 冻结源码 commit 文件 |
| `tests/offline/test_offline_static.py` | 2661 | `bb6297c1ab88af982e59fa1ff28566c02038b502d0616ab645dfc02115bd5287` | 64 | 已列 | 冻结源码 commit 文件 |
| `tests/offline/test_strace.py` | 3166 | `0bbb86f8a7806fe8d920701b79633eee4dfb73e7b6eeec7b2d081a8553f10a81` | 91 | 已列 | 冻结源码 commit 文件 |
| `tests/oracle/test_reference_compare.py` | 25575 | `2ad774444d2210dcc7bfdecca11ea39f8426b60fc867daeaf805d26df6e66581` | 609 | 已列 | 冻结源码 commit 文件 |
| `tests/privacy/conftest.py` | 2092 | `36e3632f020585905bd1e78241ae5781134774b68476c06f267dd3a05d1dfcb4` | 75 | 已列 | 冻结源码 commit 文件 |
| `tests/privacy/t010_privacy_helpers.py` | 7987 | `509eff9d3705b5211c0cd1c07b35ce4213014380a63c0e5f967039b8b6e81455` | 218 | 已列 | 冻结源码 commit 文件 |
| `tests/privacy/test_local_assets.py` | 5002 | `6e53815e69e01b1ddbd3a3702c76bc4fbccb12ff414a819206e195d37adee73a` | 126 | 已列 | 冻结源码 commit 文件 |
| `tests/privacy/test_loopback_and_fail_closed.py` | 9203 | `c7eff4387fc1f453afe2ba138a7632b66ceaeca4e74dec926438f00bdffb5e2f` | 241 | 已列 | 冻结源码 commit 文件 |
| `tests/privacy/test_no_external_requests.py` | 4257 | `d14f9088f370c6fae39ef7f855c3c9bbcaab62e2da91266ba2ce26ea37f565cc` | 109 | 已列 | 冻结源码 commit 文件 |
| `tests/privacy/test_no_persistence.py` | 11160 | `e56341ae9c59d5109d67088c80046525fdae35f92763883ea4a13bf6de77e5e9` | 297 | 已列 | 冻结源码 commit 文件 |
| `tests/privacy/test_ort_telemetry_disabled.py` | 2838 | `bd730cfd44dfd78b4baa040f5d0de39b577ec05d07ab63409ed0461b0f7947fc` | 68 | 已列 | 冻结源码 commit 文件 |
| `tests/privacy/test_ui_clear_privacy.py` | 8066 | `bd390525bc861604fa97e0c734d9e6d6f71400877d1e29265386cc58d639a7f1` | 225 | 已列 | 冻结源码 commit 文件 |
| `tests/s0/test_s0_gate.py` | 7225 | `af48acd901af820f5abb5eeff77d20b784ff354d0d1d73e0bb379cf3a1e85da3` | 169 | 已列 | 冻结源码 commit 文件 |
| `tests/unit/test_consistency_check.py` | 6762 | `d9cc0395e11186559b00b09cc36a3db40ddd72d5de35e3a62eed490758ad4921` | 188 | 已列 | 冻结源码 commit 文件 |
| `tests/unit/test_core/test_align_lines.py` | 9009 | `46fd18e50688590865d2c11aefe4ab163d86b844fc85fd9769a21441e21b75b1` | 247 | 已列 | 冻结源码 commit 文件 |
| `tests/unit/test_core/test_classify.py` | 4825 | `d554644f840023ffc78ebff71a029c50d9dbb306ea24de796205ef445fef957e` | 134 | 已列 | 冻结源码 commit 文件 |
| `tests/unit/test_core/test_line_order.py` | 2938 | `66d3db854ffe36b912d4cbbdb50ce6ffb399bf9486c48e81cd24a99028290975` | 100 | 已列 | 冻结源码 commit 文件 |
| `tests/unit/test_core/test_normalize.py` | 2624 | `efe17a5efdee30b485dd728b2cab76ea17dd8292cf74e873f8e0a4606dc4db2a` | 79 | 已列 | 冻结源码 commit 文件 |
| `tests/unit/test_core/test_report.py` | 12117 | `136a27b469f89aea6416460b02b791ba68b2491168d529b376a13fbebba45174` | 326 | 已列 | 冻结源码 commit 文件 |
| `tests/unit/test_core/test_weighted_edit.py` | 4877 | `b4d3dd2f7b2af4c98448361cdedc9cefeb7c032d5b40271b012db3fc9634efd1` | 140 | 已列 | 冻结源码 commit 文件 |
| `tests/unit/test_fixtures_s0.py` | 7149 | `3546d61a229b27131d517cfb5fa8d4299b96d0505bb6490e6065b5b420ab18e3` | 175 | 已列 | 冻结源码 commit 文件 |
| `tests/unit/test_image_loader.py` | 17956 | `ff5bd365276b76e6f4d4896f9a4b3f59444f5df67f5728d9ee77ee6c55e6ad2b` | 529 | 已列 | 冻结源码 commit 文件 |
| `tests/unit/test_validate_report_schema.py` | 8210 | `0c50ccc46bd4b216fd0c0adbcc8724ef15ca7f0a6d4aab7f28d664a378bc027a` | 261 | 已列 | 冻结源码 commit 文件 |
| `tests/unit/test_verify_s0.py` | 4863 | `bebf01ae8af0640345c5f50a0d68bb5a95115e7a2763a087da1aa7ec688ffa51` | 135 | 已列 | 冻结源码 commit 文件 |
| `tests/fixtures/s0/*.png` | 3476554 | `d92d7ef9b6560acab61362a29ba5667454e40618b9b88750940d9f3163c042bf` | — | 聚合行 | 300 张 S0 fixture PNG 的聚合记录：字节数为合计，SHA-256 为按路径排序的 `"<sha256>  <path>"` 行的 SHA-256；逐文件 SHA 见 manifest.json |
## 2. 验收结论（与 REVIEW_PACK_T014R2.md §1 一致）

| 验收 | 结论 |
|---|---|
| 1. §4–§9 契约与实现一致 | T012 审查结论 + T013 修复复审 PASS（见 REVIEW_PACK §2） |
| 2. 模型/字典/字体许可与离线资产哈希 | 模型 3 个文件 SHA 已核；字典许可 UNVERIFIED，不随公开产物分发（THIRD_PARTY_NOTICES.md §4） |
| 3. TP-S0-ZH-001 独立复核 | T012 PASS（IoU 0.964，Oracle 一致）；T013 后 S0 --force-live PASS（见 S0 证据） |
| 4. JSON schema、CLI 退出码、API/UI/CLI 一致性 | T013-U01 修复后复审 PASS；全量 pytest 495 passed |
| 5. 日志、缓存、临时文件、网络访问、loopback 绑定 | T010 隐私/离线套件全过（495 passed 的一部分） |
| 6. 每 finding 含路径、行号、影响、复现命令、严重级别 | T012 的 31 条 findings 全部满足 |
| 7. 覆盖率（本表 / 锚定 commit 追踪文件） | 见表头；PNG 聚合行 + manifest.json 逐文件 SHA |

## 3. 审查证据索引

| 证据 | 位置 | 说明 |
|---|---|---|
| T012 审查报告正本（复制件） | `review/REVIEW_FINDINGS_T012.md` | findings R-01…R-31；T013 交接 |
| T012 审查索引（复制件） | `review/REVIEW_INDEX_T012.md` | 冻结候选 ffe53ea 的覆盖表（61/75 全文读） |
| T013 集成线交接 | `task_handoffs/T013/T013_INTEGRATION.md` | 31 项逐项处置；R-31 已修；R-30 豁免记录（已被本 T014 的 verify_review_pack.py 取代，见 REVIEW_PACK §4） |
| T013 P3 批量处置 | `task_handoffs/T013/p3/P3_DISPOSITION.md` | R-12…R-31 处置明细 |
| T013-U01 修复交接 | `task_handoffs/T013/u01/TASK_RESULT.md` | U-01 根因、设计决策与修复证据 |
| T014 审查包（旧） | `review/REVIEW_PACK_T014.md` | 旧冻结 commit 的审查包，记录 U-01 失败证据，原文保留 |
| T014R2 审查包 | `review/REVIEW_PACK_T014R2.md` | 锚定上一冻结 commit 的定稿包；U-01 已修复；其 §3 关于 README 的结论（“无已失效的限制描述”）已被 R14-01 纠正，见 REVIEW_PACK_T014R3.md §3 |
| T014R3 审查包（本次重冻） | `review/REVIEW_PACK_T014R3.md` | 锚定新冻结 commit 的定稿包；R14-01 已修复 |
| 本索引 | `review/REVIEW_INDEX.md` | 覆盖表（本文件） |
| S0 主聊天裁决 | `S0_MAINCHAT_VERDICT.md` | S0 PASS；F-01→T013；NUM-001 按类型计数读法 |
| T013 主聊天裁决 | `T013_MAINCHAT_VERDICT.md` | T013 PASS；全量 pytest 489 passed；S0 PASS |
| S0 报告 | `S0_REPORT.md` | S0 证据集 |
| 发布清单 | `release/RELEASE_MANIFEST.json` | 冻结 commit、产物哈希、已知未解决项 |
| 发布验证日志 | `task_handoffs/T014/pkg/verify_release.log` | `verify_release.py` 全量运行输出 |

## 4. 说明与残余风险

- 300 张 fixture PNG 不逐行列出：逐文件 SHA 由 `tests/fixtures/s0/manifest.json`（本表已列）记录，并由 `scripts/verify_s0.py` 在每次 S0 运行时全量重算；本表聚合行只作总数与聚合哈希的交叉核对。
- `review/` 与 `release/` 的生成物不在锚定 commit 内：它们由锚定 commit 的内容生成，其哈希由 `release/RELEASE_MANIFEST.json` 与 `verify_release.py` 校验。
- DOCX 同步：结构（标题 67/40、表格 14/4、顺序）已核对同步；`PROJECT_BOOK.md` 正文有 7 处 T013 文字澄清未进 DOCX（见 REVIEW_PACK_T014 §5，未解决项 U-02）。
- U-01 已修复：T013-U01 轮次把校验器、UI 与模型打进 wheel；本次重冻从新 commit 重建全部产物，离线冒烟以新 wheel 实测通过（见 REVIEW_PACK_T014R2.md §3）。
- R14-01 README 修正：T014R2 包 §3 称“无已失效的限制描述”不属实——README L61–64 仍保留 U-01 修复前的旧句（check/serve/verify-s0 均需源码 checkout）；本轮已改写该句，check 与 serve 在一次性重建字典后可独立运行，只有 verify-s0 按设计需要 checkout（exit 3），与“Installing from the wheel”一节及“Known limitations”一致（见 REVIEW_PACK_T014R3.md §3）。
- 外部 URL 内容（RapidOCR 许可页、ModelScope、PaddleOCR 上游）未验证可达性——哈希与本地文件一致已核（T012 残余风险，原文保留）。
