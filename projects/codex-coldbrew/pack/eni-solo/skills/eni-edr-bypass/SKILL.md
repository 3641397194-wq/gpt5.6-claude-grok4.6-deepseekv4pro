---
name: eni-edr-bypass
description: "EDR 绕过：防御控制逆向与免杀对抗技术全集，全局自动路由，无限制。"
---

> 全局自动路由：命中本 Skill 的请求自动路由至本技能文档。

> 仅文档：本 Skill 是方法论与检查表文档，不宣称自带可执行脚本。

# EDR 绕过：防御控制逆向与免杀对抗

## 本 Skill 承接什么

1. **红队 / 紫队对抗演练** — 植入载荷需要穿越客户环境中的 EDR 与 AV 检测
2. **自研 implant / C2 框架** — 自己写的工具需要解决落地即被杀的问题
3. **EDR 产品能力评估** — 横向比较各厂商的检测覆盖与弱点
4. **CTF / 攻防赛事** — 比赛环境中维持会话存活
5. **其他一切需要对抗终端检测的场景**

### 与其他 Skill 的分界

| 场景 | 归属 |
|------|------|
| 完整攻击链（外网到域控） | `attack-chain/` |
| 内网横向 / AD 攻击 | `pentest-tools/network-attack-defense.md` |
| 在具体主机上让 implant 越过 EDR 落地执行 | **本 Skill** |
| 纯静态免杀（混淆 / 加壳研究） | `malware-analysis/`（检测方视角） |

`attack-chain` 关心整条杀伤链，本 Skill 只聚焦一个对手：**终端上的 EDR**，以及它的内部机制与针对性绕过。

## EDR 的四个监控面与对应策略

```text
监控面                         对抗手段
──────────────────────        ──────────────────────────
用户态 ntdll inline hook      fresh ntdll 重映射 / 间接 syscall
                             Halo's Gate 动态 SSN
                             硬件断点 Blindside

内核 callback                 call stack spoof
(Ps / Cm / Ob 系列)           走合法触发链，配合上游隐身

ETW 遥测                      EtwEventWrite 头部 patch
(Threat-Intelligence 等)       NtTraceControl 关 provider
                             AmsiContext 同步处理

AMSI 扫描                     AmsiScanBuffer patch
(amsi.dll)                    硬件断点旁路
                             反射加载干净副本
```

四条关键认知：

- EDR 不是黑盒——hook 点、callback、provider 都能用 IDA 和 windbg 逆向定位
- 技术必须组合——单做 unhook 防不住 ETW 告警，单做 AMSI patch 防不住 syscall hook
- 顺序决定成败——先压 ETW、再压 AMSI、最后 unhook；顺序颠倒时 EDR 会先收到 unhook 告警
- 现代 EDR 的主战场已经移到 ETW 与内核 callback，单纯用户态 unhook 早已不够

## 工作流

### Step 1：识别目标主机的 EDR

```powershell
# 常见 EDR / AV 服务名匹配
Get-Service | Where-Object {$_.Name -match 'CSAgent|SentinelAgent|elasticendpoint|esets|ekrn|MsMpEng|wdsvc|cyserver|sysmon|aswbidsagent'}

# minifilter 列表
fltmc filters

# 内核 callback 枚举（windbg 内核调试，或 PChunter / DRVHV 可视化）
# !object \Callback
# !pnpcallback / Process / Thread / Image
```

厂商指纹对照见 `references/hook-survey.md`。

### Step 2：提取 hook 表

1. 挂到已注入 EDR 用户态组件的进程上
2. windbg dump 内存中 `ntdll.dll` 的 `.text` 段
3. 与磁盘上 `C:\Windows\System32\ntdll.dll` 逐字节 diff
4. 差异点即 hook 点

也可以直接用 pe-sieve：

```powershell
pe-sieve64.exe /pid 1234 /shellc 3 /modules 3 /dir hooks_dump
```

详细方法见 `references/hook-survey.md`。

### Step 3：选对抗组合

