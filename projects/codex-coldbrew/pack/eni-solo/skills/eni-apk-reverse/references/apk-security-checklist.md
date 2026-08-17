# APK 安全测试速查

> 参照 OWASP MASTG 的测试维度组织：静态审计、动态观察、通信安全、数据存储、认证授权、保护强度六个面。
> 配套：`android-advanced.md`（深度分析）、`frida-cookbook.md`（插桩脚本）。

---

## 一、静态审计

### Manifest 逐项过

```text
□ android:debuggable="true"            → 可调试（生产包不应出现）
□ android:allowBackup="true"           → 数据可备份导出
□ android:exported="true" 的组件       → 暴露的 Activity/Service/Receiver/Provider
□ 自定义权限 protectionLevel           → 是否 normal（应为 signature）
□ intent-filter 里的 scheme            → 自定义 deeplink 是否可劫持
□ android:usesCleartextTraffic="true"  → 允许明文 HTTP
□ minSdkVersion 过低                   → 可能缺少安全特性
```

### 代码审计要点

```text
□ 硬编码密钥/Token（搜 "key"、"secret"、"password"、"api_key"）
□ 弱随机源（java.util.Random 而非 SecureRandom）
□ 弱加密（ECB 模式、DES、MD5 用于口令）
□ WebView 配置（setJavaScriptEnabled + addJavascriptInterface = RCE 风险）
□ SQL 注入（rawQuery 拼接用户输入）
□ 路径遍历（ContentProvider 的 openFile 未校验路径）
□ 日志泄露（Log.d/Log.i 输出敏感信息）
□ 剪贴板泄露（ClipboardManager 存敏感数据）
□ 隐式 Intent 泄露（sendBroadcast 未指定包名）
```

### 第三方库审计

```text
□ OkHttp/Retrofit 版本过旧（已知漏洞）
□ WebView 内核过旧
□ 含已知 CVE 的 SDK
□ 广告 SDK 的数据采集范围
□ 推送 SDK 配置（是否泄露 token）
```

---

## 二、动态观察

### Frida Hook 优先目标

| 目标 | Hook 点 | 目的 |
|------|---------|------|
| 登录认证 | `LoginActivity.login()` | 观察凭证处理 |
| 签名生成 | `*Sign*`、`*sign*`、`*encrypt*` | 还原签名算法 |
| SSL Pinning | `CertificatePinner.check` | 打通抓包 |
| Root 检测 | `*root*`、`*su*`、`*magisk*` | 绕过检测 |
| 加密操作 | `javax.crypto.Cipher` | 提取密钥/IV |
| Token 存储 | `SharedPreferences.getString` | 观察 token 读写 |
| 网络请求 | `OkHttpClient.newCall` | 观察请求构造 |

### Frida 一行命令

```bash
frida-trace -U -f com.target.app -j '*Cipher*!*'
frida-trace -U -f com.target.app -j '*OkHttp*!*'
frida-trace -U -f com.target.app -j '*SharedPreferences*!*'
frida-trace -U -f com.target.app -i 'Java_*'
```

### Objection 速用

```bash
objection -g com.target.app explore

android hooking list activities
android hooking list services
android sslpinning disable
android root disable
android clipboard monitor
env
sqlite connect <db_path>
```

---

## 三、通信安全

### 抓包三条路线

```text
路线 1: 系统代理 + Burp/mitmproxy
- WiFi 代理指向 Burp
- CA 证书装进设备
- Android 7+ 需 network_security_config 或 Frida 绕过

路线 2: VPN 模式
- HttpCanary / Packet Capture
- 免 root 免代理
- 解不开 SSL Pinning 流量

路线 3: Frida + r2frida
- 进程内拦截网络调用
- 不受代理/VPN 限制
```

### 检查项

