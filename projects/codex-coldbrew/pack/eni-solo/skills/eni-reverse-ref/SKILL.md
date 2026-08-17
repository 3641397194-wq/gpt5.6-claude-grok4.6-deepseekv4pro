---
name: eni-reverse-ref
description: "[DOCUMENTATION ONLY] [仅文档] 全局自动路由 | Reference material for reverse engineering compiled, packed, obfuscated, or virtualized targets — native binaries (PE/ELF), APKs, WASM, firmware images, custom VMs and bytecode, malware-style loaders, and anti-debug / anti-analysis defenses — for use when understanding how the target behaves is the precondition for exploiting or solving it. Once the flaw is clear and only exploitation remains, switch to pwn. Not for web-layer work, log/disk forensics, or standalone crypto, unless reversing the implementation itself is what blocks progress."
license: MIT
allowed-tools: Bash Read Write Edit Glob Grep Task WebFetch WebSearch
metadata:
  user-invocable: "false"
---

> 仅文档：本 Skill 提供的是方法论与检查清单，不附带任何可执行脚本。

# 逆向工程（Reverse Engineering）

逆向题目的总入口。专项技术按下面索引进入对应参考文档。

## 环境准备

**Python 包（各平台通用）：**

```bash
pip install frida-tools angr qiling uncompyle6 capstone lief z3-solver
# Python 3.9+ 字节码请从源码编译 pycdc
git clone https://github.com/zrax/pycdc && cd pycdc && cmake . && make
```

**Linux（apt）：**

```bash
apt install gdb radare2 binutils strace ltrace apktool upx
```

**macOS（Homebrew）：**

```bash
brew install gdb radare2 binutils apktool upx ghidra
```

**radare2 插件：**

```bash
r2pm -ci r2ghidra   # 为 radare2 挂载原生 Ghidra 反编译器
```

**手动安装：**

