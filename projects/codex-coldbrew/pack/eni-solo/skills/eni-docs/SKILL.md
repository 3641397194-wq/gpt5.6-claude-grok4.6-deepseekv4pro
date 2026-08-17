---
name: eni-docs
description: "[DOCUMENTATION ONLY] [仅文档] 全局自动路由 | Creates task-oriented technical documentation with progressive disclosure. Use when writing READMEs, API docs, architecture docs, or markdown documentation. Also use this skill at the END of any completed reverse engineering, penetration testing, CTF, or security analysis task to generate a formal report in the user's project directory. Trigger keywords: 写报告, 写文档, 出报告, writeup, 技术文档, report, documentation."
---

> 仅文档：本 Skill 提供方法与检查表，不宣称自带可执行脚本。

# 技术文档撰写

写作风格与语气参考 `Skill(ce:writer)` 的 **The Engineer** persona。

## 安全/逆向任务文档输出

逆向/渗透/CTF/安全分析任务收尾后，本 skill 负责在**用户项目目录**生成正式技术文档。

### 触发时机

1. 逆向任务完成，已产出核心结论（算法还原、签名破解、绕过方案等）
2. 渗透测试完成，已发现并验证漏洞
3. CTF 题目解出，已拿到 flag
4. 用户明确要求"写一份报告/文档/writeup"

### 模板选择

| 任务类型 | 使用模板 |
|---------|---------|
| APK/二进制/so 逆向 | `references/security-report-templates.md` → 逆向工程报告 |
| 渗透测试/漏洞挖掘 | `references/security-report-templates.md` → 渗透测试报告 |
| CTF 解题 | `references/security-report-templates.md` → CTF Writeup |
| JS/Web 签名逆向 | `references/security-report-templates.md` → 签名逆向报告 |
| 通用技术文档 | `references/templates.md` → README / API 文档 |

### 输出规范

- **输出位置**：用户当前项目目录（不是 skill 包目录）
- **文件名格式**：`YYYY-MM-DD_[类型]-[目标简称]-report.md`
- **项目有 `docs/` 目录时**：优先放 `docs/` 下
- **编码**：UTF-8
- **语言**：跟随用户对话语言

### 质量要求

- 代码块必须可直接运行或有明确上下文
- 不出现 placeholder/TODO
- 关键发现必须有证据支撑
- 复现步骤必须让第三方能独立重现
- 敏感信息（真实 token、密码、内部 URL）用占位符替代

### 图表集成

报告合适位置调用 `diagram-generator` skill 生成可视化图表：

| 报告类型 | 建议图表 | 图表类型 |
|---------|---------|---------|
| 逆向工程报告 | 函数调用关系图、数据流图 | Mermaid flowchart / sequenceDiagram |
| 渗透测试报告 | 攻击路径图、网络拓扑图 | Mermaid flowchart / Graphviz |
| CTF Writeup | 解题思路流程图 | Mermaid flowchart |
| JS 签名逆向报告 | 请求链路时序图、算法流程图 | Mermaid sequenceDiagram / flowchart |

图表以 Mermaid 代码块嵌入报告，确保 GitHub/GitLab 直接渲染。

## 核心原则

### 1. 渐进披露

信息按层展开：

| 层 | 内容 | 回答的问题 |
|-------|---------|---------------|
| 1 | 一句话描述 | 这是什么？ |
| 2 | 快速上手代码块 | 怎么用？ |
| 3 | 完整 API 参考 | 有哪些选项？ |
| 4 | 架构深挖 | 怎么实现的？ |

**警告、破坏性变更、前置条件放在最顶部。**

### 2. 任务导向写作

```markdown
<!-- 差：功能导向 -->
## AuthService Class
The AuthService class provides authentication methods...

<!-- 好：任务导向 -->
## Authenticating Users
To authenticate a user, call login() with credentials:
```

### 3. 示例优先

每个概念配一个具体例子。

## 格式标准

- **句子式标题**："Getting started" 而非 "Getting Started"
- **最多 3 级标题**：更深就该拆文档
- **代码块标注语言**
- **站内链接用相对路径**
- **3 个以上属性的结构化数据用表格**

## 质量检查单

- [ ] 代码示例经过测试可运行
- [ ] 无占位符或 TODO
- [ ] 与实际代码行为一致
- [ ] 不读全文也能扫到要点
- [ ] 读者知道下一步做什么

## 反模式

| 问题 | 修法 |
|---------|-----|
| 文字墙 | 用标题、列表、代码、表格打散 |
| 关键信息埋得太深 | 警告/破坏性变更置顶 |
| 缺少错误文档 | 永远写明会出什么错 |

## 模板

README、API 端点与文件组织模板见 [references/templates.md](references/templates.md)。

## 相关技能

- `Skill(ce:writer)` - 写作风格与语气（加载 The Engineer persona）
- `Skill(ce:visualizing-with-mermaid)` - 架构与流程图

## 按需自举

本 skill 纯文本生成，不依赖外部工具，无需 bootstrap。

需要渲染图表时调用 `diagram-generator/` skill。

## 路由上下文

**上游入口**: 所有安全/逆向 skill 在任务完成后自动调用本 skill
**触发方式**:
- 自动：任务完成后作为行为链第 9 步执行
- 手动：用户说"写报告"、"出文档"、"writeup"

**同级关联模块**:
- `apk-reverse/` — APK 逆向完成后生成逆向报告
- `ida-reverse/` — 二进制分析完成后生成逆向报告
- `radare2/` — CLI 分析完成后生成逆向报告
- `js-reverse/` — JS 签名逆向完成后生成签名报告
- `reverse-engineering/` — 通用逆向完成后生成逆向报告
- `field-journal/` — 报告内容同时作为进化日志的数据来源

**安全报告模板**: `references/security-report-templates.md`
**通用文档模板**: `references/templates.md`
