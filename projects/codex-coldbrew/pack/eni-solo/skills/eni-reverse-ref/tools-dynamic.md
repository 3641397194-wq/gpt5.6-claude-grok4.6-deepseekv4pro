# 动态分析工具

## 目录

- [Frida（动态插桩）](#frida动态插桩)
- [angr（符号执行）](#angr符号执行)
- [lldb（LLVM 调试器）](#lldbllvm-调试器)
- [x64dbg（Windows 调试器）](#x64dbgwindows-调试器)
- [Qiling 框架（跨平台模拟）](#qiling-框架跨平台模拟)
- [Triton（动态符号执行）](#triton动态符号执行)
- [Intel Pin 指令计数侧信道（Hackover CTF 2015）](#intel-pin-指令计数侧信道)
- [Intel Pin + 遗传算法（hxp CTF 2017）](#intel-pin--遗传算法)
- [仅 opcode 的执行迹重建（0CTF 2016）](#仅-opcode-的执行迹重建)
- [LD_PRELOAD 冻结 time()（EKOPARTY 2017）](#ld_preload-冻结-time)
- [LD_PRELOAD memcmp 逐字节 oracle（Blaze CTF 2018）](#ld_preload-memcmp-逐字节-oracle)

---

## Frida（动态插桩）

Frida 把 JavaScript 注入运行进程做实时 hook、追踪与修改。反调试绕过、运行时检查与移动端逆向的必需品。

### 安装

```bash
pip install frida-tools frida
# 验证
frida --version
```

### 基本函数 Hook

```javascript
// hook.js — 拦函数并记参数/返回值
Interceptor.attach(Module.findExportByName(null, "strcmp"), {
    onEnter: function(args) {
        this.arg0 = Memory.readUtf8String(args[0]);
        this.arg1 = Memory.readUtf8String(args[1]);
        console.log(`strcmp("${this.arg0}", "${this.arg1}")`);
    },
    onLeave: function(retval) {
        console.log(`  → ${retval}`);
    }
});
```

```bash
# 附到运行进程
frida -p $(pidof binary) -l hook.js

# 启动即插桩
frida -f ./binary -l hook.js --no-pause

# 一行：hook strcmp dump 比较
frida -f ./binary --no-pause -e '
Interceptor.attach(Module.findExportByName(null, "strcmp"), {
    onEnter(args) {
        console.log("strcmp:", Memory.readUtf8String(args[0]), Memory.readUtf8String(args[1]));
    }
});
'
```

### 反调试绕过

```javascript
// 绕 ptrace(PTRACE_TRACEME) — 返回 0（成功）不真调
Interceptor.attach(Module.findExportByName(null, "ptrace"), {
    onEnter: function(args) {
        this.request = args[0].toInt32();
    },
    onLeave: function(retval) {
        if (this.request === 0) { // PTRACE_TRACEME
            retval.replace(ptr(0));
            console.log("[*] ptrace(TRACEME) bypassed");
        }
    }
});

// 绕 IsDebuggerPresent（Windows）
var isDbg = Module.findExportByName("kernel32.dll", "IsDebuggerPresent");
Interceptor.attach(isDbg, {
    onLeave: function(retval) {
        retval.replace(ptr(0));
    }
});

// 绕时间检查——hook clock_gettime 返常量
Interceptor.attach(Module.findExportByName(null, "clock_gettime"), {
    onLeave: function(retval) {
        // 恒定时间戳击败时间检查
        var ts = this.context.rsi || this.context.x1; // x86 或 ARM
        Memory.writeU64(ts, 0);        // tv_sec
        Memory.writeU64(ts.add(8), 0); // tv_nsec
    }
});
```

### 内存扫描与补丁

```javascript
// 扫内存找 flag 模式
Process.enumerateRanges('r--').forEach(function(range) {
    Memory.scan(range.base, range.size, "66 6c 61 67 7b", { // "flag{"
        onMatch: function(address, size) {
            console.log("[FLAG] Found at:", address, Memory.readUtf8String(address, 64));
        },
        onComplete: function() {}
    });
});

// Patch 指令（NOP 掉检查）
var addr = Module.findBaseAddress("binary").add(0x1234);
Memory.patchCode(addr, 2, function(code) {
    var writer = new X86Writer(code, { pc: addr });
    writer.putNop();
    writer.putNop();
    writer.flush();
});
```

### 函数替换

```javascript
// 校验函数替换成恒真
var checkFlag = Module.findExportByName(null, "check_flag");
Interceptor.replace(checkFlag, new NativeCallback(function(input) {
    console.log("[*] check_flag called with:", Memory.readUtf8String(input));
    return 1; // 恒合法
}, 'int', ['pointer']));
```

### 追踪与 Stalker

```javascript
// 迹一个函数里的全部调用（Stalker — 指令级追踪）
var targetAddr = Module.findExportByName(null, "main");
Stalker.follow(Process.getCurrentThreadId(), {
    transform: function(iterator) {
        var instruction;
        while ((instruction = iterator.next()) !== null) {
            if (instruction.mnemonic === "call") {
                iterator.putCallout(function(context) {
                    console.log("CALL at", context.pc, "→", ptr(context.pc).readPointer());
                });
            }
            iterator.keep();
        }
    }
});
```

### r2frida（Radare2 + Frida）

```bash
# 经 Frida 把 radare2 附到进程
r2 frida://spawn/./binary

# r2frida 命令
\ii                    # 导入列表
\il                    # 加载模块列表
\dt strcmp             # 迹 strcmp 调用
\dc                    # 继续执行
\dm                    # 内存映射
```

### Android/iOS 的 Frida

```bash
# Android（需 root 或 Frida server）
adb push frida-server /data/local/tmp/
adb shell "chmod 755 /data/local/tmp/frida-server && /data/local/tmp/frida-server &"

# Hook Android Java 方法
frida -U -f com.example.app -l hook_android.js --no-pause
```

```javascript
// hook_android.js — hook Java 方法
Java.perform(function() {
    var MainActivity = Java.use("com.example.app.MainActivity");
    MainActivity.checkPassword.implementation = function(input) {
        console.log("[*] checkPassword called with:", input);
        var result = this.checkPassword(input);
        console.log("[*] Result:", result);
        return result;
    };
});
```

**要点：** Frida 强在静态分析失效处——混淆代码、加壳二进制、运行时生成数据。hook 比较函数（`strcmp`、`memcmp`、自定义校验器）无需逆算法即拿期望值。`Interceptor.attach` 观察，`Interceptor.replace` 修改。

**适用：** 反调试绕过、运行时密钥提取、hook 加密函数 dump 明文、移动应用分析、加壳二进制检查。

### Frida 记忆化加速递归函数（hxp CTF 2017）

Frida hook 递归函数、记忆化结果、回放缓存跳过冗余计算。指数复杂度的 Fibonacci 类递归题瞬间线性。

```javascript
// memo_hook.js — 记忆化递归函数跳过冗余调用
var memo = {};
var funcAddr = ptr("0x400abc");    // 递归函数地址
var retAddr = ptr("0x400def");     // 函数 ret 指令地址

Interceptor.attach(funcAddr, {
    onEnter: function(args) {
        this.key = args[0].toInt32();
        if (memo[this.key] !== undefined) {
            // 整个跳过计算：设返回值并跳 ret
            this.context.rax = memo[this.key];
            this.context.rip = retAddr;
        }
    },
    onLeave: function(retval) {
        // 缓存结果供同参数复用
        memo[this.key] = retval.toInt32();
    }
});
```

```bash
# 用法
frida -f ./binary -l memo_hook.js --no-pause
```

多参数函数用组合键：

```javascript
Interceptor.attach(funcAddr, {
    onEnter: function(args) {
        this.key = args[0].toInt32() + "," + args[1].toInt32();
        if (memo[this.key] !== undefined) {
            this.context.rax = memo[this.key];
            this.context.rip = retAddr;
        }
    },
    onLeave: function(retval) {
        memo[this.key] = retval.toInt32();
    }
});
```

**要点：** Frida 的 `Interceptor` 能读写寄存器状态——设 `rax`（返回值）与 `rip`（指向 `ret`）即可整段跳过函数执行。对同参数同结果的递归函数通用。指数时间递归（Fibonacci、Ackermann、树遍历）记忆化后变线性。

**References:** hxp CTF 2017

---

## angr（符号执行）

angr 自动探索程序路径找满足约束的输入。手动要数小时的 flag 校验二进制，几分钟解掉。

### 安装

```bash
pip install angr
```

### 基本路径探索

```python
import angr
import claripy

# 载二进制
proj = angr.Project('./binary', auto_load_libs=False)

# 找 "Correct!" 打印地址，避 "Wrong!" 打印
# 从反汇编拿（objdump -d 或 Ghidra）
FIND_ADDR = 0x401234    # 成功路径地址
AVOID_ADDR = 0x401256   # 失败路径地址

# 建模拟管理器并探索
simgr = proj.factory.simgr()
simgr.explore(find=FIND_ADDR, avoid=AVOID_ADDR)

if simgr.found:
    found = simgr.found[0]
    # 拿到达目标的 stdin
    print("Flag:", found.posix.dumps(0))  # fd 0 = stdin
```

### 带约束的符号输入

```python
import angr
import claripy

proj = angr.Project('./binary', auto_load_libs=False)

# 建符号输入（如 32 字节 flag）
flag_len = 32
flag_chars = [claripy.BVS(f'flag_{i}', 8) for i in range(flag_len)]
flag = claripy.Concat(*flag_chars + [claripy.BVV(b'\n')])

# 约束为可打印 ASCII
state = proj.factory.entry_state(stdin=flag)
for c in flag_chars:
    state.solver.add(c >= 0x20)
    state.solver.add(c <= 0x7e)

# 约束已知前缀: "flag{"
state.solver.add(flag_chars[0] == ord('f'))
state.solver.add(flag_chars[1] == ord('l'))
state.solver.add(flag_chars[2] == ord('a'))
state.solver.add(flag_chars[3] == ord('g'))
state.solver.add(flag_chars[4] == ord('{'))
state.solver.add(flag_chars[flag_len-1] == ord('}'))

simgr = proj.factory.simgr(state)
simgr.explore(find=0x401234, avoid=0x401256)

if simgr.found:
    found = simgr.found[0]
    result = found.solver.eval(flag, cast_to=bytes)
    print("Flag:", result.decode())
```

### Hook 函数简化分析

```python
import angr

proj = angr.Project('./binary', auto_load_libs=False)

# Hook printf 防 I/O 路径爆炸
@proj.hook(0x401100, length=5)  # printf 调用地址
def skip_printf(state):
    pass  # 什么都不做，跳过

# Hook sleep/反调试函数
@proj.hook(0x401050, length=5)  # sleep 调用地址
def skip_sleep(state):
    pass

# 用摘要替换函数
class AlwaysSucceed(angr.SimProcedure):
    def run(self):
        return 1

proj.hook_symbol('check_license', AlwaysSucceed())
```

### 从指定地址探索

```python
# 从函数中部开始（跳初始化）
state = proj.factory.blank_state(addr=0x401200)

# 手工设寄存器/内存
state.regs.rdi = 0x600000  # 输入缓冲指针
state.memory.store(0x600000, b"AAAA" + b"\x00" * 28)

simgr = proj.factory.simgr(state)
simgr.explore(find=0x401300, avoid=0x401350)
```

### 常见模式与提示

```python
# 模式 1: argv 输入
state = proj.factory.entry_state(args=['./binary', flag_sym])

# 模式 2: 多 find/avoid 地址
simgr.explore(
    find=[0x401234, 0x401300],     # 任一成功路径
    avoid=[0x401256, 0x401400]     # 全部失败路径
)

# 模式 3: 按输出字符串找（无需地址）
def is_successful(state):
    stdout = state.posix.dumps(1)  # fd 1 = stdout
    return b"Correct" in stdout

def should_avoid(state):
    stdout = state.posix.dumps(1)
    return b"Wrong" in stdout

simgr.explore(find=is_successful, avoid=should_avoid)

# 模式 4: 超时保护
simgr.explore(find=0x401234, avoid=0x401256, num_find=1)
# 或探索技术:
simgr.use_technique(angr.exploration_techniques.DFS())  # 深度优先
simgr.use_technique(angr.exploration_techniques.LengthLimiter(max_length=500))
```

### 应对路径爆炸

```python
# flag checker 用 DFS 替代默认 BFS
simgr.use_technique(angr.exploration_techniques.DFS())

# 限符号内存操作
state.options.add(angr.options.ZERO_FILL_UNCONSTRAINED_MEMORY)
state.options.add(angr.options.ZERO_FILL_UNCONSTRAINED_REGISTERS)

# Hook 昂贵函数（加密、哈希）防爆炸
import hashlib
class SHA256Hook(angr.SimProcedure):
    def run(self, data, length, output):
        # 具体化输入算哈希
        concrete_data = self.state.solver.eval(
            self.state.memory.load(data, self.state.solver.eval(length)),
            cast_to=bytes
        )
        h = hashlib.sha256(concrete_data).digest()
        self.state.memory.store(output, h)

proj.hook_symbol('SHA256', SHA256Hook())
```

### angr CFG 恢复

```python
# 控制流图理解结构
cfg = proj.analyses.CFGFast()
print(f"Functions found: {len(cfg.functions)}")

# 找 main
for addr, func in cfg.functions.items():
    if func.name == 'main':
        print(f"main at {addr:#x}")
        break

# 交叉引用
node = cfg.model.get_any_node(0x401234)
print("Predecessors:", [hex(p.addr) for p in cfg.model.get_predecessors(node)])
```

**要点：** angr 对成功/失败路径清晰的 flag checker 最佳。复杂二进制 hook 昂贵函数（加密、I/O）并用 DFS。先最简打法（仅 find/avoid 地址），不够再加约束。angr 慢就把输入约束到可打印 ASCII 加已知前缀。

**适用：** 分支校验器、迷宫/寻路二进制、约束密集检查、自动二进制分析。弱项：重加密、浮点数学、复杂堆操作。

---

## lldb（LLVM 调试器）

macOS/iOS 主调试器。Linux 也可用。Swift/Objective-C 与 Apple 平台二进制首选。

### 基本命令

```bash
lldb ./binary
(lldb) run                          # 运行
(lldb) b main                       # main 断点
(lldb) b 0x401234                   # 地址断点
(lldb) breakpoint set -r "check.*"  # 正则断点
(lldb) c                            # 继续
(lldb) si                           # 步指令
(lldb) ni                           # 步过
(lldb) register read                # 全部寄存器
(lldb) register write rax 0         # 改寄存器
(lldb) memory read 0x401000 -c 32   # 读 32 字节
(lldb) x/s $rsi                     # 看字符串（GDB 式）
(lldb) dis -n main                  # 反汇编函数
(lldb) image list                   # 加载模块 + 基址
```

### 脚本（Python）

```python
# lldb Python 脚本
import lldb

def hook_strcmp(debugger, command, result, internal_dict):
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    thread = process.GetSelectedThread()
    frame = thread.GetSelectedFrame()
    arg0 = frame.FindRegister("rdi").GetValueAsUnsigned()
    arg1 = frame.FindRegister("rsi").GetValueAsUnsigned()
    s0 = process.ReadCStringFromMemory(arg0, 256, lldb.SBError())
    s1 = process.ReadCStringFromMemory(arg1, 256, lldb.SBError())
    print(f'strcmp("{s0}", "{s1}")')

# lldb 注册: command script add -f script.hook_strcmp hook_strcmp
```

**要点：** macOS 二进制（Mach-O）、iOS 应用、GDB 不可用时用 lldb。`image list` 给 PIE 二进制的 ASLR 滑动。脚本 API 比 GDB 更结构化。

---

## x64dbg（Windows 调试器）

开源 Windows 调试器，现代 UI。Windows 逆向题替代 OllyDbg/WinDbg。

### 关键功能

```bash
# 启动
x64dbg.exe binary.exe         # 64 位
x32dbg.exe binary.exe         # 32 位

# 常用快捷键
F2      → 切换断点
F7      → 步进
F8      → 步过
F9      → 运行
Ctrl+G  → 跳地址
Ctrl+F  → 内存找模式
```

### 脚本

```bash
# x64dbg 命令行
bp 0x401234                    # 断点
SetBPX 0x401234, 0, "log {s:utf8@[esp+4]}"  # 命中时记字符串参数
run                            # 继续
StepOver                       # 步过
```

### 常见 CTF 工作流

1. GUI cracker 断 `GetWindowTextA`/`MessageBoxA`
2. 从成功/失败消息回追
3. 加壳二进制用 **Scylla** 插件重建 IAT
4. **Snowman** 反编译插件快速伪 C

**要点：** x64dbg 内置模式扫描、硬件断点、条件日志。Windows CTF 二进制的动态分析常快于 IDA/Ghidra。**xAnalyzer** 插件自动标注函数参数。

---

## Qiling 框架（跨平台模拟）

Qiling 带 OS 层支持（系统调用、文件系统、注册表）模拟二进制。基于 Unicorn，补上 Unicorn 缺的 OS 层。

### 安装

```bash
pip install qiling
# 下载目标 OS 的 rootfs：
git clone https://github.com/qilingframework/rootfs
```

### 基本用法

```python
from qiling import Qiling
from qiling.const import QL_VERBOSE

# Linux ELF 模拟
ql = Qiling(["./binary", "arg1"], "rootfs/x8664_linux",
            verbose=QL_VERBOSE.DEFAULT)
ql.run()

# Windows PE 模拟（无需 Windows！）
ql = Qiling(["rootfs/x86_windows/bin/binary.exe"], "rootfs/x86_windows")
ql.run()

# ARM/MIPS 模拟（IoT 固件）
ql = Qiling(["rootfs/arm_linux/bin/binary"], "rootfs/arm_linux")
ql.run()
```

### 经模拟绕反调试

```python
from qiling import Qiling

ql = Qiling(["./binary"], "rootfs/x8664_linux")

# Hook ptrace 系统调用 — 返回 0（成功）
def hook_ptrace(ql, ptrace_request, pid, addr, data):
    ql.log.info("ptrace bypassed")
    return 0

ql.os.set_syscall("ptrace", hook_ptrace)

# Hook 特定地址（如反 VM 检查）
def skip_check(ql):
    ql.arch.regs.rax = 0  # 强制成功
    ql.log.info(f"Skipped check at {ql.arch.regs.rip:#x}")

ql.hook_address(skip_check, 0x401234)

ql.run()
```

### 输入模糊

```python
# 不同输入模拟找 flag
import string
from qiling import Qiling

def test_input(candidate):
    ql = Qiling(["./binary"], "rootfs/x8664_linux",
                verbose=QL_VERBOSE.DISABLED, stdin=candidate.encode())
    ql.run()
    return ql.os.stdout.read()

for ch in string.printable:
    output = test_input("flag{" + ch)
    if b"Correct" in output:
        print(f"Found: {ch}")
```

**相对 GDB/Frida 的优势：**

- 零调试器痕迹（默认绕过一切反调试）
- 免硬件跨平台（x86 主机上 ARM、MIPS、RISC-V）
- Python 脚本化（迭代快于 GDB）
- 快照/恢复做爆破

**要点：** Qiling 模拟整个 OS 层（系统调用、文件系统、注册表），不只是 CPU。`ptrace(TRACEME)` 类反调试自然返回成功无需 patch，且无需 QEMU 或真机即可在 x86 主机分析 ARM/MIPS。

**适用：** 异架构二进制、IoT 固件、重度反调试、多输入自动测试。

---

## Triton（动态符号执行）

完整 Triton 参考见 [tools-advanced.md](tools-advanced.md#triton动态符号执行)。快速用法：

```python
from triton import *

ctx = TritonContext(ARCH.X86_64)

# 符号化输入缓冲
for i in range(32):
    ctx.symbolizeMemory(MemoryAccess(0x600000 + i, CPUSIZE.BYTE), f"flag_{i}")

# 处理指令收集约束
# 比较点处求解 flag
model = ctx.getModel(ctx.getPathConstraintsAst())
flag = ''.join(chr(v.getValue()) for _, v in sorted(model.items()))
```

**要点：** Triton 长于单路径 DSE（动态符号执行），正是 angr 路径爆炸的痛点场景。喂具体执行迹、符号化特定输入、比较点解约束。线性代码路径比 angr 快。

**最佳场景：** 单路径符号执行、去混淆、污点分析。

---

## Intel Pin 指令计数侧信道（Hackover CTF 2015）

**模式：** 用 Intel Pin 的 `inscount0` 工具对二进制做逐字符爆破。正确字符让比较逻辑执行更深（指令更多）。

```python
import string
from subprocess import Popen, PIPE

pin = './pin'
tool = './source/tools/ManualExamples/obj-ia32/inscount0.so'
binary = './target'

key = ''
while True:
    best_count, best_char = 0, ''
    for c in string.printable:
        cmd = [pin, '-injection', 'child', '-t', tool, '--', binary]
        p = Popen(cmd, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        p.communicate((key + c + '\n').encode())
        with open('inscount.out') as f:
            count = int(f.read().split()[-1])
        if count > best_count:
            best_count, best_char = count, c
    key += best_char
    print(f"Found: {key}")
```

**要点：** Movfuscated 二进制（movfuscator 编译）把每条指令展开成 `mov` 序列，静态分析不现实。但逐字符比较仍有可测的指令数差异。Pin 的 `inscount0.so` 数总执行指令——每位置正确字符引发 ~1000+ 条额外指令（在比较中走得更深）。对带顺序输入检查的混淆二进制同样有效。

---

## Intel Pin + 遗传算法（hxp CTF 2017）

自修改代码只在每字符检查通过后才解密下一块时，标准逐字符 Pin 计数失败——搜索空间太大且字符可能交互。用遗传算法更高效地探索输入空间。

```python
import subprocess
import random
import string

PIN_PATH = '/tmp/pin-3.5/pin'
TOOL_PATH = 'source/tools/ManualExamples/obj-intel64/inscount0.so'

def fitness(candidate):
    """Pin 下跑二进制，指令数作适应度。"""
    proc = subprocess.Popen(
        [PIN_PATH, '-t', TOOL_PATH, '--', './binary'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate(candidate.encode())
    # inscount0 把计数写到 stderr 或 inscount.out
    try:
        with open('inscount.out') as f:
            return int(f.read().split()[-1])
    except:
        return 0

def mutate(individual, rate=0.1):
    """随机变异个体字符。"""
    result = list(individual)
    for i in range(len(result)):
        if random.random() < rate:
            result[i] = random.choice(string.printable[:62])
    return result

# 遗传算法参数
FLAG_LEN = 40
POP_SIZE = 100
SURVIVORS = 20

# 初始化随机种群
population = [random.choices(string.printable[:62], k=FLAG_LEN) for _ in range(POP_SIZE)]

for generation in range(10000):
    # 指令数给个体打分
    scored = [(fitness(''.join(p)), p) for p in population]
    scored.sort(reverse=True)
    best_score, best_individual = scored[0]
    print(f"Gen {generation}: {best_score} {''.join(best_individual)}")

    # 留顶尖幸存者，变异补满种群
    survivors = [s[1] for s in scored[:SURVIVORS]]
    population = survivors + [mutate(random.choice(survivors)) for _ in range(POP_SIZE - SURVIVORS)]
```

**Go 二进制（查表式 flag 检查）的定制 Pin：**

标准 `inscount` 失效（计数器增量与正确性不相关，如查表比较）时，改 Pin 的 icount 工具只数成功分支地址的执行次数。用定向计数器逐字符爆破：

```cpp
// 定制 inscount0.cpp — 只数特定地址的执行
static ADDRINT target_addr = 0x401234;  // 成功分支地址
static UINT64 target_count = 0;

VOID CountAtTarget(ADDRINT ip) {
    if (ip == target_addr) target_count++;
}

VOID Instruction(INS ins, VOID *v) {
    INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)CountAtTarget,
                   IARG_INST_PTR, IARG_END);
}
```

**要点：** 每个正确字符解锁新代码段（自修改或多级解密）时，指令数随正确性单调增。遗传算法比逐字符爆破更高效——可同时发现多个正确字符。40 字符 flag 约 30 分钟收敛。总指令数不相关的查表比较，改靶向特定分支地址计数。

**References:** hxp CTF 2017

---

## 仅 opcode 的执行迹重建（0CTF 2016）

只有 opcode（无寄存器/内存值）的执行迹：按地址排序去重恢复代码布局、切基本块、标注函数。排序算法尤易受攻击——分支决策泄露元素顺序。

**打法：**

1. 迹条目按地址排序、去重恢复代码布局
2. 识别基本块边界（跳转、调用、返回）
3. 从迹顺序映射分支走/未走决策
4. 排序算法的分区比较揭示全部输入元素的相对顺序

**要点：** 无数据值的执行迹仍经分支决策泄露信息。快排分区比较揭示每步哪个元素大/小，仅靠分支方向即可完整恢复被排序的输入。

---

## LD_PRELOAD 冻结 time()（EKOPARTY 2017）

LD_PRELOAD 覆写 `time()` 返回常量，冻结任何时间戳种子 PRNG。二进制密码确定化后，无需理解 VM 或密码内部即可逐字节爆破输出。

```c
// freeze_time.c — 编译: gcc -shared -fPIC -o freeze.so freeze_time.c
#include <time.h>

time_t time(time_t *t) {
    if (t) *t = 1234567890;
    return 1234567890;
}
```

```bash
# 构建与使用:
gcc -shared -fPIC -o freeze.so freeze_time.c
LD_PRELOAD=./freeze.so ./binary

# 逐字节 oracle: 冻结时间跑，试每个候选字节，
# 看输出——正确字节产生期望输出字符。
for byte in $(seq 0 255); do
    output=$(echo -n "$(printf '\x%02x' $byte)" | LD_PRELOAD=./freeze.so ./binary)
    # 与已知/期望输出比对
done
```

`rand()` 也涉及时一并覆写：

```c
int rand(void) { return 42; }
```

**要点：** LD_PRELOAD 拦截冻结非确定性源（time、rand）。确定化后，再复杂的 VM 也变成可逐字节 oracle。

**References:** EKOPARTY CTF 2017

---

## LD_PRELOAD memcmp 逐字节 oracle（Blaze CTF 2018）

**模式：** 用 LD_PRELOAD 库替换 `memcmp`，返回匹配字节数而非标准 -1/0/1。任何 memcmp 校验都变成逐字节 oracle。配 GDB Python 脚本自动逐位置爆破。

```c
// memcmp_hook.c - 编译: gcc -shared -fPIC -o hook.so memcmp_hook.c
int memcmp(const char *s1, const char *s2, int n) {
    int cnt = 0;
    for (int i = 0; i < n; ++i) {
        if (s1[i] == s2[i]) cnt++;
        else break;
    }
    return cnt;
}
```

```bash
# 配 GDB 用: LD_PRELOAD=./hook.so gdb ./binary
# memcmp 后断点，读返回值数匹配字节
# 逐位置迭代字符，找让计数增的那个
```

**要点：** LD_PRELOAD 替换 memcmp 返回匹配数，把任何比较式校验变成逐字节 oracle。配 GDB 脚本自动爆破密码/flag 检查，无需逆校验算法。

**识别：** 二进制用 `memcmp` 或 `strcmp` 校验 flag（`ltrace` 输出或导入表可见）。比较函数拿用户输入与计算/存储的期望值比较。

**References:** Blaze CTF 2018
