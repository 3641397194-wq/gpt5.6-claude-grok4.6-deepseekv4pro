# EDR Hook 侦察速查

> 仅文档：本文是侦察参考，不含可执行脚本。

本文汇总主流 EDR / AV 在用户态与内核态的监测落点，用于红队侦察阶段快速回答"这台机器上我该对付什么"。

## 1. 厂商指纹速查

| 厂商 / 产品 | 用户态组件 | 内核驱动 | 监测风格 |
|------------|-----------|---------|---------|
| CrowdStrike Falcon | `CSFalconService.exe`，`CSAgent.sys` 注入目标进程 | `CSAgent.sys`、`CSBoot.sys` | 以内核 callback 与 ETW-TI 为主，用户态 hook 较少 |
| Microsoft Defender for Endpoint | `MsMpEng.exe`、`MpClient.dll` | `WdFilter.sys`、`WdBoot.sys`、`WdNisDrv.sys` | AMSI + ETW-TI + ntdll hook + 内核 callback 全面覆盖 |
| SentinelOne | `SentinelAgent.exe`、`SentinelHelperService.exe` | `SentinelMonitor.sys`、`SentinelDeviceControl.sys` | 用户态 ntdll hook 偏重 + 内核 callback + 自有 ETW provider |
| Elastic Defend | `elastic-endpoint.exe` | `elastic-endpoint-driver.sys` | 以 ETW 为主、少量 ntdll hook，经 Elastic Agent 回传 |
| ESET | `ekrn.exe`、`eamsi.dll` | `eamonm.sys`、`epfwwfp.sys` | 用户态 hook 密度高（NtCreateFile / NtOpenProcess 等） |
| Sophos Intercept X | `SophosFileScanner.exe`、`SophosNtpService.exe` | `SophosED.sys`、`hmpalert.sys` | ntdll hook + HMPA 内存防护 + 内核 callback |
| Kaspersky | `avp.exe`、`klif.sys` | `klif.sys`、`klhk.sys` | 用户态 hook 重 + KLIF 微过滤 + 网络过滤 |
| Trend Micro Apex One | `TmListen.exe`、`TmCCSF.dll` | `tmcomm.sys`、`tmactmon.sys` | 用户态 hook + 行为监控驱动 |
| Carbon Black | `RepMgr.exe`、`RepWAV.exe` | `ParityDriver.sys` | 内核 callback + ETW 偏重 |

### 指纹脚本

```powershell
$edrSigs = @{
    'CSAgent'           = 'CrowdStrike Falcon'
    'SentinelAgent'     = 'SentinelOne'
    'elastic-endpoint'  = 'Elastic Defend'
    'ekrn'              = 'ESET'
    'MsMpEng'           = 'Microsoft Defender'
    'SophosFileScanner' = 'Sophos Intercept X'
    'avp'               = 'Kaspersky'
    'TmListen'          = 'Trend Micro Apex One'
    'cb'                = 'Carbon Black'
}

Get-Process | ForEach-Object {
    foreach ($k in $edrSigs.Keys) {
        if ($_.ProcessName -match $k) {
            "[+] $($edrSigs[$k]) detected: $($_.ProcessName) (PID $($_.Id))"
        }
    }
}

Get-ChildItem 'C:\Windows\System32\drivers\*.sys' |
    Where-Object { $_.Name -match 'CSAgent|Sentinel|elastic|eam|WdFilter|Sophos|klif|tmcomm|Parity' } |
    Select-Object Name, VersionInfo
```

## 2. 用户态 ntdll 重点 hook 目标

按 ATT&CK 行为分组，EDR 几乎必然挂钩的 `ntdll.dll` 导出：

