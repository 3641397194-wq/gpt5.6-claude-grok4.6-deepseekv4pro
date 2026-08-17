# Kali Linux 适配层说明

> 本目录面向 Kali Linux 2026.1（2026 年 3 月发布，内核 6.18）。核心知识库（`skills/`、`CTF-Sandbox-Orchestrator/`）与 Windows 版共用同一份，本层只承载 Kali 专属的脚本、说明与规则入口。

---

## 0. 目录定位

```text
项目根目录/
├── skills/                    # 共享：SKILL.md、routing.md、references、field-journal
├── CTF-Sandbox-Orchestrator/  # 共享：40+ CTF 子技能
├── kali/                      # ← 本目录（Kali 适配层）
│   ├── scripts/
│   │   ├── bootstrap-reverse.sh
│   │   ├── refresh-tool-index.sh
│   │   ├── bootstrap-manifest.json
│   │   └── lib/tool-discovery.sh
│   ├── RULES-kali.md
│   └── README-kali.md
├── RULES.md                   # Windows 版规则
└── Readme.md                  # Windows 版说明
```

## 0.1 与 Windows 版的能力对齐

Kali 层不复制 Windows 文档，而是同一套**能力名**配两套实现：

- Windows：`skills/scripts/bootstrap-reverse.ps1`
- Kali：`kali/scripts/bootstrap-reverse.sh`

Kali 脚本覆盖 Windows manifest 里的全部能力名——`jadx`、`apktool`、`frida`、`jshookmcp`、`anything-analyzer`、`idapro`、`r2`、`adb`、`ghidra-mcp`、`seclists`、`burpsuite-mcp`、`nmap`、`pentestswarm`——并额外支持 Kali 原生项：`mcp-kali-server`、`metasploitmcp`、`hexstrike-ai`、`sstimap`、`xsstrike`、`netexec` 等。

**共享不动**：全部 `SKILL.md`/`routing.md`、全部 `references/`、`field-journal/`、`CTF-Sandbox-Orchestrator/`、`docs-generator/`、`diagram-generator/`。

**Kali 专属**：bash 脚本、apt 包管理、Linux 路径（`/opt/`、`~/tools/`、`/usr/bin/`）、大量工具预装导致 bootstrap 大幅简化。

---

## 1. Kali 的开箱能力

### 经典预装

| 工具 | Kali 包名 | 状态 |
|------|----------|------|
| nmap | nmap | 预装 |
| sqlmap | sqlmap | 预装 |
| hashcat | hashcat | 预装 |
| john | john | 预装 |
| hydra | hydra | 预装 |
| metasploit | metasploit-framework | 预装 |
| gobuster | gobuster | 预装 |
| ffuf | ffuf | 预装 |
| radare2 | radare2 | 预装 |
| binwalk | binwalk | 预装 |
| frida | python3-frida-tools | 预装或 pip |
| burpsuite | burpsuite | 预装 |
| wireshark | wireshark | 预装 |
| nikto | nikto | 预装 |
| wfuzz | wfuzz | 预装 |
| impacket | impacket-scripts | 预装 |
| netexec | netexec | 预装 |
| responder | responder | 预装 |
| aircrack-ng | aircrack-ng | 预装 |
| bloodhound | bloodhound | apt 可装 |
| ghidra | ghidra | apt 可装 |

### 2026.1 新收录（2026 年 3 月）

| 工具 | 包名 | 定位 |
|------|------|------|
| AdaptixC2 | adaptixc2 | 后渗透与对抗模拟框架 |
| Atomic-Operator | atomic-operator | 跨平台 Atomic Red Team 执行器 |
| Fluxion | fluxion | WiFi 审计与社会工程 |
| GEF | gef | GDB 增强调试框架 |
| MetasploitMCP | metasploitmcp | Metasploit 的 MCP 服务端 |
| SSTImap | sstimap | 服务端模板注入检测利用 |
| WPProbe | wpprobe | 轻量 WordPress 插件枚举 |
| XSStrike | xsstrike | 高级 XSS 扫描器 |

### 2025.4 新收录（2025 年 12 月）

| 工具 | 包名 | 定位 |
|------|------|------|
| evil-winrm-py | evil-winrm-py | Python 版 WinRM 远程执行 |
| hexstrike-ai | hexstrike-ai | AI MCP 安全自动化平台（150+ 工具） |
| bpf-linker | bpf-linker | BPF 静态链接器 |

### Kali 原生 MCP 三件套

| 工具 | 包名 | 用途 | 安装 |
|------|------|------|------|
| mcp-kali-server | mcp-kali-server | Kali 官方 MCP，AI 直接调用终端工具 | `apt install mcp-kali-server` |
| MetasploitMCP | metasploitmcp | Metasploit 的 MCP 接口 | `apt install metasploitmcp` |
| HexStrike AI | hexstrike-ai | 150+ 安全工具 MCP 编排 | `apt install hexstrike-ai` |

这是 Kali 版相对 Windows 版最大的红利：三个 MCP 全部 apt 直装，不用手动配 GitHub/npm/Docker，`bootstrap-reverse.sh` 的活少一大半。

---

## 2. 快速开始

### 2.1 全新系统一键初始化（需要 root）

