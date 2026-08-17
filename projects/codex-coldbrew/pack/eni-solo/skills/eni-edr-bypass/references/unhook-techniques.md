# 用户态 Hook 对抗技术清单

> 仅文档：本文是方法论参考，不含可执行脚本。

本文盘点当前主流的"绕过用户态 hook"手段，从最经典的 fresh ntdll 到硬件断点 Blindside，按演进顺序排列。全部技术对照 MITRE ATT&CK T1562.001 / T1027 / T1055，便于报告引用。

## 1. Fresh Ntdll：从磁盘重映射

### 原理

EDR 的 hook 全部写进**当前进程内存里的 ntdll.dll**。磁盘上 `C:\Windows\System32\ntdll.dll` 始终是干净的。把磁盘副本重新映射进进程、覆盖内存中的 `.text` 段，hook 即被抹掉。

```text
当前进程 ntdll.dll
  ┌─────────────────────────┐
  │ .text (含 EDR hook jmp) │ ◄── 用磁盘干净 .text 覆盖
  └─────────────────────────┘
        ▲
        │ NtMapViewOfSection(disk_ntdll)
        │
  磁盘 C:\Windows\System32\ntdll.dll  ← 干净
```

### 实现要点

```c
// 1. CreateFileW("\\Device\\HarddiskVolumeX\\Windows\\System32\\ntdll.dll")  // 原生路径绕监控
// 2. NtCreateSection (SEC_IMAGE)
// 3. NtMapViewOfSection 映射到新地址
// 4. 定位新地址的 .text 段
// 5. NtProtectVirtualMemory 把当前 ntdll .text 改为 RW
// 6. memcpy 覆盖
// 7. NtProtectVirtualMemory 还原为 RX
```

### 三个注意点

- `NtProtectVirtualMemory` 本身可能被 hook，形成链式问题——先用直接 syscall 调它
- 现代 EDR 会监控对 ntdll 内存的 W 操作，需配合 ETW patch
- fresh ntdll 会留下 `KERNEL_MODULE_LOAD`、`PROTECTVM` 事件，必须先压 ETW 再动手

## 2. 直接 syscall

### 原理

不调用 ntdll 导出函数，自己实现 syscall stub：

```asm
NtAllocateVirtualMemory:
    mov r10, rcx
    mov eax, 0x18      ; SSN（随 Windows 版本变化）
    syscall
    ret
```

`syscall` 指令从用户态直入内核 SSDT，天然跳过用户态 hook。

### SysWhispers3 用法

```powershell
git clone https://github.com/klezVirus/SysWhispers3
cd SysWhispers3
python3 syswhispers.py --preset all --action edit -o syscalls
```

产物：

```text
syscalls.h
syscalls.c
syscalls.asm
syscallsstubs.std.x64.asm
```

Visual Studio 集成：

```text
1. .asm 加入工程，启用 MASM (Custom Build Tool)
2. include syscalls.h
3. 用 Sw3NtAllocateVirtualMemory(...) 替换原调用
```

### 最小示例：直接 syscall 调 NtCreateFile

```c
#include <windows.h>
#include "syscalls.h"

int main(void) {
    HANDLE hFile = NULL;
    OBJECT_ATTRIBUTES oa;
    UNICODE_STRING uName;
    IO_STATUS_BLOCK iosb;
    WCHAR path[] = L"\\??\\C:\\Windows\\Temp\\edr_test.bin";

    uName.Buffer = path;
    uName.Length = (USHORT)(wcslen(path) * sizeof(WCHAR));
    uName.MaximumLength = uName.Length + sizeof(WCHAR);

    InitializeObjectAttributes(&oa, &uName, OBJ_CASE_INSENSITIVE, NULL, NULL);

    NTSTATUS st = Sw3NtCreateFile(
        &hFile,
        FILE_GENERIC_WRITE,
        &oa,
        &iosb,
        NULL,
        FILE_ATTRIBUTE_NORMAL,
        0,
        FILE_OVERWRITE_IF,
        FILE_SYNCHRONOUS_IO_NONALERT,
        NULL,
        0
    );

    if (st >= 0) {
        Sw3NtClose(hFile);
        return 0;
    }
    return (int)st;
}
```

