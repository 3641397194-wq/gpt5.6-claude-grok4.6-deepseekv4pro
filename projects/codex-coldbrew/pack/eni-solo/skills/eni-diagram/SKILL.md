---
name: eni-diagram
description: 全局自动路由 | generate, refine, validate, and render diagrams from natural language, notes, code snippets, schemas, tables, or existing diagram source. use for flowcharts, swimlanes, sequence diagrams, state diagrams, er diagrams, class diagrams, architecture/c4-style diagrams, dependency graphs, gantt charts, mind maps, user journeys, sankey-style flows, org charts, network graphs, and other visual models. supports mermaid by default, graphviz dot for complex graph layout, plantuml for uml-heavy engineering diagrams, and svg output when direct markup is more reliable.
---

# 图表生成

## 目标

把杂乱或结构化的输入变成清晰、可编辑的图表。优先产出文本型图表源码，方便审阅、版本化与反复修改。仅在用户要图片/PDF、或可下载制品有实际价值时渲染成文件。

## 默认工作流

1. 识别用户意图、受众与原始材料。
2. 用下方决策表选图表类型与语言。
3. 写码前先归一化实体、关系、标签、状态、分支与时间/顺序信息。
4. 生成简洁可读的图表源码。
5. 心智校验语法；生成文件时运行 `scripts/render_diagram.py`。
6. 返回源码并附简短的假设说明；生成文件时附输出链接。

请求信息不足时不过度追问，做合理假设并简短标注。

## 语言决策表

默认用 Mermaid，除非另一种语言明显更合适。

| 用户要什么 | 首选 | 理由 |
|---|---|---|
| 流程、决策树、简单泳道 | Mermaid flowchart | 可读性好，易贴进 Markdown |
| 系统/用户交互时序 | Mermaid sequenceDiagram 或 PlantUML sequence | 文档用 Mermaid；正式 UML 用 PlantUML |
| 生命周期、状态机、迁移 | Mermaid stateDiagram-v2 或 PlantUML state | 迁移语法紧凑 |
| 库表、实体、关系 | Mermaid erDiagram | 可移植 ER 记法 |
| 类/接口/对象模型 | Mermaid classDiagram 或 PlantUML class | 文档用 Mermaid；详尽 UML 用 PlantUML |
| 项目排期 | Mermaid gantt | 时间轴语法简洁 |
| 层级、想法、笔记 | Mermaid mindmap | 思路图默认解 |
| 客户/产品旅程 | Mermaid journey | 内置旅程记法 |
| git 历史 | Mermaid gitGraph | 内置 git 记法 |
| 依赖图、包图、大网络 | Graphviz DOT | 稠密图布局引擎更强 |
| 分层/聚簇/边界架构 | Mermaid 子图、Graphviz clusters 或 PlantUML C4 风格 | 按保真度要求选 |
| 加权流/桑基式关系 | Mermaid sankey-beta（渲染器支持时），否则 SVG 或 Graphviz | 各渲染器支持不一 |
| 文本语言表达不了的定制视觉 | SVG | 布局与样式精确可控 |

## 输出策略

- 除非用户只要图片，永远附可编辑源码。
- 默认给一张最优图，确有必要才给备选。
- 优先稳定简单的语法，少用新版特性，避免老渲染器不认。
- 标签要短；长文本拆到图外注释。
- 节点 ID 用 ASCII，标签用人类可读文字。
- 保留用户术语，图内大小写统一。
- 技术图带上隐含边界：客户端、服务、数据库、队列、外部 API、操作者/用户。
- 业务流程图区分：主路径、决策点、失败、重试、人工步骤。
- 从不确定文本生成时，代码后附 `Assumptions` 小节。

## Mermaid 生成规则

紧凑模板见 `references/diagram-patterns.md`。

通用规则：

- 开头用正确指令：`flowchart TD`、`sequenceDiagram`、`erDiagram`、`gantt`、`mindmap`、`journey`。
- 流程图默认 `flowchart TD`；架构与管道用 `flowchart LR`（用户指定左右向时除外）。
- 泳道或架构分层用 subgraph，名字用可读标签。
- 节点 ID 稳定且 ASCII：`ingest_service[Ingest Service]`。
- 含易混淆标点的标签加引号。
- 分支用菱形：`decision{Condition?}`。
- 边标签统一：`-- yes -->`、`-- no -->`、`-. async .->`、`== critical ==>` 仅在语义成立时用。
- 时序图先声明参与者再发消息；人用 `actor`，系统用 `participant`。
- 条件/可选/循环/并行用 `alt/else/end`、`opt/end`、`loop/end`、`par/and/end`。

