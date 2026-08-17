# CI/CD 管道安全审计

## 威胁视角

按"谁在攻击管道"组织审计，而不是按组件清单：

| 攻击者视角 | 典型手法 | 审计焦点 |
|------|---------|---------|
| 外部 PR 提交者 | 利用触发器拿到 secrets、注入脚本 | `pull_request_target` 用法、用户输入进 shell |
| 内部开发者 | 绕过评审、直接改制品 | 分支保护、强制评审、制品不可篡改 |
| 恶意依赖 | 构建期执行恶意代码 | 依赖来源锁定、构建环境网络控制 |
| 泄露的密钥 | 用长期密钥冒名推送 | 密钥轮换、OIDC 短期凭据 |
| 坏镜像 | 替换基础镜像 | digest 固定、签名验证 |
| 供应链上游 | 投毒流行组件 | 锁文件审查、第三方 Action 审计 |

## 审计清单

### 1. Pipeline as Code 配置

```yaml
# 危险模式示例
on:
  pull_request_target:  # 可访问 secrets 的 PR 触发
    types: [opened]

- run: echo "${{ github.event.issue.title }}"  # 用户输入 → shell

permissions: write-all

# 安全模式示例
on:
  pull_request:  # 无 secrets 访问
    types: [opened]

- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # 固定 SHA

permissions:
  contents: read
```

### 2. 密钥治理

```bash
# 历史提交扫密钥
gitleaks detect --source . --verbose
trufflehog git file://. --only-verified

# 检查 Secrets 清单
gh secret list
# 确认: 无硬编码、定期轮换、最小权限

# 运行时注入
# ✅ OIDC 替代长期密钥
# ✅ Secrets 只暴露给需要的步骤
```

### 3. 构建完整性

```bash
# 生成不可篡改的构建记录（SLSA L2+）
slsa-provenance generate --source . --output provenance.json

# 制品签名
cosign sign-blob --key cosign.key artifact.tar.gz

# 验证
cosign verify-blob --key cosign.pub --signature artifact.tar.gz.sig artifact.tar.gz
```

### 4. Runner 安全

```text
□ 是否使用托管 Runner（每次全新环境，推荐）
□ Self-hosted Runner 是否隔离在专用 VM/容器
□ 是否运行过 fork PR（self-hosted 风险极高）
□ Runner 出站网络是否受限
□ 构建缓存是否可能跨构建泄漏
```

### 5. 依赖拉取

```text
□ npm: package-lock.json 是否提交？禁止 --force / --legacy-peer-deps
□ pip: requirements.txt 是否冻结版本？禁止从未验证源安装
□ Docker: FROM 是否固定 digest？禁止 latest tag
□ Go: go.sum 是否提交？
□ 私有包: 注册表认证是否用短期 token？
```

## 自动化检查流水线

```yaml
# .github/workflows/supply-chain.yml
name: Supply Chain Security
on: [push, pull_request]

jobs:
  sca:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: SBOM Generate
        run: |
          npm install -g @cyclonedx/cdxgen
          cdxgen -o sbom.json

      - name: OSV Scan
        run: |
          go install github.com/google/osv-scanner/cmd/osv-scanner@latest
          osv-scanner scan --sbom sbom.json --format sarif > osv-results.sarif

      - name: Trivy Scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: fs
          severity: CRITICAL,HIGH
          exit-code: 1

      - name: Secret Scan
        run: |
          docker run --rm -v $PWD:/src ghcr.io/gitleaks/gitleaks:latest \
            detect --source /src --verbose

      - name: Dependency-Track Upload
        run: |
          curl -X POST https://dtrack.example.com/api/v1/bom \
            -H "X-Api-Key: ${{ secrets.DTRACK_API_KEY }}" \
            -F "autoCreate=true" -F "project=myapp" -F "bom=@sbom.json"
```

参考：SLSA Framework、OWASP CI/CD Top 10、GitHub Security Lab。
