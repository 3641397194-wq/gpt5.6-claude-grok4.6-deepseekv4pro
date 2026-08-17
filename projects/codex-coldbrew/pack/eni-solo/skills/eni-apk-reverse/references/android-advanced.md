# Android 高级逆向参考

> 覆盖：Native SO 分析、JNI 注册机制、Frida 进阶插桩、SSL Pinning 逐框架绕过、Root 检测对抗、加固识别与脱壳、React Native/Flutter 专项。

---

## 一、Native SO 逆向

### 分析流程

```text
1. 抽取 .so
   unzip app.apk lib/arm64-v8a/*.so -d extracted/

2. 确认架构与基本信息
   file libxxx.so
   rabin2 -I libxxx.so

3. 找 JNI 入口
   - JNI_OnLoad（动态注册）
   - Java_com_xxx_yyy（静态注册）
   - nm -D libxxx.so | grep -i java

4. IDA/Ghidra 加载
   - 导入 jni.h 类型定义
   - 给 JNIEnv* 参数做标注
   - 找 RegisterNatives 调用点还原动态注册表

5. 定位关键逻辑
   - 从 Java 层 native 方法名倒追
   - 从字符串（密钥、URL、错误文案）交叉引用
   - 从 crypto 库函数（AES/MD5/SHA）调用点回溯
```

### JNI 注册的两种形态

```c
// 静态注册：符号名即 Java_包名_类名_方法名
JNIEXPORT jstring JNICALL Java_com_example_app_Security_getSign(
    JNIEnv *env, jobject thiz, jstring input) { ... }

// 动态注册：JNI_OnLoad 里 RegisterNatives 挂表
static JNINativeMethod methods[] = {
    {"getSign", "(Ljava/lang/String;)Ljava/lang/String;", (void*)native_getSign},
};

JNIEXPORT jint JNI_OnLoad(JavaVM *vm, void *reserved) {
    JNIEnv *env;
    vm->GetEnv((void**)&env, JNI_VERSION_1_6);
    jclass clazz = env->FindClass("com/example/app/Security");
    env->RegisterNatives(clazz, methods, sizeof(methods)/sizeof(methods[0]));
    return JNI_VERSION_1_6;
}
```

### IDA 里处理 JNI 的要点

```text
1. 导入类型库
   File → Load File → Parse C Header → jni.h

2. 把第一个参数标成 JNIEnv*
   参数上右键 → Set type → JNIEnv*
   之后 env->FindClass / env->GetMethodID 等调用会自动识别

3. 找 RegisterNatives
   搜索对 JNIEnv vtable 偏移 0x35C (ARM64) 的调用
   → 第三个参数是 JNINativeMethod 数组
   → 从数组里还原全部 native 函数地址
```

---

## 二、Frida 进阶用法

### Hook Native 函数

```javascript
// 拦截 libc 的 open，过滤 root 探测路径
Interceptor.attach(Module.findExportByName("libc.so", "open"), {
    onEnter: function(args) {
        this.path = args[0].readUtf8String();
        console.log("[open] " + this.path);
    },
    onLeave: function(retval) {
        if (this.path.includes("su") || this.path.includes("magisk")) {
            console.log("[open] Blocked root check: " + this.path);
            retval.replace(-1);
        }
    }
});

// 按偏移 Hook 自定义 SO 里的函数
var base = Module.findBaseAddress("libsecurity.so");
var target = base.add(0x1234);
Interceptor.attach(target, {
    onEnter: function(args) {
        console.log("arg0: " + args[0].readUtf8String());
    },
    onLeave: function(retval) {
        console.log("return: " + retval.readUtf8String());
    }
});
```

### Hook Java 方法

```javascript
Java.perform(function() {
    var Security = Java.use("com.example.app.Security");

    Security.getSign.implementation = function(input) {
        console.log("[getSign] input: " + input);
        var result = this.getSign(input);
        console.log("[getSign] output: " + result);
        return result;
    };

    Security.$init.overload('java.lang.String').implementation = function(key) {
        console.log("[Security.<init>] key: " + key);
        this.$init(key);
    };

    Security.encrypt.overload('java.lang.String', 'int').implementation = function(data, mode) {
        console.log("[encrypt] data=" + data + " mode=" + mode);
        return this.encrypt(data, mode);
    };
});
```

