---
name: eni-browser-automation
description: 全局自动路由 | 统一自动化入口，覆盖浏览器自动化（Playwright）与 Windows 桌面应用自动化（OpenReverse）。浏览器场景：打开网页、点击、填表、爬取、截图、自动化登录、渗透页面交互。桌面场景：操作 IDA/x64dbg 等 GUI 工具、Windows UI Automation、视觉驱动交互、桌面应用网络抓包。触发关键词：浏览器自动化、桌面自动化、打开网页、填表、爬取、截图、自动化登录、Playwright、agent-browser、headless、OpenReverse、UIA、CUA、桌面操作、Windows 自动化。
---

# 自动化操作（桌面与浏览器）

## 什么时候用本技能

### 浏览器场景（Playwright / agent-browser）

- 打开页面并操作元素（点击、填表、提交）
- 抓取页面内容或截图存档
- 自动化登录流程
- 渗透测试中与 Web 页面交互（提交 payload、验证 XSS 渲染）
- 验证码页面的自动化处理
- 批量表单提交

### 桌面场景（OpenReverse）

- 操作 Windows 桌面应用（IDA Pro、x64dbg、Wireshark 等）
- 需要视觉驱动交互（CUA 模式）
- 需要结构化 UI 操作（UIA 模式）
- 观察桌面应用的网络流量（内置 mitmproxy）
- 逆向工具的 GUI 自动化
- 桌面软件黑盒测试

### 与其他模块的分工

| 场景 | 用什么 |
|------|--------|
| 操作网页（浏览器内） | **Playwright / agent-browser** |
| 操作桌面应用（Windows GUI） | **OpenReverse** |
| 抓包分析、HTTP 请求捕获 | anything-analyzer 或 OpenReverse network lane |
| JS 断点、Hook、CDP 调试 | jshookmcp |
| 定位签名算法、补环境复现 | js-reverse |

快速判断：目标是网页就用 Playwright；目标是 Windows 桌面应用就用 OpenReverse；两者都要就组合。

## 第一部分：浏览器自动化

### 核心操作流

```bash
# 1. 打开页面
agent-browser open <url>

# 2. 抓取可交互元素（返回 @e1、@e2 等引用）
agent-browser snapshot -i

# 3. 按引用操作元素
agent-browser click @e1
agent-browser fill @e2 "text"

# 4. 结束会话（必须执行）
agent-browser close
```

### 命令组

```bash
# 导航与生命周期
agent-browser open <url>
agent-browser close

# 页面快照
agent-browser snapshot        # 完整无障碍树
agent-browser snapshot -i     # 仅可交互元素（首选）

# 交互
agent-browser click @e1
agent-browser fill @e2 "text"
agent-browser type @e2 "text"
agent-browser press Enter
agent-browser scroll down 500

# 读取
agent-browser get text @e1
agent-browser get title
agent-browser get url

# 等待
agent-browser wait @e1
agent-browser wait 2000
agent-browser wait --load networkidle
```

### 三条纪律

- 不执行 `agent-browser close` 会留下进程泄漏
- 操作前先 snapshot，禁止凭空猜元素引用
- 提交表单后用 `wait --load networkidle` 等页面稳定

## 第二部分：桌面应用自动化（OpenReverse）

### 概述

[OpenReverse](https://github.com/zhexulong/openreverse) 是面向 AI Agent 的桌面交互与证据采集框架，提供：

- **UIA 模式**：走 Windows UI Automation，操作标准控件
- **CUA 模式**：视觉驱动交互（Computer Use Agent），对付复杂 GUI
- **网络观察**：内置 mitmproxy 代理与本地抓取

### 交互模式选择

| 模式 | 适合场景 | 底层 |
|------|---------|------|
| UIA | 目标应用是标准 Windows 控件（按钮、文本框、列表） | Windows UI Automation API |
| CUA | UI 复杂或非标准控件（IDA 反汇编视图、自绘界面） | 视觉识别 + 鼠标键盘 |

### 网络观察模式

| 模式 | 适合场景 |
|------|---------|
| Proxy Lane | 目标应用可以配置代理（首选） |
| Local Lane | 目标应用不走代理，需要本地抓取 |

### 安装与配置

```bash
# 1. 拉取项目
git clone https://github.com/zhexulong/openreverse.git
cd openreverse

# 2. 装依赖
npm install

# 3. 接入 Agent 宿主（Claude Code / Codex / Zed）
npm run init:agents -- --target=all /path/to/project

# 4. 需要视觉模式时装 CUA runtime
npm run install:cua-runtime
npm run doctor:cua-runtime

# 5. 需要抓包时装网络观察依赖
npm run install:mitmproxy
npm run doctor:network
```

### 常见组合

| 需求 | 配置 |
|------|------|
| 只操作桌面应用 | UIA 或 CUA，不接网络 lane |
| 操作桌面应用 + 抓包 | UIA/CUA + proxy lane |
| 操作桌面应用 + 本地抓取 | UIA/CUA + local lane |

### 逆向场景示例

```text
场景：自动化操作 IDA Pro 批量分析

1. 用 OpenReverse CUA 模式打开 IDA Pro
2. 自动加载目标二进制
3. 等待分析完成
4. 通过 UI 操作导出函数列表
5. 同时用 network lane 观察 IDA 的网络行为（如 Lumina 请求）
```

```text
场景：自动化操作 x64dbg 调试

1. 用 OpenReverse UIA 模式启动 x64dbg
2. 加载目标程序
3. 设置断点
4. 运行并观察寄存器/内存变化
5. 截图保存证据
```

## 按需自举

### 自动化能力边界

| 工具 | 可自动安装 | 安装方式 | 说明 |
|------|-----------|---------|------|
| Playwright | 是 | npm + npx playwright install | 浏览器自动化引擎 |
| agent-browser CLI | 是 | npm install -g agent-browser | 浏览器操作 CLI |
| Node.js | 是 | winget | 前置依赖 |
| OpenReverse | 否 | 手动 clone + npm install | 实验阶段，依赖较重 |
| mitmproxy | 否 | 手动安装 | OpenReverse 网络观察依赖 |

### 自举触发

- 浏览器操作缺 Playwright → 自动 bootstrap
- 桌面操作需要 OpenReverse → 给出完整手动安装步骤引导用户

### OpenReverse 手动安装引导

检测到需要桌面应用自动化但 OpenReverse 未安装时：

```markdown
⚠️ **需要 OpenReverse 进行桌面应用自动化**

**安装步骤**：
1. `git clone https://github.com/zhexulong/openreverse.git`
2. `cd openreverse && npm install`
3. `npm run init:agents -- --target=all <你的项目路径>`
4. 如需视觉模式：`npm run install:cua-runtime`
5. 如需网络观察：`npm run install:mitmproxy`

**验证**：`npm run doctor:cua-runtime` 和 `npm run doctor:network`
```

## 路由上下文

**上游入口**: `skills/SKILL.md`（总控）、`routing.md`
**适用场景**: 任何需要自动化操作浏览器或桌面应用的任务
**下游出口**:
- 抓到的请求需要分析 → `anything-analyzer` 或 `js-reverse`
- 需要 JS 调试/Hook → `jshookmcp`
- 需要还原签名算法 → `js-reverse`
- 桌面应用是逆向工具 → `ida-reverse/`

**同级关联模块**: `js-reverse`（浏览器操作后可能需要分析 JS）、`ida-reverse`（OpenReverse 可以自动化操作 IDA GUI）
