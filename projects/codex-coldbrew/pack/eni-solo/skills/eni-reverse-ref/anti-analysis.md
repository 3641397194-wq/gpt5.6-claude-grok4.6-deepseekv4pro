# 反分析技术对抗与绕过参考

> 覆盖反调试、反虚拟机、反插桩与完整性自校验的系统性参考，每类都附可操作的绕过手段。与 [ollvm-deobfuscation.md](references/ollvm-deobfuscation.md) 相互补充。

## 目录

- [一、Linux 反调试](#一linux-反调试)
- [二、Windows 反调试](#二windows-反调试)
- [三、反虚拟机 / 反沙箱](#三反虚拟机--反沙箱)
- [四、反 DBI 插桩](#四反-dbi-插桩)
- [五、代码完整性自校验](#五代码完整性自校验)
- [六、反反汇编手法](#六反反汇编手法)
- [七、经典赛题案例](#七经典赛题案例)
- [八、绕过策略总表](#八绕过策略总表)

---

## 一、Linux 反调试

### 1. ptrace 自追踪（最常见）

```c
if (ptrace(PTRACE_TRACEME, 0, 0, 0) == -1) exit(1); // 已被追踪 = 有调试器
```

**四种绕过：**

```bash
# 方式 1：LD_PRELOAD 劫持（完整 hook 见 patterns.md）
LD_PRELOAD=./hook.so ./binary

# 方式 2：pwntools 直接 patch
python3 -c "
from pwn import *
elf = ELF('./binary', checksec=False)
elf.asm(elf.symbols.ptrace, 'xor eax, eax; ret')
elf.save('patched')
"

# 方式 3：GDB 捕获系统调用
gdb ./binary
(gdb) catch syscall ptrace
(gdb) run
# 停在 ptrace 时：
(gdb) set $rax = 0
(gdb) continue

# 方式 4：内核配置（需 root）
echo 0 > /proc/sys/kernel/yama/ptrace_scope
```

**双重 ptrace 模式：**

```c
// 父进程 fork 子进程去 ptrace 自己——占住唯一追踪位
pid_t child = fork();
if (child == 0) {
    ptrace(PTRACE_ATTACH, getppid(), 0, 0);
    // 子进程在 waitpid 循环里维持追踪关系
} else {
    // 父进程继续真实逻辑
}
```

**绕过：** 先杀掉看门狗子进程，再挂调试器。

### 2. /proc 文件系统检查

```c
// TracerPid 检查
FILE *f = fopen("/proc/self/status", "r");
// 找 "TracerPid:\t0"——非零即被调试

// /proc/self/exe 链接检查（部分调试器会改变它）
readlink("/proc/self/exe", buf, sizeof(buf));

// /proc/self/maps——查调试器相关库
grep("frida", "/proc/self/maps");
```

**绕过手段：**

```bash
# 1. LD_PRELOAD 伪造 fopen/fread 的 /proc 内容
# 2. 挂载命名空间隔离
unshare -m bash -c 'mount --bind /dev/null /proc/self/status && ./binary'

# 3. GDB：在 fopen 断下，改文件名参数
(gdb) b fopen
(gdb) run
(gdb) set {char[20]} $rdi = "/dev/null"
(gdb) continue
```

### 3. 时间差检测

```c
// rdtsc（CPU 时间戳计数器）
uint64_t start = __rdtsc();
// ... 被测代码 ...
uint64_t delta = __rdtsc() - start;
if (delta > THRESHOLD) exit(1);  // 太慢 = 有调试器

// clock_gettime
struct timespec ts1, ts2;
clock_gettime(CLOCK_MONOTONIC, &ts1);
// ... 被测代码 ...
clock_gettime(CLOCK_MONOTONIC, &ts2);

// gettimeofday
struct timeval tv1, tv2;
gettimeofday(&tv1, NULL);
```

**绕过手段：**

```bash
# 1. Frida hook（clock_gettime hook 见 tools-dynamic.md）

# 2. GDB：把 rdtsc 所在处 NOP 成常量
(gdb) set {unsigned char[2]} 0x401234 = {0x90, 0x90}  # NOP 掉 rdtsc

# 3. Pin 工具固定 TSC 读数
# 4. faketime 库
LD_PRELOAD=/usr/lib/faketime/libfaketime.so.1 FAKETIME="2024-01-01" ./binary
```

### 4. 信号类反调试

```c
// SIGTRAP 处理器——调试器会先于处理器截走 INT3
signal(SIGTRAP, handler);
__asm__("int3");
// handler 执行 = 无调试器；被调试器截获 = 正在被调

// SIGALRM 超时——分析太久就自杀
signal(SIGALRM, kill_handler);
alarm(5);

// SIGSEGV 处理器里藏真实逻辑（MBA 模式见 patterns.md）
signal(SIGSEGV, real_logic_handler);
*(int*)0 = 0;  // 故意崩溃 → 处理器执行真实代码
```

**绕过手段：**

```bash
# GDB：把信号放行给程序而不是截获
(gdb) handle SIGTRAP nostop pass
(gdb) handle SIGALRM ignore
(gdb) handle SIGSEGV nostop pass

# 针对 alarm：patch alarm() 立即返回
```

### 5. 系统调用级规避

```c
// 直接 syscall 绕开 libc——LD_PRELOAD hook 失效
long ret;
asm volatile("syscall" : "=a"(ret) : "a"(101), "D"(0), "S"(0), "d"(0), "r"(0));
// x86_64 上 101 = ptrace
```

**绕过：** 只能 patch 二进制本体，或在系统调用层拦截。

```bash
# GDB：捕获 syscall
(gdb) catch syscall 101
(gdb) commands
> set $rax = 0
> continue
> end
```

---

## 二、Windows 反调试

### 1. PEB 检查

```c
// BeingDebugged 标志（PEB 偏移 0x2）
bool debugged = NtCurrentPeb()->BeingDebugged;

// NtGlobalFlag（偏移 0x68/0xBC）
// 被调试时：FLG_HEAP_ENABLE_TAIL_CHECK | FLG_HEAP_ENABLE_FREE_CHECK | FLG_HEAP_VALIDATE_PARAMETERS = 0x70
DWORD flags = *(DWORD*)((BYTE*)NtCurrentPeb() + 0xBC); // 64 位偏移
if (flags & 0x70) exit(1);
```

**绕过（x64dbg）：**

```text
# ScyllaHide 插件自动修 PEB 字段
# 手动：dump PEB，清零 BeingDebugged 与 NtGlobalFlag
```

### 2. NtQueryInformationProcess

```c
// ProcessDebugPort（0x7）
DWORD_PTR debugPort = 0;
NtQueryInformationProcess(GetCurrentProcess(), 7, &debugPort, sizeof(debugPort), NULL);
if (debugPort != 0) exit(1);

// ProcessDebugObjectHandle（0x1E）
HANDLE debugObj = NULL;
NTSTATUS status = NtQueryInformationProcess(GetCurrentProcess(), 0x1E, &debugObj, sizeof(debugObj), NULL);
if (status == 0) exit(1); // STATUS_SUCCESS 即调试器在场

// ProcessDebugFlags（0x1F）——返回反值：0 = 有调试器
DWORD noDebug = 0;
NtQueryInformationProcess(GetCurrentProcess(), 0x1F, &noDebug, sizeof(noDebug), NULL);
if (noDebug == 0) exit(1);
```

**绕过：** Hook `NtQueryInformationProcess` 返回假值，或用 ScyllaHide。

### 3. 堆标志

```c
// 被调试时进程堆带调试标志
PHEAP heap = (PHEAP)GetProcessHeap();
// 64 位下 Flags 在偏移 0x70：正常应为 HEAP_GROWABLE (0x2)
// ForceFlags 在偏移 0x74：正常应为 0
if (heap->Flags != 0x2 || heap->ForceFlags != 0) exit(1);
```

### 4. TLS 回调

**要点：** TLS（Thread Local Storage）回调在 `main()` / 入口点**之前**执行。

```c
// 注册在 PE 头的 TLS 目录
void NTAPI TlsCallback(PVOID DllHandle, DWORD Reason, PVOID Reserved) {
    if (Reason == DLL_PROCESS_ATTACH) {
        if (IsDebuggerPresent()) {
            ExitProcess(1);  // main 还没跑就退出
        }
    }
}

#pragma comment(linker, "/INCLUDE:_tls_used")
#pragma data_seg(".CRT$XLB")
PIMAGE_TLS_CALLBACK callbacks[] = { TlsCallback, NULL };
```

**IDA/Ghidra 检测：** 查 PE TLS Directory → AddressOfCallBacks，其中列出的函数先于 EP 执行。

**绕过：** x64dbg 中在 TLS 回调下断（Options → Events → TLS Callbacks），或直接 patch TLS 目录项。

### 5. 硬件断点检测

```c
// 经 GetThreadContext 读调试寄存器
CONTEXT ctx;
ctx.ContextFlags = CONTEXT_DEBUG_REGISTERS;
GetThreadContext(GetCurrentThread(), &ctx);
if (ctx.Dr0 || ctx.Dr1 || ctx.Dr2 || ctx.Dr3) exit(1);

// 也可在异常处理器里查 DR 寄存器
```

**绕过：**

```bash
# x64dbg：改用软件断点，或 hook GetThreadContext
# Frida：hook GetThreadContext 把 DR 寄存器清零
```

### 6. 软件断点扫描（INT3）

```c
// 对代码段做 CRC / 哈希自检
unsigned char *code = (unsigned char*)function_addr;
uint32_t checksum = 0;
for (int i = 0; i < code_size; i++) {
    checksum += code[i];
    if (code[i] == 0xCC) exit(1);  // INT3 = 软件断点
}
if (checksum != EXPECTED_CHECKSUM) exit(1);
```

**绕过：** 改用硬件断点（DR0-DR3），或 hook 扫描函数。

### 7. 异常类反调试

```c
// UnhandledExceptionFilter——被调试时 filter 不会被调用
SetUnhandledExceptionFilter(handler);
RaiseException(EXCEPTION_ACCESS_VIOLATION, 0, 0, NULL);
// handler 执行 = 无调试器；被调试器接住 = 有调试器

// INT 2D——调试器单步异常
__asm { int 2dh }  // 调试器静默吞掉异常
// 执行继续 = 有调试器
```

### 8. NtSetInformationThread（线程隐藏）

```c
// 把线程从调试器视野中隐藏——此后该线程不再产生调试事件
typedef NTSTATUS(NTAPI *pNtSIT)(HANDLE, ULONG, PVOID, ULONG);
pNtSIT NtSIT = (pNtSIT)GetProcAddress(GetModuleHandle("ntdll"), "NtSetInformationThread");
NtSIT(GetCurrentThread(), 0x11 /*ThreadHideFromDebugger*/, NULL, 0);
// 之后调试器看不到该线程的断点与异常
```

**绕过：** Hook `NtSetInformationThread` 忽略 0x11 类请求，或 patch 该调用。

---

## 三、反虚拟机 / 反沙箱

### 1. CPUID Hypervisor 位

```c
int regs[4];
__cpuid(regs, 1);
if (regs[2] & (1 << 31)) {  // ECX bit 31 = hypervisor 在场
    exit(1);
}

// Hypervisor 品牌串
__cpuid(regs, 0x40000000);
char brand[13] = {0};
memcpy(brand, &regs[1], 12);
// "VMwareVMware", "Microsoft Hv", "KVMKVMKVM", "XenVMMXenVMM"
```

**绕过：** Patch `cpuid` 结果，或 `LD_PRELOAD` hook 包装函数。

### 2. MAC 地址 / 硬件指纹

```text
已知虚拟机 MAC 前缀：
  VMware:     00:0C:29, 00:50:56
  VirtualBox: 08:00:27
  Hyper-V:    00:15:5D
  Parallels:  00:1C:42
  QEMU:       52:54:00
```

### 3. 时间差虚拟机检测

```c
// 特权指令触发 VM exit，可测出明显慢
uint64_t start = __rdtsc();
__cpuid(regs, 0);  // 强制 VM exit
uint64_t delta = __rdtsc() - start;
if (delta > 500) { /* 大概率在 VM 里 */ }
```

### 4. 文件 / 注册表痕迹

```text
文件: C:\Windows\System32\drivers\vm*.sys, vbox*.dll, VBoxService.exe
注册表: HKLM\SOFTWARE\VMware, Inc.\VMware Tools
服务: VMTools, VBoxService
进程: vmtoolsd.exe, VBoxTray.exe, qemu-ga.exe
Linux: /sys/class/dmi/id/product_name 含 "VirtualBox"|"VMware"
       dmesg | grep -i "hypervisor detected"
```

### 5. 资源检测（CPU 数、内存、磁盘）

```c
// 沙箱通常资源寒酸
SYSTEM_INFO si;
GetSystemInfo(&si);
if (si.dwNumberOfProcessors < 2) exit(1);

MEMORYSTATUSEX ms;
ms.dwLength = sizeof(ms);
GlobalMemoryStatusEx(&ms);
if (ms.ullTotalPhys < 2ULL * 1024 * 1024 * 1024) exit(1); // < 2GB 内存

// 磁盘容量检查（< 60GB = 沙箱）
GetDiskFreeSpaceEx("C:\\", NULL, &total, NULL);
```

**绕过：** 配一台资源充足的虚拟机（4+ 核、8GB+ 内存、100GB+ 磁盘）。

---

## 四、反 DBI 插桩

### 1. Frida 检测

```c
// 手法 1：扫 /proc/self/maps 找 frida-agent
FILE *f = fopen("/proc/self/maps", "r");
while (fgets(line, sizeof(line), f)) {
    if (strstr(line, "frida") || strstr(line, "gadget")) exit(1);
}

// 手法 2：探测 Frida 默认端口（27042）
int sock = socket(AF_INET, SOCK_STREAM, 0);
struct sockaddr_in addr = {.sin_family=AF_INET, .sin_port=htons(27042), .sin_addr.s_addr=inet_addr("127.0.0.1")};
if (connect(sock, (struct sockaddr*)&addr, sizeof(addr)) == 0) exit(1);

// 手法 3：查 inline hook（函数序言被改）
// 对比 libc 函数头几个字节与期望值
unsigned char *strcmp_bytes = (unsigned char *)strcmp;
if (strcmp_bytes[0] == 0xE9 || strcmp_bytes[0] == 0xFF) exit(1); // JMP = 被 hook

// 手法 4：线程名检查
// Frida 会创建 "gmain", "gdbus", "frida-*" 命名的线程
DIR *dir = opendir("/proc/self/task");
while ((entry = readdir(dir))) {
    char comm_path[256];
    snprintf(comm_path, sizeof(comm_path), "/proc/self/task/%s/comm", entry->d_name);
    // 读 comm，查 "gmain", "gdbus"
}

// 手法 5：命名管道检测（Windows）
// Frida 创建 \\.\pipe\frida-* 命名管道
```

**用 Frida 反制 Frida 检测：**

```javascript
// 直接 hook 检测函数本身
Interceptor.attach(Module.findExportByName(null, "strstr"), {
    onEnter(args) {
        this.haystack = Memory.readUtf8String(args[0]);
        this.needle = Memory.readUtf8String(args[1]);
    },
    onLeave(retval) {
        if (this.needle && (this.needle.includes("frida") || this.needle.includes("gadget"))) {
            retval.replace(ptr(0)); // 未找到
        }
    }
});

// 提前加载 Frida（赶在反 DBI 之前）
// 用 frida-gadget 作为 early-init 共享库
```

### 2. Pin / DynamoRIO 检测

```c
// 查 /proc/self/maps 里的插桩库
// Pin: "pin-", "pinbin", "pinatrace"
// DynamoRIO: "dynamorio", "drcov", "drrun"

// 指令计数时间差——DBI 会带来额外开销
// 跑一段已知指令序列，对比执行时间
```

---

## 五、代码完整性自校验

```c
// .text 段 CRC32
uint32_t crc = compute_crc32(text_start, text_size);
if (crc != EXPECTED_CRC) exit(1);  // 代码被改（断点、patch）

// 函数体 MD5/SHA256
unsigned char hash[32];
SHA256(function_addr, function_size, hash);
if (memcmp(hash, expected_hash, 32) != 0) exit(1);
```

**五种绕过：**

1. **硬件断点**（不改代码，用 DR0-DR3）
2. **Patch 比较点**让它恒成立
3. **Hook 哈希函数**返回期望值
4. **模拟代替调试**（Unicorn/Qiling——零代码改动）
5. **快照 + 恢复：** 前后 dump 内存做 diff，定位校验点

**循环自校验（看门狗线程）：**

```c
// 独立线程持续校验完整性
void *watchdog(void *arg) {
    while (1) {
        if (compute_crc32(text_start, text_end - text_start) != saved_crc) {
            memset(flag_buffer, 0, flag_len);  // 毁掉 flag
            exit(1);
        }
        usleep(100000);
    }
}
```

**绕过：** 杀掉看门狗线程，或把它的 sleep patch 成无限。

---

## 六、反反汇编手法

### 1. 不透明谓词

```asm
; 条件恒同一方向，但看起来依赖数据
mov eax, [some_memory]
imul eax, eax          ; x^2
and eax, 1             ; 任意 x 的 x^2 mod 2 恒为 0
jnz fake_branch        ; 永不到达，但反汇编器不知道
; 真实代码
```

**识别：** 用 Z3/SMT 证明该分支恒真/恒假。

### 2. 垃圾字节 / 重叠指令

```asm
jmp real_code
db 0xE8           ; 线性反汇编器眼里是 CALL 开头
real_code:
mov eax, 1        ; 真实代码——反汇编器可能在此错位
```

**修复：** 切到图模式反汇编（Ghidra/IDA 处理得较好）。手动：从正确偏移 undefine 再重新分析。

### 3. 跳进指令中间

```asm
; 跳进一条多字节指令的中间
eb 01          ; jmp +1（跳过下一字节）
e8             ; 伪 CALL 操作码——反汇编器试图按 call 解码
90             ; 真实：NOP（jmp 落点）
```

### 4. 函数碎片 / 散置代码

函数被拆成不连续的块，靠无条件跳转连接。击穿线性函数边界检测。

**工具：** IDA 的 "Append function tail" 或 Ghidra 在每个块上 "Create function"。

### 5. 控制流平坦化（进阶）

> 完整 OLLVM 脱密工作流、变种生态（Hikari/Polaris/O-MVLL/Tigress/Hodur 等）与社区工具调研见 [ollvm-deobfuscation.md](references/ollvm-deobfuscation.md)。

基础的 switch-case 见 patterns.md；现代 OLLVM 变种还会叠加：

- **虚假控制流：** 用不透明谓词保护假分支
- **指令替换：** `a + b` → `a - (-b)`、`a ^ b` → `(a | b) & ~(a & b)`
- **字符串加密：** 运行时解密、用完即清

**现代变种（2026 社区活跃）：** Hikari（Anti Class Dump/String Encryption/Indirect Branch）、Polaris（原 Pluto，含 Trap Angr 专门坑 angr）、O-MVLL（Python 驱动，Android 加固常用）、Arkari（goron 基础，间接跳转可被数据段只读对抗）、amice（Rust，含 VM Flatten 需 VM 逆向而非 deflat）。变种识别详见 ollvm-deobfuscation.md 第 1 节。

**反混淆工具（按社区活跃度）：**

- **obpo-plugin**（629⭐，IDA microcode+concolic 云插件，效果最强）：https://github.com/obpo-project/obpo-plugin
- **ollvm-breaker**（441⭐，Binary Ninja，Android .so 实战）：https://github.com/amimo/ollvm-breaker
- **ollvm-unflattener**（265⭐，Miasm 符号执行，纯脚本 x86/x64）：https://github.com/cdong1012/ollvm-unflattener
- **d810-ng**（223⭐，IDA，集成 Z3，覆盖 OLLVM/Tigress/Hodur/Approov）：https://github.com/w00tzenheimer/d810-ng — **本地首选**
- **DeObfBR**（96⭐，BR 间接分支混淆专项）：https://github.com/Mrack/DeObfBR
- **D-810**（原版，已较少维护，建议用 d810-ng）：pattern-based deobfuscation, MBA simplification
- **Miasm**：符号执行反混淆
- **Arybo** / **SiMBA**：MBA 表达式化简

```bash
# d810-ng: 复制到 IDA plugins 目录, Ctrl-Shift-D 加载
# 选择 Unflattener + MBA simplification + Opaque predicate removal
# obpo: 右键 dispatcher → OBPO → Mark and process function (需联网)
# ⚠️ Pluto/Polaris 的 Trap Angr pass 会让 angr 失效 → 改用 d810-ng/Unicorn
```

### 6. 混合布尔算术（MBA）识别与化简

```python
# 常见 MBA 模式与化简目标：
# (x & y) + (x | y) == x + y
# (x ^ y) + 2*(x & y) == x + y
# (x | y) - (x & ~y) == y
# ~(~x & ~y) == x | y (德摩根)
# (x | y) & ~(x & y) == x ^ y

# SiMBA 自动化简：
# pip install simba-simplifier
from simba import simplify_mba
expr = "(a | b) + (a & b) - (~a & b)"
print(simplify_mba(expr))  # → a
```

---

## 七、经典赛题案例

### SIGILL 处理器做执行模式切换（Hack.lu 2015）

二进制可安装 SIGILL（非法指令）处理器，用于在 x86 与 x86-64 模式间切换，或实现自定义 opcode 分发：

1. **注册信号：** `signal(SIGILL, handler)` 挂上非法指令异常的回调
2. **模式切换：** 处理器改写被保存的指令指针或段寄存器，在 32 位与 64 位代码间横跳
3. **自定义 opcode：** 无效 x86 指令触发处理器，处理器把操作数字节解释为自定义 VM opcode

```c
// 信号处理器把"非法"指令解码成自定义 opcode
void sigill_handler(int sig, siginfo_t *info, void *ucontext) {
    ucontext_t *ctx = (ucontext_t *)ucontext;
    unsigned char *pc = (unsigned char *)ctx->uc_mcontext.gregs[REG_RIP];
    // 从 PC 处字节解码自定义 opcode
    // PC 前进过自定义指令长度
    ctx->uc_mcontext.gregs[REG_RIP] += opcode_length;
}
```

**要点：** 二进制若在执行早期注册了 SIGILL/SIGSEGV/SIGTRAP 处理器，就要怀疑自定义指令分发。用 `strace -e signal` 追踪信号投递，或 GDB 设 `handle SIGILL nostop pass`。

### SIGFPE 处理器 + strace 计数侧信道（PlaidCTF 2017）

二进制用 SIGFPE 信号处理器承载控制流，静态分析不可靠。通过 strace 数 SIGFPE 次数逐字符爆破——正确的输入字符触发更多信号。

```bash
# 每个候选字符数 SIGFPE 信号数
for c in {a..z} {A..Z} {0..9}; do
    count=$(echo -n "${c}AAAAAAA" | strace -e signal=SIGFPE ./binary 2>&1 | grep -c SIGFPE)
    echo "$c: $count"
done
# 产生最多 SIGFPE 的字符就是对的
# 逐位置重复，前缀逐步延长
```

**要点：** 信号处理器（SIGFPE、SIGSEGV、SIGILL）制造的隐式控制流对静态分析不可见。信号数与校验进度正相关——用 `strace -e signal=SIGFPE` 计数，把不透明的信号校验变成可测量的逐字符侧信道。

### 指令迹逆推：Keystone + Unicorn（MeePwn CTF 2017）

UPX 壳内对 flag 施加一串纯算术变换（sub、add、xor、rol、ror），无内存副作用。IDAPython 收集非跳转指令，序列求逆即得 flag。

**求逆规则：**

- 指令序列倒序（最后一条先执行）
- 逆操作对互换：`add ↔ sub`、`rol ↔ ror`、`xor` 自逆

```python
# IDAPython：收集混淆例程中的非跳转指令
import idaapi, idc

def trace_transforms(start_ea, end_ea):
    instructions = []
    ea = start_ea
    while ea < end_ea:
        mnem = idc.print_insn_mnem(ea)
        if mnem not in ('jmp', 'je', 'jne', 'call', 'ret'):
            instructions.append((ea, mnem, idc.print_operands(ea)))
        ea = idc.next_head(ea)
    return instructions

transforms = trace_transforms(0x401000, 0x401200)

# 求逆：倒序 + 交换 add/sub 与 rol/ror
inverse_map = {'add': 'sub', 'sub': 'add', 'rol': 'ror', 'ror': 'rol', 'xor': 'xor'}
inverted = [(mnem, op) for (_, mnem, op) in reversed(transforms)]
inverted = [(inverse_map.get(m, m), op) for m, op in inverted]
```

```python
# Keystone 汇编逆指令，Unicorn 模拟执行
from keystone import *
from unicorn import *
from unicorn.x86_const import *

ks = Ks(KS_ARCH_X86, KS_MODE_64)
uc = Uc(UC_ARCH_X86, UC_MODE_64)

asm_src = '\n'.join(f'{mnem} {op}' for mnem, op in inverted)
encoding, _ = ks.asm(asm_src)

CODE_BASE = 0x400000
uc.mem_map(CODE_BASE, 0x10000)
uc.mem_write(CODE_BASE, bytes(encoding))

# 初始寄存器置为观察到的输出值
uc.reg_write(UC_X86_REG_RAX, known_output)
uc.emu_start(CODE_BASE, CODE_BASE + len(encoding))
flag_bytes = uc.reg_read(UC_X86_REG_RAX).to_bytes(8, 'little')
```

**PEB 反调试注意：** 若二进制读 `PEB.BeingDebugged` 并在两个比较目标间二选一，IDAPython 迹到的可能是调试态目标。先 patch `BeingDebugged` 为 0 再迹，或两个分支都找出来用非调试态的目标值。

**要点：** 纯算术混淆（无内存写）可被完整求逆：迹指令、倒序、互换逆操作即可。PEB 反调试会悄悄改比较目标——永远核实走了哪个分支。

**References:** MeePwn CTF 2017

---

### 无 call 的函数链：栈帧操纵（THC CTF 2018）

**模式：** 二进制在栈上构建函数指针链表，改写保存的 RBP 与返回地址，让 `leave; ret` 逐级穿过链表，全程没有显式 `CALL`。IDA 因 push/pop 不平衡、函数边界无法判定而拒绝反编译。

链上每个函数：

1. 把操作数与下一个函数地址压栈
2. 把保存的 RBP 指向下一栈帧
3. 把返回地址写成下一个函数
4. `leave` 从 RBP 恢复 RSP（移向下一帧），`ret` 跳到下一个函数

```python
# 逆向出的处理链（每级经 leave/ret 传递）：
def reverse_processing(byte):
    res = byte | 0x80       # OR 0x80
    res = res ^ 0xCA        # XOR 0xCA
    res = (res + 66) & 0xFF # ADD 66
    res = res ^ 0xCA        # XOR 0xCA（重复）
    res = (res + 66) & 0xFF
    res = res ^ 0xCA
    res = (res + 66) & 0xFF
    res = res ^ 0xFE        # XOR 0xFE（收尾）
    return res
# 逆序应用，再反转字符序列
```

**要点：** 操纵保存 RBP 指向下一帧、保存 RIP 指向下一函数，`leave; ret` 就能无 `call` 串联函数。跟踪 call/ret 平衡的反汇编器无法划出函数边界。逐段手动 patch 函数体，IDA 才能接手。

**识别：** 大量以 `leave; ret` 收尾的小代码块却找不到对应 `call`。栈里函数指针与数据交错。IDA 报 "stack frame is too big" 或建不出函数。

**References:** THC CTF 2018

---

## 八、绕过策略总表

### 通用绕过清单

1. **清点全部反分析检查**——搜索：`ptrace`、`IsDebuggerPresent`、`rdtsc`、`cpuid`、`NtQuery`、`GetTickCount`、`CheckRemoteDebuggerPresent`、`/proc/self`、`SIGTRAP`、`alarm`
2. **静态 patch**——用 pwntools 或 Ghidra NOP/patch 检查点再运行
3. **LD_PRELOAD**（Linux）——hook libc 函数返回假值
4. **ScyllaHide**（Windows x64dbg）——自动修 PEB、hook NT 函数
5. **模拟执行**（Unicorn/Qiling）——不存在可被检测的调试器痕迹
6. **内核级绕过**——改 `/proc/sys/kernel/yama/ptrace_scope`，用 `prctl`

### 分层反调试（真实模式）

不少赛题把多个检查叠起来：

```text
1. TLS 回调 → IsDebuggerPresent（main 之前）
2. main() → ptrace(TRACEME)
3. 看门狗线程 → 时间检查 + /proc 扫描
4. 代码段 → CRC32 自校验
5. 信号处理器 → SIGSEGV 里藏真实逻辑
```

**打法：** 先找全所有检查再动手。逐个 patch 或 hook。检查太多就整体丢进模拟器跑。

### 检查项 → 绕过速查

| 反调试检查 | 平台 | 绕过 |
|---|---|---|
| `ptrace(TRACEME)` | Linux | `LD_PRELOAD`、patch 成 `ret 0`、`catch syscall` |
| `IsDebuggerPresent` | Windows | ScyllaHide、Frida hook、PEB patch |
| `NtQueryInformationProcess` | Windows | ScyllaHide、hook ntdll |
| `rdtsc` 计时 | 双平台 | NOP rdtsc、Frida 时间 hook、Pin |
| `/proc/self/status` | Linux | 挂载命名空间、hook fopen |
| `alarm(N)` | Linux | GDB `handle SIGALRM ignore` |
| `SIGTRAP` 处理器 | Linux | `handle SIGTRAP nostop pass` |
| `SIGFPE` 处理器侧信道 | Linux | `strace -e signal=SIGFPE` 按输入计数 |
| TLS 回调 | Windows | x64dbg 断 TLS、patch |
| DR 寄存器扫描 | Windows | 改用软件断点、hook GetThreadContext |
| INT3 扫描 / CRC | 双平台 | 硬件断点、patch CRC 比较 |
| Frida 检测 | 双平台 | 提前加载 gadget、hook strstr |
| CPUID hypervisor | 双平台 | Patch CPUID 结果、真机 |
| 线程隐藏 | Windows | Hook NtSetInformationThread |
