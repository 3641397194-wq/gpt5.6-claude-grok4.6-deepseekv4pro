# Frida 实战脚本速查

> 素材整理自 [awesome-frida](https://github.com/dweinstein/awesome-frida)、[Frida-Mobile-Scripts](https://github.com/m0bilesecurity/Frida-Mobile-Scripts)、[frida-codeshare-scripts](https://github.com/zengfr/frida-codeshare-scripts) 等开源项目，按场景分类。

---

## 通用 Hook 模板

### Hook 任意 Java 方法

```javascript
Java.perform(function() {
    var Klass = Java.use("com.target.ClassName");

    // 无参方法
    Klass.methodName.implementation = function() {
        console.log("[*] methodName invoked");
        var ret = this.methodName();
        console.log("[*] -> " + ret);
        return ret;
    };

    // 有参重载
    Klass.methodName.overload('java.lang.String', 'int').implementation = function(str, num) {
        console.log("[*] methodName(" + str + ", " + num + ")");
        var ret = this.methodName(str, num);
        console.log("[*] -> " + ret);
        return ret;
    };
});
```

### Hook 构造函数

```javascript
Java.perform(function() {
    var Klass = Java.use("com.target.ClassName");
    Klass.$init.overload('java.lang.String').implementation = function(arg) {
        console.log("[*] new ClassName(" + arg + ")");
        this.$init(arg);
    };
});
```

### 枚举全部方法

```javascript
Java.perform(function() {
    var Klass = Java.use("com.target.ClassName");
    Klass.class.getDeclaredMethods().forEach(function(m) {
        console.log(m.toString());
    });
});
```

---

## 加密/签名 Hook

### Hook AES 加解密

```javascript
Java.perform(function() {
    var Cipher = Java.use("javax.crypto.Cipher");

    Cipher.doFinal.overload('[B').implementation = function(input) {
        var mode = this.getOpmode ? this.getOpmode() : "?";
        console.log("[Cipher.doFinal] mode=" + mode);
        console.log("  in : " + toHex(input));
        var result = this.doFinal(input);
        console.log("  out: " + toHex(result));
        return result;
    };

    // 密钥构造
    var SecretKeySpec = Java.use("javax.crypto.spec.SecretKeySpec");
    SecretKeySpec.$init.overload('[B', 'java.lang.String').implementation = function(key, algo) {
        console.log("[SecretKeySpec] algo=" + algo + " key=" + toHex(key));
        this.$init(key, algo);
    };

    // IV 构造
    var IvParameterSpec = Java.use("javax.crypto.spec.IvParameterSpec");
    IvParameterSpec.$init.overload('[B').implementation = function(iv) {
        console.log("[IvParameterSpec] iv=" + toHex(iv));
        this.$init(iv);
    };
});

function toHex(bytes) {
    var out = [];
    for (var i = 0; i < bytes.length; i++) {
        out.push(('0' + (bytes[i] & 0xFF).toString(16)).slice(-2));
    }
    return out.join('');
}
```

### Hook MD5/SHA

```javascript
Java.perform(function() {
    var MessageDigest = Java.use("java.security.MessageDigest");

    MessageDigest.digest.overload('[B').implementation = function(input) {
        console.log("[MessageDigest.digest] algo=" + this.getAlgorithm());
        console.log("  in  : " + toHex(input));
        var result = this.digest(input);
        console.log("  hash: " + toHex(result));
        return result;
    };

    MessageDigest.digest.overload().implementation = function() {
        console.log("[MessageDigest.digest] algo=" + this.getAlgorithm());
        var result = this.digest();
        console.log("  hash: " + toHex(result));
        return result;
    };
});
```

### Hook HMAC

```javascript
Java.perform(function() {
    var Mac = Java.use("javax.crypto.Mac");

    Mac.doFinal.overload('[B').implementation = function(input) {
        console.log("[Mac.doFinal] algo=" + this.getAlgorithm());
        console.log("  in : " + toHex(input));
        var result = this.doFinal(input);
        console.log("  mac: " + toHex(result));
        return result;
    };

    Mac.init.overload('java.security.Key').implementation = function(key) {
        console.log("[Mac.init] key=" + toHex(key.getEncoded()));
        this.init(key);
    };
});
```

---

## 网络请求 Hook

### Hook OkHttp3 请求/响应

```javascript
Java.perform(function() {
    var RealCall = Java.use("okhttp3.RealCall");

    RealCall.execute.implementation = function() {
        var req = this.request();
        console.log("[OkHttp] " + req.method() + " " + req.url().toString());
        var headers = req.headers();
        for (var i = 0; i < headers.size(); i++) {
            console.log("  " + headers.name(i) + ": " + headers.value(i));
        }
        var resp = this.execute();
        console.log("[OkHttp] Response: " + resp.code());
        return resp;
    };
});
```

### Hook URL 连接

```javascript
Java.perform(function() {
    var URL = Java.use("java.net.URL");
    URL.openConnection.overload().implementation = function() {
        console.log("[URL] " + this.toString());
        return this.openConnection();
    };
});
```

### Hook WebView

```javascript
Java.perform(function() {
    var WebView = Java.use("android.webkit.WebView");
    WebView.loadUrl.overload('java.lang.String').implementation = function(url) {
        console.log("[WebView.loadUrl] " + url);
        this.loadUrl(url);
    };

    WebView.evaluateJavascript.implementation = function(script, callback) {
        console.log("[WebView.evaluateJavascript] " + script.substring(0, 200));
        this.evaluateJavascript(script, callback);
    };
});
```

---

## 绕过类 Hook

### 通用 SSL Pinning 绕过

```javascript
Java.perform(function() {
    // OkHttp3 CertificatePinner
    try {
        var CertificatePinner = Java.use("okhttp3.CertificatePinner");
        CertificatePinner.check.overload('java.lang.String', 'java.util.List').implementation = function() {
            console.log("[*] SSL Pinning bypassed (OkHttp3)");
        };
    } catch(e) {}

    // TrustManagerImpl
    try {
        var TrustManagerImpl = Java.use("com.android.org.conscrypt.TrustManagerImpl");
        TrustManagerImpl.verifyChain.implementation = function(untrustedChain) {
            console.log("[*] SSL Pinning bypassed (TrustManagerImpl)");
            return untrustedChain;
        };
    } catch(e) {}

    // X509TrustManager 全放行
    try {
        var X509TrustManager = Java.use("javax.net.ssl.X509TrustManager");
        Java.registerClass({
            name: "com.bypass.TrustManager",
            implements: [X509TrustManager],
            methods: {
                checkClientTrusted: function() {},
                checkServerTrusted: function() {},
                getAcceptedIssuers: function() { return []; }
            }
        });
    } catch(e) {}

    // Network Security Config (Android 7+)
    try {
        var NetworkSecurityConfig = Java.use("android.security.net.config.NetworkSecurityConfig");
        NetworkSecurityConfig.isCleartextTrafficPermitted.implementation = function() { return true; };
    } catch(e) {}
});
```

### 通用 Root 检测绕过

```javascript
Java.perform(function() {
    var File = Java.use("java.io.File");
    var rootPaths = ["su", "Superuser", "magisk", "busybox", "xposed",
                     "/system/xbin/su", "/system/bin/su", "/sbin/su",
                     "/data/local/xbin/su", "/data/local/bin/su"];

    File.exists.implementation = function() {
        var path = this.getAbsolutePath();
        for (var i = 0; i < rootPaths.length; i++) {
            if (path.toLowerCase().indexOf(rootPaths[i].toLowerCase()) !== -1) {
                console.log("[Root] Blocked: " + path);
                return false;
            }
        }
        return this.exists();
    };

    var Runtime = Java.use("java.lang.Runtime");
    Runtime.exec.overload('java.lang.String').implementation = function(cmd) {
        if (cmd.indexOf("su") !== -1 || cmd.indexOf("which") !== -1) {
            console.log("[Root] Blocked exec: " + cmd);
            throw Java.use("java.io.IOException").$new("Permission denied");
        }
        return this.exec(cmd);
    };

    var Build = Java.use("android.os.Build");
    Build.TAGS.value = "release-keys";
});
```

### 反调试绕过

```javascript
Java.perform(function() {
    var Debug = Java.use("android.os.Debug");
    Debug.isDebuggerConnected.implementation = function() {
        console.log("[AntiDebug] isDebuggerConnected -> false");
        return false;
    };

    // native 层：拦截 /proc/self/status 的 TracerPid 读取
    var fopen = Module.findExportByName("libc.so", "fopen");
    Interceptor.attach(fopen, {
        onEnter: function(args) {
            this.path = args[0].readUtf8String();
        },
        onLeave: function(retval) {
            if (this.path && this.path.indexOf("/proc/") !== -1 && this.path.indexOf("/status") !== -1) {
                // 可进一步 hook fgets 修改 TracerPid
            }
        }
    });
});
```

### 模拟器检测绕过

```javascript
Java.perform(function() {
    var Build = Java.use("android.os.Build");
    Build.FINGERPRINT.value = "google/walleye/walleye:8.1.0/OPM1.171019.011/4448085:user/release-keys";
    Build.MODEL.value = "Pixel 2";
    Build.MANUFACTURER.value = "Google";
    Build.BRAND.value = "google";
    Build.DEVICE.value = "walleye";
    Build.PRODUCT.value = "walleye";
    Build.HARDWARE.value = "walleye";

    var TelephonyManager = Java.use("android.telephony.TelephonyManager");
    TelephonyManager.getDeviceId.implementation = function() { return "352099001761481"; };
    TelephonyManager.getSubscriberId.implementation = function() { return "310260000000000"; };
    TelephonyManager.getSimSerialNumber.implementation = function() { return "89014103211118510720"; };
});
```

---

## 数据存储 Hook

### Hook SharedPreferences

```javascript
Java.perform(function() {
    var SharedPreferencesImpl = Java.use("android.app.SharedPreferencesImpl");

    SharedPreferencesImpl.getString.implementation = function(key, defValue) {
        var value = this.getString(key, defValue);
        console.log("[SP.get] " + key + " = " + value);
        return value;
    };

    var Editor = Java.use("android.app.SharedPreferencesImpl$EditorImpl");
    Editor.putString.implementation = function(key, value) {
        console.log("[SP.put] " + key + " = " + value);
        return this.putString(key, value);
    };
});
```

### Hook SQLite

```javascript
Java.perform(function() {
    var SQLiteDatabase = Java.use("android.database.sqlite.SQLiteDatabase");

    SQLiteDatabase.rawQuery.implementation = function(sql, args) {
        console.log("[SQL] " + sql);
        if (args) console.log("  args: " + JSON.stringify(args));
        return this.rawQuery(sql, args);
    };

    SQLiteDatabase.execSQL.overload('java.lang.String').implementation = function(sql) {
        console.log("[SQL.exec] " + sql);
        this.execSQL(sql);
    };
});
```

---

## 脱壳 Hook

### 通用 DEX Dump

```javascript
Java.perform(function() {
    Java.enumerateClassLoaders({
        onMatch: function(loader) {
            try {
                var pathList = Java.cast(loader, Java.use("dalvik.system.BaseDexClassLoader")).pathList.value;
                var dexElements = pathList.dexElements.value;
                for (var i = 0; i < dexElements.length; i++) {
                    var dexFile = dexElements[i].dexFile.value;
                    if (dexFile) {
                        console.log("[DEX] " + dexFile.getName());
                        // 可进一步 dump dex 内容
                    }
                }
            } catch(e) {}
        },
        onComplete: function() {}
    });
});
```

### Hook ClassLoader.loadClass

```javascript
Java.perform(function() {
    var ClassLoader = Java.use("java.lang.ClassLoader");
    ClassLoader.loadClass.overload('java.lang.String').implementation = function(name) {
        if (name.indexOf("com.target") !== -1) {
            console.log("[ClassLoader] " + name);
        }
        return this.loadClass(name);
    };
});
```

---

## 实用工具函数

```javascript
// 字节数组转十六进制
function toHex(bytes) {
    if (!bytes) return "null";
    var out = [];
    for (var i = 0; i < bytes.length; i++) {
        out.push(('0' + (bytes[i] & 0xFF).toString(16)).slice(-2));
    }
    return out.join('');
}

// 打印调用栈
function printStack() {
    console.log(Java.use("android.util.Log").getStackTraceString(
        Java.use("java.lang.Throwable").$new()));
}

// 打印对象所有字段
function printFields(obj) {
    obj.class.getDeclaredFields().forEach(function(field) {
        field.setAccessible(true);
        try {
            console.log("  " + field.getName() + " = " + field.get(obj));
        } catch(e) {}
    });
}

// 搜索内存中的类实例
function findInstances(className) {
    Java.choose(className, {
        onMatch: function(instance) {
            console.log("[Instance] " + instance);
            printFields(instance);
        },
        onComplete: function() {}
    });
}
```

---

## 参考资源

| 资源 | 说明 | 链接 |
|------|------|------|
| Frida 官方文档 | API 参考 | https://frida.re/docs/ |
| Frida CodeShare | 社区脚本分享 | https://codeshare.frida.re/ |
| awesome-frida | 资源大全 | https://github.com/dweinstein/awesome-frida |
| frida-codeshare-scripts | 全网脚本收集 | https://github.com/zengfr/frida-codeshare-scripts |
| Objection | Frida 封装工具 | https://github.com/sensepost/objection |
| r2frida | radare2 + Frida 集成 | https://github.com/nowsecure/r2frida |