### 内存搜索与改写

```javascript
// 模块内搜字节序列
Process.enumerateModules().forEach(function(m) {
    if (m.name === "libtarget.so") {
        Memory.scan(m.base, m.size, "48 65 6C 6C 6F", {
            onMatch: function(addr, size) { console.log("Found at: " + addr); }
        });
    }
});

// patch 一条指令为 NOP（ARM64）
var addr = Module.findBaseAddress("libsecurity.so").add(0x5678);
Memory.patchCode(addr, 4, function(code) {
    var writer = new Arm64Writer(code, {pc: addr});
    writer.putNop();
    writer.flush();
});
```

---

## 三、SSL Pinning 绕过

### 通用组合拳

```javascript
Java.perform(function() {
    // 1. 自定义全放行 TrustManager
    var TrustManager = Java.registerClass({
        name: 'com.custom.TrustManager',
        implements: [Java.use('javax.net.ssl.X509TrustManager')],
        methods: {
            checkClientTrusted: function(chain, authType) {},
            checkServerTrusted: function(chain, authType) {},
            getAcceptedIssuers: function() { return []; }
        }
    });

    // 2. 替换默认 SSLContext
    var SSLContext = Java.use('javax.net.ssl.SSLContext');
    var sslContext = SSLContext.getInstance("TLS");
    sslContext.init(null, [TrustManager.$new()], null);

    // 3. OkHttp CertificatePinner 置空
    try {
        var CertificatePinner = Java.use('okhttp3.CertificatePinner');
        CertificatePinner.check.overload('java.lang.String', 'java.util.List').implementation = function() {};
    } catch(e) {}
});
```

### 各框架对照

| 框架 | 绕过手法 |
|------|---------|
| OkHttp3 | Hook `CertificatePinner.check` 置空 |
| Retrofit | 同 OkHttp（底层即 OkHttp） |
| Volley | Hook `HurlStack` 的 SSL 工厂 |
| Flutter | Hook `dart:io` 的 `SecurityContext`（需专项脚本） |
| React Native | Hook `OkHttpClientProvider` |
| WebView | Hook `WebViewClient.onReceivedSslError` |

### Flutter 专项

```javascript
// 定位 libflutter.so 的 ssl_verify_peer_cert 并替换返回值为 0
var flutter = Module.findBaseAddress("libflutter.so");
var pattern = "FF 03 05 D1 FD 7B 0F A9";  // ARM64 特征
Memory.scan(flutter, Module.findModuleByName("libflutter.so").size, pattern, {
    onMatch: function(address) {
        Interceptor.replace(address, new NativeCallback(function() {
            return 0;
        }, 'int', []));
    }
});
```

---

## 四、Root 检测对抗

### 检测手段与反制对照

| 检测手段 | 反制 |
|---------|------|
| 检查 `/system/app/Superuser.apk` | Hook `File.exists()` 返回 false |
| 探测 `su` 命令 | Hook `Runtime.exec()` 拦截 su 调用 |
| 读 `/proc/self/mounts` 找 magisk | Hook 文件读取过滤关键词 |
| SafetyNet/Play Integrity | Magisk Hide / Zygisk + Shamiko |
| 检查 Magisk 包名 | 随机化 Magisk 包名 |
| 检查 `/data/adb/` | Hook `opendir`/`access` |

### Frida 通用 Root 绕过

```javascript
Java.perform(function() {
    var File = Java.use("java.io.File");
    File.exists.implementation = function() {
        var path = this.getAbsolutePath();
        var blacklist = ["su", "Superuser", "magisk", "busybox", "xposed"];
        for (var i = 0; i < blacklist.length; i++) {
            if (path.toLowerCase().includes(blacklist[i])) {
                return false;
            }
        }
        return this.exists();
    };

    var System = Java.use("java.lang.System");
    System.getProperty.overload('java.lang.String').implementation = function(key) {
        if (key === "ro.debuggable" || key === "ro.secure") {
            return "1";
        }
        return this.getProperty(key);
    };
});
```