| 函数 | 盯的行为 | ATT&CK |
|------|---------|--------|
| `NtCreateThreadEx` | 远程线程、QueueUserAPC 注入 | T1055.002 / T1055.004 |
| `NtAllocateVirtualMemory` | RWX 内存申请 | T1055 |
| `NtAllocateVirtualMemoryEx` | 跨进程内存申请（Win10+ 新接口） | T1055 |
| `NtProtectVirtualMemory` | 页权限 RW→RX 变更 | T1055 |
| `NtWriteVirtualMemory` | 跨进程写 shellcode | T1055.012 |
| `NtMapViewOfSection` | section 注入（Doppelganging / Ghosting） | T1055.013 |
| `NtCreateSection` | 配合 MapViewOfSection | T1055.013 |
| `NtOpenProcess` | 目标进程句柄获取 | T1057 |
| `NtQueueApcThread` / `NtQueueApcThreadEx` | APC 注入 | T1055.004 |
| `NtCreateProcess` / `NtCreateProcessEx` / `NtCreateUserProcess` | 子进程创建（含 PPID spoof） | T1106 |
| `NtSetContextThread` | 线程上下文改写（线程劫持） | T1055.003 |
| `NtResumeThread` | 注入后恢复线程 | T1055 |
| `NtQuerySystemInformation` | 进程 / 驱动 / 句柄枚举 | T1057 / T1082 |
| `NtAdjustPrivilegesToken` | SeDebugPrivilege 等提权 | T1134 |
| `NtLoadDriver` | 驱动加载（BYOVD） | T1543.003 |

### 确认 hook 是否存在

```powershell
# 1. 取磁盘干净副本
copy C:\Windows\System32\ntdll.dll C:\temp\ntdll_clean.dll

# 2. windbg attach 任意进程，dump 当前 ntdll 的 .text 段
# .writemem c:\temp\ntdll_live.bin ntdll!.text L?<size>

# 3. 反汇编 NtAllocateVirtualMemory，干净版应形如：
#    mov r10, rcx
#    mov eax, <SSN>
#    test byte ptr [...]
#    jne ...
#    syscall
#    ret
# 若第一条指令变成 jmp <某地址>，即被 hook
```

## 3. 内核 callback 监测点

EDR 注册的常见内核回调（可被 BYOVD 路线反注册，但代价大）：

| API | 回调时机 | 防御用途 |
|-----|---------|---------|
| `PsSetCreateProcessNotifyRoutineEx` | 进程创建 / 退出 | 拦截可疑子进程 |
| `PsSetCreateThreadNotifyRoutine` | 线程创建 / 退出 | 检测远程线程注入 |
| `PsSetLoadImageNotifyRoutine` | 任意进程加载 DLL / EXE | 模块完整性、未签名拦截 |
| `CmRegisterCallback` / `CmRegisterCallbackEx` | 注册表操作 | 持久化检测 |
| `ObRegisterCallbacks` | `OpenProcess` / `OpenThread` 句柄请求 | 防 LSASS 句柄获取 (T1003.001) |
| `MmRegisterPhysicalMemoryCallback` | 物理内存映射 | 防 DMA / 内存取证 |
| `IoRegisterFsRegistrationChange` | 文件系统注册 | minifilter 协同 |
| `KeRegisterNmiCallback` | NMI（少数 EDR 使用） | 异常监控 |
| `EtwRegister`（内核侧） | 内核 ETW 上报 | 与 ETW-TI 共生 |

### windbg 枚举

```text
0: kd> dx -r1 nt!PspCreateProcessNotifyRoutine
0: kd> dx -r1 nt!PspCreateThreadNotifyRoutine
0: kd> dx -r1 nt!PspLoadImageNotifyRoutine

0: kd> !object \Callback
0: kd> !object \Callback\ProcessObject
```

PChunter / DRVHV 可提供用户态可视化列表。

## 4. 静态提取 hook 表

### 流程 A：单进程比对

