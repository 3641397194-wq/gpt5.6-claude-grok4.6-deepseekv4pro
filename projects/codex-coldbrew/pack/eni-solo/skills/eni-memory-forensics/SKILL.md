---
name: eni-memory-forensics
description: 全局自动路由 | Cross-platform memory forensics: process memory, dumps, heap, pointer chains, signatures, and structure recovery for Windows, Linux, Android, Unity IL2CPP, Unreal, native apps, crash dumps, and raw memory images.
---

# 内存取证分析

以证据为起点解析运行时地址与数据结构，再沉淀为可重复使用的工具代码。

## 开始前

1. 先确认架构、指针宽度、字节序、目标 OS/运行时与工件类型。
2. 区分几类地址形态：绝对地址、模块相对偏移、签名、指针链、句柄与生成式引用。
3. 记录模块映射、页面保护属性、线程/堆上下文与地址来源。
4. 通配字节模式扫描用 `scripts/aob_scan.py`，带偏移的 ASCII/UTF-16 字符串提取用 `scripts/dump_strings.py`。

## 参考选择

- Windows 活动进程、转储、WinDbg、RPM/WPM：读 `references/windows.md`。
- Linux、Android、Frida、IL2CPP：读 `references/linux-android.md`。
- 原始转储、结构体、指针链、内存取证：读 `references/dump-structures.md`。

## 执行准则

- 优先用模块解析、签名和经过验证的指针路径，而不是硬编码绝对地址。
- 用受控状态变更、内存 diff、watchpoint、分配 hook 与访问宽度模式来还原结构体。
- 访问前先验证区域可读/可写并检查边界。
- 做 patch 时：先抓原始字节，校验预期字节，恢复保护属性，并提供回滚方案。

## 交付物

返回地址推导过程、映射证据、还原出的结构体、完整的 reader/scanner/hook/patch 代码、错误处理、日志与验证步骤。
