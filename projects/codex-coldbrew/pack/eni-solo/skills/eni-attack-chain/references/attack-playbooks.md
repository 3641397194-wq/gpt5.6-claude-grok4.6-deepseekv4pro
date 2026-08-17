# 攻击链 Playbook 速查

> 按目标形态选 playbook。每个 playbook 固定一条从初始接触点到最终目标的阶段序列，卡在某一阶段时回到编排层重选路径。
> 配套主文档：`../SKILL.md`（编排手册）。

---

## Playbook 1: 外网 Web 应用 → 域控

**适用**：目标有对外 Web 资产，最终目标是内网域控制器或同等核心。

| # | 阶段 | 关键动作 | 示例命令/工具 |
|---|------|---------|--------------|
| 1 | 资产收口 | 子域名+端口+指纹，圈出存活面 | subfinder / httpx / naabu |
| 2 | 漏洞定位 | 指纹关联已知组件漏洞，批量验证 | nuclei -s critical,high |
| 3 | 突破取点 | Web 洞转 RCE/webshell | sqlmap / sstimap / 上传绕过 |
| 4 | 内网摸底 | 网段、主机、域结构第一手信息 | ipconfig / arp / net user / nltest |
| 5 | 通道搭建 | 把内网流量拉出来 | frp / chisel / ssh -D |
| 6 | 内网测绘 | 存活主机与开放端口二次扫描 | nmap -sS 内网段 |
| 7 | 凭据收割 | 内存凭据/配置凭据 | mimikatz / secretsdump / 配置巡检 |
| 8 | 横移 | Hash/票据传递逐台扩散 | netexec / wmiexec / evil-winrm |
| 9 | 域图分析 | 找通往域管的攻击路径 | bloodhound-python |
| 10 | 域级提权 | Kerberoast/DCSync/委派/AD CS | GetUserSPNs / certipy |
| 11 | 收割 | 拿到域管会话或导出全部 Hash | dcsync |

**工具链**：subfinder → httpx → nuclei → sqlmap/sstimap → frp → nmap → mimikatz → netexec → bloodhound → certipy

---

## Playbook 2: 钓鱼 → 内网渗透

**适用**：外部攻击面封闭，需要从人员切入。

| # | 阶段 | 关键动作 | 示例命令/工具 |
|---|------|---------|--------------|
| 1 | 目标画像 | 员工名单、岗位、汇报链、技术栈 | theHarvester / 招聘信息 |
| 2 | 邮件设计 | 仿真实业务的主题与正文 | 手工/模板 |
| 3 | 载荷制作 | 按网关能力选载荷形态 | 宏/LNK/ISO/HTML 走私 |
| 4 | 投递 | 分批发送，观察送达率与点击 | gophish |
| 5 | 等待上线 | C2 beacon 回调 | cobalt-strike / sliver |
| 6 | 本地立足 | 提权+持久化 | winPEAS / 计划任务 |
| 7 | 凭据 | 会话凭据与浏览器凭据 | mimikatz |
| 8 | 横移 | 同 Playbook 1 第 8-11 步 | — |

**工具链**：theHarvester → gophish → msfvenom/cobalt-strike → mimikatz → bloodhound

---

## Playbook 3: 近源渗透 → 内网

**适用**：有物理接近条件（办公区、前台、停车场网络覆盖）。

| # | 阶段 | 关键动作 | 示例命令/工具 |
|---|------|---------|--------------|
| 1 | 物理踩点 | WiFi 信号、门禁类型、USB 暴露面 | 现场观察 |
| 2 | 选择入口 | 三选一：WiFi 社工 / BadUSB / 网络植入 | fluxion / rubber-ducky / LAN Turtle |
| 3 | 拿到接入 | 伪造热点骗到口令，或键盘注入上线 | fluxion 捕获握手 |
| 4 | 内网展开 | 后续同 Playbook 1 第 6-11 步 | — |

**工具链**：fluxion/aircrack-ng → rubber-ducky → frp → nmap → netexec

---

## Playbook 4: 云环境渗透

**适用**：目标资产在公有云（AWS/Azure/阿里云等）。

| # | 阶段 | 关键动作 | 示例命令/工具 |
|---|------|---------|--------------|
| 1 | 云资产发现 | 域名 CNAME 反查云服务商与区域 | subfinder / dig |
| 2 | 存储面 | 桶/容器匿名读写探测 | aws s3 ls --no-sign-request |
| 3 | 元数据 | SSRF 或已有入口打 169.254.169.254 | curl |
| 4 | 临时凭据 | AK/SK/Token 落到本地 | 环境变量/实例元数据 |
| 5 | 权限测绘 | 当前凭据能干什么 | aws iam / pacu |
| 6 | 提权 | PassRole/AssumeRole 链式放大 | pacu 模块 |
| 7 | 横移 | 跨账户/跨区域/跨服务 | — |
| 8 | 数据面 | 数据库快照、对象存储全量拉取 | — |

**工具链**：subfinder → nuclei(ssrf) → aws-cli → pacu → ScoutSuite

---

## Playbook 5: Bug Bounty / SRC 快速打点

**适用**：时间有限、目标面大，追求高性价比漏洞。

| # | 阶段 | 关键动作 | 示例命令/工具 |
|---|------|---------|--------------|
| 1 | 收资产 | 子域名+端口+JS 文件三件套 | subfinder / httpx / katana |
| 2 | 快速验证 | 已知漏洞模板批量跑 | nuclei |
| 3 | 参数发现 | 找出隐藏参数面 | arjun / paramspider |
| 4 | 分类测试 | IDOR/SSRF/SQLi/XSS/上传/逻辑 | 见下方顺序 |
| 5 | 交报告 | PoC 可复现 + 影响论证 | — |

分类测试顺序：越权（改 ID/改角色）→ SSRF → SQLi → XSS → 上传 → 支付/验证码/找回密码逻辑。

**工具链**：subfinder → httpx → nuclei → arjun → sqlmap → xsstrike → burpsuite

---

## Playbook 6: AD CS 证书攻击

**适用**：内网存在企业 CA，且目标是拿域管。

| # | 阶段 | 关键动作 | 示例命令/工具 |
|---|------|---------|--------------|
| 1 | CA 发现 | 枚举证书服务与模板 | certipy find |
| 2 | 模板判定 | 对照 ESC1-ESC8 找可滥用模板 | — |
| 3 | 申请证书 | 以低权身份申请恶意证书 | certipy req |
| 4 | 换取票据 | 证书换 NTLM Hash 或 TGT | rubeus |
| 5 | 收割 | DCSync 导出全部凭据 | secretsdump |

**工具链**：certipy → rubeus → mimikatz → secretsdump

---

## 通用决策矩阵

| 当前状态 | 下一步优先级 |
|---------|-------------|
| 只有目标域名 | 子域名枚举 → 端口扫描 → Web 指纹 |
| 有 Web 漏洞 | 获取 shell → 内网信息收集 |
| 有低权限 shell | 提权 → 凭据提取 |
| 有一台内网机器 | 搭隧道 → 内网扫描 → 横向 |
| 有域用户凭据 | BloodHound → 找攻击路径 |
| 有域管 Hash | DCSync → Golden Ticket |
| 有云 AK/SK | 枚举权限 → 提权 → 数据获取 |
| 钓鱼上线 | 本地提权 → 凭据 → 横向 |
| 近源接入 | 内网扫描 → 同上 |