### 短板

syscall 指令落在 implant 自己的 `.text` 段（不在 ntdll 内）→ 内核侧遥测容易发现 "syscall from non-ntdll address"。这正是间接 syscall 的由来。

## 3. 间接 syscall

### 原理

syscall 指令仍借用 ntdll 内的合法地址，只由我们自己控制 SSN 与返回地址：

```text
implant 代码：
    mov r10, rcx
    mov eax, <SSN>
    jmp [<ntdll 中某 syscall;ret gadget 地址>]
```

跳转目标通常是某个 `Nt*` 函数末尾的 `syscall; ret` 两字节。内核 ETW provider 看到的 RIP 位于 ntdll，符合合法行为模式。

### SysWhispers3 生成

```powershell
python3 syswhispers.py --preset all --action edit --mode jumper -o syscalls
# --mode jumper            => 间接 syscall
# --mode jumper_randomized => 随机化 jmp 目标，降低签名风险
```

stub 形态：

```asm
Sw3NtAllocateVirtualMemory PROC
    mov [rsp+8], rcx
    ...
    mov ecx, 0x18                  ; function hash
    call Sw3GetSyscallNumber       ; 返回 SSN -> eax
    call Sw3GetSyscallAddress      ; 返回 ntdll 内 syscall;ret 地址 -> rbx
    ...
    mov r10, rcx
    jmp rbx
Sw3NtAllocateVirtualMemory ENDP
```

## 4. Hell's Gate / Halo's Gate / Tartarus Gate

三者解决同一个问题的演进：SSN 动态解析。

### Hell's Gate

- 前提假设：ntdll 未被 hook
- 启动时遍历 ntdll 的 `Nt*` 导出，从前 4 字节 `mov eax, <SSN>` 提取 SSN
- 优点：不写死 SSN，跨版本通用
- 缺点：ntdll 已被 hook（首字节变 jmp）时提取失败

### Halo's Gate

- 修复 Hell's Gate 的 hook 问题
- 发现某函数被 hook 时，向上 / 向下扫描相邻 ±N 个函数
- 利用 ntdll 中 `Nt*` 函数 SSN 连续递增的规律，从邻居反推被 hook 函数的 SSN

```text
NtAllocateVirtualMemory   SSN = 0x18
NtQueryInformationProcess SSN = 0x19
NtProtectVirtualMemory    SSN = 0x50

若 NtAllocateVirtualMemory 被 hook 读不到 SSN：
  上一邻居 = 0x17，下一邻居 = 0x19
  → 目标 SSN = 0x18
```

### Tartarus Gate

- 应对"hook 改了 SSN 但保留 syscall 指令"的高级 hook
- 同时校验 SSN 与 syscall;ret gadget 地址
- 三者叠加构成最稳的间接 syscall 底座

### 参考实现

```text
Hell's Gate:    am0nsec/HellsGate
Halo's Gate:    am0nsec/HellsGate (fallback 逻辑) / SafeBreach-Labs/HalosGate-PoC
Tartarus Gate:  trickster0/TartarusGate
SysWhispers3:   三者均已集成
```

## 5. 硬件断点 Blindside

### 原理

用调试寄存器 `DR0-DR3` 在 EDR hook trampoline 入口设硬件断点；VEH 在断点命中时把 RIP 直接改到 trampoline 之后，落到 ntdll 真正的 syscall 段。

### 优势

- 不写 ntdll 内存（无 `NtProtectVirtualMemory` 告警）
- 不 unhook（hook 原样保留，只是被绕过）
- ETW-TI 看不到内存修改

### 骨架