## Graphviz DOT 生成规则

大、稠密或布局敏感的图用 Graphviz。

- 有向关系 `digraph G`，无向网络 `graph G`。
- 顶部设布局友好属性：`rankdir=LR`、`nodesep`、`ranksep`，必要时 `splines=true`。
- 边界与子系统用 `subgraph cluster_name`。
- 标签朴素，样式克制。
- 边标签只在有信息量时加。
- 节点多时按域分簇，避免全连接式交叉。

## PlantUML 生成规则

用户点名 UML 或需要正式 UML 记法时用。

- `@startuml` / `@enduml` 包裹。
- 适当使用 `actor`、`participant`、`database`、`queue`、`collections`、`component` 原型。
- 架构边界用 `package`、`rectangle`、`node`。
- 类图只列重要字段/方法，除非用户要求穷尽。
- 活动图用明确的起止标记与分支标签。

## SVG 生成规则

仅当文本图语言表达不了目标视觉时用 SVG。

- 简单、可访问、可编辑。
- 带 `<title>` 与有意义文本标签。
- 优先矩形、线、箭头、组，少用复杂路径。
- 不嵌外部字体或远程图片。

## 渲染文件

用户要 PNG/SVG/PDF 时，先建源码文件再运行：

```bash
python "<SKILL_ROOT>/diagram-generator/scripts/render_diagram.py" input.mmd --format svg --out output.svg
python "<SKILL_ROOT>/diagram-generator/scripts/render_diagram.py" input.dot --format png --out output.png
python "<SKILL_ROOT>/diagram-generator/scripts/render_diagram.py" input.puml --format svg --out output.svg
```

> `<SKILL_ROOT>` 是本包 `skills/` 目录的实际路径，AI 应自动检测。

渲染器刻意做成依赖容忍：先试常见本地工具，渲染器缺失时输出可操作的安装提示，而不是报错。脚本成功执行且输出文件存在之前，不得声称"已渲染"。

## 校验清单

定稿前：

- 图表类型与用户任务匹配
- 源码对所选语言语法上站得住
- 标签短到放得下
- 边与消息顺序忠实于输入
- 输入不完整时假设已标注
- 生成的文件存在且大小非零

## 常用应答模板

多数图表问题用这个结构：

```markdown
下面是可编辑的 [language] 版本：

```[language]
[source]
```

Assumptions:
- [仅需要时]

Rendered file: [link] [仅生成时]
```

英文用户回英文，中文用户回中文。

---

## 按需自举

### 自动化能力边界

| 工具 | 可自动安装 | 安装方式 | 说明 |
|------|-----------|---------|------|
| Mermaid CLI (mmdc) | 是 | npm install -g @mermaid-js/mermaid-cli | 渲染 Mermaid 为 PNG/SVG |
| Graphviz (dot) | 否 | 手动安装 | https://graphviz.org/download/ |
| PlantUML | 否 | 需要 Java + plantuml.jar | https://plantuml.com/download |
| Python (render script) | 是 | 已在 bootstrap 中 | `scripts/render_diagram.py` 依赖 |

### 说明

本 skill 主要输出文本格式图表源码（Mermaid/DOT/PlantUML），不一定需要本地渲染工具。仅当用户明确要求生成 PNG/SVG/PDF 文件时才需要对应渲染器。

渲染器不可用时，`scripts/render_diagram.py` 输出安装提示而不是报错。

---

## 路由上下文

**上游入口**: `skills/SKILL.md`（总控）、`routing.md`
**触发条件**: 用户说"画图"、"流程图"、"架构图"、"攻击路径图"、"时序图"、"Mermaid"、"Graphviz"、"PlantUML"
**下游出口**:
- 生成的图表可嵌入 `docs-generator/` 的报告中
- 攻击路径图可配合 `pentest-tools/` 的渗透报告

**同级关联模块**: `docs-generator/`（报告中嵌入图表）
