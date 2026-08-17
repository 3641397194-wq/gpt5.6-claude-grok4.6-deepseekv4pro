---
name: eni-apk-reverse
description: 全局自动路由 | 纯 CLI 环境下的 Android APK 逆向作业规范：覆盖 APK 解包、Java 层反编译、smali 补丁、重打包签名、Frida 动态插桩，并按需转入 so/native 分析。优先复用本机已装的 jadx、apktool、frida、adb，必要时联动 ida-reverse 与 radare2
---

# APK 逆向 CLI 作业规范

## 适用范围

出现以下任务形态时，优先走本 skill：

- 读懂 APK 的 Java 业务逻辑
- 定位登录、签名、风控、证书校验、root 检测实现
- 查看与修改 `AndroidManifest.xml`
- 查看与修改 smali
- 重打包 APK
- 用 Frida 做 Java/native 动态插桩
- APK 内含 `.so` 时转入 native 分析

## 本机已验证可用的 CLI 工具

- `jadx` `1.5.5`
- `apktool` `3.0.2`
- `frida-ps` `17.9.6`
- `adb`
- `java`

## 优先用自带脚本的场景

以下流程高频且参数容易踩错，优先走 skill 自带脚本：

- 一次跑完 `jadx + apktool` 落盘并产出摘要：`scripts/decode.ps1`
- Frida 设备检查、进程列举、spawn/attach 注入：`scripts/frida-run.ps1`
- 重建、对齐、签名、安装闭环：`scripts/rebuild-sign-install.ps1`
- 快速抽取 Manifest 关键组件与权限：`scripts/manifest-summary.ps1`

一行命令保持直接调用，不单独封装：

- `adb devices`
- `adb logcat`
- `frida-ps -U`
- `jadx --version`
- `apktool --version`

## 自带脚本

### `scripts/decode.ps1`

职责：

- 统一跑 `jadx` 与 `apktool`
- 默认在原 APK 同目录创建任务输出目录
- 产出 `package`、`java_files`、`smali_dirs`、`so_files` 等摘要
- 容忍 `jadx` 部分反编译失败但仍有可用产物的情况

示例：

```powershell
pwsh -File "<skill-root>\apk-reverse\scripts\decode.ps1" -ApkPath "D:\DOWNLOAD\app.apk" -Clean
pwsh -File "<skill-root>\apk-reverse\scripts\decode.ps1" -ApkPath "D:\DOWNLOAD\app.apk" -Name demo -SkipJadx
```

### `scripts/frida-run.ps1`

职责：

- 统一 Frida 的设备、进程、spawn/attach 入口
- 避免手写参数时混淆 `-f`、`-n`、`-U`

示例：

```powershell
pwsh -File "<skill-root>\apk-reverse\scripts\frida-run.ps1" -ListDevices
pwsh -File "<skill-root>\apk-reverse\scripts\frida-run.ps1" -Usb -ListProcesses
pwsh -File "<skill-root>\apk-reverse\scripts\frida-run.ps1" -Usb -Spawn -Package com.example.app -ScriptPath "D:\hooks\test.js"
```

### `scripts/rebuild-sign-install.ps1`

职责：

- `apktool b` 重建
- `zipalign` 对齐
- `apksigner` 签名与验签
- 可选直接 `adb install`

示例：

```powershell
pwsh -File "<skill-root>\apk-reverse\scripts\rebuild-sign-install.ps1" -ProjectDir "C:\work\apktool_out" -Clean
pwsh -File "<skill-root>\apk-reverse\scripts\rebuild-sign-install.ps1" -ProjectDir "C:\work\apktool_out" -Install -Reinstall -DeviceSerial "127.0.0.1:7555"
```

说明：

- 默认生成并复用调试 keystore
- 默认输出到 `ProjectDir` 同目录，方便与原始包、解包目录放一起

### `scripts/manifest-summary.ps1`

职责：

- 抽取包名
- 列权限
- 列 activity/service/receiver/provider
- 标出主启动 activity

示例：

```powershell
pwsh -File "<skill-root>\apk-reverse\scripts\manifest-summary.ps1" -ManifestPath "C:\work\apktool_out\AndroidManifest.xml"
```

涉及 `lib/arm64-v8a/*.so`、`lib/armeabi-v7a/*.so` 分析时，联动 `ida-reverse`、`radare2`。

## 工具分工

### `jadx`

定位：

- Java 反编译阅读
- 包名、类名、方法名检索
- 先建立高层业务理解

常用命令：

```bash
jadx -d jadx_out app.apk
jadx --single-class com.example.LoginActivity -d jadx_out app.apk
jadx --deobf -d jadx_out app.apk
```

### `apktool`

定位：

- 解包 APK
- 查看和修改 `AndroidManifest.xml`
- 查看和修改 smali
- 重建 APK

常用命令：

```bash
apktool d app.apk -o apktool_out
apktool b apktool_out -o rebuilt.apk
```

### `frida`

定位：

- 动态观察 Java 方法调用
- Hook native 导出函数
- 绕过 root 检测、证书校验、调试检测

常用命令：

```bash
frida-ps -U
frida -U -f com.example.app -l hook.js
frida-trace -U -f com.example.app -j '*!*certificate*'
```

### `adb`

定位：

- 设备连接
- 安装 APK
- 查看日志
- 拉取文件

常用命令：

```bash
adb devices
adb install -r app.apk
adb shell pm list packages
adb logcat
adb pull /data/local/tmp/file .
```

## 推荐工作流

### 1. Triage

先摸清 APK 的构成，不急着改包或 Hook：

