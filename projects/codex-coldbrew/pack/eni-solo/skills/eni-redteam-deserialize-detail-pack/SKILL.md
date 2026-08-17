---
name: eni-redteam-deserialize-detail-pack
description: "[DOCUMENTATION ONLY] [仅文档] 授权范围内不安全反序列化测试的领域路由与边界手册，覆盖 Java、PHP、Python、.NET 与 gadget chain 分析。当任务落入反序列化测试领域、需要明确范围、证据、转向或退出标准时加载。"
---

# 反序列化漏洞纵深手册

> 文档性质：本手册属于纯文档资源（DOCUMENTATION ONLY / 仅文档），提供方法框架与检查清单，不捆绑任何可执行脚本。

## 一、手册职责与领域声明

当前任务归类于 **反序列化漏洞测试** 领域，测试范围限定在不安全反序列化面：Java、PHP、Python、.NET 的序列化机制与 gadget chain 构造等。

本手册只为代理解决三件事：划清测试边界、受阻时给出转向选项、收尾时卡住证据质量。它不教授固定攻击步骤，不替代用户授权范围，不把任何推测当作结论。

若 scope、target 或授权边界未明确，任务直接进入 blocked 或 plan-only 状态，不进行真实执行。

## 二、攻击面地形

反序列化的危险来自"数据被还原成可执行语义"。凡是接受序列化对象的入口——Cookie、请求体、消息队列、RPC 参数、文件上传——都在攻击面上。判型靠特征字节：Java 以 AC ED 00 05 开头，PHP 常见 O: 与 a: 前缀，Python pickle 有特定协议头，.NET BinaryFormatter 有对象图结构。有了类型才能选 chain，有了 chain 才能谈利用。

| 入口 | 典型载体 | 观察方式 |
|------|---------|---------|
| Cookie/参数 | base64 编码的序列化对象 | 解码后特征字节识别 |
| 请求体 | XML/JSON/二进制格式 | 类型标注与解析路径 |
| RPC/消息 | 跨服务对象传递 | 序列化边界与协议分析 |
| 文件上传 | 序列化文件、存档格式 | 上传点解析链路检查 |
| 盲执行面 | 无回显环境 | 延时、DNS/HTTP 带外探测 |

## 三、变体速览

| 变体 | 触发条件 | 高价值场景 |
|------|---------|-----------|
| Java | Commons-Collections/JNDI | 经典 gadget 直取 RCE |
| PHP | __wakeup/__destruct 链 | 魔术方法触发文件操作 |
| Python | pickle/yaml.load | 对象构造注入 |
| .NET | TypeNameHandling/BinaryFormatter | 类型解析链命令执行 |

## 四、执行纪律与禁区

- 只围绕用户明确提供或授权的目标工作，不超出目标域名、IP、应用或系统边界。
- 不得通过 RCE 执行破坏性操作。
- 证据纪律：不伪造、不夸大、不补写不存在的证据；不在缺少证据时声明任务完成。
- 不把候选风险、公开 CVE 或组件指纹直接等同于可利用漏洞——指纹只是线索，验证才是结论。
- 若 scope、target 或授权边界不明确，进入 blocked 或 plan-only，不进行真实执行。

## 五、受阻转向

- 序列化格式未知 → 检查特征字节（AC ED 00 05=Java、O:/a:=PHP），解码 Cookie 与参数中的 base64。
- 已知 gadget 不可用 → 尝试不同库版本的 chain、JNDI 注入、二次反序列化。
- WAF 拦截 payload → 编码变体、分块传输、Content-Type 混淆。
- 所有反序列化点均安全 → 记录已测试点，回退到上级知识库重新选择测试方向。

## 六、收尾与证据标准

### 正向退出（有发现）

- 关键结论至少具备 supported 级证据；漏洞成立、影响判断或最终报告必须有 verified 级证据。
- 交付 reproduction 证据包，须包含：完整请求（含序列化 payload）；RCE、文件读取或 SSRF 执行证明；gadget chain 标注与影响评估。
- 每份 artifact 能说明来源、目标、时间、观察结果和判断依据。

### 负向退出（未发现）

- 最少尝试次数：3。
- 记录已测试反序列化点与失败原因，提交 negative report 后回退上级。
- 措辞纪律：只输出"当前证据下未发现"，不输出"确认不存在"。
