---
name: eni-game-security
description: 全局自动路由 | 防御性游戏安全与作弊研究，覆盖外部与内部作弊架构、trainer、内存篡改、ESP/overlay、瞄准自动化、注入与 hook、封包篡改、反作弊遥测、完整性、Unity IL2CPP、Unreal、事件分析与检测验证。
---

# Cold Coffee Game Security

从信任边界到可观测行为梳理滥用路径，然后落地检测与加固。

## 启动步骤

1. 识别引擎、平台、架构、网络模型、权威状态、反作弊组件与可用工件。
2. 对技术分类：外部内存、注入/内部、输入自动化、overlay/ESP、运行时补丁、封包/协议、资产/配置、内核/驱动、DMA/硬件或账户/经济滥用。
3. 映射所需的访问能力、被修改的状态、数据来源、持久化/生命周期与可观测痕迹。
4. 只复现验证检测或防御假设所需的最小行为。

## 参考资料选择

- 作弊类别、数据流与可观测面：读 `references/cheat-architecture.md`。
- 反作弊架构与控制点放置：读 `references/anti-cheat-design.md`。
- Unity/IL2CPP 与 Unreal 分析：读 `references/engine-security.md`。
- 调查与证据：读 `references/incident-analysis.md`。

## 工具

- 用 `scripts/integrity_manifest.py` 创建或校验签名文件哈希清单。
- 用 `scripts/telemetry_analyze.py` 汇总玩家/输入遥测并标记可解释的异常指示器。
- 与 `$eni-reverse-deep`、`$eni-memory-forensics`、`$eni-case-lab` 组合，用于二进制、运行时状态与证据管理。

## 交付

返回技术分类、信任边界失效点、所需能力、可观测痕迹、复现装置、完整性/遥测检查、误报考量、缓解方案与回归计划。明确区分"检测假设"与"已确认的作弊工件"。