1. `jadx -d jadx_out app.apk` 导出 Java
2. `apktool d app.apk -o apktool_out` 导出 smali 与资源
3. 先看 `AndroidManifest.xml`、主 `package`、`application`/`activity`/`service`/`receiver`、`lib/` 下有无 `.so`

### 2. Java 逻辑观察

优先从 `jadx_out` 读：`MainActivity`、`Application`、登录/网络/加密/风控相关类、第三方 SDK 初始化类。

高频关键词：`login`、`sign`、`encrypt`、`cipher`、`token`、`root`、`certificate`、`trust`、`okhttp`、`retrofit`、`webview`

Java 代码可读时，先在这里定位业务逻辑。

### 3. Smali 与资源层确认

`jadx` 结果残缺、混淆重、或需要实际 patch 时，切到 `apktool_out`：

- 看 `smali*/`
- 看 `res/values/strings.xml`
- 看 `AndroidManifest.xml`

优先 patch 点：`android:exported`、调试标记、root 检测返回值、登录验证逻辑、证书校验分支。

### 4. 重建与安装

修改后：

```bash
apktool b apktool_out -o rebuilt.apk
```

或直接用脚本闭环：

```powershell
pwsh -File "<skill-root>\apk-reverse\scripts\rebuild-sign-install.ps1" -ProjectDir "apktool_out" -Install -Reinstall -DeviceSerial "127.0.0.1:7555"
```

说明：

- 本 skill 只保证 `apktool` 重建链路
- 正式安装到设备需要签名流程，进入签名/对齐时补 `apksigner` / `zipalign`

### 5. 动态插桩

静态分析不够时上 Frida：Hook 登录函数、`OkHttp`/`Retrofit`/`WebView` 关键点、`javax.crypto`、`MessageDigest`、root 检测函数、SSL pinning 逻辑。

原则：

- 先 Java 层后 native 层
- 先打印参数与返回值，再决定是否主动改返回值

建议：一次性命令直接 `frida-*`；需要稳定复用的注入流程走 `scripts/frida-run.ps1`。

### 6. Native `.so` 分流

APK 含关键 `.so` 时：

- 用 `apktool` 或 `jadx` 定位 `lib/**/*.so`
- 只看导出符号、字符串、快速 triage 用 `radare2`
- 长期深入分析、反编译、改名、类型恢复用 `ida-reverse`

出现这些信号尽快切 native：Java 层只是 JNI 包装、核心签名逻辑不在 Java、`System.loadLibrary()` 后关键逻辑消失、证书校验/风控在 `.so` 中。

## 输出要求

最终至少说明：

- 入口组件与关键类
- 关键逻辑在 Java、smali 还是 `.so`
- 已确认的敏感点：登录、签名、root、SSL、WebView、JNI
- 做了 patch 的，说明改了什么
- 做了 Hook 的，说明 Hook 了哪个类/方法/导出函数

## 禁止事项

- 一开始就盲目改 smali
- 没看 manifest 和主入口就写 Hook
- 把 Java 反编译不完整直接等同于"逻辑不可分析"
- `.so` 明显承载核心逻辑时继续死磕 Java 层

## 快速命令备忘

```bash
# 反编译 Java
jadx -d jadx_out app.apk

# 解包 APK
apktool d app.apk -o apktool_out

# 重建 APK
apktool b apktool_out -o rebuilt.apk

# 设备与进程
adb devices
frida-ps -U

# 启动并注入
frida -U -f com.example.app -l hook.js
```

---

## 路由上下文

**上游入口**: `skills/SKILL.md`（总控）、`routing.md`
**下游出口**:
- 核心逻辑在 `.so` → `ida-reverse/` 或 `radare2/`
- 需动态 Hook/验证 → `reverse-engineering/tools-dynamic.md`（Frida 章节）
- 通用逆向方法论 → `reverse-engineering/SKILL.md`

**同级关联模块**: `reverse-engineering/`（.so 分析和 Frida 进阶用法）

---

## 按需自举（On-Demand Bootstrap）

本 skill 的入口脚本已接入统一自举系统，缺少工具时自动尝试安装而非直接报错。

### 自动化能力边界

| 工具 | 可自动安装 | 安装方式 | 说明 |
|------|-----------|---------|------|
| jadx | ✓ | GitHub Release ZIP | 自动下载解压到 `%USERPROFILE%\Tools\jadx\` |
| apktool | ✓ | GitHub Release JAR + wrapper | 自动下载 jar 并生成 bat 到 `%USERPROFILE%\Tools\apktool\` |
| frida / frida-ps | ✓ | pip install frida-tools | 需要 Python 已安装 |
| adb | ✓ | winget / fallback path | 自动安装 Android Platform-Tools |
| zipalign | ✗ | 需手动安装 Android Build-Tools | `sdkmanager "build-tools;35.0.0"` |
| apksigner | ✗ | 需手动安装 Android Build-Tools | 同上 |

### 自举触发点

- `scripts/decode.ps1`：缺 jadx 或 apktool 时自动调用 `bootstrap-reverse.ps1`
- `scripts/rebuild-sign-install.ps1`：缺 adb 或 apktool 时自动调用 bootstrap
- `scripts/frida-run.ps1`：当前仍为手动检查（frida 通常已通过 pip 安装）

### 自举失败时

自动安装失败则抛出明确错误并附带手动安装链接。常见原因：

- 网络不通（GitHub API / PyPI 不可达）
- winget 不可用（Windows 版本过低）
- Java 未安装（apktool 依赖 JDK）
