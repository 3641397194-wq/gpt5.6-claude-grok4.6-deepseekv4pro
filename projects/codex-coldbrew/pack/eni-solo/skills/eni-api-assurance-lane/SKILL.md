---
name: eni-api-assurance-lane
description: "[DOCUMENTATION ONLY] [仅文档] API assurance workflow for sequential eni-solo execution."
---

# API 保障工作流

> 仅文档：本 Skill 提供阶段方法，不自带审批或打分引擎。

## 定位

面向 API 的按序执行保障车道，阶段固定、顺序执行，适配 eni-solo 串行执行模式。

## 阶段链

`contract-discovery → auth-session-model → authorization-matrix → negative-tests → reproduce → evidence → remediation → regression → verify → deliver`

### 1. contract-discovery 契约发现

- 汇总 OpenAPI/Swagger/GraphQL SDL/流量记录，形成接口清单
- 每个端点记录：方法、路径、参数、认证要求、角色假设

### 2. auth-session-model 认证会话建模

- 画出认证状态机：匿名、登录、特权、过期
- 明确每类会话能访问什么

### 3. authorization-matrix 授权矩阵

- 用"身份 × 端点 × 对象"三维矩阵列出预期结果
- 矩阵本身成为后续测试的断言来源

### 4. negative-tests 负向测试

- 逐单元格验证越权、缺权、边界输入
- 攻击组与控制组成对执行

### 5. reproduce 复现

- 每个异常结果用最小请求复现
- 记录环境差异与偶然因素

### 6. evidence 证据

- 请求/响应、时间戳、身份上下文、哈希归档
- 证据编号与矩阵单元格绑定

### 7. remediation 修复

- 按根因给出修复方案，标注修复层

### 8. regression 回归

- 修复后重跑相关矩阵单元格

### 9. verify 验证

- 用精确复测请求确认行为符合预期

### 10. deliver 交付

- 输出：接口清单、矩阵、发现、证据、修复与复测记录

## 工具使用

直接使用环境中可用的请求、代理、浏览器与测试工具，不假设特定产品。

## 衔接

- 深度测试方法参考 `eni-api-security`
- 收尾交付走 `eni-universal-workflow` 的 deliver 阶段
