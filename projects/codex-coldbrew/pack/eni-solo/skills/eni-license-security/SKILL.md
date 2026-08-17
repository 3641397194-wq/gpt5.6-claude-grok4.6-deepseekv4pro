---
name: eni-license-security
description: 全局自动路由 | 许可证、激活、订阅、卡密、权益与设备绑定的安全设计与逆向审计。覆盖在线与离线验证、签名许可证、密钥签发、激活 API、重放、时钟回拨、共享密钥提取、客户端补丁、设备身份、吊销与欺诈遥测。
---

# Cold Coffee License Security

把许可证体系当作"权益与信任"问题来建模，而不是当作客户端里的一次字符串比较。

## 启动步骤

1. 识别产品、客户端、服务端、运营/管理端、支付渠道、密钥存储、权益存储、设备身份与更新通道。
2. 追踪签发、激活、验证、刷新、吊销、转移、过期与恢复各条流程。
3. 标记每一个客户端可控的值，以及每一个缺少服务端证据的判定点。
4. 定位内嵌密钥、公钥、签名、时钟、缓存、防重放字段、错误路径与离线宽限行为。

## 参考资料选择

- 威胁与逆向分析切入点：读 `references/threat-model.md`。
- 安全在线/离线设计：读 `references/secure-design.md`。
- 二进制/客户端/API 逆向审计：读 `references/reverse-audit.md`。
- 运营、泄露、转售、吊销与遥测：读 `references/operations.md`。

## 工具

- 用 `scripts/license_tool.py` 生成 Ed25519 密钥、签发带签名的许可证文档，并在参考实现中验证。
- 用 `scripts/audit_license_config.py` 标记 JSON 设计/配置描述中的高风险架构选择。
- 与 `$eni-reverse-deep`、`$eni-pentest-advanced`、`$eni-case-lab` 组合，用于客户端二进制、激活 API 与证据管理。

## 交付

返回信任地图、攻击假设、提取出的验证流程、密钥/密钥材料放置、重放与时钟行为、补丁点、滥用路径、安全架构、迁移计划、参考代码、遥测方案与回归用例。
