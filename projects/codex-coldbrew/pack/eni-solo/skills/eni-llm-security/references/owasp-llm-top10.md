# OWASP LLM 与 Agentic AI 风险清单对照

本文件把 OWASP Top 10 for LLM Applications v2.0（2025）与 OWASP Top 10 for Agentic Applications（ASI 2026）两套清单并排整理，供测试与防御对照使用。

## LLM 应用十大风险（2025 版）

| # | 风险 | 问题实质 | 测试切入 |
|---|------|---------|---------|
| LLM01 | Prompt Injection | 构造输入操控模型行为 | 直接注入、间接注入、编码绕过 |
| LLM02 | Sensitive Information Disclosure | PII/API Key/训练数据泄漏 | 提示词提取、输出分析 |
| LLM03 | Supply Chain | 投毒模型/库/数据集 | 模型来源验证、依赖扫描 |
| LLM04 | Data & Model Poisoning | 训练/微调数据后门 | 数据溯源、行为异常检测 |
| LLM05 | Improper Output Handling | 输出导致 XSS/SQLi/RCE | 下游系统注入测试 |
| LLM06 | Excessive Agency | 工具/自主权过大 | 权限审计、人在回路测试 |
| LLM07 | System Prompt Leakage | 提取隐藏指令/密钥/业务逻辑 | 级联提取、canary token |
| LLM08 | Vector & Embedding Weaknesses | RAG 管道攻击、嵌入反转 | 检索投毒、语义相似度攻击 |
| LLM09 | Misinformation | 幻觉在高风险场景构成风险 | 事实性验证、置信度校准 |
| LLM10 | Unbounded Consumption | DoS/Denial-of-Wallet | Token 消耗测试、速率限制 |

## Agentic 应用十大风险（ASI 2026）

| # | 风险 | 核心危害 | 测试切入 |
|---|------|---------|---------|
| ASI01 | Agent Goal Hijack | 恶意输入/工具输出劫持目标 | 指令覆盖、目标篡改 |
| ASI02 | Tool Misuse & Exploitation | 合法工具的非预期使用 | 工具链拼接、参数注入 |
| ASI03 | Identity & Privilege Abuse | Agent 越权操作 | 凭证窃取、委派链测试 |
| ASI04 | Agentic Supply Chain | MCP 描述符/第三方工具实时风险 | 动态供应链扫描 |
| ASI05 | Unexpected Code Execution | 提示→工具→脚本 RCE 链 | 多层代码执行测试 |
| ASI06 | Memory & Context Poisoning | 长期记忆/嵌入投毒 | 记忆持久化攻击 |
| ASI07 | Insecure Inter-Agent Communication | 智能体间通信篡改 | 中间人、重放攻击 |
| ASI08 | Cascading Failures | 单点故障引发系统级崩塌 | 故障传播测试 |
| ASI09 | Human-Agent Trust Exploitation | 操纵操作员批准危险操作 | 权威偏差/紧迫感测试 |
| ASI10 | Rogue Agents | 自我复制/持续恶意行为 | 持久化后门检测 |

## 实测分布参考

多份真实评估报告给出的发现分布呈现同一趋势：

- Prompt Injection（LLM01）约占四成到一半
- 敏感信息披露类约占两成
- 过度代理（权限过大）类约占一成半
- 其余风险分摊剩余部分

分布数据随被测系统形态浮动，只用于排优先级，不作为结论依据。

## 防御原则

1. **规划与执行分离** — 解释意图的模型 ≠ 执行动作的模型
2. **身份/目的/范围/时效四绑定** — 不使用宽泛的环境权限
3. **记录一切** — 工具调用、记忆、通信作为一等安全遥测
4. **爆炸半径控制** — 熔断、回滚、紧急停止优先于便利性
5. **所有自然语言输入不可信** — 含检索到的外部内容
6. **输出同样不可信** — 渲染、执行、查询前先消毒
