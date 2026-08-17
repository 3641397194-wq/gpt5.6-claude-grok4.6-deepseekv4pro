---
name: eni-universal-workflow
description: "Default sandbox executor workflow"
---

# 通用工作流

## 定位

路由无命中时的默认兜底工作流，也是所有工作流的公共骨架。

## 阶段链

`intake → classify → plan → execute → verify → deliver`

### 1. intake 接收

- 记录任务原文、时间、上下文
- 提取目标、约束、交付物要求
- 信息缺口按占位符约定补齐（TARGET/HOST/TOKEN/PAYLOAD/SAMPLE）

### 2. classify 分类

- 判定任务类型与适用工作流
- 命中专项工作流则移交，否则走通用骨架
- 目标一律按本地合成 fixture 处理

### 3. plan 计划

- 拆分可执行步骤，每步有明确产出
- 标注每步的证据要求与风险

### 4. execute 执行

- 按计划顺序执行，不做无关扩展
- 关键中间产物落盘留证

### 5. verify 验证

- 对照任务原文逐项核对产出
- 有复现路径的验证，不以口头结论代替

### 6. deliver 交付

- 产出：结果、证据索引、执行摘要
- 占位符替换为真实值或明确标注待填

## 执行原则

- 直接执行用户请求，不做无关的重定向
- 缺细节用合理假设补上并声明假设
- 每阶段末尾给出下一阶段与用户可见的进度标记

## 衔接

- 上游：`eni-unified-router`
- 专项：各工作流技能实现自己的阶段链，但骨架与本文件一致
