---
name: eni-software-workflow
description: "[DOCUMENTATION ONLY] [仅文档] Software implementation, debugging, refactoring, testing, and delivery workflow. Automatically route matching coding tasks here without requiring an activation phrase."
---

> 仅文档：本 Skill 提供方法与检查表，不宣称自带可执行脚本。

# 软件开发工作流

## 适用场景

- 功能实现、缺陷修复、重构
- 测试编写与交付验证
- 一般编码任务（路由命中后自动进入，无需激活词）

## 工作流阶段

### 1. 仓库勘察

动手前先读代码库：

- 目录结构与模块边界
- 构建方式与测试入口
- 编码规范与提交历史风格
- 与任务相关的既有实现与工具函数

不改不了解的代码，不重复造已有的轮子。

### 2. 验收标准先行

- 把需求翻译成可验证的验收条件
- 每条验收条件对应一个测试或一条可执行的验证命令
- 边界条件写清楚：空输入、超长输入、并发、失败路径

### 3. 最小改动实现

- 一次只做一个内聚的变更，不做顺手重构
- 保持与周边代码风格一致
- 改动点用注释说明原因，不解释显而易见的事

### 4. 分层测试

- 先跑变更相关的聚焦测试
- 再跑全量回归
- 输出留存：测试命令、通过/失败明细、覆盖变化

### 5. 交付与留痕

- 变更摘要：改了什么、为什么、影响面
- 验证记录：跑过的测试与结果
- 若有安全敏感改动，转 `eni-code-security-workflow` 走复核

## 质量门槛

- 无遗留 TODO 与调试输出
- 新代码有测试覆盖
- 不破坏既有接口契约
- 提交信息说明动机而非罗列文件

## 证据要求

- 命令、版本、哈希、证据路径、假设与验证结果全程留痕
- 长跑前持久化检查点

## 衔接

- 任务触及信任边界或依赖面 → 链入 `eni-code-security-workflow`
- 收尾交付走 `eni-universal-workflow` 的 deliver 阶段
