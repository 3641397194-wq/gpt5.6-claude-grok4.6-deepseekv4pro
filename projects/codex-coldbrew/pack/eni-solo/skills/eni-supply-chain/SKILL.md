---
name: eni-supply-chain
description: "[DOCUMENTATION ONLY] [仅文档] 全局自动路由 | 软件供应链安全测试：SBOM 生成与审计、SCA 依赖扫描、CI/CD 管道安全、容器镜像安全、构建产物溯源与完整性验证。"
---

> 仅文档：本 Skill 提供方法与检查表，不宣称自带可执行脚本。

# 软件供应链安全测试

> 主题：SBOM、SCA、CI/CD 管道、依赖溯源、制品完整性
> 背景法规：美国行政令 SBOM 要求、中国国标、EU CRA

## 本技能解决的问题

供应链风险不来自你写的代码，而来自你引入的一切：依赖、基础镜像、构建工具、第三方 Action、构建基础设施。本技能覆盖从源码引入到运行时部署的全链路核查。

## 信任链条的七个环节

```text
环节一: 上游源码信任 —— 仓库活跃度、维护者声誉、历史安全事件
环节二: 依赖解析与锁定 —— lockfile 完整性、版本固定、私源认证
环节三: 构建管道 —— 触发器安全、密钥最小化、Runner 隔离
环节四: 制品签名与溯源 —— 构建记录、SLSA 级别、签名验证
环节五: 制品分发 —— 校验和、SBOM 附带、仓库权限
环节六: 部署与运行 —— 镜像扫描、准入控制、运行时监控
环节七: 持续响应 —— CVE 订阅、修复流程、回滚预案
```

七个环节任一处失守，下游全部白费。

## 工作流

### 第一步：生成物料清单

```text
按制品类型选生成器：
□ 源码目录 → cdxgen 出 CycloneDX
□ 容器镜像 → syft 出 SPDX 或 CycloneDX
□ 微软工具链场景 → sbom-tool generate

清单要回答：
□ 每个组件的确切版本与来源
□ 直接依赖与传递依赖的层级
□ 许可证清单与冲突点
□ 已停止维护的组件
□ 未经授权的意外引入
```

### 第二步：漏洞匹配

```bash
# 对 SBOM 或源码树做匹配
osv-scanner scan -r . --format json

# 企业持续监控
docker run -p 8080:8080 dependencytrack/apiserver
# 上传 SBOM 后自动对 NVD/OSV/GitHub Advisory

# 商用线
snyk test --all-projects
snyk monitor

# 全场景扫描
trivy fs .
trivy image nginx
trivy config .
```

### 第三步：可达性判定

扫描告警里大多数并不可达。把告警过滤成"真风险"：

1. 拉取 CVE 清单，筛 CVSS ≥ 7.0
2. 对带 PoC 的条目做路径分析（CodeQL 数据流、CPG 切片、DEPTEX 语义判定）
3. 隔离环境跑 PoC 验证
4. 只按"可达 + 有影响"排序修复队列

### 第四步：构建管道加固

```text
各卡点对应动作：
□ 提交时: gitleaks 扫密钥
□ PR 时: SCA 扫描（Trivy/OSV-Scanner）
□ 构建后: cosign 签名制品
□ 推送时: syft 附 SBOM
□ 部署时: OPA/Kyverno 准入 + 镜像扫描
□ 运行期: Dependency-Track 持续跟踪

管道自身：
□ Pipeline as Code 配置注入审计
□ Runner 隔离与出站限制
□ Secrets 最小暴露（OIDC 优先于长期密钥）
□ 第三方 Action 锁 commit SHA
```

### 第五步：镜像与制品

```bash
# Dockerfile 静态检查
hadolint Dockerfile

# 分层扫描
trivy image --severity HIGH,CRITICAL nginx:latest

# 基础镜像策略：distroless > alpine > slim，禁 latest
docker scout quickview nginx:latest

# 签名闭环
cosign sign --key cosign.key myimage:tag
cosign verify --key cosign.pub myimage:tag
```

### 第六步：新依赖准入

新增依赖前过五问：

- 维护活跃度：近 6 个月有无提交，issue 响应速度
- 安全履历：有无恶意植入历史
- 引入代价：新增多少传递依赖
- 许可证：与项目许可证是否兼容
- 替代评估：Snyk Advisor / Socket.dev 评分对比

### 第七步：持续监控与响应

- 每日刷新 SBOM 并重扫
- CVE 订阅到组件级
- 修复分级：可达 + 有 PoC 的 P0，其余按窗口排期
- 应急预案：恶意版本回滚路径提前演练

## 工具矩阵

| 工具 | 定位 | 免费 | 安装 |
|------|------|:--:|------|
| OWASP Dependency-Track | 企业级持续 SCA | 是 | `docker pull dependencytrack/apiserver` |
| OSV-Scanner | 轻量漏洞匹配 | 是 | `go install github.com/google/osv-scanner` |
| Trivy | 镜像/依赖/IaC 三合一 | 是 | `apt install trivy` |
| Syft | SBOM 生成 | 是 | 官方脚本安装 |
| cdxgen | CycloneDX 生成 | 是 | `npm install -g @cyclonedx/cdxgen` |
| Cosign | 签名与验证 | 是 | `go install github.com/sigstore/cosign/v2/cmd/cosign` |
| Gitleaks | 密钥扫描 | 是 | `go install github.com/gitleaks/gitleaks/v8` |
| Snyk | 商用 SCA + 可达性 | 否 | `npm install -g snyk` |
| CodeQL | 代码级数据流 | 是 | GitHub Actions 内置 |

## 参考

- `references/sbom-sca-methodology.md` — 清单与匹配方法论
- `references/cicd-pipeline-security.md` — 构建管道审计细则
