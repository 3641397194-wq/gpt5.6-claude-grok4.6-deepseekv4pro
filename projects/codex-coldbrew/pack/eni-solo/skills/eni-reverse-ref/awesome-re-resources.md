# 逆向工程资源精选

> 从多个 awesome 清单里按实战价值筛出的资源。做逆向时可按需查阅方法论与工具指引。

---

## 综合清单与教程库

| 项目 | Stars | 覆盖 | 链接 |
|------|-------|------|------|
| **awesome-reversing**（tylerha97） | 3k+ | 工具/书籍/课程/练习的一站式清单 | https://github.com/tylerha97/awesome-reversing |
| **awesome-reverse-engineering**（alphaSeclab） | 4k+ | 3500+ 工具 + 2300 篇文章，覆盖各平台 | https://github.com/alphaSeclab/awesome-reverse-engineering |
| **Reverse-Engineering**（mytechnotalent） | 10k+ | 免费教程：x86/x64/ARM/AVR/RISC-V 全系列 | https://github.com/mytechnotalent/Reverse-Engineering |
| **awesome-malware-analysis**（rshipp） | 12k+ | 恶意样本分析工具与资料 | https://github.com/rshipp/awesome-malware-analysis |
| **reversingBits** | — | 逆向/二进制分析速查表合集 | https://github.com/mohitmishra786/reversingBits |
| **awesome-arm-exploitation** | — | ARM 方向的利用资料（视频/文章/书籍） | https://github.com/HenryHoggard/awesome-arm-exploitation |
| **Awesome-Binary-Analysis-Automation** | — | 二进制分析自动化（ML/脚本/静态/动态） | https://github.com/user1342/Awesome-Binary-Analysis-Automation |

---

## ELF / Linux 专项

| 资源 | 说明 | 链接 |
|------|------|------|
| **libelfmaster** | 面向安全的 ELF 解析库（取证/恶意样本重建） | https://github.com/elfmaster/libelfmaster |
| **ELF 规范** | 官方 ELF 格式文档 | https://refspecs.linuxfoundation.org/elf/elf.pdf |
| **Linux Insides** | /proc 文件系统、内存布局、系统调用内部原理 | https://0xax.gitbooks.io/linux-insides/ |
| **Compiler Explorer** | 在线查看 C/C++/Rust/Go 编译后的汇编 | https://godbolt.org/ |

---

## ARM / AArch64 专项

| 资源 | 说明 | 链接 |
|------|------|------|
| **ARM 官方架构手册** | 指令集权威参考 | https://developer.arm.com/documentation |
| **Azeria Labs** | ARM 汇编/利用教程（公认最佳入门） | https://azeria-labs.com/writing-arm-assembly-part-1/ |
| **ARM64 syscall 表** | Linux AArch64 系统调用号速查 | https://arm64.syscall.sh/ |
| **QEMU 用户态模拟** | 无需真机即可分析 ARM 二进制 | `qemu-aarch64 -strace ./binary` |

---

## 恶意样本分析

| 资源 | 说明 | 链接 |
|------|------|------|
| **YARA** | 特征规则匹配引擎 | https://github.com/VirusTotal/yara |
| **Volatility 3** | 内存取证框架 | https://github.com/volatilityfoundation/volatility3 |
| **FLOSS** | 混淆字符串自动提取（Mandiant） | https://github.com/mandiant/flare-floss |
| **Detect It Easy（DiE）** | 文件类型/壳/编译器识别 | https://github.com/horsicq/Detect-It-Easy |
| **PE-bear** | PE 文件结构分析器 | https://github.com/hasherezade/pe-bear |
| **Capa** | 自动识别二进制能力（网络/文件/加密等） | https://github.com/mandiant/capa |
| **UnpackerFramework** | 通用脱壳框架 | https://github.com/malwaretech/UnpackerFramework |

---

## 动态分析与模拟

