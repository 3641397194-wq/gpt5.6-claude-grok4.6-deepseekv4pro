# 进阶工具与反混淆

> 商业壳/保护器、二进制 diffing、反混淆框架、模拟与 angr 之外的符号执行。

## 目录

- [VMProtect 分析](#vmprotect-分析)
- [Themida / WinLicense 分析](#themida--winlicense-分析)
- [二进制 diffing](#二进制-diffing)
- [反混淆框架](#反混淆框架)
- [Qiling 框架（模拟）](#qiling-框架模拟)
- [Triton（动态符号执行）](#triton动态符号执行)
- [Manticore（符号执行）](#manticore符号执行)
- [Rizin / Cutter](#rizin--cutter)
- [RetDec（可重定向反编译器）](#retdec可重定向反编译器)
- [自定义 VM 字节码提升到 LLVM IR（Google CTF 2017）](#自定义-vm-字节码提升到-llvm-ir)
- [高级 GDB 技术](#高级-gdb-技术)
- [高级 Ghidra 脚本](#高级-ghidra-脚本)
- [补丁策略](#补丁策略)
- [GDB 约束提取 + ILP/LP 求解器（BackdoorCTF 2017）](#gdb-约束提取--ilplp-求解器)
- [GDB 位置编码输入 + 零标志监控（EKOPARTY 2017）](#gdb-位置编码输入--零标志监控)
- [LD_PRELOAD dump 仅执行二进制（BackdoorCTF 2017）](#ld_preload-dump-仅执行二进制)

---

## VMProtect 分析

VMProtect 把 x86/x64 代码虚拟化成由生成 VM 解释的自定义字节码。CTF 里最有挑战的保护器之一。

### 识别

```bash
# VMProtect 签名
strings binary | grep -i "vmp\|vmprotect"
# PE 节: .vmp0, .vmp1（VMProtect 加自己的节）
readelf -S binary | grep ".vmp"
# 某些节熵 > 7.5 的大二进制
```

**关键指标：**

- `push`/`pop` 密集序言（VM 入口把全部寄存器压栈）
- 大 switch-case 分发器（VM handler 循环）
- VM handler 内嵌反调试检查
- 变异引擎：同 opcode 每次构建 handler 不同

### 打法

```text
1. 识别 VM 入口点——找 pushad/pushaq 式序列
2. 找 handler 表——大间接跳转（jmp [reg + offset]）
3. 迹 handler 执行——每个 handler 以跳下一个收尾
4. 识别 handlers:
   - vAdd, vSub, vMul, vXor, vNot（算术）
   - vPush, vPop（栈操作）
   - vLoad, vStore（内存访问）
   - vJmp, vJcc（控制流）
   - vRet（VM 退出——恢复真实寄存器）
5. 建 VM 字节码反汇编器
6. 化简/去混淆提升出的 IL
```

### 工具

- **VMPAttack**（IDA 插件）：自动识别 VM handlers
- **NoVmp**：经 VTIL 反虚拟化（开源）
- **VMProtect devirtualizer 脚本**：社区 IDA/Binary Ninja 脚本
- **CTF 打法：** 迹特定操作（加密、比较）往往比完整反虚拟化省事

### CTF 策略

```python
# 动态迹 VM 执行提取 flag 上的操作
# Hook VM handler 分发记录 opcode + 操作数

import frida

script = """
var vm_dispatch = ptr('0x...');  // handler 表跳转地址
Interceptor.attach(vm_dispatch, {
    onEnter(args) {
        // 记 handler 序号与栈状态
        var handler_idx = this.context.rax;  // 或相应寄存器
        console.log('Handler:', handler_idx, 'RSP:', this.context.rsp);
    }
});
"""
```

**要点：** CTF 很少需要完整反虚拟化。聚焦追踪输入上执行了哪些操作。hook VM 内调用的比较/加密函数。

---

## Themida / WinLicense 分析

类似 VMProtect，但多几层反调试。

### Themida 识别

- 节：`.themida`、`.winlice`
- 极重反调试（内核级检查、驱动安装）
- 代码变异 + 虚拟化 + 加壳复合

### CTF 打法

1. **dump 脱壳代码：** 让它跑，脱壳后 dump 进程内存
2. **绕反调试：** x64dbg 里 ScyllaHide 选 Themida 预设
3. **修导入：** Scylla 插件重建 IAT
4. **聚焦 dump：** 脱壳后当普通二进制分析

```bash
# Themida 的 x64dbg 工作流：
1. 加载二进制
2. ScyllaHide → Profile: Themida
3. 跑到 OEP（Original Entry Point）——可能要试几次
4. Scylla dump: OEP → IAT Autosearch → Get Imports → Dump
5. 修 dump: Scylla → Fix Dump
6. Ghidra/IDA 分析修好的 dump
```

---

## 二进制 diffing

补丁分析、1-day 利用开发与给两个版本二进制的 CTF 题的关键能力。

### BinDiff

```bash
# 先从 IDA/Ghidra 导出，再 diff
# IDA: File → BinExport → Export as BinExport2
# Ghidra: BinExport 插件

# 命令行 diff
bindiff primary.BinExport secondary.BinExport
# BinDiff GUI 打开——显示匹配/未匹配函数
```

**关键指标：**

- 每函数对相似度分（0.0-1.0）
- 变化指令高亮
- 未匹配函数 = 新增/删除代码

### Diaphora

BinDiff 的免费开源替代，IDA 插件。

```bash
# IDA 里：
# File → Script file → diaphora.py
# 先导出第一个二进制，再开第二个 diff

# Ghidra 版: diaphora_ghidra.py
```

**CTF 用处：** 题目给 "patched" 与 "original" 双二进制时，diff 直接暴露漏洞或隐藏功能。

---

## 反混淆框架

> OLLVM 脱密完整工作流、变种生态与社区工具调研见 [ollvm-deobfuscation.md](references/ollvm-deobfuscation.md)。

### d810-ng（IDA）——本地首选

D-810 的现代维护版（Next Generation），集成 **Z3 SMT** 求解器，覆盖 OLLVM / Tigress / Hodur(PlugX) / Approov 多种变种。

```text
能力:
- MBA 化简（Z3 验证）: (a ^ b) + 2*(a & b) → a + b
- 不透明谓词去除（Pred0/PredFF/PredSetz/PredSetnz）
- 常量折叠（22 条规则）
- 控制流去平坦化（多种 unflattener）:
  * Unflattener           → O-LLVM（switch/if-chain）
  * UnflattenerSwitchCase → Tigress（m_jtbl）
  * UnflattenerTigressIndirect → Tigress（m_ijmp）
  * HodurUnflattener      → Hodur/PlugX（while(1) + jnz state）
  * BadWhileLoop          → Approov（0xF6000–0xF6FFF 状态常量）
- Hacker's Delight 位运算等价
- PlugX (Hodur) 恶意软件专用 MBA 模式

安装: clone → 复制到 IDA plugins 目录 → Ctrl-Shift-D 加载
源码: https://github.com/w00tzenheimer/d810-ng
```

### obpo-plugin（IDA）——效果最强，云插件

基于 Hex-Rays **microcode** + 数据流跟踪 + 程序切片 + 混合执行（concolic）。社区公认效果最强之一。

```text
- 在 microcode 层优化反编译输出（不是改 ASM）
- 支持 IDA 7.5-7.7 + Hex-Rays，多架构（ARM/ARM64/x86/x64/PPC/MIPS）
- 云插件：目标函数上传 obpo-server 处理（核心闭源，插件免费）
- ⚠️ 敏感样本慎用（二进制上传云服务）
- 用法：右键 dispatcher → OBPO → Mark and process function
源码: https://github.com/obpo-project/obpo-plugin
```

### ollvm-unflattener — Miasm 纯脚本

无 IDA 依赖，基于 Miasm 符号执行，BFS 多层处理，支持 x86/x64 Win/Linux。

```bash
git clone https://github.com/cdong1012/ollvm-unflattener
pip install -r requirements.txt   # miasm, graphviz, keystone-engine
python unflattener -i <input> -o <output> -t <func_addr> -a   # -a 自动多层
```

### ollvm-breaker（Binary Ninja）

Binary Ninja 去平坦化，仓库自带 Android 加固样本 `libvdog.so` 实战。源码：amimo/ollvm-breaker

### DeObfBR — BR 混淆专项

专门去除 Goron/Arkari 风格的 BR（间接分支）混淆。简易技巧：设置数据段只读可部分对抗。源码：Mrack/DeObfBR

### deollvm — ARM64 Unicorn

无 IDA 时处理 ARM64 .so 的备选，基于 Unicorn。源码：GeT1t/deollvm

### GOOMBA（Ghidra）

```text
GOOMBA (Ghidra-based Obfuscated Object Matching and Bytes Analysis):
- 与 Ghidra 的 P-Code 集成
- 化简 MBA 表达式
- 已知混淆模式匹配

安装: .jar 复制到 Ghidra extensions
用法: Code Browser → Analysis → GOOMBA
```

### Miasm

带符号执行与 IR 提升的强力逆向框架。

```python
from miasm.analysis.binary import Container
from miasm.analysis.machine import Machine
from miasm.expression.expression import *

# 载二进制提升到 Miasm IR
cont = Container.from_stream(open("binary", "rb"))
machine = Machine(cont.arch)
mdis = machine.dis_engine(cont.bin_stream, loc_db=cont.loc_db)

# 反汇编函数
asmcfg = mdis.dis_multiblock(entry_addr)

# 提升到 IR
lifter = machine.lifter_model_call(loc_db=cont.loc_db)
ircfg = lifter.new_ircfg_from_asmcfg(asmcfg)

# 符号执行
from miasm.ir.symbexec import SymbolicExecutionEngine
sb = SymbolicExecutionEngine(lifter)
# 符号执行，再化简表达式
```

**用途：** 脱混淆表达式树、化简复杂算术、穿混淆代码追数据流。

---

## Qiling 框架（模拟）

基于 Unicorn 的跨平台模拟框架，带 OS 层支持（系统调用、文件系统、注册表）。

```python
from qiling import Qiling
from qiling.const import QL_VERBOSE

# 模拟 Linux ELF
ql = Qiling(["./binary"], "rootfs/x8664_linux",
            verbose=QL_VERBOSE.DEBUG)

# Hook 特定地址
@ql.hook_address
def hook_check(ql, address, size):
    if address == 0x401234:
        ql.arch.regs.rax = 0  # 绕过检查
        ql.log.info("Anti-debug bypassed")

# Hook 系统调用
@ql.hook_syscall(name="ptrace")
def hook_ptrace(ql, request, pid, addr, data):
    return 0  # 恒成功

# Hook API（Windows）
@ql.set_api("IsDebuggerPresent", target=ql.os.user_defined_api)
def hook_isdebug(ql, address, params):
    return 0

ql.run()
```

**相对 Unicorn 的优势：**

- OS 模拟（文件 I/O、网络、注册表）
- 多平台（Linux、Windows、macOS、Android、UEFI）
- 内置调试器接口
- 库加载 rootfs

**CTF 用途：**

- 异架构二进制模拟（ARM、MIPS、RISC-V）
- 一次绕过全部反调试（零调试器痕迹）
- 免硬件模糊嵌入式/IoT 固件
- 无代码修改的执行追踪

---

## Triton（动态符号执行）

基于 Pin 的动态二进制分析框架，带符号执行、污点分析与 AST 化简。

```python
from triton import *

ctx = TritonContext(ARCH.X86_64)

# 载二进制节
with open("binary", "rb") as f:
    binary = f.read()
ctx.setConcreteMemoryAreaValue(0x400000, binary)

# 符号化输入
for i in range(32):
    ctx.symbolizeMemory(MemoryAccess(INPUT_ADDR + i, CPUSIZE.BYTE), f"input_{i}")

# 模拟指令
pc = ENTRY_POINT
while pc:
    inst = Instruction(pc, ctx.getConcreteMemoryAreaValue(pc, 16))
    ctx.processing(inst)

    # 比较点提取路径约束
    if pc == CMP_ADDR:
        ast = ctx.getPathConstraintsAst()
        model = ctx.getModel(ast)
        for k, v in sorted(model.items()):
            print(f"input[{k}] = {chr(v.getValue())}", end="")
        break

    pc = ctx.getConcreteRegisterValue(ctx.registers.rip)
```

**Triton vs angr：**

| 特性 | Triton | angr |
|---|---|---|
| 执行 | 具体 + 符号（DSE） | 全符号 |
| 速度 | 快（具体驱动） | 慢（全路径探索） |
| 路径爆炸 | 不易（跟单路径） | 大问题 |
| API | C++ / Python | Python |
| 最佳场景 | 单路径去混淆、污点追踪 | 多路径探索 |

**关键用途：** Triton 长于去混淆——具体跑程序、跟踪符号状态、化简收集的约束。

---

## Manticore（符号执行）

Trail of Bits 的符号执行工具。类似 angr，但原生支持 EVM（以太坊）。

```python
from manticore.native import Manticore

m = Manticore("./binary")

# Hook 成功/失败
@m.hook(0x401234)
def success(state):
    buf = state.solve_one_n_batched(state.input_symbols, 32)
    print("Flag:", bytes(buf))
    m.kill()

@m.hook(0x401256)
def fail(state):
    state.abandon()

m.run()
```

**最佳场景：** EVM/智能合约分析、较简单的 Linux 二进制。复杂 RE 任务 angr 通常更成熟。

---

## Rizin / Cutter

Rizin 是 radare2 的维护分支。Cutter 是其 Qt GUI。

```bash
# Rizin CLI（r2 兼容命令）
rizin -d ./binary
> aaa                    # 全分析
> afl                    # 函数列表
> pdf @ main             # 反汇编
> VV                     # 可视化图模式

# Cutter GUI
cutter binary           # GUI + 反编译器打开
```

**Cutter 优势：**

- 内置 Ghidra 反编译器（r2ghidra 插件）
- 单 GUI 集图视图、hex 编辑器、调试面板
- 集成 Python/JavaScript 脚本控制台
- 免费开源

---

## RetDec（可重定向反编译器）

基于 LLVM 的多架构反编译器。免费开源。

```bash
# 安装
pip install retdec-decompiler
# 或网页: https://retdec.com/decompilation/

# CLI
retdec-decompiler binary
# 输出: binary.c（反编译 C）, binary.dsm（反汇编）

# 特定函数
retdec-decompiler --select-ranges 0x401000-0x401100 binary
```

**强项：** 多架构（x86、ARM、MIPS、PowerPC、PIC32）、免费、产出可编译 C。Ghidra 支持不佳的架构好使。

---

## 自定义 VM 字节码提升到 LLVM IR（Google CTF 2017）

复杂自定义 VM：VM 字节码转译成 LLVM IR，用 LLVM 优化 pass 化简，再反编译优化后的 IR。

```python
# 流水线: VM 字节码 → 自定义反汇编器 → LLVM IR → 优化 → 反编译
# 1. 给自定义 VM opcode 写反汇编器
# 2. 每个 opcode 发 LLVM IR:
#    INC reg  → %reg = add i32 %reg, 1
#    CDEC reg → 条件减
#    CALL fn  → call void @fn()
# 3. MCJIT 或 llc 优化:
#    opt -O3 -S vm_lifted.ll -o vm_optimized.ll
# 4. 优化 IR 载 IDA 或 RetDec 反编译
# 结果: 1300 行 → 内联 + 常量折叠后 150 行
```

**要点：** LLVM 优化 pass（内联、常量折叠、死代码消除）戏剧性化简提升的 VM 字节码。26 寄存器 3 opcode 的自定义 VM 产出 1300 行 IL，`-O3` 后降到约 150 行，暴露底层算法（如 Collatz 序列计算）。

---

## 高级 GDB 技术

### Python 脚本

```python
# ~/.gdbinit 或 GDB 里 source
import gdb

class TraceCompare(gdb.Breakpoint):
    """记录全部比较操作。"""
    def __init__(self, addr):
        super().__init__(f"*{addr}", gdb.BP_BREAKPOINT)

    def stop(self):
        frame = gdb.selected_frame()
        rdi = int(frame.read_register("rdi"))
        rsi = int(frame.read_register("rsi"))
        rdx = int(frame.read_register("rdx"))
        # 读被比较缓冲
        inferior = gdb.selected_inferior()
        buf1 = inferior.read_memory(rdi, rdx).tobytes()
        buf2 = inferior.read_memory(rsi, rdx).tobytes()
        print(f"memcmp({buf1!r}, {buf2!r}, {rdx})")
        return False  # 不停，只记录

# GDB 用法:
# (gdb) source trace_cmp.py
# (gdb) python TraceCompare(0x401234)
```

### GDB 脚本爆破

```python
# 经 GDB Python API 逐字节爆破
import gdb, string

def bruteforce_flag(check_addr, success_addr, fail_addr, flag_len):
    flag = []
    for pos in range(flag_len):
        for ch in string.printable:
            candidate = ''.join(flag) + ch + 'A' * (flag_len - pos - 1)
            gdb.execute('start', to_string=True)
            gdb.execute(f'b *{check_addr}', to_string=True)
            # 候选写入 stdin 管道
            # ...（设输入）
            gdb.execute('continue', to_string=True)
            rip = int(gdb.parse_and_eval('$rip'))
            if rip == success_addr:
                flag.append(ch)
                break
        gdb.execute('delete breakpoints', to_string=True)
    return ''.join(flag)
```

### 条件断点

```bash
# 寄存器为特定值才断
(gdb) b *0x401234 if $rax == 0x41
(gdb) b *0x401234 if *(char*)$rdi == 'f'

# 第 N 次命中才断
(gdb) b *0x401234
(gdb) ignore 1 99    # 跳前 99 次，第 100 次断

# 只记不停
(gdb) b *0x401234
(gdb) commands
> silent
> printf "rax=%lx rdi=%lx\n", $rax, $rdi
> continue
> end
```

### Watchpoints

```bash
# 硬件 watchpoint — 内存变时断
(gdb) watch *(int*)0x601050        # 写该地址断
(gdb) rwatch *(int*)0x601050       # 读断
(gdb) awatch *(int*)0x601050       # 读写断

# 按名看变量（需调试符号）
(gdb) watch flag_buffer[0]

# 条件 watchpoint
(gdb) watch *(int*)0x601050 if *(int*)0x601050 == 0x42
```

### 反向调试（rr）

```bash
# 记录执行
rr record ./binary
# 带回滚能力的重放
rr replay

# rr replay 里（GDB 命令外加）：
(gdb) reverse-continue     # 反跑到上一断点
(gdb) reverse-stepi        # 反步一条指令
(gdb) reverse-next         # 反向 next
(gdb) when                 # 当前事件号

# 设检查点并返回
(gdb) checkpoint
(gdb) restart 1           # 回检查点 1
```

**关键用途：** 步过关键时刻时倒回去，不用重来。对破坏状态的反调试无价。

### GDB Dashboard / GEF / pwndbg

```bash
# pwndbg（CTF 最流行）
# https://github.com/pwndbg/pwndbg
git clone https://github.com/pwndbg/pwndbg && cd pwndbg && ./setup.sh

# pwndbg 关键命令：
pwndbg> context           # 寄存器、栈、代码、回溯
pwndbg> vmmap             # 内存映射（如 /proc/self/maps）
pwndbg> search -s "flag{" # 内存搜字符串
pwndbg> telescope $rsp 20 # 智能栈 dump
pwndbg> cyclic 200        # 生成 De Bruijn 模式
pwndbg> hexdump $rdi 64   # 漂亮 hex dump
pwndbg> got               # GOT 条目
pwndbg> plt               # PLT 条目

# GEF（替代）
# https://github.com/hugsy/gef
bash -c "$(curl -fsSL https://gef.blah.cat/sh)"

# GEF 关键命令：
gef> xinfo $rdi           # 地址详情
gef> checksec             # 二进制安全特性
gef> heap chunks          # 堆块列表
gef> pattern create 100   # De Bruijn 模式
```

---

## 高级 Ghidra 脚本

```python
# Ghidra Python (Jython) — Script Manager 或 headless 运行

# 按模式批量重命名函数
from ghidra.program.model.symbol import SourceType
fm = currentProgram.getFunctionManager()
for func in fm.getFunctions(True):
    if func.getName().startswith("FUN_"):
        # 查函数是否含特定指令模式
        body = func.getBody()
        inst_iter = currentProgram.getListing().getInstructions(body, True)
        for inst in inst_iter:
            if inst.getMnemonicString() == "CPUID":
                func.setName("anti_vm_check_" + hex(func.getEntryPoint().getOffset()),
                            SourceType.USER_DEFINED)
                break

# 提取函数全部 XOR 常量
def extract_xor_constants(func):
    """找全部 XOR 操作及其立即数操作数。"""
    constants = []
    body = func.getBody()
    inst_iter = currentProgram.getListing().getInstructions(body, True)
    for inst in inst_iter:
        if inst.getMnemonicString() == "XOR":
            for i in range(inst.getNumOperands()):
                op = inst.getOpObjects(i)
                if op and hasattr(op[0], 'getValue'):
                    constants.append(int(op[0].getValue()))
    return constants

# 批量反编译搜模式
from ghidra.app.decompiler import DecompInterface
decomp = DecompInterface()
decomp.openProgram(currentProgram)

for func in fm.getFunctions(True):
    result = decomp.decompileFunction(func, 30, monitor)
    if result.depiledFunction():
        code = result.getDecompiledFunction().getC()
        if "strcmp" in code or "memcmp" in code:
            print(f"Comparison in {func.getName()} at {func.getEntryPoint()}")
```

---

## 补丁策略

### Binary Ninja 补丁（Python API）

```python
import binaryninja as bn

bv = bn.open_view("binary")

# NOP 指令
bv.write(0x401234, b"\x90" * 5)  # 5 字节 NOP

# Patch 条件跳转（JNZ → JZ）
bv.write(0x401234, b"\x74")  # 0x75 (JNZ) → 0x74 (JZ)

# 插恒真（mov eax, 1; ret）
bv.write(0x401234, b"\xb8\x01\x00\x00\x00\xc3")

bv.save("patched")
```

### LIEF（可执行格式插桩库）

```python
import lief

# 解析修改 ELF/PE/Mach-O
binary = lief.parse("binary")

# 加新节
section = lief.ELF.Section(".patch")
section.content = list(b"\xcc" * 0x100)
section.type = lief.ELF.SECTION_TYPES.PROGBITS
section.flags = lief.ELF.SECTION_FLAGS.EXECINSTR | lief.ELF.SECTION_FLAGS.ALLOC
binary.add(section)

# 改入口点
binary.header.entrypoint = 0x401000

# Hook 导入函数
binary.patch_pltgot("strcmp", 0x401000)

binary.write("patched")
```

**LIEF 优势：** 跨格式（ELF、PE、Mach-O）、Python API、可加节/段、改头、patch 导入。

---

## GDB 约束提取 + ILP/LP 求解器（BackdoorCTF 2017）

二进制强制输入字节间线性算术关系时，GDB 自动提取约束、ILP 求解器求解。

**技术：** 发位置编码输入（`input[i] = i`），比较触发时即知涉哪些位置、其和/差须为何值。记录比较日志收集全部约束，喂 PuLP 或 Gurobi。

```python
from pulp import *

n = 32  # flag 长度
prob = LpProblem("crackme", LpMinimize)
x = [LpVariable(f'x{i}', 32, 126, cat='Integer') for i in range(n)]
prob += 0  # 虚拟目标

# GDB 自动提取的约束（input[i]=i，监控比较）:
prob += x[3] + x[7] == 0xAB
prob += x[1] - x[5] == 0x0C
# ... 加全部提取约束 ...

# 约束为可打印 ASCII
for xi in x:
    prob += xi >= 32
    prob += xi <= 126

prob.solve(PULP_CBC_CMD(msg=0))
flag = ''.join(chr(int(value(xi))) for xi in x)
print("Flag:", flag)
```

**GDB 自动提取约束：**

```python
# GDB Python: input[i]=i 跑，记录每个 CMP 指令结果
import gdb

class CmpLogger(gdb.Breakpoint):
    def stop(self):
        frame = gdb.selected_frame()
        # 读比较值，经位置编码映射回输入索引
        return False
```

**要点：** 二进制强制输入字节间线性算术关系时，GDB 自动化提取约束后 ILP 求解器直接给满足赋值。

**References:** BackdoorCTF 2017

---

## GDB 位置编码输入 + 零标志监控（EKOPARTY 2017）

发 `input[i] = i`（位置编码）输入。单步二进制监控 CPU 零标志（ZF）。某位置的比较 ZF 置位即匹配——记下该位置的期望值。

```python
import gdb

# 脚本: 位置编码输入单步二进制, 看 ZF
class ZFMonitor(gdb.Breakpoint):
    def stop(self):
        zf = (int(gdb.parse_and_eval('$eflags')) >> 6) & 1
        if zf:
            rip = int(gdb.parse_and_eval('$rip'))
            # 反汇编 rip 附近找比较的立即数
            disasm = gdb.execute(f'x/1i {rip-5}', to_string=True)
            print(f"ZF set at {rip:#x}: {disasm.strip()}")
        return False

# 用输入 b'\x00\x01\x02\x03...\x1f' 跑一次
# 比较与位置自身值匹配时 ZF 触发 -> 那就是密钥字节
```

一次通过映射每个输入字节到所需值，免手工逆向。

**要点：** 位置编码输入（`input[i]=i`）配零标志监控一遍暴露完整密钥/密码——位置 i 的期望值等于 i 时零标志触发。

**References:** EKOPARTY CTF 2017

---

## LD_PRELOAD dump 仅执行二进制（BackdoorCTF 2017）

二进制只有执行权限（mode `--x`，无读位）。文件不可直接读、标准工具也读不了，但执行时内核仍把它映射进内存。

LD_PRELOAD 一个带构造函数的共享库，在进程内经 `/proc/self/mem` 读自身内存：

```c
// dump_xo.c — 编译: gcc -shared -fPIC -o dump_xo.so dump_xo.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

__attribute__((constructor)) void dump() {
    FILE *maps = fopen("/proc/self/maps", "r");
    char line[256];
    unsigned long base = 0, end = 0;

    // 找仅执行二进制的映射（r-xp 或 --xp）
    while (fgets(line, sizeof(line), maps)) {
        if (strstr(line, "binary_name")) {
            sscanf(line, "%lx-%lx", &base, &end);
            break;
        }
    }
    fclose(maps);

    FILE *mem = fopen("/proc/self/mem", "rb");
    fseek(mem, base, SEEK_SET);
    size_t size = end - base;
    void *buf = malloc(size);
    fread(buf, 1, size, mem);
    fclose(mem);

    FILE *out = fopen("/tmp/dumped_binary", "wb");
    fwrite(buf, 1, size, out);
    fclose(out);
}
// 用法: LD_PRELOAD=./dump_xo.so ./binary_xo
```

**要点：** 仅执行挡文件读取不挡执行。LD_PRELOAD 构造函数跑在进程内，`/proc/self/mem` 无视文件权限提供映射内存访问。

**References:** BackdoorCTF 2017
