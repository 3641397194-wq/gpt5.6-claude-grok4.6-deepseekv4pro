---
name: eni-redteam-recon-intake
description: "[DOCUMENTATION ONLY] [仅文档] 侦察入口技能：处理裸域名、URL 或 IP 地址的首次接触。用于建立初始 recon_profile，并为 CVE 查询与攻击路径路由提供事实输入。"
---

# 侦察入口

> 文档性质：本手册属于纯文档资源（DOCUMENTATION ONLY / 仅文档），提供方法框架与检查清单，不捆绑任何可执行脚本。

## 一、本技能的位置

当目标以裸域名、URL 或 IP 地址的形式首次进入评估流程时，本技能负责从零建立资产画像（recon_profile），为下游的 CVE 查询与攻击路径分配提供事实依据。

## 二、工作序列

1. DNS 解析与存活探测。
2. 端口扫描与服务指纹。
3. 子域枚举。
4. Web 目录与敏感文件探测。
5. WAF/CDN 识别。
6. 技术栈指纹（CMS、框架、中间件版本）。

## 三、执行纪律

- 不执行任何主动漏洞利用。
- 不发送破坏性请求（DELETE、DROP、shutdown）。
- 不进行暴力破解或密码喷洒。
- 不绕过速率限制；如被限速则降速或暂停。
- 侦察深度止于信息收集，不进入漏洞验证阶段。

## 四、受阻转向

- WAF/CDN 阻断直连 → 尝试历史 DNS、邮件头、证书搜索获取真实 IP。
- 子域枚举受限 → 证书透明度日志、DNS 区域传送、关联域反查。
- 目录扫描被封 → 降速、换 User-Agent、使用自定义字典。
- 端口全部过滤 → 检查 IPv6、尝试常见高端口、确认目标存活。
- 信息收集饱和 → 整理已有信息，输出 recon_profile 并推进到下一阶段。

## 五、收尾与证据标准

- Required: recon_profile, port_scan_result, service_fingerprint
- min_attempts: 4
