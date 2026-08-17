---
name: eni-reverse-deep
description: 全局自动路由 | 面向 PE、ELF、Mach-O、固件、驱动、APK/DEX、.NET、Go、Rust、Unity IL2CPP、Unreal、加壳二进制、自定义 VM 与未公开协议的深度逆向工程。当 Codex 收到二进制、反汇编、伪代码、崩溃、原生库、游戏工件、固件镜像、混淆应用，或需要 IDA/Ghidra/Frida/angr/Unicorn 自动化、算法恢复、脱壳、补丁或协议重建时使用。
---

# Cold Coffee Reverse Deep

从工件推进到经过验证的恢复行为。

## 启动步骤

1. 用 `scripts/triage_binary.py` 做哈希与分诊。
2. 保留原始文件；衍生文件放进独立工作目录。
3. 识别格式、架构、编译器/运行时线索、保护、导入、字符串与可能的入口路径。
4. 边分析边建立地址/函数/结构地图。

## 参考资料选择

- 原生 PE/ELF/Mach-O、驱动、固件：读 `references/native-workflow.md`。
- .NET、Java/Android、Go/Rust、Unity/Unreal：读 `references/managed-game.md`。
- 壳、反调试、虚拟化、控制流混淆：读 `references/unpacking-obfuscation.md`。
- 网络消息或二进制格式：读 `references/protocol-reverse.md`。

## 执行

- 静态反编译与调试器跟踪、watchpoint、hook、转储与受控输入变更相结合。
- 恢复调用约定、结构体、vtable、状态机、封包布局与数据变换。
- 优先用脚本做可重复提取：IDAPython、Ghidra、r2pipe、Frida、angr/Z3、Unicorn、解析器、扫描器与补丁器。
- 恢复出的算法要用原始样本回归验证。

## 交付

返回工件哈希、目标画像、关键地址/函数、恢复出的数据结构、确认的行为、脚本、调试器命令与验证结果。区分"已确认的观察"与"假设"。