```bash
sudo bash kali/scripts/quick-setup.sh                 # 完整：更新系统+装新工具+配 MCP+刷索引
sudo bash kali/scripts/quick-setup.sh --skip-update   # 网络慢时跳过系统更新
sudo bash kali/scripts/quick-setup.sh --minimal       # 最小安装（不装 AD/内网套件）
```

### 2.2 首次配置

```bash
cd /path/to/cybersecurity-skills-router
chmod +x kali/scripts/*.sh kali/scripts/lib/*.sh
bash kali/scripts/refresh-tool-index.sh
cat skills/tool-index.md
```

### 2.3 配齐原生 MCP（强烈推荐）

```bash
bash kali/scripts/bootstrap-reverse.sh mcp-kali-server metasploitmcp hexstrike-ai
# 配置自动写入 ~/.claude/mcp.json；用 Kiro 则手动复制到 ~/.kiro/settings/mcp.json
```

### 2.4 装 2026.1 新工具

```bash
bash kali/scripts/bootstrap-reverse.sh adaptixc2 atomic-operator sstimap xsstrike wpprobe fluxion gef
bash kali/scripts/bootstrap-reverse.sh coercer evil-winrm-py netexec responder bloodhound certipy   # AD/内网套件
```

### 2.5 补单个工具

```bash
bash kali/scripts/bootstrap-reverse.sh jadx
bash kali/scripts/bootstrap-reverse.sh jadx apktool frida jshookmcp
bash kali/scripts/bootstrap-reverse.sh idapro --start-services
```

### 2.6 让 AI 客户端自动路由

让客户端读取 `kali/RULES-kali.md`，即完成全局注入。

---

## 3. 路径约定

| 用途 | Kali 路径 |
|------|----------|
| 工具安装目录 | `~/tools/` 或 `/opt/` |
| jadx | `/opt/jadx/` 或 `~/tools/jadx/` |
| apktool | `/usr/local/bin/apktool`（apt）或 `~/tools/apktool/` |
| Ghidra | `/opt/ghidra/` 或 `~/tools/ghidra/` |
| IDA Pro | `/opt/idapro/`（如有 Linux 版） |
| Android SDK | `~/Android/Sdk/` |
| SecLists | `/usr/share/seclists/`（apt）或 `~/tools/SecLists/` |
| Node.js | `/usr/bin/node`（apt/nvm） |
| Python | `/usr/bin/python3` |
| MCP 配置 | `~/.claude/mcp.json` 或 `~/.kiro/settings/mcp.json` |

---

## 4. 与 Windows 版差异速览

| 维度 | Windows 版 | Kali 版 |
|------|-----------|---------|
| 脚本语言 | PowerShell (.ps1) | Bash (.sh) |
| 包管理 | winget / GitHub Release ZIP | apt / pip / npm / GitHub tar.gz |
| 路径分隔符 | `\` | `/` |
| 环境变量 | `%USERPROFILE%` | `$HOME` |
| 预装工具 | 几乎没有 | 大量安全工具预装 |
| IDA 启动 | `start.ps1` | 手动启动 Linux 版 IDA；脚本只注册/检查 MCP |
| MCP 配置路径 | `%USERPROFILE%\.claude\mcp.json` | `~/.claude/mcp.json` |
| 端口检测 | `TcpClient` | `nc -z` 或 `ss` |

---

## 5. 验收命令

```bash
# ─── 基础环境 ───
java -version && python3 --version && pip3 --version && node -v

# ─── 逆向工具 ───
jadx --version && apktool --version && adb version && frida --version
r2 -v && gdb --version        # GEF 自动加载

# ─── 渗透工具（预装应全过） ───
nmap --version && sqlmap --version && hashcat --version
msfconsole --version && gobuster version && ffuf -V && nuclei -version

# ─── 2026.1 新工具 ───
sstimap -h 2>&1 | head -3
xsstrike -h 2>&1 | head -3
wpprobe --help 2>&1 | head -3

# ─── AD/内网 ───
netexec --help 2>&1 | head -3
responder -h 2>&1 | head -3
certipy --version 2>&1 | head -1

# ─── 原生 MCP ───
which kali-server-mcp && which metasploitmcp && which hexstrike-ai

# ─── 索引与服务 ───
bash kali/scripts/refresh-tool-index.sh
nc -z 127.0.0.1 5000  && echo "mcp-kali-server OK"  || echo "offline"
nc -z 127.0.0.1 8085  && echo "metasploitmcp OK"    || echo "offline"
nc -z 127.0.0.1 13337 && echo "IDA MCP OK"          || echo "offline"
```

---

## 6. 常见问题

### Q: Kali 自带的 radare2 偏旧

```bash
bash kali/scripts/bootstrap-reverse.sh r2
# 默认走 apt 补齐；要追新版可按平台文档改用 GitHub/source 安装
```

### Q: Parrot OS / BlackArch 能用吗

可以。脚本按"命令是否存在"探测，不绑定发行版；只是 apt 路径在 BlackArch 上需换 pacman。

### Q: IDA Pro Linux 版如何接入

装到 `/opt/idapro/`，改 `kali/scripts/bootstrap-manifest.json` 中 `idapro` 的 `startScript` 路径。

### Q: Windows 与 Kali 同时用

`skills/` 通过 Git 同步，`field-journal/` 经验两边共享；执行时 Windows 走 `skills/scripts/*.ps1`，Kali 走 `kali/scripts/*.sh`。
