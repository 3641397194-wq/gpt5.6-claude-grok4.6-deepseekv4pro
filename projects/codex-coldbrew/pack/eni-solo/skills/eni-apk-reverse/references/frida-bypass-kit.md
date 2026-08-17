# Frida Bypass Kit — Android 通用安全绕过框架

> 上游项目：[FridaBypassKit](https://github.com/okankurtuluss/FridaBypassKit)（2025）
> 适用场景：APK 动态分析时一次性解决 root 检测、SSL pinning、模拟器检测、反调试四类拦路问题。

## 概述

FridaBypassKit 是一个把四类绕过能力打包进单个脚本的通用框架，不需要针对具体 APP 定制，加载即生效。

## 四类绕过能力

### 1. Root 检测绕过

- Hook `File.exists()` 隐藏 su 二进制
- 拦截 `Runtime.exec()` 的 root 检查调用
- 从 PackageManager 隐藏 root 相关包（Magisk、SuperSU 等）
- 修改系统属性让设备呈现未 root 状态

### 2. SSL Pinning 绕过

- Hook `TrustManagerImpl.verifyChain()`
- Hook `TrustManagerImpl.checkTrustedRecursive()`
- 绕过证书链验证
- 返回空证书链避免校验
- 兼容 OkHttp、Retrofit 与自定义实现

### 3. 模拟器检测绕过

- 伪造 TelephonyManager 返回值
- 返回假电话号码与运营商名称
- 修改 Build 属性

### 4. 反调试绕过

- Hook `Debug.isDebuggerConnected()`
- 阻止调试器检测
- 绕过反调试检查

## 使用方法

```bash
# 前置条件
pip install frida-tools
adb push frida-server /data/local/tmp/
adb shell chmod 755 /data/local/tmp/frida-server
adb shell su -c /data/local/tmp/frida-server &

# 注入目标 APP
frida -U -f com.example.app -l FridaBypassKit.js
```

## 其他推荐的 Frida 绕过脚本

| 项目 | 特点 | 链接 |
|------|------|------|
| httptoolkit/frida-interception-and-unpinning | 直接 MitM 所有 HTTPS 流量 | [GitHub](https://github.com/httptoolkit/frida-interception-and-unpinning) |
| 0xCD4/SSL-bypass | 通用非定制 SSL 绕过 | [GitHub](https://github.com/0xCD4/SSL-bypass) |
| incogbyte/ssl-bypass gist | 绕过常见 SSL pinning 方法 | [Gist](https://gist.github.com/incogbyte/1e0e2f38b5602e72b1380f21ba04b15e) |
| Zero3141/Frida-OkHttp-Bypass | 专门针对 OkHttp CertificatePinner | [GitHub](https://github.com/Zero3141/Frida-OkHttp-Bypass) |

## 与本包的集成

在 `apk-reverse` 工作流中按症状启用：

1. APP 检测到 root 拒绝运行 → Root Detection Bypass
2. 抓包时 HTTPS 看不到明文 → SSL Pinning Bypass
3. APP 检测到模拟器拒绝运行 → Emulator Detection Bypass
4. 附加 Frida 后 APP 崩溃 → Debug Detection Bypass

推荐组合使用：先跑完整 FridaBypassKit，再针对性调整。