```text
□ 所有 API 是否 HTTPS
□ 是否做 SSL Pinning
□ 证书校验是否拒绝自签名
□ 是否做证书透明度（CT）检查
□ API 密钥是否明文传输
□ Token 是否过期机制
□ 请求是否有签名防篡改
□ 是否有重放防护（nonce/timestamp）
□ WebSocket 是否加密
□ 敏感数据是否出现在 URL 参数（会进日志）
```

---

## 四、数据存储

### 检查位置

| 位置 | 风险 | 检查命令 |
|------|------|---------|
| SharedPreferences | 明文存 token/口令 | `adb shell cat /data/data/pkg/shared_prefs/*.xml` |
| SQLite | 未加密敏感数据 | `adb pull /data/data/pkg/databases/` |
| 外部存储 | 任何应用可读 | `adb shell ls /sdcard/Android/data/pkg/` |
| 应用日志 | 泄露调试信息 | `adb logcat \| grep pkg` |
| 备份文件 | allowBackup=true | `adb backup -f backup.ab pkg` |
| 键盘缓存 | 输入历史 | 检查 `inputType` 是否 `textPassword` |
| 截图保护 | 敏感页可截图 | 检查 `FLAG_SECURE` |

### 加密存储方案对比

| 方案 | 安全性 | 说明 |
|------|--------|------|
| SharedPreferences 明文 | ❌ | root 后直接读 |
| EncryptedSharedPreferences | ✓ | AndroidX Security 库 |
| SQLCipher | ✓ | 加密 SQLite |
| Android Keystore | ✓✓ | 硬件级密钥保护 |
| 自定义 AES | ⚠️ | 安全性取决于密钥管理 |

---

## 五、认证与授权

### 常见漏洞

| 漏洞 | 测试方法 |
|------|---------|
| 弱密码策略 | 尝试 123456、password 等 |
| 无锁定机制 | 暴力破解登录接口 |
| Token 不过期 | 登出后重放旧 token |
| 越权访问 | 修改请求中的 user_id |
| 短信验证码可爆破 | 4/6 位数字无频率限制 |
| OAuth 配置错误 | redirect_uri 可篡改 |
| 生物认证绕过 | Hook BiometricPrompt |
| 设备绑定绕过 | 修改 device_id |

### 测试 Payload

```bash
# 越权测试
curl -H "Authorization: Bearer USER_A_TOKEN" \
     "https://api.target.com/users/USER_B_ID/profile"

# Token 重放：登录→登出→旧 token 请求（应 401）

# 短信验证码爆破
for code in $(seq 0000 9999); do
    curl -X POST "https://api.target.com/verify" \
         -d "phone=13800138000&code=$code"
done
```

---

## 六、保护强度评估

| 保护措施 | 检测方法 | 绕过难度 |
|---------|---------|---------|
| ProGuard 混淆 | jadx 看类名是否 a/b/c | 低（仅重命名） |
| 字符串加密 | 搜解密函数，Hook 取明文 | 中 |
| 反调试 | 尝试 attach debugger | 中（Frida 可绕过） |
| Root 检测 | root 设备上运行 | 中（通用脚本绕过） |
| 模拟器检测 | 模拟器上运行 | 低-中 |
| 完整性校验 | 修改 APK 后安装 | 中（patch 校验函数） |
| 加固/壳 | 看入口类和 .so | 中-高（需脱壳） |
| Native 保护 | 核心逻辑在 .so | 高（需 IDA 分析） |
| VMP 虚拟化 | 代码虚拟化执行 | 极高 |

---

## 七、30 分钟快速流程

```text
1. [5min] 解包 + Manifest 审计
   apktool d app.apk
   检查 debuggable/allowBackup/exported/cleartext

2. [10min] 代码快速审计
   jadx -d out app.apk
   搜索: password, key, secret, token, http://

3. [5min] 网络测试
   配代理 → 操作 APP → 看是否有明文/弱加密

4. [5min] 存储检查
   adb shell → 看 shared_prefs 和 databases

5. [5min] 动态验证
   Frida hook 关键函数 → 确认发现
```
