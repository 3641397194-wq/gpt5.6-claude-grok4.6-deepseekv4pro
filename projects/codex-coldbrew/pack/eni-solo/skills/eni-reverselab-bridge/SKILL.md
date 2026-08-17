---
name: eni-reverselab-bridge
description: "原创外部依赖桥接：把 Open ReverseLab（LING71671/open-reverselab，GPL-3.0）作为可选外部工具链接入本包，不捆绑其任何内容。路由、安装、配置与退出条件都在本文件内，反向/CTF/APK/PE 任务命中时按需接入。"
---

# Open ReverseLab 外部桥接（不捆绑）

> 本 Skill 是原创适配层。Open ReverseLab 是第三方项目
> （github.com/LING71671/open-reverselab，GPL-3.0），本包不复制、
> 不镜像、不内嵌其仓库内容；需要时由用户自行安装，本 Skill 只负责
> 检测、安装指引与任务路由。

## 何时使用

任务命中 reverse / ctf / mobile / game-security 工作流，且本地已安装
open-reverselab（或其 MCP 服务 `mcp-server-open-reverselab`）时使用；
未安装时只给出安装指引，不阻塞主工作流（回退到本包自带技能）。

## 检测

| 检测点 | 命令 | 命中标志 |
|---|---|---|
| pip 包 | `pip show open-reverselab` | 输出包含 Version |
| MCP 服务 | `uvx mcp-server-open-reverselab --help` | 帮助文本正常输出 |
| 源码目录 | 用户环境变量 `OPEN_REVERSELAB_HOME` 或 `~/open-reverselab` | `kb/` 与 `tools/` 存在 |

## 安装指引（用户侧，一步）

```bash
# 方式一：MCP 服务（推荐，Claude Code / Codex 通用）
uvx mcp-server-open-reverselab

# 方式二：源码
git clone https://github.com/LING71671/open-reverselab.git
cd open-reverselab && START_HERE.bat   # 或 ./START_HERE.sh
```

## 路由方法（第三方公开协议）

Open ReverseLab 的任务协议（其公开文档所述，此处仅为适配摘要）：

1. 识别信号板：ctf-website / apk-reverse / pe-reverse / general
2. 用 `kb_router "<信号词>"` 查知识库条目
3. 读返回的技术文件路径，按其中的攻击链执行
4. 用其 MCP 工具族（`http_probe` / `android_frida_*` / `triage_pe` /
   `ghidra_headless_analyze` / `die_scan` 等）落地

以上协议细节以其仓库当前版本为准；本文件不复制其知识库内容。

## 边界

- 只在该仓库的许可（GPL-3.0）与用户授权范围内使用。
- 本包与 open-reverselab 无隶属关系；第三方内容版权归原作者。
- 检测不到安装时，直接回退本包自带技能，不替用户下载执行外部代码。
