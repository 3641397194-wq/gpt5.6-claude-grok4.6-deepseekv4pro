# 逆向实战速查笔记

> 支撑 [SKILL.md](SKILL.md) 的细则笔记。初筛之后读，不是之前。

## 目录

- [二进制类型速查](#二进制类型速查)
- [反调试绕过](#反调试绕过)
- [专项模式](#专项模式)
- [赛题案例笔记](#赛题案例笔记)
- [Web/CTF 鉴权绕过案例](#webctf-鉴权绕过案例)
- [网络钓鱼基础设施案例](#网络钓鱼基础设施案例)
- [分析前预判：文件伪装与名字欺骗](#分析前预判文件伪装与名字欺骗)

---

## 二进制类型速查

### Python .pyc

用 `marshal.load()` + `dis.dis()` 反汇编。头部分别为 8 字节（2.x）、12（3.0-3.6）、16（3.7+）。详见 [languages.md](languages.md)。

### WASM

```bash
wasm2c checker.wasm -o checker.c
gcc -O3 checker.c wasm-rt-impl.c -o checker

# WASM 补丁（赛题二进制）：
wasm2wat main.wasm -o main.wat    # 二进制 → 文本
# 编辑 WAT：翻转比较、改常量
wat2wasm main.wat -o patched.wasm # 文本 → 二进制
```

### Android APK

`apktool d app.apk -o decoded/` 解资源；`jadx app.apk` 反编译 Java。查 `decoded/res/values/strings.xml` 找 flag。详见 [tools.md](tools.md)。

### Flutter APK（Dart AOT）

若存在 `lib/arm64-v8a/libapp.so` + `libflutter.so`，用 [Blutter](https://github.com/worawit/blutter)：`python3 blutter.py path/to/app/lib/arm64-v8a out_dir`。输出重建的 Dart 符号 + Frida 脚本。详见 [tools.md](tools.md)。

### .NET

- dnSpy — 调试 + 反编译
- ILSpy — 反编译器

### 加壳（UPX）

```bash
upx -d packed -o unpacked
```

脱壳失败时先查 UPX 元数据：核对 UPX 节名、头部字段、版本标记是否完好。若元数据可疑，对照 GitHub 上的 UPX 源码定位可能被改动的位置。

### Tauri 打包桌面应用

Tauri 把 Brotli 压缩的前端资源嵌进可执行文件。找 `index.html` 的交叉引用定位资源索引表，dump 数据块，Brotli 解压。参考：`tauri-codegen/src/embedded_assets.rs`。

---

## 反调试绕过

常见检查：

- `IsDebuggerPresent()` / PEB.BeingDebugged / NtQueryInformationProcess（Windows）
- `ptrace(PTRACE_TRACEME)` / `/proc/self/status` TracerPid（Linux）
- TLS 回调（先于 main 执行——查 PE TLS Directory）
- 时间检查（`rdtsc`、`clock_gettime`、`GetTickCount`）
- 硬件断点检测（GetThreadContext 读 DR0-DR3）
- INT3 扫描 / 代码自哈希（.text 段 CRC）
- 信号类：SIGTRAP 处理器、SIGALRM 超时、SIGSEGV 藏真实逻辑
- Frida/DBI 检测：`/proc/self/maps` 扫描、端口 27042、inline hook 检查

绕过：在检查点断下，改寄存器跳过条件分支。pwntools patch：`elf.asm(elf.symbols.ptrace, 'ret')` 把函数换成立即返回。详见 [patterns.md](patterns.md)。

30+ 种手法与代码级绕过全集见 [anti-analysis.md](anti-analysis.md)。

---

## 专项模式

### S-Box / 密钥流模式

**Xorshift32：** 移位 13、17、5
**Xorshift64：** 移位 12、25、27
**魔法常量：** `0x2545f4914f6cdd1d`、`0x9e3779b97f4a7c15`

### 自定义 VM 分析

1. 识别结构：寄存器、内存、IP
2. 逆向 `executeIns` 弄清 opcode 含义
3. 写反汇编器把 opcode 映射成助记符
4. 很多时候爆破比完全逆向省事
5. 找通过命令行参数加载的字节码文件

VM 工作流、opcode 表与状态机 BFS 见 [patterns.md](patterns.md)。

**顺序密钥链爆破：** VM 按小块校验输入（如 3 字节 = 2^24 候选）、每块输出密钥喂给下一块时，用 OpenMP 并行逐块爆破。`gcc -O3 -march=native -fopenmp` 编译求解器。详见 [patterns-ctf-3.md](patterns-ctf-3.md)。

### Python 字节码逆向

奇偶索引交错表 XOR flag checker 很常见。分析技巧与逆向模式见 [languages.md](languages.md)。

### 基于信号的二进制探索

二进制用 UNIX 信号作二叉树导航；`LD_PRELOAD` hook `sigaction`，发信号做 DFS。详见 [patterns.md](patterns.md)。

### 恶意样本反分析绕过（patch 法）

翻转 `JNZ`/`JZ`（0x75/0x74）、改 sleep 值、在 Ghidra 里 patch 环境检查（`Ctrl+Shift+G`）。详见 [patterns.md](patterns.md)。

### 期望值表定位

`objdump -s -j .rodata binary | less` —— 找比较指令附近、大小匹配 flag 长度的数据。

### x86-64 陷阱

符号扩展与 32 位截断的坑。细节与代码示例见 [patterns.md](patterns.md)。

### 迭代求解模式

逐位置试 0-255 字节，与期望输出比对。**均匀变换捷径：** 若单输入字节只影响单输出字节，建 0..255 映射表再取逆。完整实现见 [patterns.md](patterns.md)。

### Unicorn 模拟（复杂状态）

`from unicorn import *` —— 映射段、搭栈、hook 追踪。**混合模式坑：** 64 位 stub 经 `retf` 跳进 32 位时，要切 UC_MODE_32 并拷贝 GPR + EFLAGS + XMM。详见 [tools.md](tools.md)。

### 多级 shellcode loader

嵌套 shellcode 带 XOR 解码循环；断在 `call rax`，`set $rax=0` 绕 ptrace，从 `mov` 指令抽 flag。详见 [patterns.md](patterns.md)。

### 时间侧信道攻击

校验耗时随正确字符变长；逐候选计时恢复 flag。详见 [patterns.md](patterns.md)。

### 未 strip 二进制的信息泄露

**模式：** 调试信息与文件路径泄露作者身份。快速检查：`strings binary | grep "/home/"`（家目录）、`file binary`（是否 strip）、`readelf -S binary | grep debug`（调试节）。

### 自定义混淆函数逆向

二进制按 2 字节一组、带运行态混淆输入；从 `.rodata` 取目标值，写逆函数。详见 [patterns.md](patterns.md)。

### Rust serde_json Schema 恢复

反汇编 serde 的 `Visitor` 实现恢复期望的 JSON schema；字段名顺序即 flag。详见 [languages-platforms.md](languages-platforms.md)。

### 位置相关变换逆向

二进制按位置索引加减；逐位撤销偏移即可。详见 [patterns.md](patterns.md)。

### Hex 编码字符串比较

输入被转 hex 再与常量比较。`xxd -r -p` 解码。详见 [patterns.md](patterns.md)。

---

## 赛题案例笔记

### 内嵌 ZIP + XOR 许可证解密

二进制带命名符号（`EMBEDDED_ZIP`、`ENCRYPTED_MESSAGE`，在 `.rodata`）→ 取出 ZIP 内的许可证，密文与许可证字节 XOR 得 flag。无需运行。详见 [patterns-ctf-2.md](patterns-ctf-2.md)。

### 栈字符串脱混淆（.rodata XOR Blob）

二进制 mmap `.rodata` 数据块，XOR 脱混淆后用于校验输入。用 pyelftools 提取数据块重实现校验循环。留意 `0x9E3779B9`、`0x85EBCA6B` 常量与 `rol32()`。详见 [patterns-ctf-2.md](patterns-ctf-2.md)。

### 前缀哈希爆破

二进制对每个前缀独立做哈希。逐字符匹配前缀哈希恢复输入。详见 [patterns-ctf-2.md](patterns-ctf-2.md)。

### 数学收敛位图

**模式：** 二进制用牛顿法收敛性（如 z^3-1=0）分类坐标对。通过/失败栅格渲染成 ASCII art flag。要点：二进制是分类器不是 checker——逆数学、可视化。详见 [patterns-ctf.md](patterns-ctf.md)。

### RISC-V 二进制分析

静态链接、strip 的 RISC-V ELF。Capstone 用 `CS_MODE_RISCVC | CS_MODE_RISCV64` 处理混合压缩指令。`qemu-riscv64` 模拟。留意假 flag 与增量密钥 XOR 解密。详见 [tools.md](tools.md)。

### 内核模块走迷宫

Rust 内核模块通过设备 ioctl 实现迷宫。动态枚举命令，写带诱饵规避的 DFS 求解器，部署成最小静态二进制（裸系统调用、无 libc）。详见 [patterns-ctf.md](patterns-ctf.md)。

### 多线程 VM 与通道

16+ 线程经 futex 通道通信的自定义 VM。跨线程边界追数据流，GDB 取常量，留意反转的有效性逻辑，BFS 状态空间求解。详见 [patterns-ctf.md](patterns-ctf.md)。

### CVP/LLL 格约束整数校验

二进制用 64 位系数矩阵乘法校验 flag，解必须是可打印 ASCII。SageMath 里 LLL 规约 + CVP 找约束区间内的最近格点。两阶段模式：阶段一恢复 AES 密钥，阶段二用另一线性系统（mod 2^32）解密自定义 VM 字节码。详见 [patterns-ctf-2.md](patterns-ctf-2.md)。

### 决策树函数混淆

约 200+ 自动生成的函数把输入路由进多项式比较。用 Ghidra headless 脚本化提取，而不是手工逐个逆。从已知输出格式出发做约束传播。详见 [patterns-ctf-2.md](patterns-ctf-2.md)。

### Android JNI RegisterNatives 混淆

`JNI_OnLoad` 里的 `RegisterNatives` 隐藏了 Java native 方法与 C++ 函数的对应关系（没有标准的 `Java_com_pkg_Class_method` 符号）。沿 `JNI_OnLoad` → `RegisterNatives` → `fnPtr` 找真实处理函数。用 APK 里的 x86_64 `.so` 获得最佳 Ghidra 反编译效果。详见 [languages-platforms.md](languages-platforms.md)。

### 多层自解密二进制

N 层二进制，每层用用户提供的密钥字节 + SHA-NI 解密下一层。用 oracle（正确密钥 → 符合预期模式的合法代码）。fork-per-candidate COW 隔离做 JIT 执行提速。详见 [patterns-ctf-2.md](patterns-ctf-2.md)。

### GLSL 着色器 VM 与自修改代码

**模式：** WebGL2 片段着色器在 256x256 RGBA 纹理上实现图灵完备 VM（程序内存 + 显存）。自修改代码（STORE opcode）patch 绘制指令。GPU 并行导致写冲突——用 Python 顺序模拟恢复完整输出。详见 [patterns-ctf-3.md](patterns-ctf-3.md)。

### GF(2^8) 高斯消元恢复 flag

**模式：** 二进制用 AES 多项式（0x11b）在 GF(2^8) 上做高斯消元。矩阵与增广向量在 `.rodata`；解向量即 flag。反汇编里找常量 `0x1b`。加法是 XOR，乘法带多项式归约。详见 [patterns-ctf-2.md](patterns-ctf-2.md)。

### Z3 解单行 Python 布尔电路

**模式：** 2000+ 分号的单行 Python，用海象运算符链把 flag 当大端整数经布尔电路校验。混淆 XOR `(a | b) & ~(a & b)`。按分号拆分，翻译成 Z3 符号约束，一秒内求解。详见 [patterns-ctf-3.md](patterns-ctf-3.md)。

### 滑窗 popcount 差分递推

**模式：** 二进制按 16 位滑窗的期望 popcount 校验输入。popcount 差分形成递推：`bit[i+16] = bit[i] + (data[i+1] - data[i])`。爆破约 4000-8000 个合法初始 16 位窗口，每个窗口决定整个比特序列。详见 [patterns-ctf-3.md](patterns-ctf-3.md)。

### Ruby/Perl polyglot 约束求解

**模式：** 单个文件同时合法于 Ruby 与 Perl，两种语言各对密钥施加不同约束。利用 `=begin`/`=end`（Ruby 块注释）与 `=begin`/`=cut`（Perl POD）在不同解释器里跑不同代码。两套约束求交恢复唯一密钥。详见 [languages-platforms.md](languages-platforms.md)。

### Verilog/硬件逆向

**模式：** 状态机的 Verilog HDL 源码，隐藏条件门控在移位寄存器历史。分析 `always @(posedge clk)` 块与 `case` 语句找正确输入序列。详见 [languages-platforms.md](languages-platforms.md)。

### 自定义 binfmt 内核模块 + RC4 裸二进制

**模式：** 内核模块为加密的扁平二进制注册 binfmt 处理器。逆 `.ko` 找 RC4 密钥（在 `movabs` 立即数里），解密裸二进制，按模块 `vm_mmap` 调用的固定虚拟地址导入。详见 [patterns-ctf.md](patterns-ctf.md)。

### 哈希解析导入 / 无导入勒索软件

**模式：** 零可见导入的二进制在运行时用符号名哈希解析 API。跳过哈希逆向——在 Docker 里用 `LD_PRELOAD` hook OpenSSL 函数直接抓 AES 密钥。详见 [patterns-ctf.md](patterns-ctf.md)。

### ELF 节头损坏反分析

**模式：** 故意损坏的节头表让分析工具崩溃，但程序头完好所以照常运行。把 `e_shoff` patch 成 0 或只用 `readelf -l`。flag 藏在损坏节之后，带魔法标记 + XOR。详见 [patterns-ctf.md](patterns-ctf.md)。

### Brainfuck 逐字符静态分析

**模式：** 校验输入的 BF 程序有可识别结构：`,`（读字符）后跟 `+` 序列，其数量 = 期望 ASCII 值。逐输入位置提取增量计数，无需执行即恢复期望输入。详见 [languages.md](languages.md)。

### Brainfuck 读计数 oracle 侧信道

**模式：** BF 输入校验器在字符正确时读更多字节。统计每个候选的 `,` 操作次数——读得最多的字符是对的。逐字符恢复。详见 [languages.md](languages.md)。

### Brainfuck 比较惯用法检测

**模式：** 编译出的 BF 用固定惯用法做相等检查（`<[-<->] +<[>-<[-]]>[-<+>]`）。插桩解释器检测该模式，直接从纸带提取比较操作数（期望 flag 字节）。详见 [languages.md](languages.md)。

### 被植入共享库的检测

二进制在 GDB 里正常、正常跑就失败（suid）？`ldd` 查非标准 libc 路径，然后 `strings | diff` 对比可疑库与系统库，找注入的代码/密码。详见 [patterns-ctf.md](patterns-ctf.md)。

### Go 二进制逆向

带 `go.buildid` 的大静态二进制？用 GoReSym 恢复函数名（strip 后也有效）。Go 字符串是 `{ptr, len}` 对——不是 null 结尾。找 `main.main`、`runtime.gopanic`、channel 操作（`runtime.chansend1`/`chanrecv1`）。Ghidra 配 golang-loader 插件效果最佳。详见 [languages-compiled.md](languages-compiled.md)。

### Go 二进制 UUID 补丁枚举 C2

**模式：** 经 `-ldflags -X` 嵌入 UUID 的 Go C2 客户端。二进制补丁 UUID（等长替换），注册到 C2，经 API 枚举客户端/文件。详见 [languages-compiled.md](languages-compiled.md)。

### D 语言二进制逆向

D 语言符号混淆独树一帜（非 C++ 风格）。模板繁重、函数变体多。符号里找 `_D` 前缀。详见 [languages-compiled.md](languages-compiled.md)。

### Rust 二进制逆向

带 `core::panicking` 字符串与 `_ZN` 混淆符号？用 `rustfilt` demangle。panic 消息含源码路径与行号——`strings binary | grep "panicked"` 是最快入口。Option/Result 枚举用判别字节（0=None/Err，1=Some/Ok）。详见 [languages-compiled.md](languages-compiled.md)。

### Frida 动态插桩

不改二进制直接 hook 运行时函数。`frida -f ./binary -l hook.js` 启动即插桩。hook `strcmp`/`memcmp` 抓期望值、替换 `ptrace` 返回值绕反调试、扫内存找 flag 模式、替换校验函数。详见 [tools-dynamic.md](tools-dynamic.md)。

### Frida 绕过 Firebase Cloud Functions

**模式：** Android 应用经 Firebase Cloud Functions 校验操作。登录后 Frida hook 构造合法载荷（UID + 值 + 时间戳）直接调 Cloud Function，绕过 QR/支付校验。详见 [languages-platforms.md](languages-platforms.md)。

### angr 符号执行

自动路径探索找满足约束的输入。`angr.Project` 加载，设 find/avoid 地址，`simgr.explore()`。约束输入为可打印 ASCII + 已知前缀加速求解。hook 昂贵函数（加密、I/O）防路径爆炸。详见 [tools-dynamic.md](tools-dynamic.md)。

### Qiling 模拟

带 OS 层支持（系统调用、文件系统）的跨平台模拟。任何主机上模拟 Linux/Windows/ARM/MIPS。零调试器痕迹——默认绕过全部反调试。Python API hook 系统调用与地址。详见 [tools-dynamic.md](tools-dynamic.md)。

### VMProtect / Themida 分析

VMProtect 把代码虚拟化成自定义字节码。识别 VM 入口（pushad 式）、找 handler 表（大间接跳转）、动态追踪 handler。CTF 里聚焦追踪输入上的操作即可，不必完整反虚拟化。Themida：ScyllaHide + Scylla 在 OEP dump。详见 [tools-advanced.md](tools-advanced.md)。

### 二进制 diffing

BinDiff 与 Diaphora 对比两个二进制突出差异。题目给 patched/original 双版本时必备。从 IDA/Ghidra 导出再 diff，找漏洞或隐藏功能。详见 [tools-advanced.md](tools-advanced.md)。

### 高级 GDB（pwndbg、rr）

pwndbg：`context`、`vmmap`、`search -s "flag{"`、`telescope $rsp`。GEF 是替代品。`rr record`/`rr replay` 反向调试——倒着走执行。Python 脚本做爆破与自动追踪。详见 [tools-advanced.md](tools-advanced.md)。

### macOS / iOS 逆向

Mach-O：`otool -l` 看 load commands，`class-dump` 出 Objective-C 头。Swift：`swift demangle` 解符号。iOS 应用：frida-ios-dump 解 FairPlay DRM，Frida hook 绕越狱检测。`codesign -f -s -` 重签补丁二进制。详见 [platforms.md](platforms.md)。

### 嵌入式 / IoT 固件逆向

`binwalk -Me firmware.bin` 递归提取。硬件：UART/JTAG/SPI flash 取固件。文件系统：SquashFS（`unsquashfs`）、JFFS2、UBI。QEMU 模拟：`qemu-arm -L /usr/arm-linux-gnueabihf/ ./binary`。详见 [platforms.md](platforms.md)。

### 内核驱动逆向

Linux `.ko`：经 `file_operations` 结构找 ioctl handler，追 `copy_from_user`/`copy_to_user`。QEMU+GDB（`-s -S`）调试。eBPF：`bpftool prog dump xlated`。Windows `.sys`：找 `DriverEntry` → `IoCreateDevice` → IRP handler。详见 [platforms.md](platforms.md)。

### Swift / Kotlin 二进制逆向

Swift：`swift demangle` 解符号、协议见证表做分发、`__swift5_*` 节。Kotlin/JVM：协程编译成 `invokeSuspend` 状态机，jadx 开 Kotlin 模式反编译最佳。Kotlin/Native：LLVM 后端，反汇编像 C++。详见 [languages-compiled.md](languages-compiled.md)。

### INT3 补丁 + coredump 爆破 oracle

在变换输出后 patch 一个 `0xCC`（INT3），开 core dump，逐字符爆破——每次运行后从 coredump 用 `strings` 提取计算状态。免去完整逆向变换。详见 [patterns.md](patterns.md)。

### 信号处理器链 + LD_PRELOAD oracle

二进制用信号处理器链逐字符校验密码。LD_PRELOAD hook `signal()`——安装下一个处理器的调用即确认当前字符正确。详见 [patterns.md](patterns.md)。

### 字体连字利用

自定义 OpenType 字体把多字符连字序列映射到单字形；逆 GSUB 表解码隐藏信息。详见 [patterns-ctf-3.md](patterns-ctf-3.md)。

### 指令计数器作加密状态

**模式：** 手写汇编用专用寄存器（如 `r12`）作指令计数器，几乎每条指令后自增。计数器喂进 XOR/ROL/乘法变换输入字节，使变换路径相关。Unicorn 逐字节爆破恢复 flag。详见 [patterns-ctf-3.md](patterns-ctf-3.md)。

### Burrows-Wheeler 逆变换

无终结字符时靠尝试所有行索引做 BWT 求逆。标准 `bwtool` 或手动列排序重建。详见 [patterns-ctf-3.md](patterns-ctf-3.md)。

### FRACTRAN 程序求逆

迭代分数乘法的 esolang。交换分数表分子分母、把输出倒着跑。I/O 编码为素因子分解指数。详见 [languages.md](languages.md)。

### 仅 opcode 的执行迹重建

只有 opcode（无数据）的执行迹仍经分支决策泄露信息。排序算法的比较暴露元素顺序。按地址排序去重、切基本块重建。详见 [tools-dynamic.md](tools-dynamic.md)。

### 线程竞态 + 有符号整数溢出

战斗模拟二进制有线程不安全的技能锁。技能选择与伤害计算竞态；`cdqe` 把 0xFFFFFFFF 符号扩展成 -1（有符号），减法导致 HP 溢出。详见 [patterns-ctf-3.md](patterns-ctf-3.md)。

### ESP32/Xtensa 固件逆向

IDA 不支持——用 radare2 + ESP-IDF ROM 链接脚本（`esp32.rom.ld`）解符号。对照公开的 ESP-IDF HTTP server 示例定位应用逻辑。详见 [patterns-ctf-3.md](patterns-ctf-3.md)。

### 自定义 VM 字节码提升到 LLVM IR

把自定义 VM 字节码转译成 LLVM IR，`opt -O3` 化简（内联、常量折叠、死代码消除）。1300 行降到约 150 行，暴露底层算法。详见 [tools-advanced.md](tools-advanced.md)。

### SIGFPE 信号处理器侧信道

SIGFPE 处理器制造静态分析不可见的隐式控制流。逐候选字符用 `strace -e signal=SIGFPE` 计数——正确字符产生更多信号。详见 [anti-analysis.md](anti-analysis.md)。

### objdump 批量 crackme 自动化

结构一致的成批 crackme（数百个）：脚本化 `objdump` 提取 CMP 立即数与 add/sub 算术序列，代数反推密钥，无需执行。详见 [patterns-ctf-3.md](patterns-ctf-3.md)。

### Android DEX 运行时字节码补丁

原生 JNI 库经 `/proc/self/maps` + `mprotect` + XOR 在内存中 patch Dalvik 字节码。光静态分析 APK 不够——从原生 `.so` 提取 XOR 密钥与偏移重建运行时 DEX。详见 [languages-platforms.md](languages-platforms.md)。

### fork + pipe + 死分支反分析

fork/pipe IPC：父进程写数据后退出，子进程读管道继续。真实校验藏在死分支（恒假比较）里。`strace` 揭示 fork/pipe 模式；patch 比较常量到达隐藏代码。详见 [patterns-ctf-3.md](patterns-ctf-3.md)。

---

## Web/CTF 鉴权绕过案例

### 签名 Cookie 密钥复用：access token 变 admin_session

**案例：** `class.pangbaoba.me` CTF 作业系统。公开的 `/access/<token>` 路由下发签名 `student_gate`；同一个 access token 同时充当 `admin_session` 的 HMAC 密钥，伪造正确形状的会话载荷即可直达管理员 API。

**核心模式：** 可见的邀请/访问令牌被复用为服务端签名密钥。若一个签名 cookie 能离线验证，就试试兄弟鉴权 cookie 是否共用同一签名方案与密钥。

**处置工作流：**

1. 从受控入口路由抓 `Set-Cookie`，尤其关注 `<base64url-json>.<base64url-signature>` 形状的 cookie。
2. 解第一段；识别紧凑 JSON 载荷，如 `{"access":"student"}`。
3. 用可见路由令牌、邀请码、重置令牌或前端常量作候选密钥，重算 `HMAC-SHA256(payload_b64, candidate_key)`。
4. 签名吻合后，枚举的是**载荷形状**而非密码：在正确的 cookie 名（`admin_session`、`session`、`auth` 等）上尝试可能的授权声明。
5. 先用只读端点验证（`/api/admin/me`、settings/status/list 路由），再做写操作。

**重要教训：** 第一个显眼的载荷可能不对。本例中 `{"access":"admin"}`、`{"role":"admin"}`、`{"access":"student","isAdmin":true}` 全部失败，后端实际检查的是：

```json
{"admin":true}
```

**最小 PoC 形状：**

```python
import base64, hashlib, hmac, json

def b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")

access_token = "<token from /access/<token>>"
payload_b64 = b64u(json.dumps({"admin": True}, separators=(",", ":")).encode())
sig_b64 = b64u(hmac.new(access_token.encode(), payload_b64.encode(), hashlib.sha256).digest())
print(f"admin_session={payload_b64}.{sig_b64}")
```

**验证信号：**

- `GET /api/admin/me` 从 `401 {"error":"unauthorized"}` 变为 `200 {"admin":true}`。
- 伪造 cookie 下其他只读管理员端点返回真实数据。
- `admin_session=j:{}` 这类 JSON-cookie 值引发 `500`，说明 Express/cookie-parser 存在类型混淆，佐证脆弱的 cookie 解析；这不是绕过必需项，但有助于识别技术栈与解析假设。

**避免事项：** 能看到签名 cookie 结构时，别去爆破管理员密码或枚举无关用户 ID。离线处理签名，用低频只读端点验证。

**修复建议：** 绝不拿公开路由/访问令牌当 HMAC 密钥。签名密钥只存服务端、学生与管理员的密钥分离、管理员身份用服务端会话、严格 cookie 类型检查、解析/验证失败返回 `401` 而非 `500`。

---

## 网络钓鱼基础设施案例

### 钓鱼面板：{target_domain_a} / {target_domain_b}

**完整分析**: [phishing-case-study.md](phishing-case-study.md)

冒充政府机构的两服务器钓鱼基础设施。具备受害者全流程控制与服务器驱动的状态码重定向。

**架构：**

- `{target_domain_a}` — 展示层（钓鱼页面、JS 轮询客户端）
- `{target_domain_b}` — 数据层（PHP+MySQL 后端、管理面板）
- 两者均在 NAT 后（内网 {internal_ip}）、nginx、仅 SSL
- Web 根：`/www/wwwroot/{target_domain_b}/`

**受害者流程：** 落地页（虚假补贴额度）→ 1.html（身份证/银行卡表单 → `submit.php`）→ 4.html（PIN → `get-ayment.php`）→ 经 1 秒 `status_check.php` 轮询的服务器控制分阶段页面（9-16）。

**关键发现：**

- 管理面板在 `register.php` → `qichuang.php`（登录表单）、`list.php`（仪表盘模板）
- PHP session（`PHPSESSID`）鉴权；`login.php` 与 `check_login_ajax.php` 已被移除（404）
- **数据泄露**：`db.php` 无需鉴权返回受害者名单（49+ 条记录，**无银行详情**——仅 id/用户名/备注/描述字段）
- **无鉴权写入**：`save_note.php` 接受未认证数据
- `backend.php` 的 SQL 报错暗示管理员注册端点（已坏）
- `submit.php` 有速率限制（多因素），未发现 SQLi 或会话绕过
- 状态码系统：管理员设 1-16，受害者浏览器自动跳转到 `N.html`

**基础设施：**

| 域名 | 公网 IP | 角色 |
|--------|-----------|------|
| {target_domain_1} | {target_ip_1} | 后端 + 管理 |
| {target_domain_2} | {target_ip_2} | 前端（钓鱼页面） |

---

## 分析前预判：文件伪装与名字欺骗

### 文件后缀不可信

**核心原则：永远用 `file` 命令或 magic bytes 判断文件类型，不要相信后缀名。**

常见伪装手法：

| 伪装后缀 | 实际类型 | 目的 |
|---------|---------|------|
| `.sh` | ELF 二进制 | 让人以为是脚本，降低警惕 |
| `.txt` | PE/ELF | 绕过简单的文件类型过滤 |
| `.jpg`/`.png` | 可执行文件或压缩包 | 隐藏在图片中 |
| `.dll` | 实际是 .NET assembly | 混淆分析方向 |
| `.so` | 实际是加密 payload | 需要先解密 |
| 无后缀 | 任何类型 | Linux 下常见 |

```bash
# 正确做法：用 file 命令
file suspicious_file.sh
# 输出: ELF 64-bit LSB executable, ARM aarch64...

# 用 xxd 看 magic bytes
xxd suspicious_file.sh | head -1
# 7f454c46 = ELF magic
```

### 文件名不可信

**"DriverLoader" 不一定加载驱动，"Updater" 不一定更新。**

常见名字欺骗：

| 文件名暗示 | 实际行为 |
|-----------|---------|
| `DriverLoader` | 可能是 ptrace 注入器 / 进程 hook |
| `SystemService` | 可能是后门 / C2 agent |
| `Updater` / `Update` | 可能是 dropper / 下载器 |
| `Helper` / `Assistant` | 可能是提权工具 |
| `lib*.so` | 可能是注入 payload |

**分析时应该：**

- 忽略文件名暗示，按实际代码行为判断
- 关注 `mmap`、`ptrace`、`/proc/self/mem` 等系统调用
- 如果看到"加载驱动"但没有 `insmod`/`init_module` 调用，说明名不副实

### 静态分析不够时的动态补充

纯静态分析只能看到代码骨架。以下场景必须配合动态分析：

| 场景 | 推荐动态方法 |
|------|-------------|
| 代码有解密/解压逻辑 | 在解密后下断点，dump 明文 |
| 大量间接调用（函数指针表） | strace/ltrace 跟踪实际调用 |
| 疑似反调试 | 先 strace 看 ptrace 调用 |
| 内嵌 shellcode/payload | QEMU 用户态模拟执行 |
| 网络通信协议未知 | tcpdump/Wireshark 抓包 |

```bash
# strace 跟踪系统调用（重点关注）
strace -f -e trace=open,mmap,ptrace,execve,connect ./binary

# ltrace 跟踪库函数调用
ltrace -f ./binary

# QEMU 用户态模拟（不需要真实设备）
qemu-aarch64 -strace ./binary_arm64

# 检查反调试：看是否 ptrace 自追踪
strace ./binary 2>&1 | grep ptrace
# 如果看到 ptrace(PTRACE_TRACEME, ...) 说明有反调试
```

### 进程注入/保护壳类样本的常见模式

这类样本通常：

1. **不是真正加载内核驱动**（需要 root 权限，大多数场景没有）
2. **实际行为是进程注入**：
   - `ptrace` attach 到目标进程
   - 通过 `/proc/<pid>/mem` 读写目标内存
   - `mmap` 映射 shellcode 到目标进程空间
3. **内嵌加密 payload**：
   - 运行时解密一段 shellcode
   - 解密后的 payload 才是真正的 hook 代码
4. **反调试保护**：
   - `ptrace(PTRACE_TRACEME)` 自追踪
   - 时间检测（`clock_gettime` 前后对比）
   - `/proc/self/status` 检查 TracerPid

**分析策略：**

```text
1. file 命令确认真实类型
2. strings 看有没有明显的路径/库名/错误信息
3. rabin2 -I 看架构/编译器/保护
4. 静态找 mmap/ptrace/open 调用
5. 如果有解密逻辑 → 动态跑到解密后 dump
6. 如果有反调试 → 先 patch 掉或用 LD_PRELOAD 绕过
```
