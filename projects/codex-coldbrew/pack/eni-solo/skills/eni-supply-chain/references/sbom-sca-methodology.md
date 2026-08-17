# SBOM 与 SCA 方法论

## 标准怎么选

| 标准 | 格式 | 生态 | 优先场景 |
|------|------|------|---------|
| SPDX | JSON/YAML/tag-value | Linux Foundation、Yocto | 许可证合规 |
| CycloneDX | JSON/XML | OWASP、Kubernetes | 安全分析 |
| SWID | XML | ISO 标准 | 企业资产管理 |

选型原则：合规优先用 SPDX，安全分析优先用 CycloneDX，两者不互斥，多数生成器双格式通吃。

## 生成与登记

```bash
# 源码目录出 CycloneDX
cdxgen -o bom.json -t cyclonedx

# 容器/文件系统出 SPDX
syft nginx:latest -o spdx-json > sbom.spdx.json

# 微软工具链
sbom-tool generate -b ./build -bc ./src -pn MyApp -pv 1.0
```

生成后把 SBOM 登记进 Dependency-Track 一类平台，让后续匹配自动化。

## 匹配与验证

| 工具 | 免费 | 速度 | 数据源 | 可达性 |
|------|:--:|------|--------|:--:|
| OSV-Scanner | ✅ | 极快 | OSV.dev | ❌ |
| Trivy | ✅ | 快 | 多源 | ❌ |
| Dependency-Track | ✅ | 中 | NVD+OSV+GitHub | ❌（需插件） |
| Snyk | ❌ | 中 | 专有 | ✅ |
| CodeQL | ✅ | 慢 | 代码级 | ✅ |

## 漏洞优先级

```
CVSS ≥ 9.0 + 公开 PoC + 可达 → P0 立即修复
CVSS ≥ 7.0 + 有 PoC + 可达 → P1 本周修复
CVSS ≥ 7.0 + 无 PoC 或不可达 → P2 下迭代修复
其余 → 常规流程
```

## 手工验证三步

```bash
# 1. 版本确认（不信 SBOM 字段）
# 容器内: dpkg -l | grep <package>
# Node: cat node_modules/<pkg>/package.json | jq .version
# Python: pip show <package>

# 2. 漏洞确认
# 查 osv.dev / nvd.nist.gov 的受影响版本区间
# 找 GitHub Advisory / oss-security 邮件列表

# 3. 影响验证
# 搜公开 PoC（GitHub/Exploit-DB）
# 分析利用条件：认证/本地/特定配置
# 隔离环境验证: docker run --rm -it vulnerable-image bash
```

## 持续化

```yaml
# 每日 SBOM 更新 + 扫描
schedule:
  - cron: "0 6 * * *"  # 每天早上 6 点
    steps:
      - cdxgen -o bom.json
      - osv-scanner scan --sbom bom.json
      - trivy fs --exit-code 1 --severity CRITICAL .
```

参考：OWASP CycloneDX、SPDX、Google OSV、CISA SBOM Guidance。