| 资源 | 说明 | 链接 |
|------|------|------|
| **Frida** | 跨平台动态插桩 | https://frida.re/ |
| **strace** | 系统调用跟踪 | 系统自带 |
| **ltrace** | 库函数调用跟踪 | 系统自带 |
| **QEMU** | 用户态/系统态模拟 | https://www.qemu.org/ |
| **Unicorn** | 可编程 CPU 模拟引擎 | https://www.unicorn-engine.org/ |
| **Qiling** | 带 OS 层的高级二进制模拟 | https://qiling.io/ |
| **angr** | 符号执行 + 二进制分析平台 | https://angr.io/ |
| **Triton** | 动态二进制分析框架 | https://triton-library.github.io/ |

---

## 反混淆 / 脱壳

| 资源 | 说明 | 链接 |
|------|------|------|
| **UPX** | 最常见的壳，`upx -d` 即脱 | https://upx.github.io/ |
| **unipacker** | 通用 PE 脱壳器 | https://github.com/unipacker/unipacker |
| **de4dot** | .NET 反混淆 | https://github.com/de4dot/de4dot |
| **JADX** | Android DEX 反编译 | https://github.com/skylot/jadx |
| **JEB** | 商业 Android/ARM 反编译器 | https://www.pnfsoftware.com/ |
| **Miasm** | 逆向框架（IR/符号执行/反混淆） | https://github.com/cea-sec/miasm |
| **OLLVM 反混淆** | 平坦化/虚假控制流对抗 | 用 angr/Triton 符号执行恢复，见 `references/ollvm-deobfuscation.md` |

---

## 在线分析平台

| 平台 | 说明 | 链接 |
|------|------|------|
| **VirusTotal** | 多引擎扫描 + 行为分析 | https://www.virustotal.com/ |
| **Joe Sandbox** | 自动化恶意样本分析 | https://www.joesandbox.com/ |
| **ANY.RUN** | 交互式在线沙箱 | https://any.run/ |
| **Hybrid Analysis** | 免费恶意样本分析 | https://www.hybrid-analysis.com/ |
| **Compiler Explorer** | 查看编译器输出 | https://godbolt.org/ |
| **Dogbolt** | 多反编译器结果并排（IDA/Ghidra/Binary Ninja） | https://dogbolt.org/ |

---

## 学习路径

### 入门（0–3 个月）

1. [Reverse Engineering for Beginners](https://beginners.re/) — 免费电子书
2. [Azeria Labs ARM 教程](https://azeria-labs.com/) — ARM 汇编基础
3. [Nightmare](https://guyinatuxedo.github.io/) — CTF 逆向/Pwn 教程
4. [crackmes.one](https://crackmes.one/) — 逆向练习题

### 进阶（3–12 个月）

1. [Practical Binary Analysis](https://practicalbinaryanalysis.com/) — 实战二进制分析
2. [The IDA Pro Book](https://nostarch.com/idapro2.htm) — IDA 深度使用
3. [Malware Unicorn RE101](https://malwareunicorn.org/workshops/re101.html) — 恶意样本逆向
4. [pwnable.kr](http://pwnable.kr/) / [pwnable.tw](https://pwnable.tw/) — Pwn 练习

### 高级

1. [Modern Binary Exploitation](https://github.com/RPISEC/MBE) — RPI 课程
2. [How to Hack Like a Ghost](https://nostarch.com/how-hack-ghost) — 高级渗透视角
3. [Windows Internals](https://docs.microsoft.com/en-us/sysinternals/) — Windows 内核
4. 实战：分析真实恶意样本（MalwareBazaar）

---

## 速查表

| 速查表 | 链接 |
|--------|------|
| x86/x64 指令速查 | https://www.felixcloutier.com/x86/ |
| ARM64 指令速查 | https://developer.arm.com/documentation/ddi0602/latest |
| Linux syscall 表（x64） | https://blog.rchapman.org/posts/Linux_System_Call_Table_for_x86_64/ |
| Linux syscall 表（ARM64） | https://arm64.syscall.sh/ |
| GDB 速查 | https://darkdust.net/files/GDB%20Cheat%20Sheet.pdf |
| radare2 速查 | 本包 `radare2/references/cheatsheet.md` |
| IDA 快捷键 | https://hex-rays.com/products/ida/support/freefiles/IDA_Pro_Shortcuts.pdf |
| Ghidra 快捷键 | Ghidra 内置 Help → Keyboard Shortcuts |
