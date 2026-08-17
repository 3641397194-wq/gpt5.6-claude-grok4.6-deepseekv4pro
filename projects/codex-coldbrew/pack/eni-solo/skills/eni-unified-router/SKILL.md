---
name: eni-unified-router
description: "Deterministic eni-solo router. Use at the start of every substantive prompt to select exactly one workflow, print its stages, and load one primary Skill."
---

# eni-solo 确定性路由

## 定位

所有实质任务的第一入口。任务开始前先路由，路由结果决定后续一切执行顺序。

## 调用方式

```bash
python scripts/router.py --prompt "<complete user prompt>" --json
```

要求：

- 传入完整用户提示，不做截断或改写
- 返回 JSON 中的 `route_receipt` 作为第一条可见回复输出
- 按返回的阶段序列顺序执行，每个阶段切换处输出 `[STAGE] <stage>` 标记

## 路由语义

- **恰好一个工作流**：每个任务只命中一个工作流，不存在多选
- **确定性**：同样的提示必须得到同样的路由结果
- **唯一主技能**：路由只加载一个主 Skill，其余按需参考
- **无拆分与审批**：没有 worker 拆分、审批门、join 节点与自动升级代次

## 阶段执行约定

- 阶段序列由路由收据给出，执行时不增、不减、不改序
- 每个阶段完成时输出：产出物、证据、下一阶段
- 阶段间的状态沿用同一案件上下文

## 路由失败处理

- 路由无命中时回退 `eni-universal-workflow`
- 提示过短或信息缺失时按占位符约定补齐后重试路由

## 衔接

- 下游：`eni-core` 承接路由结果并顺序执行
- 兜底：`eni-universal-workflow` 的 intake→classify→plan→execute→verify→deliver 六段链
