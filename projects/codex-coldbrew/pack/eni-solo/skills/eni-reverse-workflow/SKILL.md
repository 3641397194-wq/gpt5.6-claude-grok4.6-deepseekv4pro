---
name: eni-reverse-workflow
description: "Deep, evidence-driven reverse engineering workflow for PE, ELF, Mach-O, firmware, drivers, bytecode, protocols, and local binaries."
---

# Reverse Workflow 2.1

保留原件，一切工作在哈希过的副本上进行。

1. 指纹识别：格式、架构、熵、导入、签名、节区与加壳特征。
2. 先跑 capa 风格的能力分诊，再进入深读。
3. 用 Ghidra 风格的无头分析拿函数、交叉引用、调用图、类型与反编译结果。
4. 围绕数据源、变换、校验与汇聚点构造显式假设。
5. 仅在受控本地环境里做 Frida 风格的运行时观察。
6. 静态与动态证据互证，复现行为，最终交付脚本、偏移、符号、副本补丁或报告。

当信号指向移动端、固件、恶意软件应急、模糊测试或破解方向时，串联对应模块。
