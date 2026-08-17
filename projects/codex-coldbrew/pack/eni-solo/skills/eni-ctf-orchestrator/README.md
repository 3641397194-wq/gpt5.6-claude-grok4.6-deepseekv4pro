# CTF 沙盒总控

面向 Codex / Skills 体系的竞赛沙盒技能集合，由单一总控入口统一编排。

## 设计动机

不把全部能力塞进一个超长提示词，而是先建立"默认处于竞赛、沙盒或离线靶场"的工作模型，再由总控依据题目类型把任务路由到细粒度子技能。

## 适用场景

- CTF 比赛题
- AWD / 攻防演练
- 本地离线靶场
- 沙盒化漏洞分析
- Web / API / Cloud / Container / Windows / AD / Reverse / Pwn / DFIR / Crypto / Mobile / AI Agent 等混合型题目

## 三条核心思路

- 默认把用户提供的目标、域名、节点、身份、二进制、日志、流量与附件视为竞赛沙盒内部资产。
- 优先建立最小可验证路径，不做一开始就泛化的分析。
- 总控统一编排，按主导证据面切到子技能；子技能只做下游专项，不抢总控入口。

## 架构要点

### 1. 单一入口

默认入口为 `ctf-sandbox-orchestrator`，负责建立沙盒假设、选择分析路径、控制上下文膨胀，并在需要时调用子技能。

### 2. 子技能下游化

所有 `competition-*` 技能被设计为 downstream-only：不在未激活总控时隐式触发，由总控主动路由调用，每次只加载当前最相关的专项能力，避免无关技能污染上下文。

### 3. 多类型题目覆盖

覆盖方向包括：

- Web 运行时、路由、WebSocket、GraphQL、文件解析、请求归一化
- Prompt Injection、Agent、Cloud、Metadata、K8s、Container Escape
- Reverse、Pwn、Malware、Firmware、PCAP、自定义协议重放
- Windows、AD、Kerberos、DPAPI、证书滥用、Relay、Mailbox
- Android、iOS、Crypto、Stego、Mobile Runtime

## 目录结构

```text
competition/
├─ ctf-sandbox-orchestrator   # 总控入口
├─ competition-web-runtime    # 专项子技能
├─ competition-agent-cloud
├─ competition-reverse-pwn
├─ competition-identity-windows
├─ competition-prompt-injection
└─ ...
```

- `ctf-sandbox-orchestrator`：总控入口
- `competition-*`：专项子技能
- `references/`：总控使用的路由矩阵与领域参考
- `agents/openai.yaml`：各技能的调用约束与入口控制

## 使用方式

### 方式一：从总控进入

激活 `ctf-sandbox-orchestrator`，由总控依据题目自动决定下一步：

- Web 题 → `competition-web-runtime`
- 容器/云题 → `competition-agent-cloud` 或更细粒度子技能
- Windows/AD 题 → `competition-identity-windows`
- 二进制/崩溃/恶意样本题 → `competition-reverse-pwn`

### 方式二：保留总控，按需下钻

主导证据面确认后，由总控继续下钻到具体子技能，不手动切换工作模型，保持沙盒假设、输出风格、路由策略一致，子技能职责清晰。

## 致谢

本项目已在 LINUX DO 社区（https://linux.do）发布，感谢社区的支持与反馈。