---

## 五、加固识别与脱壳

### 常见加固厂商特征

| 加固 | 识别特征 | 脱壳路径 |
|------|---------|---------|
| 360 加固 | `libjiagu.so`、`com.stub.StubApp` | FART / Frida dump dex |
| 腾讯乐固 | `libshell*.so`、`com.tencent.StubShell` | FART / BlackDex |
| 梆梆加固 | `libDexHelper.so`、`com.secneo.apkwrapper` | FART |
| 爱加密 | `libexec.so`、`s.h.e.l.l` | Frida dump |
| 网易易盾 | `libnesec.so` | Frida dump |
| 娜迦 | `libnaga.so` | Frida dump |

### 通用脱壳路线

```text
路线 A: FART（ART 环境脱壳）
- 刷 FART ROM 或使用 Frida 版 FART
- 自动 dump 所有 ClassLoader 加载的 dex

路线 B: Frida DEX Dump
- frida -U -f com.target.app -l dex_dump.js
- 在 DexFile::OpenMemory 处 hook，dump 内存中的 dex

路线 C: BlackDex
- 免 root 脱壳工具
- 安装 BlackDex APK，选择目标应用脱壳

路线 D: 手动 dump
- Frida 枚举所有 ClassLoader
- 定位应用 ClassLoader → 取 DexFile 对象
- 读 dex 内存区域并保存
```

### Frida DEX Dump 脚本

```javascript
Java.perform(function() {
    Java.enumerateClassLoaders({
        onMatch: function(loader) {
            try {
                var dexFiles = loader.getDexFileList();
                console.log("ClassLoader: " + loader);
                console.log("  DEX files: " + dexFiles);
            } catch(e) {}
        },
        onComplete: function() {}
    });
});
```

---

## 六、React Native / Flutter 逆向

### React Native

```text
1. 解压 APK → assets/index.android.bundle（JS 代码）
2. 格式化 JS → 搜 API 地址、密钥、签名逻辑
3. 有 Hermes 字节码（.hbc）→ 用 hermes-dec 反编译
4. Hook: Frida hook Java 层的 ReactBridge
```

### Flutter

```text
1. Flutter 代码编译为 libapp.so（Dart AOT）
2. 无法直接反编译为 Dart 源码
3. 分析手段：
   - reFlutter：patch libflutter.so 获取 snapshot
   - Doldrums：解析 Dart snapshot 恢复类/函数信息
   - Frida hook libflutter.so 关键函数
4. 网络分析：Flutter 不走系统代理，SSL 需专项处理
```

---

## 七、工具速查

| 工具 | 用途 | 安装 |
|------|------|------|
| jadx | Java 反编译 | 已在 bootstrap 中 |
| apktool | 解包/重打包 | 已在 bootstrap 中 |
| Frida | 动态插桩 | `pip install frida-tools` |
| Objection | Frida 封装（更易用） | `pip install objection` |
| MobSF | 自动化移动安全分析 | Docker 部署 |
| BlackDex | 免 root 脱壳 | APK 安装 |
| FART | ART 脱壳 | 刷入 ROM 或 Frida 版 |
| hermes-dec | Hermes 字节码反编译 | npm 安装 |
| reFlutter | Flutter 逆向辅助 | pip 安装 |
| Magisk + Shamiko | Root 隐藏 | 刷入 |

---

## 八、参考资源

| 资源 | 定位 | 链接 |
|------|------|------|
| OWASP MASTG | 移动安全测试官方指南 | https://mas.owasp.org/ |
| FridaBypassKit | 四合一通用绕过框架 | https://github.com/okankurtuluss/FridaBypassKit |
| SSL-bypass | 通用 SSL Pinning 绕过脚本 | https://github.com/0xCD4/SSL-bypass |
| awesome-frida | Frida 生态资源合集 | https://github.com/dweinstein/awesome-frida |
| Android Security Awesome | Android 安全资源导航 | https://github.com/ashishb/android-security-awesome |
