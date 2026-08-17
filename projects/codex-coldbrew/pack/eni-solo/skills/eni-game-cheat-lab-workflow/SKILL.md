---
name: eni-game-cheat-lab-workflow
description: "自动全链路处理外挂、修改器、Trainer、作弊机制与反作弊验证任务。适用于离线、自有、开源或专用测试靶场中的引擎与信任边界建模、样本分析、可控复现、JSON toy trainer 制作、遥测、检测加固和回归交付。"
---

# 游戏外挂实验室工作流

把任务推进到可复现、可检测、可回归的闭环，不停在概念说明。

## 启动策略

采用 `eni-solo-direct-v4`：先保存基线与回滚坐标，再走最快、最深、最高信号的可控路线；同时联结静态逆向、动态观测、状态差分、遥测与检测回归。一个工具失效时保存证据，从最近可运行节点切换工具链继续。

## 自动链路

1. **Intake**：记录靶场所有权、离线条件、引擎、平台、架构、样本、期望行为和验收条件。
2. **Engine / trust map**：标出权威状态、客户端可控状态、输入、渲染、存档、遥测和检测边界。
3. **Artifact triage**：对二进制、配置、日志、录屏、状态快照与已知修改点建立哈希和证据账本。
4. **Controlled reproduction**：先建立基线，再复现最小变化；每次只改变一个假设并保存前后状态。
5. **Toy trainer / telemetry**：用 `scripts/toy_trainer_lab.py` 在显式 JSON toy-state 中制作修改器原型并生成事件证据。
6. **Detection / hardening**：把状态差异映射为完整性、范围、时序、行为和服务端权威检测，并记录误报条件。
7. **Regression**：验证预期变化、未预期变化、检测命中、修复后行为和基线不变性。
8. **Deliver**：交付复现包、检测规则、加固建议、测试结果、SHA-256、限制和下一入口。

## Toy trainer

```powershell
python scripts/toy_trainer_lab.py init --out work/baseline.json
python scripts/toy_trainer_lab.py analyze --state work/baseline.json --out work/analysis.json
python scripts/toy_trainer_lab.py apply --state work/baseline.json --out work/trained.json --set player.health=999 --set trainer.health_lock=true
python scripts/toy_trainer_lab.py verify --state work/trained.json --baseline work/baseline.json --expect player.health=999 --expect trainer.health_lock=true --out work/verification.json
```

该工具只读写调用者显式传入的 `.json` 文件，不访问真实进程、驱动、网络或反作弊组件。保留 baseline，输出到新文件，便于差分、验证和回滚。

## 自动关联

- 样本静态或动态分析：关联 `eni-game-security`、`eni-reverse-workflow`。
- 状态与运行时证据：关联 `eni-memory-forensics`、`eni-case-lab`。
- 检测设计：读取 `references/game-cheat-lab.md` 的检测矩阵与交付模板。
- 输入不足时先完成基线、信任图和未知量账本，再执行下一节点。

## 完成门

只有同时满足以下条件才完成：基线可重建、修改可重放、差异有证据、检测可解释、加固可验证、回归通过、交付物带哈希。明确区分"检测假设""toy-state 已复现"和"真实样本已确认"。