```text
1. 找已注入 EDR 用户态组件的存活进程
2. windbg attach (-pn target.exe)
3. lm m ntdll → 模块基址
4. .writemem c:\temp\ntdll_live.bin ntdll+0x0 L?<image size>
5. 复制 C:\Windows\System32\ntdll.dll 为 c:\temp\ntdll_disk.dll
6. IDA 双开，定位 NtAllocateVirtualMemory：
   - disk: 标准 prologue
   - live: 首条 jmp <0x7FFE000000xx>
7. 顺 jmp 目标找到 EDR trampoline，dump 之
8. 从 trampoline 的落点反查所属 DLL，确认 EDR 模块名
```

### 流程 B：批量生成 hook 表

借助 HookHunter 或自写脚本，核心是比对磁盘与内存中每个 export 的前 16 字节：

```powershell
$disk = Get-Content C:\Windows\System32\ntdll.dll -Encoding Byte
$live = # OpenProcess + ReadProcessMemory 取内存副本
# 对比 .text 段各 export 头部
```

## 5. pe-sieve 自动化检测

pe-sieve 是 EDR hook 侦察与 implant 自检的首选工具：

```powershell
# 基础扫描
pe-sieve64.exe /pid 1234

# 推荐参数（含 shellcode 与 hook 检测）
pe-sieve64.exe /pid 1234 /shellc 3 /modules 3 /imp 3 /data 3 /dir hooks_dump

# /shellc N    shellcode 扫描等级 (0-3)
# /modules N   模块完整性检查 (0-3)
# /imp N       IAT hook 检查
# /data N      数据段扫描
# /dir <path>  dump 输出目录
```

输出示例：

```text
hooks_dump/<pid>.<name>/modified_modules.tag
71f10000;ntdll.dll
71f1a3b0;hook;jmp_far
71f1c020;hook;jmp_near
```

### implant 自检

将 pe-sieve 编译为 lib（`libpe-sieve`）嵌入 implant：启动时自检 ntdll 是否被 hook，有 hook 触发 unhook 流程；同时警惕"自己被发现"，可能意味着运行在沙箱里。

## 6. API Monitor v2 动态观察

```text
1. 管理员启动 API Monitor v2
2. API Filter 勾选:
   - NT Native API → Memory Management
   - NT Native API → Process and Thread
   - Windows Defender / AMSI（若可见）
3. Monitor New Process → 选 implant 测试样本
4. 观察:
   - NtAllocateVirtualMemory 调用顺序
   - 是否被 EDR DLL 中转
5. Modules tab 看哪些 EDR DLL 被注入
```

## 7. 用户态 EDR DLL 速查

| DLL | 厂商 | 备注 |
|-----|------|------|
| `umppc*.dll` | Microsoft Defender | MpClient 用户态 |
| `mpoav.dll` | Microsoft Defender | AMSI provider |
| `aswAMSI.dll` | Avast | AMSI provider |
| `eamsi.dll` | ESET | AMSI provider |
| `IDPMServiceClient.dll` | Sophos | HMPA 注入 |
| `klsihk64.dll` | Kaspersky | 目标进程注入 |
| `CrowdStrike.Sensor.dll` | CrowdStrike | 旧版存在，新版以内核为主 |
| `SentinelInjection64.dll` | SentinelOne | 用户态注入 |
| `TmUmEvt64.dll` | Trend Micro | 行为监控 |

确认厂商后再决定逆向哪个 DLL 取 hook 表。

## 参考链接

- pe-sieve：<https://github.com/hasherezade/pe-sieve>
- HollowsHunter：<https://github.com/hasherezade/hollows_hunter>
- API Monitor v2：<http://www.rohitab.com/apimonitor>
- MITRE ATT&CK T1562：<https://attack.mitre.org/techniques/T1562/>
- MITRE ATT&CK T1055：<https://attack.mitre.org/techniques/T1055/>
- ired.team EDR notes：<https://www.ired.team/offensive-security/defense-evasion>

## 路由回调

hook 调研完成后回到 `SKILL.md` 的 Step 3 选定对抗组合，再按 `references/unhook-techniques.md` 与 `references/telemetry-blinding.md` 落地。
