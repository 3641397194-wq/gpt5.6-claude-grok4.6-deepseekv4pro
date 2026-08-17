---
name: eni-mobile-security-workflow
description: "[DOCUMENTATION ONLY] [仅文档] Android 与 iOS 静态、动态分析工作流：MobSF 式分诊与 Frida 式运行时观测。"
---

> 文档性质：本手册属于纯文档资源（DOCUMENTATION ONLY / 仅文档），提供方法框架与检查清单，不捆绑任何可执行脚本。

# Mobile Security Workflow

## 工作流

1. 保留 APK 或 IPA 原件并记录哈希。
2. 映射元数据与权限，反编译资源与代码。
3. 识别信任边界。
4. 在受控设备或模拟器中观测运行时行为。
5. 关联网络流量，验证假设。
6. 交付证据。

## 检查点纪律

长时间运行前持久化检查点。记录命令、版本、哈希、证据路径、假设与验证结果。经 eni-universal-workflow 串联，以交付收尾。