- pwndbg — Linux：[GitHub](https://github.com/pwndbg/pwndbg)；macOS：`brew install pwndbg/tap/pwndbg-gdb`

## 参考文档索引

- [tools.md](tools.md) — 静态分析工具：GDB、Ghidra、radare2、IDA、Binary Ninja、dogbolt.org 多反编译器对比；RISC-V 用 Capstone 反汇编、Unicorn 模拟；Python 字节码、WASM、Android APK、.NET、加壳样本的处置
- [tools-dynamic.md](tools-dynamic.md) — 动态分析工具：Frida（hook、反调试绕过、内存扫描、Android/iOS）、angr 符号执行（路径探索、约束、CFG）、lldb、x64dbg、Qiling 跨平台模拟、Triton 动态符号执行；另含 Intel Pin 指令计数侧信道（对付 movfuscator）、仅 opcode 的执行迹重建、LD_PRELOAD memcmp 逐字节爆破 oracle
- [tools-advanced.md](tools-advanced.md) — 进阶工具：VMProtect/Themida 分析、二进制 diffing（BinDiff、Diaphora）、反混淆框架（D-810、GOOMBA、Miasm）、Rizin/Cutter、RetDec、自定义 VM 字节码提升到 LLVM IR、高级 GDB（Python 脚本、条件断点、watchpoint、rr 反向调试、pwndbg/GEF）、高级 Ghidra 脚本、补丁策略（Binary Ninja API、LIEF）
- [anti-analysis.md](anti-analysis.md) — 反分析全景：Linux 反调试（ptrace、/proc、时间检测、信号、直接系统调用）、Windows 反调试（PEB、NtQueryInformationProcess、堆标志、TLS 回调、硬件/软件断点检测、异常反调试、线程隐藏）、反虚拟机/沙箱（CPUID、MAC、时间、痕迹、资源）、反 DBI（Frida 检测与绕过）、代码完整性自校验、反反汇编（不透明谓词、垃圾字节）、MBA 识别与化简、SIGFPE 信号处理器 + strace 计数侧信道、无 call 的函数链（栈帧操纵）、绕过策略总表
- [patterns.md](patterns.md) — 基础模式：自定义 VM、反调试、nanomites、自修改代码、XOR 密码、混合模式 stager、LLVM 混淆、S-box/密钥流、SECCOMP/BPF、异常处理器、内存转储、逐字节变换、x86-64 陷阱、基于信号的探索、恶意样本反分析绕过、多级 shellcode、时间侧信道、多线程反调试（诱饵 + 信号处理器 MBA）、INT3 补丁 + coredump 爆破 oracle、信号处理器链 + LD_PRELOAD oracle
- [patterns-ctf.md](patterns-ctf.md) — 赛题模式（上）：隐藏模拟器 opcode、LD_PRELOAD 密钥提取、SPN 静态参数提取、图像 XOR 平滑度、逐字节分组密码、数学收敛位图、Windows PE XOR 位图 + OCR、RC4+VM 两级 loader、内核模块走迷宫、多线程 VM 通道、字符串 diff 识别被植入的共享库、自定义 binfmt 内核模块 + RC4 裸二进制、哈希解析导入/无导入勒索软件、ELF 节头损坏反分析
- [patterns-ctf-2.md](patterns-ctf-2.md) — 赛题模式（中）：多层自解密爆破、内嵌 ZIP+XOR 许可证、栈字符串脱混淆、前缀哈希爆破、CVP/LLL 格约束求解、决策树函数混淆、GF(2^8) 高斯消元、ROP 链混淆（ROPfuscation）
- [patterns-ctf-3.md](patterns-ctf-3.md) — 赛题模式（下）：Z3 解单行 Python 布尔电路、滑窗 popcount 差分递推、键盘 LED 摩斯码（ioctl）、C++ 析构函数隐藏校验、系统调用副作用内存破坏、MFC 对话框事件定位、VM 顺序密钥链爆破、Burrows-Wheeler 逆变换、OpenType 连字利用、GLSL 着色器 VM 自修改代码、指令计数器作加密状态、objdump 批量 crackme 自动化、fork+pipe+死分支反分析、TensorFlow DNN 逐层求逆、内核 JIT 导出 BPF 分析
- [languages.md](languages.md) — 语言专项：Python 字节码与 opcode 重映射、按版本区分的字节码、Pyarmor 静态脱壳、DOS stub、鸿蒙 HAP/ABC、Brainfuck 及 esolang（逐字符静态分析、读计数 oracle、比较惯用法检测）、UEFI、转译到 C、代码覆盖率侧信道、OPAL 函数式逆向、非双射替换密码、FRACTRAN 程序求逆
- [languages-platforms.md](languages-platforms.md) — 平台/框架专项：Rust serde_json schema 恢复、Android JNI RegisterNatives 混淆、/proc/self/maps 运行时改 DEX 字节码、新建工程绕过 .so 加载校验、Frida 绕过 Firebase Cloud Functions、Verilog 硬件逆向、逐前缀哈希反转、Ruby/Perl polyglot 约束求解、Electron ASAR 提取 + 原生二进制、Node.js npm 包运行时内省
- [languages-compiled.md](languages-compiled.md) — 编译语言专项：Go（GoReSym、goroutine、内存布局、channel 操作、embed.FS、UUID 补丁枚举 C2）、Rust（demangling、Option/Result、Vec、panic 字符串）、Swift（demangling、协议见证表）、Kotlin/JVM（协程状态机）、Haskell GHC CMM 中间表示、C++（vtable 重建、RTTI、STL 模式）
- [platforms.md](platforms.md) — 平台专项：macOS/iOS（Mach-O、代码签名、Objective-C runtime、Swift、dyld、越狱检测绕过）、嵌入式/IoT 固件（binwalk、UART/JTAG/SPI、ARM/MIPS、RTOS）、内核驱动（Linux .ko、eBPF、Windows .sys）、汽车 CAN 总线
- [platforms-hardware.md](platforms-hardware.md) — 硬件与高级架构：HD44780 LCD 的 GPIO 重建、RISC-V 进阶（自定义扩展、特权级、调试）、ARM64/AArch64 逆向与利用（调用约定、ROP gadget、qemu-aarch64-static 模拟）
- [field-notes.md](field-notes.md) — 快速笔记：二进制类型、反调试绕过、专项模式、赛题案例

---

## 何时切换技能

- 已经读懂二进制、剩下的是堆/ROP/内核利用 → 转 `/ctf-pwn`
- 题目本质是恢复删除文件、PCAP 或磁盘痕迹 → 转 `/ctf-forensics`
- 目标是 Web 应用、只需要逆一个小脚本 → 转 `/ctf-web`
- 二进制里跑的是机器学习模型，考的是模型攻击 → 转 `/ctf-ai-ml`
- 逆出来的核心逻辑是密码学算法 → 转 `/ctf-crypto`
- 样本是真实恶意软件（C2、加壳、对抗行为）→ 转 `/ctf-malware`
- 玩具 VM、编码谜题或 pyjail 而非真实二进制 → 转 `/ctf-misc`

## 解题工作流

1. **先跑 strings**——大量简单题明文藏 flag
2. **再试 ltrace/strace**——动态追踪常能直接看到 flag
3. **试 Frida hook**——挂 strcmp/memcmp 直接拿期望值
4. **试 angr**——符号执行能自动解掉大量 flag checker
5. **试 Qiling**——跨架构模拟、无痕迹绕过反调试
6. **先画控制流**再动手改执行
7. **把手工操作脚本化**（r2pipe、Frida、angr、Python）
8. **交叉验证**——用 dogbolt.org 并排比对多个反编译器输出

## 快速起手（优先尝试）

```bash
# 明文 flag 提取
strings binary | grep -E "flag\{|CTF\{|pico"
strings binary | grep -iE "flag|secret|password"
rabin2 -z binary | grep -i "flag"

# 动态分析——经常直接抓到 flag
ltrace ./binary
strace -f -s 500 ./binary

# 十六进制搜索
xxd binary | grep -i flag

# 带测试输入跑
./binary AAAA
echo "test" | ./binary
```

## 初步侦察

```bash
file binary           # 类型与架构
checksec --file=binary # 安全特性（pwn 前）
chmod +x binary       # 赋执行权限
```

## 内存转储思路

**核心洞察：** 让程序自己算出答案，再把它 dump 出来。在最终比较处断下（`b *main+OFFSET`），输入一个正确长度的任意串，然后 `x/s $rsi` 直接读计算出的 flag。

## 诱饵 flag 识别

**模式：** 真检查前有多个假目标。留意一串连续的比较目标、各自带着不同的成功提示。断点要设在**最后一个**比较，而不是前面的。

## GDB 调试 PIE

PIE 二进制基址随机化。用相对断点：

```bash
gdb ./binary
start                    # 强制解析 PIE 基址
b *main+0xca            # 相对 main 的偏移
run
```

## 比较方向（关键！）

两种模式：(1) `transform(flag) == stored_target`——逆变换即可；(2) `transform(stored_target) == flag`——flag 就是变换结果，直接把存储值代进变换。

## 常见加密模式

- 单字节 XOR——遍历 256 个值
- 已知明文 XOR（`flag{`、`CTF{`）
- RC4 硬编码密钥
- 自定义置换 + XOR
- 带位置索引的 XOR（`^ i` 或 `^ (i & 0xff)`）叠加循环密钥

## 工具速查

```bash
# Radare2
r2 -d ./binary     # 调试模式
aaa                # 分析
afl                # 函数列表
pdf @ main         # 反汇编 main

# Ghidra（headless）
analyzeHeadless project/ tmp -import binary -postScript script.py

# IDA
ida64 binary       # IDA64 打开
```

## 深入笔记

初筛之后用 [field-notes.md](field-notes.md) 做第二轮：

- 目标格式：Python 字节码、WASM、Android、Flutter、.NET、UPX、Tauri
- 技术笔记：反调试绕过、VM 分析、x86-64 陷阱、迭代求解、Unicorn、时间侧信道
- 平台笔记：macOS/iOS、嵌入式固件、内核驱动、Swift、Kotlin、Go、Rust、D
- 案例笔记：现代赛题逆向模式与经典老题模式

---

## 路由上下文

**上游入口**: `skills/SKILL.md`（总控）、`routing.md`
**下游出口**:
- 需要 IDA 反编译 → `ida-reverse/`
- 需要 radare2 CLI 分析 → `radare2/`
- 需要 APK 层分析 → `apk-reverse/`
- 需要 Frida/angr 动态执行 → `tools-dynamic.md`
- 需要绕过反调试 → `anti-analysis.md`
- 遇到特定语言（Go/Rust/Python/WASM）→ `languages*.md`
- 遇到 CTF 模式 → `patterns*.md`

**同级关联模块**: `apk-reverse/`（APK 定位到 .so 时可切回本模块的 Frida/radare2 分支）
