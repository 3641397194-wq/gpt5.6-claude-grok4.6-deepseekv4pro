# 逆向基础模式与技术

## 目录

- [自定义 VM 逆向](#自定义-vm-逆向)
- [反调试技术](#反调试技术)
- [Nanomites](#nanomites)
- [自修改代码](#自修改代码)
- [已知明文 XOR（flag 前缀）](#已知明文-xor)
- [混合模式（x86-64 / x86）Stager](#混合模式-stager)
- [LLVM 混淆（控制流平坦化）](#llvm-混淆)
- [S-Box / 密钥流生成](#s-box--密钥流生成)
- [SECCOMP/BPF 过滤器分析](#seccompbpf-过滤器分析)
- [异常处理器混淆](#异常处理器混淆)
- [内存转储分析](#内存转储分析)
- [逐字节均匀变换](#逐字节均匀变换)
- [x86-64 陷阱](#x86-64-陷阱)
- [自定义混淆函数逆向](#自定义混淆函数逆向)
- [位置相关变换逆向](#位置相关变换逆向)
- [Hex 编码字符串比较](#hex-编码字符串比较)
- [基于信号的二进制探索](#基于信号的二进制探索)
- [恶意样本反分析绕过（patch 法）](#恶意样本反分析绕过)
- [多级 shellcode loader](#多级-shellcode-loader)
- [时间侧信道攻击](#时间侧信道攻击)
- [多线程反调试：诱饵 + 信号处理器 MBA（ApoorvCTF 2026）](#多线程反调试)
- [INT3 补丁 + coredump 爆破 oracle（Pwn2Win 2016）](#int3-补丁--coredump-爆破-oracle)
- [信号处理器链 + LD_PRELOAD oracle（Nuit du Hack 2016）](#信号处理器链--ld_preload-oracle)
- [printf 格式串 VM 反编译到 Z3（SECCON 2017）](#printf-格式串-vm-反编译到-z3)

---

## 自定义 VM 逆向

### 分析步骤

1. 识别 VM 结构：寄存器、内存、指令指针
2. 逆向 `executeIns`/`runvm` 函数弄清 opcode 含义
3. 写反汇编器解析字节码
4. 反汇编出算法再理解

### 常见 VM 模式

```c
switch (opcode) {
    case 1: *R[op1] *= op2; break;      // MUL
    case 2: *R[op1] -= op2; break;      // SUB
    case 3: *R[op1] = ~*R[op1]; break;  // NOT
    case 4: *R[op1] ^= mem[op2]; break; // XOR
    case 5: *R[op1] = *R[op2]; break;   // MOV
    case 7: if (R0) IP += op1; break;   // JNZ
    case 8: putc(R0); break;            // PRINT
    case 10: R0 = getc(); break;        // INPUT
}
```

### RVA 式 opcode 分发

- opcode 是指向 handler 函数的 RVA
- handler 执行操作、读下一个 RVA、跳转
- 沿 RVA 链遍历映射全部 handler

### 状态机 VM（90K+ 状态）

```java
// BFS 找合法路径
var agenda = new ArrayDeque<State>();
agenda.add(new State(0, ""));
while (!agenda.isEmpty()) {
    var current = agenda.remove();
    if (current.path.length() == TARGET_LENGTH) {
        println(current.path);
        continue;
    }
    for (var transition : machine.get(current.state).entrySet()) {
        agenda.add(new State(transition.getValue(),
                            current.path + (char)transition.getKey()));
    }
}
```

**要点：** 题目附件里同时出现字节码 blob 与分发循环时，就是自定义 VM。先逆 opcode switch 表，再写反汇编器提升字节码，最后才尝试理解算法。

### 黑盒模糊测试发现指令集（hxp CTF 2017）

当分发循环的静态分析过于复杂时，用方法论式的黑盒方法逆未知 VM 字节码：

**第一步：确定指令对齐。** 把字节码按多种位宽（6-11 位）dump 成位串，找重复模式暗示 opcode 边界。

**第二步：随机字节模糊。** 发送单条指令观察寄存器/内存效应，映射 opcode。缩到最小程序：找产生每个可观察效应的最短输入。

**第三步：构建指令集。** 例——发现的变长 ISA（6-11 位）：

```text
000 xxxxxxxx  jmpz    001 xxxxxxxx  jmp     010 xxxxxxxx  call
011 xxxxxxxx  label   1000 xxxxxxx  loadram  1001 xxxxxxx  saveram
110 xxxxxxxx  loadi   11100 xxxxxx  shl      11101 xxxxxx  shr
111100 not    111101 and    111110 or    111111 setif
```

**第四步：写汇编器/反汇编器。** 工具化发现的 ISA，反汇编题目字节码理解算法。

**第五步：实现缺失原语。** ISA 缺运算就组合现有指令合成。例：只用 AND/OR/NOT 实现 XTEA 解密（无原生 XOR/ADD）：

```python
# AND/OR/NOT 合成 XOR:  XOR(a, b) = (a OR b) AND NOT(a AND b)
# 全加器链用 AND/OR/NOT 传播进位实现 ADD
def xor_from_primitives(a, b):
    return (a | b) & ~(a & b)

def add_from_primitives(a, b, bits=32):
    carry = 0
    result = 0
    for i in range(bits):
        ai = (a >> i) & 1
        bi = (b >> i) & 1
        sum_bit = xor_from_primitives(xor_from_primitives(ai, bi), carry)
        carry = (ai & bi) | (carry & xor_from_primitives(ai, bi))
        result |= (sum_bit << i)
    return result
```

**要点：** VM 分发循环静态分析太复杂时，黑盒模糊能更快映射 ISA。发送单条指令观察状态变化。变长指令集要试多种位宽。ISA 明确后，最小原语（AND/OR/NOT）也能实现复杂算法（XTEA）。

**References:** hxp CTF 2017

---

## 反调试技术

### 常见检查

- `IsDebuggerPresent()`（Windows）
- `ptrace(PTRACE_TRACEME)`（Linux）
- `/proc/self/status` TracerPid
- 时间检查（`rdtsc`、`time()`）
- 注册表检查（Windows）

### 绕过技术

1. 找调试检查后的 `test` 指令
2. 在 `test` 处下断点
3. 改寄存器绕过条件分支

```bash
# radare2 里
db 0x401234          # 断在 test
dc                   # 运行
dr eax=0             # 清标志
dc                   # 继续
```

### LD_PRELOAD Hook

```c
#define _GNU_SOURCE
#include <dlfcn.h>
#include <sys/ptrace.h>

long int ptrace(enum __ptrace_request req, ...) {
    long int (*orig)(enum __ptrace_request, pid_t, void*, void*);
    orig = dlsym(RTLD_NEXT, "ptrace");
    // 记录或改行为
    return orig(req, pid, addr, data);
}
```

编译：`gcc -shared -fPIC -ldl hook.c -o hook.so`
运行：`LD_PRELOAD=./hook.so ./binary`

**要点：** 反调试检查是多数逆向题的第一道障碍。在 `main()` 早段找 `ptrace`、`IsDebuggerPresent` 或时间检查，patch 或 hook 掉再深入分析。

### pwntools 二进制补丁（Crypto-Cat）

用 pwntools 直接 patch 掉反调试调用——把函数换成 `ret` 指令：

```python
from pwn import *

elf = ELF('./challenge', checksec=False)
elf.asm(elf.symbols.ptrace, 'ret')   # ptrace() 换成立即返回
elf.save('patched')                   # 保存补丁二进制
```

其他常用补丁：

```python
elf.asm(addr, 'nop')                  # NOP 掉一条指令
elf.asm(addr, 'xor eax, eax; ret')    # 返回 0（绕过检查）
elf.asm(addr, 'mov eax, 1; ret')      # 返回 1（强制成功）
```

---

## Nanomites

### Linux（基于信号）

- `SIGTRAP`（`int 3`）→ 自定义操作
- `SIGILL`（`ud2`）→ 自定义操作
- `SIGFPE`（`idiv 0`）→ 自定义操作
- `SIGSEGV`（空解引用）→ 自定义操作

### Windows（调试事件）

- `EXCEPTION_DEBUG_EVENT` → 主 handler
- 父进程经 `PTRACE_POKETEXT` 改子进程
- 魔法标记：`0x1337BABE`、`0xDEADC0DE`

### 分析

1. 查 `fork()` + `ptrace(PTRACE_TRACEME)`
2. 找 `WaitForDebugEvent` 循环
3. 把 EAX 值映射到操作
4. 记录操作重建算法

**要点：** Nanomites 把真实计算藏进信号/异常处理器，这些处理器只在调试器父进程下触发。二进制 fork 且子进程调 `ptrace(TRACEME)` 时，父进程才是真 CPU——记录它的 POKE 操作重建算法。

---

## 自修改代码

### 模式：XOR 解密

```asm
lea     rax, next_block
mov     dl, [rcx]        ; 输入字符
xor_loop:
    xor     [rax+rbx], dl
    inc     rbx
    cmp     rbx, BLOCK_SIZE
    jnz     xor_loop
jmp     rax              ; 执行解密后的代码
```

**解法：** 块首的已知操作码暴露 XOR 密钥（flag 字符）。

**要点：** 自修改代码用每个输入字符作密钥解密下一块。每块解密后的首字节若是已知操作码（如函数序言），即暴露正确密钥字节，逐字符恢复 flag。

---

## 已知明文 XOR（flag 前缀）

**模式：** 给密文；flag 格式已知（如 `0xL4ugh{`）。

**打法：**

1. 假设重复 XOR 密钥
2. 用已知前缀（与提示短语）恢复密钥字节
3. 试小密钥长度，验证输出可打印

```python
enc = bytes.fromhex("...")  # 密文
known = b"0xL4ugh{say_yes_to_me"
for klen in range(2, 33):
    key = bytearray(klen)
    ok = True
    for i, b in enumerate(known):
        if i >= len(enc):
            break
        ki = i % klen
        v = enc[i] ^ b
        if key[ki] != 0 and key[ki] != v:
            ok = False
            break
        key[ki] = v
    if not ok:
        continue
    pt = bytes(enc[i] ^ key[i % klen] for i in range(len(enc)))
    if all(32 <= c < 127 for c in pt):
        print(klen, key, pt)
```

**注意：** 题目提示语常原样出现在 flag 正文里（如 "say_yes_to_me"）。

### 变体：带位置索引的 XOR

**模式：** `cipher[i] = plain[i] ^ key[i % k] ^ i`（或 `^ (i & 0xff)`）。

**症状：**

- 重复密钥 XOR 几乎匹配已知前缀，但靠后位置断裂
- 已知前缀 XOR 出的"密钥"逐位 +1 漂移

**修法：** 先剥索引，再用已知前缀恢复密钥。

```python
enc = bytes.fromhex("...")
known = b"0xL4ugh{say_yes_to_me"
for klen in range(2, 33):
    key = bytearray(klen)
    ok = True
    for i, b in enumerate(known):
        if i >= len(enc):
            break
        ki = i % klen
        v = (enc[i] ^ i) ^ b  # 剥掉索引 XOR
        if key[ki] != 0 and key[ki] != v:
            ok = False
            break
        key[ki] = v
    if not ok:
        continue
    pt = bytes((enc[i] ^ i) ^ key[i % klen] for i in range(len(enc)))
    if all(32 <= c < 127 for c in pt):
        print(klen, key, pt)
```

---

## 混合模式（x86-64 / x86）Stager

**模式：** 64 位 ELF 经远返回（`retf`/`retfq`）跳进 32 位 blob，常在反调试之后。

**识别：**

- 字节 `0xCB`（retf）或 `0xCA`（retf imm16），有时前缀 `0x48`（retfq）
- 32 位反汇编显示紧凑循环里的 SSE 操作（`psubb`、`pxor`、`paddb`）
- 计算跳转进 32 位区域

**陷阱：**

- `retf` 弹 **6 字节**：4 字节 EIP + 2 字节 CS（不是 8）
- 32 位 blob 可能依赖继承的 **XMM 状态**与 **EFLAGS**
- 模拟器切换时丢 XMM/标志传递 → 输出错误

**绕过/模拟提示：**

1. 建 UC_MODE_32 模拟器，拷贝内存 + GPR + **EFLAGS** + **XMM 寄存器**
2. 跑 32 位块，再把内存 + 寄存器拷回 64 位
3. 反调试用 fork/ptrace + patch 时，模拟父进程记录 POKE 并在子进程应用

---

## LLVM 混淆（控制流平坦化）

### 模式

```c
while (1) {
    if (i == 0xA57D3848) { /* 块 */ }
    if (i != 0xA5AA2438) break;
    i = 0x39ABA8E6;  // 下一状态
}
```

### 反混淆

1. GDB 脚本断在 `je` 指令
2. 记录状态变量值
3. 映射状态转移
4. 重建真实控制流

**要点：** 平坦化把结构化 if/else/循环替换成单一分发 switch。状态变量是关键——运行时迹它的值即可重建原始控制流图，不必静态硬刚混淆。

---

## S-Box / 密钥流生成

### Fisher-Yates 洗牌（Xorshift32）

```python
def gen_sbox():
    sbox = list(range(256))
    state = SEED
    for i in range(255, -1, -1):
        state = ((state << 13) ^ state) & 0xffffffff
        state = ((state >> 17) ^ state) & 0xffffffff
        state = ((state << 5) ^ state) & 0xffffffff
        j = state % (i + 1) if i > 0 else 0
        sbox[i], sbox[j] = sbox[j], sbox[i]
    return sbox
```

### Xorshift64* 密钥流

```python
def gen_keystream():
    ks = []
    state = SEED_64
    mul = 0x2545f4914f6cdd1d
    for _ in range(256):
        state ^= (state >> 12)
        state ^= (state << 25)
        state ^= (state >> 27)
        state = (state * mul) & 0xffffffffffffffff
        ks.append((state >> 56) & 0xff)
    return ks
```

### 识别模式

- Xorshift32：移位 13、17、5（无乘法常量）
- Xorshift64*：移位 12、25、27，再乘 `0x2545f4914f6cdd1d`
- 其他常见常量：`0x9e3779b97f4a7c15`（黄金比例）

**要点：** S-box 生成识别靠 Fisher-Yates 洗牌模式（从 255 倒数的循环、与 PRNG 选出的下标交换）；密钥流识别靠 xorshift 常量。PRNG 家族一旦锁定，算法就完全由种子决定。

---

## SECCOMP/BPF 过滤器分析

```bash
seccomp-tools dump ./binary
```

### BPF 分析

- `A = sys_number` 后跟比较
- `mem[N] = A`、`A = mem[N]` 做内存操作
- 映射成约束方程，用 z3 求解

```python
from z3 import *
flag = [BitVec(f'c{i}', 32) for i in range(14)]
s = Solver()
s.add(flag[0] >= 0x20, flag[0] < 0x7f)
# 从过滤器加约束
if s.check() == sat:
    m = s.model()
    print(''.join(chr(m[c].as_long()) for c in flag))
```

**要点：** SECCOMP（Secure Computing Mode）过滤器把 flag 校验编码成操作 syscall 参数的 BPF 字节码。`seccomp-tools` dump 过滤器，把比较与内存操作翻译成 z3 约束，不运行二进制直接求解。

---

## 异常处理器混淆

### RtlInstallFunctionTableCallback

- 动态注册异常处理器
- handler 安装新 handler、改代码
- 用 x64dbg 断异常处理器

### 向量化异常处理器（VEH）

- `AddVectoredExceptionHandler` 安装 handler
- handler 解密异常地址处的代码
- 单步穿过，dump 解密代码

**要点：** 基于异常处理器的混淆把真实控制流藏进 SEH/VEH handler，靠故意故障触发。断点设在异常处理器里而不是故障指令上，才能跟到真实执行路径。

---

## 内存转储分析

### 二进制何时 dump 内存

- 查 `/proc/self/maps` 读取
- 查 `/proc/self/mem` 读取
- 堆数据常追加进 dump

### 已知明文攻击

```python
prologue = bytes([0xf3, 0x0f, 0x1e, 0xfa, 0x55, 0x48, 0x89, 0xe5])
encrypted = data[func_offset:func_offset+8]
partial_key = bytes(a ^ b for a, b in zip(encrypted, prologue))
```

**要点：** 二进制读 `/proc/self/mem` 或 `/proc/self/maps` 时，它在 dump 自身内存——可能已加密。用已知函数序言（`endbr64; push rbp; mov rbp, rsp`）作已知明文，从加密 dump 恢复 XOR 密钥。

---

## 逐字节均匀变换

**模式：** 输出缓冲区的每个字节独立依赖对应输入字节（无跨字节耦合）。

**检测：**

- 改一个输入位置 → 只有一个输出位置变化
- 输入填单一字节 → 输出缓冲变常量

**解法：**

1. 对每个字节值 0..255，用该字节重复填充运行程序
2. 记录输出字节 → 建映射与逆映射
3. 逆映射作用于静态目标字节 → 恢复 flag

---

## x86-64 陷阱

### 符号扩展

```python
esi = 0xffffffc7  # 不是 -57

# XOR 时：只用低字节
esi_xor = esi & 0xff  # 0xc7

# 加法时：全 32 位带溢出
r12 = (r13 + esi) & 0xffffffff
```

### 循环边界状态更新

汇编常把状态更新劈在循环边界两侧：

```asm
    jmp loop_middle        ; 第一次迭代从中间进！

loop_top:                   ; 迭代 2+ 的状态
    mov  r13, sbox[a & 0xf]
    ; 用旧 a，不是新的！

loop_middle:
    ; 主计算
    inc  a
    jne  loop_top
```

**要点：** 反编译器常把 x86-64 符号扩展与循环边界状态更新搞错。凡涉及 `movsx`/`cdqe` 的操作，以及循环变量在每次迭代中使用前还是使用后更新，永远拿反编译输出与原汇编核对。

---

## 自定义混淆函数逆向

**模式（Flag Appraisal）：** 二进制按 2 字节一组、带中间状态混淆输入，与静态目标比较。

**打法：**

1. 从 `.rodata` 提取静态目标字节
2. 理解混淆：带运行态逐对处理
3. 写逆函数（倒序处理、逐操作撤销）
4. 目标字节喂进逆函数 → 恢复 flag

**要点：** 二进制成对混淆输入、与静态目标比较时，从 `.rodata` 取目标写逆函数。目标字节倒序处理、逐操作撤销，恢复原始输入。

---

## 位置相关变换逆向

**模式（PascalCTF 2026）：** 二进制按位置索引加减变换输入。

**逆向：**

```python
expected = [...]  # 从 .rodata 提取
flag = ''
for i, b in enumerate(expected):
    if i % 2 == 0:
        flag += chr(b - i)   # 偶数位: 输入 = 输出 - i
    else:
        flag += chr(b + i)   # 奇数位: 输入 = 输出 + i
```

---

## Hex 编码字符串比较

**模式（Spider's Curse）：** 输入转 hex，与 hex 常量比较。

**快速解法：** 从 strings/Ghidra 提取 hex 常量，解码：

```bash
echo "4d65746143..." | xxd -r -p
```

---

## 基于信号的二进制探索

**模式（Signal Signal Little Star）：** 二进制把 UNIX 信号当二叉树导航机制。

**识别：**

- 多个带 `SA_SIGINFO` 的 `sigaction()` 调用
- `sigaltstack()` 设置（备用信号栈）
- handler 解码内嵌 payload，安装下一对信号
- 两种类型：Node（安装子节点）与 Leaf（打印消息后退出）

**解法：**

1. `LD_PRELOAD` hook `sigaction` 记录信号安装
2. 发信号对二叉树做 DFS
3. 每阶段观察安装了哪 2 个信号
4. 发一个，看程序退出（叶）还是再装 2 个（节点）
5. 走错叶就回溯试兄弟

```c
// LD_PRELOAD 拦截记录 sigaction 调用
int sigaction(int signum, const struct sigaction *act, ...) {
    if (act && (act->sa_flags & SA_SIGINFO))
        log("SET %d SA_SIGINFO=1\n", signum);
    return real_sigaction(signum, act, oldact);
}
```

---

## 恶意样本反分析绕过（patch 法）

**模式（Carrot）：** 恶意软件执行 payload 前有多道环境检查。

**常见检查与补丁：**

| 检查 | 技术 | 补丁 |
|-------|-----------|-------|
| `ptrace(PTRACE_TRACEME)` | 反调试 | `cmp -1` 改 `cmp 0` |
| `sleep(150)` | 反沙箱计时 | sleep 值改 1 |
| `/proc/cpuinfo` "hypervisor" | 反 VM | `JNZ` 翻 `JZ` |
| "VMware"/"VirtualBox" 字符串 | 反 VM | `JNZ` 翻 `JZ` |
| `getpwuid` 用户名检查 | 环境 | 翻转比较 |
| `LD_PRELOAD` 检查 | 反 hook | 跳过检查 |
| 风扇数 / 硬件检查 | 反 VM | `JLE` 翻 `JGE` |
| 主机名检查 | 环境 | `JNZ` 翻 `JZ` |

**Ghidra 补丁工作流：**

1. 找检查函数，识别条件跳转
2. 点指令 → `Ctrl+Shift+G` → 改操作码
3. `JNZ`（0x75）→ `JZ`（0x74），反之亦然
4. 立即数：直接改操作数字节
5. 导出：按 `O` → 选 "Original File" 格式
6. `chmod +x` 补丁二进制

**服务端校验绕过：**

- 补丁二进制给远程发系统信息时，把数据也 patch 掉
- 改数据收集函数里的字符串地址
- 改格式串直接嵌正确值

---

## 多级 shellcode loader

**模式（I Heard You Liked Loaders）：** 嵌套 shellcode 带 XOR 解码循环与反调试。

**调试工作流：**

1. 断在 launcher 的 `call rax`，步进 shellcode
2. 绕 ptrace 反调试：步到 syscall，`set $rax=0`
3. 步过 XOR 解码循环（或断在隐藏的 `int3`）
4. 每级重复直到最终 payload

**从 `mov` 指令提取 flag：**

```python
# 末级经 mov ebx, value 每次载 4 字节 flag
# 提取小端 4 字节块
values = [0x6174654d, 0x7b465443, ...]  # 来自反汇编
flag = b''.join(v.to_bytes(4, 'little') for v in values)
```

---

## 时间侧信道攻击

**模式（Clock Out）：** 校验耗时随正确字符变长（匹配时睡更久）。

**利用：**

```python
import time
from pwn import *

flag = ""
for pos in range(flag_length):
    best_char, best_time = '', 0
    for c in string.printable:
        io = remote(host, port)
        start = time.time()
        io.sendline((flag + c).ljust(total_len, 'X'))
        io.recvall()
        elapsed = time.time() - start
        if elapsed > best_time:
            best_time = elapsed
            best_char = c
        io.close()
    flag += best_char
```

---

## 多线程反调试：诱饵 + 信号处理器 MBA（ApoorvCTF 2026）

**模式（A Golden Experience Requiem）：** 分层反分析的多线程二进制：线程 1 做诱饵操作（假 AES + `ud2` 故意崩溃），线程 2 在 SIGSEGV 信号处理器里用混合布尔算术（MBA）做真实 flag 计算，线程 3 擦内存防事后分析。

**线程布局：**

| 线程 | 用途 | 陷阱 |
|--------|---------|------|
| 线程 1 | 诱饵：类 AES 操作 → `ud2` 崩溃 | 分析员浪费时间逆假加密 |
| 线程 2 | 真实 flag：SIGSEGV 处理器 + MBA 变换 | 藏在信号处理器里，不在主代码路径 |
| 线程 3 | 内存擦除：算完清零 flag 数据 | 防内存转储 |
| Main | rdtsc 反调试计时检查 | 惩罚挂调试器的执行 |

**解法——纯 Python 模拟 MBA 逻辑：**

```python
# MBA 辅助函数（从汇编提取）
def mba_add(a, b): return (a + b) & 0xff
def mba_xor(a, b): return (a ^ b) & 0xff

def mba_transform(i):
    """信号处理器里位置相关的变换。"""
    val = (i * 7 + 0x3f) & 0xff
    rotated = ((i << 3) | (i >> 5)) & 0xff
    return mba_xor(val, rotated)

# S-box（挪用的 SHA-256 初始哈希值）
SBOX = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
        0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]

def sbox_lookup(i):
    idx = i & 7
    shift = ((i >> 3) & 3) * 8
    return (SBOX[idx] >> shift) & 0xff

# 两个交错的 rodata 数组（偶下标 → array1，奇 → array2）
rodata1 = bytes.fromhex("39407691b717c97879013adf3a2adea11c2b04e0")
rodata2 = bytes.fromhex("bb19b025e37eaa786c4116e7aeea00c9c623940d")

flag = []
for i in range(40):  # flag 长度
    t = mba_transform(i)
    s = sbox_lookup(i)
    mem = rodata1[i // 2] if i % 2 == 0 else rodata2[i // 2]
    flag.append(chr(t ^ s ^ mem))

print(''.join(flag))
```

**要点：** 真实 flag 逻辑在信号处理器（SIGSEGV/SIGILL）里，不在主线程。线程 1 的类 AES 代码与 `ud2` 崩溃是刻意的误导。`rdtsc` 计时检查检测调试器并破坏输出。绕过：从汇编提取 MBA 逻辑用 Python 重实现——绝不在调试器下运行二进制。

**识别指标：**

- 多个 `pthread_create` 带不同 handler 函数
- `signal(SIGSEGV, handler)` 或 `sigaction` 设置
- `ud2` 指令（故意非法指令）
- `rdtsc` 指令做计时检查
- SHA-256 常量（0x6a09e667...）被当查找表而非哈希

---

## INT3 补丁 + coredump 爆破 oracle（Pwn2Win 2016）

不逆复杂变换逻辑，而是在变换输出后 patch 一个 `0xCC`（INT3）字节，开 core dump，逐字符爆破——每次运行后从 coredump 用 `strings` 提取变换结果。

```bash
# 变换输出点 patch 0xCC
printf '\xcc' | dd of=binary bs=1 seek=$((0x400ebb)) conv=notrunc
ulimit -c unlimited
# 逐位置爆破：
for c in $(seq 32 126); do
    echo -ne "$(printf '\\x%02x' $c)$known_suffix" | ./binary 2>/dev/null
    strings core | grep -q "$expected" && echo "Found: $c"
done
```

**要点：** 用 INT3/SIGTRAP 当断点 oracle——coredump 捕获崩溃点的计算状态。免去完整逆向变换。

---

## 信号处理器链 + LD_PRELOAD oracle（Nuit du Hack 2016）

二进制用 Unix 信号做控制流：`main()` 给自己发 1024 次 SIGINT，每个 handler 检查一个密码字符，然后调 `signal()` 安装下一个 handler。绕过：LD_PRELOAD 自定义 `signal()`，被调用即记录（说明当前字符正确），逐位置爆破。

```c
// LD_PRELOAD 库：
#include <signal.h>
sighandler_t signal(int sig, sighandler_t handler) {
    write(2, "CORRECT\n", 8);  // signal() 被调 = 字符正确
    return SIG_DFL;
}
```

**要点：** 信号处理器链反逆向可用 LD_PRELOAD hook `signal()` 击败。`signal()` 的调用（安装下一个 handler）本身就是确认当前字符的侧信道。

---

## printf 格式串 VM 反编译到 Z3（SECCON 2017）

完全用 `%hhn` 格式串实现的"虚拟机"。`%hhn` 把已打印字符数（mod 256）写到指向的字节。一串 `%Nc%hhn` 指令实现任意字节写内存，等效字节码 VM。

**第一步：识别指令类型。** 统计唯一格式模式确定指令集：

```bash
# 数字归一化后统计唯一模式
sed -e 's/[[:digit:]]\+/1/g' program.fs | sort | uniq -c | sort -nr
```

**第二步：写反编译器。** 格式模式转 C 风格伪代码。每个 `%N...%hhn` 对映射为内存写：提取写地址（参数指针）与值（字符计数）。

**第三步：识别算法。** 伪代码通常揭示字节上的线性方程组。内存地址映射到符号变量。

**第四步：生成 Z3 约束求解。**

```python
from z3 import *

flag_len = 32  # 按反编译输出调整
flag = [BitVec(f'f{i}', 8) for i in range(flag_len)]
s = Solver()

# 约束为可打印 ASCII
for f in flag:
    s.add(f >= 0x20, f <= 0x7e)

# 加反编译出的格式串操作约束
# 如 flag[3] + flag[7] == 0xAB (mod 256)
# 来自写序列：每个 %hhn 累积字符计数、把结果写到目标字节
s.add((flag[0] + flag[1]) & 0xFF == 0x9A)  # 例约束
s.add((flag[2] ^ flag[3]) & 0xFF == 0x3F)  # 例约束
# ...（加全部反编译约束）

if s.check() == sat:
    m = s.model()
    print(bytes([m[f].as_long() for f in flag]))
```

**反编译细化：**

1. 从每个 `%N...%hhn` 对提取写地址与值
2. 内存地址映射到符号变量（flag 字节）
3. 从写序列建方程组
4. Z3 求解

**要点：** 格式串 `%hhn` 把已打印字符数（mod 256）写到指向字节。`%Nc%hhn` 指令序列实现任意字节写内存，等效字节码 VM。反编译：(1) 从每个 `%N...%hhn` 对提取写地址与值，(2) 内存地址映射到符号变量，(3) 写序列建方程组，(4) Z3 求解。

**References:** SECCON 2017
