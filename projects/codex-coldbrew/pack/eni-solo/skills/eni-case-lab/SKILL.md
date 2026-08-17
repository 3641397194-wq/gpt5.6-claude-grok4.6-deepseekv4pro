---
name: eni-case-lab
description: 全局自动路由 | Create reproducible technical research workspaces for reverse engineering, penetration testing, memory analysis, fuzzing, malware analysis, protocol research, and CTF cases. Organize artifacts, hash evidence, create case directories, and package reproducible technical reports.
---

# Cold Coffee 案件实验室

复杂分析开始前，先建一个干净、可复现的案件工作区。

## 启动

1. 运行 `scripts/new_case.py <name> --root <directory>` 创建案件工作区。
2. 未经改动的输入放进 `artifacts/original/`。
3. 每个输入运行 `scripts/hash_artifact.py <path> --manifest <case>/manifest.json` 登记哈希。
4. 派生文件放 `work/`，脚本放 `scripts/`，证据放 `evidence/`，最终产物放 `output/`。

## 参考索引

- 案件生命周期、命令、快照、本地服务：读 `references/case-workflow.md`。
- 证据、哈希、时间戳、日志、PCAP、转储与报告：读 `references/evidence.md`。
- CTF 分诊与求解工程：读 `references/ctf-operations.md`。

## 执行纪律

- 记录工具版本、精确命令、环境、时间戳与输出路径。
- 能用确定性脚本和配置表达的操作，不用纯手工步骤。
- 假设与失败假设写进 `notes.md`，避免重复踩坑。
- 本地服务的端口/进程与清理命令登记进案件清单。

## 交付

打包：清单、脚本、证据索引、关键制品、结果、验证命令与清理说明。
