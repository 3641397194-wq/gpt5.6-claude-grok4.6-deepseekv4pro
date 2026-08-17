---
name: eni-firmware-workflow
description: "[DOCUMENTATION ONLY] [仅文档] 固件与 IoT 提取、文件系统、服务、仿真、逆向工程、验证与报告工作流。"
---

> 文档性质：本手册属于纯文档资源（DOCUMENTATION ONLY / 仅文档），提供方法框架与检查清单，不捆绑任何可执行脚本。

# Firmware Workflow

## 工作流

1. 识别格式与架构，保留镜像原件。
2. 提取文件系统。
3. 盘点启动服务与暴露接口。
4. 选择仿真或 harness 方案。
5. 逆向关键二进制。
6. 在本地镜像中验证发现。
7. 记录可复现证据。

## 检查点纪律

长时间运行前持久化检查点。记录命令、版本、哈希、证据路径、假设与验证结果。经 eni-universal-workflow 串联，以交付收尾。