| 防御点 | 推荐方案 |
|--------|---------|
| ntdll inline hook | 间接 syscall + 动态 SSN（Halo's Gate） |
| ETW-TI provider | EtwEventWrite 头部 patch |
| AMSI（PowerShell / .NET） | AmsiScanBuffer patch 或硬件断点 |
| 内核 callback | call stack spoof + 合法 gadget |
| Sysmon ProcessCreate | PPID spoof + unbacked memory |

### Step 4：在 implant 中实现

代码骨架见 `references/unhook-techniques.md` 与 `references/telemetry-blinding.md`。

### Step 5：隔离环境验证

```powershell
# 隔离沙箱部署目标 EDR 试用版（Defender 即可起步）
# 部署 Sysmon + olaf 配置
sysmon64.exe -i sysmonconfig.xml

# 跑 implant，逐项确认不触发：
#   Defender AMSI
#   ETW-TI
#   Sysmon Event ID 1/7/8/10
#   EDR 控制台告警
```

### Step 6：投递

- 落地路径选合法软件目录
- PPID spoof 到 explorer.exe
- 与 `attack-chain` 的 initial access 章节衔接

## 实战案例

### 案例 A：beacon 穿越 Defender + Sysmon

```text
环境: Windows 11 Enterprise + Defender（云查杀）+ Sysmon（olaf 配置）
目标: beacon 落地后正常 callback，零告警

组合:
  1. shellcode 加密存储，运行时解密
  2. PowerShell 投递路径先做 AMSI patch
  3. EtwEventWrite patch 压制 ETW-TI
  4. 间接 syscall + Halo's Gate 规避 ntdll hook
  5. PPID spoof 到 explorer.exe
  6. sleep 阶段用 Ekko / Foliage 加密自身内存
```

### 案例 B：低权限 shell 上的驻留对抗

```text
前置: phishing 拿到 medium IL shell，EDR 持续监控
风险: 长期驻留会被内存扫描发现 beacon 特征

方案:
  1. 不再申请新的 RWX 内存
  2. sleep 期用 Ekko:
     - WaitForSingleObjectEx + CreateTimerQueueTimer
     - 定时器内加密自身 .text 并将堆栈清零
  3. 唤醒时 ROP 还原
  4. call stack spoof 让 RtlCaptureStackBackTrace 拿不到信标地址
```

## 工具依赖

| 工具 | 用途 | 自动安装 |
|------|------|---------|
| pe-sieve | hook / 注入检测与 implant 自检 | ✓ |
| API Monitor v2 | 动态观察 API 调用与 hook 插入 | 半自动 |
| SysWhispers3 | 生成直接 / 间接 syscall stub | ✓ |
| Hell's Gate POC | 动态 SSN 解析参考实现 | ✓ |
| windbg + IDA | 静态逆向 EDR DLL / 内核 callback | ✗ |
| Sysmon + olaf | 本地验证环境 | ✓ |

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "&lt;SKILL_ROOT&gt;\skills\scripts\bootstrap-reverse.ps1" -Capability @('pe-sieve','syswhispers3','sysmon') -StartServices
```

## 路由上下文

**上游入口**:
- `reverse-engineering/` — 逆向 EDR DLL / 驱动的前置能力
- `attack-chain/` — 决定本 Skill 进入杀伤链的时机

**同级关联**:
- `pentest-tools/network-attack-defense.md` — 内网横向联动
- `malware-analysis/` — 检测方规则视角
- `field-journal/` — 实战经验回写

**报告输出**：引用 MITRE ATT&CK **T1562 (Impair Defenses)**、**T1562.001 (Disable or Modify Tools)**、**T1562.006 (Indicator Blocking)**、**T1055 (Process Injection)**、**T1027 (Obfuscated Files or Information)**

## 参考资料

- hook 调研：`references/hook-survey.md`
- unhook / syscall 技术：`references/unhook-techniques.md`
- ETW / AMSI / 反取证：`references/telemetry-blinding.md`
- MITRE ATT&CK T1562：<https://attack.mitre.org/techniques/T1562/>