```c
LONG CALLBACK Blindside(EXCEPTION_POINTERS* ep) {
    if (ep->ExceptionRecord->ExceptionCode == EXCEPTION_SINGLE_STEP) {
        DWORD64 rip = ep->ContextRecord->Rip;
        if (rip == g_hookedNtAllocVM) {
            // SSN 已在 eax；R10 = RCX；跳到 ntdll 的 syscall;ret
            ep->ContextRecord->Rip = (DWORD64)g_syscallGadget;
            return EXCEPTION_CONTINUE_EXECUTION;
        }
    }
    return EXCEPTION_CONTINUE_SEARCH;
}

// 1. AddVectoredExceptionHandler
// 2. 每个被 hook 函数入口设 DR0..DR3（最多 4 个，配合 single-step rotate）
// 3. SetThreadContext 写入 DRx
// 4. 断点命中 → VEH 接管 → 改写 RIP
```

### 限制

- DRx 是线程私有的，多线程要分别设置
- 部分 EDR 会 hook `NtSetContextThread` / `NtGetContextThread`，需先绕开
- Win11 22H2+ 的 HVCI 与反调试缓解可能干扰

## 6. Call Stack Spoofing

### 问题

现代 EDR 在 `NtAllocateVirtualMemory` / `NtCreateThreadEx` 等 syscall 内核入口调用 `RtlCaptureStackBackTrace` 上报完整调用栈。implant 的栈帧来自 **non-image-backed memory** → 高置信告警。

### 方案 A：CallStackSpoofer

1. syscall 前把当前线程栈 swap 成伪造的合法栈
2. 伪造帧填 `kernel32!BaseThreadInitThunk → ntdll!RtlUserThreadStart` 之类全合法返回链
3. syscall 返回后 swap 回真实栈

### 方案 B：SilentMoonwalk

用 desynchronized stack，更激进：

```text
implant 代码 → 自定义 trampoline（改 RSP / RBP / 栈内容）
             ↓
             syscall（RtlCaptureStackBackTrace 看到伪造栈）
             ↓
             trampoline 还原 → 继续执行
```

关键是 unwinding：让 `RtlVirtualUnwind` 走进伪造的 `RUNTIME_FUNCTION` / `UNWIND_INFO` 链。

### OPSEC 建议

- call stack spoof + indirect syscall + ETW patch 是当前对抗 CrowdStrike / SentinelOne 较稳的组合
- sleep 阶段同样要 spoof——EDR 会定期采样，只在执行时 spoof 不够

## 7. 技术选型对照

| 技术 | 对抗目标 | 复杂度 | 现状 | ATT&CK |
|------|---------|--------|------|--------|
| Fresh Ntdll | 用户态 hook | 低 | 中（易被 ETW 抓） | T1562.001 |
| 直接 syscall | 用户态 hook | 低 | 低-中（内核看 RIP 在 implant） | T1106 / T1562.001 |
| 间接 syscall | 用户态 hook + 内核 RIP 检测 | 中 | 中-高 | T1106 |
| Hell's / Halo's / Tartarus | SSN 解析 | 中 | 高（基础设施） | T1027 |
| HWBP Blindside | hook + 无写操作 | 高 | 高 | T1562.001 |
| CallStackSpoofer / SilentMoonwalk | 调用栈遥测 | 高 | 高 | T1564 |

推荐链：**Halo's Gate + 间接 syscall + CallStackSpoofer + ETW patch**。

## 参考资料

- SysWhispers3：<https://github.com/klezVirus/SysWhispers3>
- Hell's Gate / Halo's Gate POC：<https://github.com/am0nsec/HellsGate>、<https://github.com/SafeBreach-Labs/HalosGate-PoC>
- Tartarus Gate：<https://github.com/trickster0/TartarusGate>
- CallStackSpoofer：<https://github.com/WithSecureLabs/CallStackSpoofer>
- SilentMoonwalk：<https://github.com/klezVirus/SilentMoonwalk>
- Blindside：<https://www.cyberark.com/resources/threat-research-blog/blindside-a-new-technique-for-edr-evasion-with-hardware-breakpoints>
- MITRE T1562.001：<https://attack.mitre.org/techniques/T1562/001/>

## 路由回调

unhook 只解决了一半问题，另一半是遥测致盲：进入 `references/telemetry-blinding.md`。
