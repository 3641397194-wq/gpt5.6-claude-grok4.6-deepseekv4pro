# 平台与框架专项逆向技术

## 目录

- [Rust serde_json Schema 恢复](#rust-serde_json-schema-恢复)
- [Android JNI RegisterNatives 混淆（HTB WonderSMS）](#android-jni-registernatives-混淆)
- [Android DEX 运行时字节码补丁（Google CTF 2017）](#android-dex-运行时字节码补丁)
- [新建工程绕过 .so 加载校验（Codegate CTF 2018）](#新建工程绕过-so-加载校验)
- [Frida 绕过 Firebase Cloud Functions（BSidesSF 2026）](#frida-绕过-firebase-cloud-functions)
- [Verilog / 硬件逆向（srdnlenCTF 2026）](#verilog--硬件逆向)
- [逐前缀哈希反转（Nullcon 2026）](#逐前缀哈希反转)
- [Ruby/Perl polyglot 约束求解（BearCatCTF 2026）](#rubyperl-polyglot-约束求解)
- [Electron 应用 + 原生二进制（RootAccess2026）](#electron-应用--原生二进制)
- [Node.js npm 包运行时内省（RootAccess2026）](#nodejs-npm-包运行时内省)
- [Frida 绕过证书固定（h1702ctf 2017）](#frida-绕过证书固定)
- [Android 反调试三连（h1702ctf 2017）](#android-反调试三连)
- [日志泄露密钥（HackIT 2017）](#日志泄露密钥)
- [内存 dump + smali 补丁提密钥（HackIT 2017）](#内存-dump--smali-补丁提密钥)
- [IBM AS/400 SAVF 文件 EBCDIC 解码（EKOPARTY 2017）](#ibm-as400-savf-文件-ebcdic-解码)
- [Intel SGX Enclave 逆向（Pwn2Win 2017）](#intel-sgx-enclave-逆向)

核心语言逆向（Python、BF/esolang、DOS、OPAL）见 [languages.md](languages.md)。
Go 与 Rust 二进制逆向见 [languages-compiled.md](languages-compiled.md)。

---

## Rust serde_json Schema 恢复

**模式（Curly Crab，PascalCTF 2026）：** Rust 二进制从 stdin 读 JSON，经 serde_json 反序列化，打印成功/失败 emoji。

**打法：**

1. 反汇编 serde 生成的 `Visitor` 实现
2. 每个 visitor 的 `visit_map` / `visit_seq` 暴露期望键与类型
3. 反序列化器代码里找字符串字面量（字段名如 `"pascal"`、`"CTF"`）
4. 从 visitor 调用层级重建嵌套 JSON schema
5. visitor 方法名定值类型：`visit_str` = 字符串、`visit_u64` = 数字、`visit_bool` = 布尔、`visit_seq` = 数组

```json
{"pascal":"CTF","CTF":2026,"crab":{"I_":true,"cr4bs":1337,"crabby":{"l0v3_":["rust"],"r3vv1ng_":42}}}
```

**要点：** flag 是 schema 顺序下 JSON 键的拼接。按顺序读字段名即得 flag。

---

## Android JNI RegisterNatives 混淆（HTB WonderSMS）

**模式：** Android 应用用 `System.loadLibrary()` 加载原生库，却在 `JNI_OnLoad` 里用 `RegisterNatives` 而非标准 JNI 命名（`Java_com_pkg_Class_method`）。这隐藏了哪个 C++ 函数处理哪个 Java native 方法。

**识别：**

```java
// 反编译 Java（jadx）里：
static { System.loadLibrary("audio"); }
private final native ProcessedMessage processMessage(SmsMessage msg);
```

标准 JNI 应有符号 `Java_com_rloura_wondersms_SmsReceiver_processMessage`。`.so` 里没有该符号 → 用了 `RegisterNatives`。

**Ghidra 里找真实 handler：**

1. 定位 `JNI_OnLoad`（导出符号，必在）
2. 追到 `RegisterNatives(env, clazz, methods, count)` 调用
3. `methods` 数组含 `{name, signature, fnPtr}` 结构
4. 跟 `fnPtr` 找到实际原生函数

```c
// JNI_OnLoad 手动注册函数：
static JNINativeMethod methods[] = {
    {"processMessage", "(Landroid/telephony/SmsMessage;)LProcessedMessage;", (void*)real_handler}
};
(*env)->RegisterNatives(env, clazz, methods, 1);
```

**架构选择：**

```bash
# x86_64 的 Ghidra 反编译效果最好（最接近桌面代码）
# 从 APK 提取：
unzip WonderSMS.apk -d extracted/
ls extracted/lib/x86_64/  # 静态分析优先选它而非 arm64-v8a
```

**要点：** `RegisterNatives` 是刻意的混淆——切断 Java 方法名与原生符号名的关联，光靠字符串搜索找不到 handler。逆 strip 的 Android 原生库时永远先查 `JNI_OnLoad`。

**识别：** Java 声明 native 方法 + `.so` 里无对应 JNI 符号 + 存在 `JNI_OnLoad`。库通常被 strip。

---

## Android DEX 运行时字节码补丁（Google CTF 2017）

原生 JNI 库在运行时 patch Dalvik 字节码：读 `/proc/self/maps` 找已加载 DEX，`mprotect` 改可写，再对特定字节码偏移做 XOR 补丁。

```python
# 离线重建补丁后的 DEX：
# 1. 从 APK 提取内嵌 DEX
# 2. 在原生 .so（IDA/Ghidra）里找 XOR 密钥与补丁偏移
# 3. 对静态 DEX 施加同样补丁
import struct

with open('classes.dex', 'rb') as f:
    dex = bytearray(f.read())

# 从 .so 找到的偏移开始 patch 144 字节
xor_key = 0x5A
for i in range(patch_offset, patch_offset + 144):
    dex[i] ^= xor_key

# 4. 重算 DEX 校验和与 SHA-1
# 5. jadx 或 baksmali 反编译
```

**要点：** 原生库可经 `/proc/self/maps` + `mprotect` 改内存中的 DEX 字节码，光静态分析 APK 不够。XOR 密钥与补丁偏移必须从原生 `.so` 提取才能重建真实运行时 DEX。仅 Dalvik（API < 21）可行，ART 不行。

---

## 新建工程绕过 .so 加载校验（Codegate CTF 2018）

**模式：** 与其逆复杂的 JNI 校验逻辑，不如新建 Android Studio 工程，配相同的包名、类名与 native 方法签名。加载原 `.so` 直接调 native 函数，绕过全部 Java 层检查（随机数校验、PIN 输入、root 检测等）。

```java
// 新工程用相同包名: com.example.puing.a2018codegate
package com.example.puing.a2018codegate;
public class Main4Activity extends AppCompatActivity {
    static { System.loadLibrary("hello-libs"); }
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        String flag = stringFromJNI();  // 直接调 native，跳过所有 Java 校验
        Log.d("FLAG", flag);
    }
    public native String stringFromJNI();
}
```

**要点：** JNI 函数名编码了包路径与类名。新建包/类/方法名一致的工程，放回原 `.so`，直接调 native 函数。Java 层校验（随机检查、PIN 输入、设备检测）被整体绕过。

**识别：** 带原生 `.so` 的 APK，flag/秘密在 native 代码内计算并返回 Java。Java 层在调 native 前有多道校验门（EditText 检查、随机数比较、设备检查）。

**References:** Codegate CTF 2018

---

## Frida 绕过 Firebase Cloud Functions（BSidesSF 2026）

**模式（vinyl-drop, doremi）：** Android 应用经 Firebase Cloud Functions 校验操作（二维码、购买）。期望载荷格式含 Firebase UID、值与时间戳。登录后用 Frida hook 应用，构造合法载荷直接调 Cloud Function。

```javascript
// Frida hook 绕过 QR 校验
Java.perform(function() {
    var FirebaseFunctions = Java.use('com.google.firebase.functions.FirebaseFunctions');
    var FirebaseAuth = Java.use('com.google.firebase.auth.FirebaseAuth');

    // 登录后取当前用户 UID
    var auth = FirebaseAuth.getInstance();
    var uid = auth.getCurrentUser().getUid();

    // 构造合法载荷: uid + 金额 + 时间戳
    var unixMs = Java.use('java.lang.System').currentTimeMillis();
    var payload = uid + "+100+" + unixMs;

    // 直接调 Cloud Function
    var functions = FirebaseFunctions.getInstance();
    var data = Java.use('java.util.HashMap').$new();
    data.put("payload", payload);
    functions.getHttpsCallable("validateScanPayload").call(data);
});
```

**要点：** Firebase AppCheck 与 Cloud Functions 依赖客户端构造合法载荷。认证后 Frida 可 hook 应用、以任意参数调任何 Cloud Function，绕过客户端校验（扫码、支付流程等）。

**识别：** Android 应用带 `google-services.json`、`build.gradle` 含 Firebase 依赖、反编译代码里有 Cloud Function 调用。

**References:** BSidesSF 2026 "vinyl-drop"

---

## Verilog / 硬件逆向（srdnlenCTF 2026）

**模式（Rev Juice）：** 自动售货机的 Verilog HDL 源码，隐藏商品需特定投币与选择序列解锁。

**打法：**

1. 分析 Verilog 模块理解状态机与历史跟踪
2. 识别隐藏条件（如商品 8 仅在 `COINS_HISTORY` 数组特定抽头为特定值时启用）
3. 为每种动作建时序模型（每个操作占多少时钟周期）
4. 从所需历史值倒推构造正确输入序列

**时序模型构造：**

```python
# 从 Verilog 状态机确定每个动作的周期数
TIMING = {
    "insert_coin": 3,       # 每次投币 3 周期
    "select_success": 7,    # 成功选品 7 周期
    "select_fail": 5,       # 失败选品 5 周期
    "cancel_with_coins": 4, # 币>0 时取消 4 周期
    "cancel_at_zero": 2,    # 币=0 时取消 2 周期
}

# COINS_HISTORY 是每周期更新的移位寄存器
# 历史抽头要求（来自 Verilog 条件）：
# H[0]=1, H[7]=4, H[28]=H[33]=H[38]=6
# H[63]=H[73]=2, H[80]=9
# (H[19]+H[21]+H[56]+H[69]) mod 32 = 0
```

**要点：** 硬件题要求理解精确时序模型——每个操作占固定周期数，移位寄存器在固定抽头记录历史。从所需抽头值倒推每个周期该发生什么动作。答案常是特定序列记法（如 `I9C_SP6_CNL_I2C_SP2_I6C_SP6_SP6_SP5_CNL_I4C_SP1`）。

**识别：** `.v` 或 `.sv`（Verilog/SystemVerilog）文件、`always @(posedge clk)` 块、移位寄存器模式、带历史值隐藏条件的状态机 `case` 语句。

---

## 逐前缀哈希反转（Nullcon 2026）

完整技术见 [patterns-ctf-2.md](patterns-ctf-2.md)。本节只讲语言相关注意点。

**语言相关：**

- 哈希算法可能冷门（MD2、自定义）——不必识别它，跑二进制比对输出即可
- 用 `subprocess.run()` 配 `timeout=2` 处理坏输入下挂起的二进制
- strip 二进制可试试 `ltrace` 暴露哈希函数名（如 `MD2_Update`）

---

## Ruby/Perl polyglot 约束求解（BearCatCTF 2026）

**模式（Polly's Key）：** 单文件同时合法于 Ruby 与 Perl。两种语言各对 50 字符密钥施加不同校验约束。同时满足两者才能解密 flag。

**polyglot 结构利用：**

- Ruby：`=begin`...`=end` 是块注释
- Perl：`=begin`...`=cut` 是 POD（Plain Old Documentation），`=end` 被忽略
- 依据注释块边界，两种语言各跑不同代码

**典型约束：**

- **Ruby：** 字符集满足数学性质（如除 `^` 外全部 50 个可打印 ASCII 各用一次，且每个满足 `XOR(val, (val-16) % 257)` 是 mod 257 的本原根）
- **Perl：** 经插入排序逆序数表达的顺序约束（硬编码逆序表决定精确排列）

**求解思路：**

1. 找合法字符集（一种语言的数学约束）
2. 用顺序约束（另一种语言）确定精确排列
3. 算密钥哈希（如 MD5）并解密

```python
# 从逆序数确定字符顺序
def reconstruct_from_inversions(chars, inv_counts):
    result = []
    remaining = sorted(chars)
    for i in range(len(chars) - 1, -1, -1):
        # inv_counts[i] = 左侧大于它的元素数
        idx = inv_counts[i]
        result.insert(idx, remaining.pop(i))
    return result
```

**要点：** polyglot 文件利用各语言的注释/块语法在不同解释器里跑不同代码。两语言约束求交唯一确定密钥。用两个解释器各跑一遍文件，对比行为确定哪段代码在哪种语言里运行。

**识别：** 文件可在多个解释器下运行（`ruby file && perl file`）。题目提到 "polyglot"，或给出 `.rb` 后缀但长得像 Perl 的文件。

---

## Electron 应用 + 原生二进制（RootAccess2026）

**模式（Rootium Browser）：** Electron 桌面应用为敏感操作（保险库、加密、认证）捆绑原生 ELF/DLL。Electron 层只是壳，真实 flag 逻辑在原生二进制里。

**提取工作流：**

1. **解 Electron ASAR 归档：**

```bash
# 安装 ASAR 工具
npm install -g @electron/asar

# 提取 app.asar 归档
asar extract resources/app.asar app_extracted/
ls app_extracted/
```

2. **定位原生二进制：** 找 JavaScript 调用的 ELF/DLL：

```bash
# 找原生二进制
find app_extracted/ -name "*.node" -o -name "*.so" -o -name "*vault*" -o -name "*auth*"

# 查 JS 里的 child_process.spawn 或 ffi-napi 调用
grep -r "spawn\|execFile\|ffi\|require.*native" app_extracted/
```

3. **逆原生二进制**（XOR + 旋转密码示例）：

```python
def decrypt_password(encrypted_bytes, key):
    """常见模式: 常量 XOR + 位旋转 + 密钥 XOR。"""
    result = []
    for i, byte in enumerate(encrypted_bytes):
        decrypted = ((byte ^ 0x42) >> 3) ^ key[i % len(key)]
        result.append(chr(decrypted))
    return ''.join(result)

def decrypt_flag(encrypted_flag, password):
    """Flag 用密码作密钥，带位置相关旋转。"""
    result = []
    for i, byte in enumerate(encrypted_flag):
        key_byte = ord(password[i % len(password)])
        decrypted = ((byte ^ 0x7E) >> (i % 8)) ^ key_byte
        result.append(chr(decrypted))
    return ''.join(result)
```

**要点：** Electron 应用是 JavaScript 包着原生代码。`asar` 提取后聚焦原生二进制。JS 层常明文包含密码验证流程，暴露原生二进制期望什么。在 ELF 的 `.data` 或 `.rodata` 节找加密数据。

**识别：** `resources/` 里有 `.asar`、Electron 框架文件、`package.json` 含 electron 依赖。

---

## Node.js npm 包运行时内省（RootAccess2026）

**模式（RootAccess CLI）：** 混淆 npm 包带 RC4 编码、控制流平坦化，flag 拆成多段。静态分析不现实——用运行时内省。

**动态分析打法：**

```javascript
#!/usr/bin/env node

// 1. 加载混淆模块
const cryptoMod = require('target-package/dist/lib/crypto.js');
const vaultMod = require('target-package/dist/lib/vault.js');

// 2. 枚举所有导出属性
for (const mod of [cryptoMod, vaultMod]) {
    for (const key of Object.keys(mod)) {
        const obj = mod[key];
        console.log(`Export: ${key}`);
        // 列出全部方法（含隐藏的）
        const props = Object.getOwnPropertyNames(obj);
        const proto = Object.getOwnPropertyNames(obj.prototype || {});
        console.log('  Own:', props);
        console.log('  Proto:', proto);
    }
}

// 3. 提取 flag 段
const Engine = cryptoMod.CryptoEngine;
const total = Engine.getTotalFragments();
let flag = '';
for (let i = 1; i <= total; i++) {
    flag += Engine.getFragment(i);
}
console.log('Flag:', flag);

// 4. 查隐藏方法（常见: __getFullFlag__, _debug, _raw）
const hidden = Object.getOwnPropertyNames(Engine)
    .filter(p => p.startsWith('__') || p.startsWith('_'));
console.log('Hidden methods:', hidden);
```

**要点：** 重度混淆的 JavaScript（控制流平坦化、RC4 字符串编码、死代码）让静态分析慢到不现实。`Object.getOwnPropertyNames()` 的运行时内省能列出全部方法（含隐藏的）。模块加载时自己的解密自动执行——直接调解码后的函数即可。

**识别：** npm 包带混淆/压缩的 `dist/` 目录、题目说"逆这个 CLI 工具"、`package.json` 有自定义命令。

---

## Frida 绕过证书固定（h1702ctf 2017）

APK 用 OkHttp `CertificatePinner` 做 SSL 固定。不搭 MITM 代理、不 patch APK，直接用 Frida 在已加载类上调用原生 JNI 方法。

```javascript
Java.perform(function() {
    var Requestor = Java.use("com.h1702ctf.ctfone.Requestor");
    console.log("hName: " + Requestor.hName());
    console.log("hVal: " + Requestor.hVal());
});
```

调 `hName()` 与 `hVal()` 返回服务端检查所需的 HTTP 头名与值——秘密就在类方法里，无需绕过证书固定。

**要点：** Frida 可直接在已加载类上调用原生 JNI 方法——不必在网络层绕证书固定，也不必完整逆原生二进制。

**References:** h1702ctf 2017

---

## Android 反调试三连（h1702ctf 2017）

原生 ARM 代码实现三道顺序反分析检查：

1. 读 `/proc/self/status` 找非零 `TracerPid`（调试器已挂）
2. 查 `su` 二进制是否存在（root 检测）
3. 经 `__system_property_get` 读自定义系统属性

检查门控了所需的寄存器值计算。静态绕过：用 IDA 图视图追控制流，找出穿过三道检查的"幸福路径"，倒推每个分支处寄存器必须是什么值。

**要点：** 原生 Android 代码里的反调试检查（TracerPid、su、系统属性）可用静态图分析找正确寄存器值绕过，不必真跑调试器。

**References:** h1702ctf 2017

---

## 日志泄露密钥（HackIT 2017）

安全消息应用经 Android 的 `Log.d()` 记录密码学材料：

- Curve25519 基协商值
- 每条消息的临时共享密钥
- 消息 ID 与移位计数器

AES-CBC 的 IV 派生自记录下的临时/共享值；密钥派生自记录下的基协商值与累积移位计数器。`adb logcat` 收全日志条目，重建 AES-CBC 参数解密拦截的消息。

```bash
adb logcat | grep -E "(agreement|ephemeral|shared|key)" > crypto_log.txt
# 解析日志重建: key = f(base_agreement, shift_counter)
#              iv  = f(ephemeral_shared)
```

**要点：** 安全敏感应用里过度详细的日志，泄露的状态足以在不拿任何私钥的情况下重建加密参数。

**References:** HackIT CTF 2017

---

## 内存 dump + smali 补丁提密钥（HackIT 2017）

JNI 原生库负责请求签名，密钥在 `.data` 节里 XOR 混淆，使用前才在运行时解混淆。

**工作流：**

1. 在 root 设备上用 IDA + GDB stub 加载库
2. 在 XOR 解密例程后下断点
3. dump 含解密密钥的内存区域
4. `baksmali` 反汇编 APK 的 DEX，找出构造签名 POST 请求的 smali 文件
5. Patch smali 改掉被签名的参数，`apktool` 重建重装

```bash
# 反编译 APK
apktool d target.apk -o target_decompiled/
# 改 smali: 把签名参数从原值换成目标值
# 重建
apktool b target_decompiled/ -o target_patched.apk
# 签名并安装
```

**要点：** JNI 签名场景：执行中 dump 解密密钥区域，再 patch smali 给目标参数签名——免去完整逆向原生签名算法。

**References:** HackIT CTF 2017

---

## IBM AS/400 SAVF 文件 EBCDIC 解码（EKOPARTY 2017）

IBM AS/400 SAVF（Save File）二进制用 EBCDIC 而非 ASCII。flag 与假文本按 take-2-skip-2 模式交错。

```python
import codecs

with open('savefile.savf', 'rb') as f:
    data = f.read()

# EBCDIC 转 ASCII
ascii_data = data.decode('cp500')  # cp500 是 IBM EBCDIC International

# 过滤: 保留大写字母与下划线（flag 字符集）
flag_chars = [c for c in ascii_data if c.isupper() or c == '_']
# 或解码后按 take-2-skip-2 模式取
flag = ''.join(ascii_data[i] for i in range(0, len(ascii_data), 4)
               if ascii_data[i].isupper() or ascii_data[i] == '_')
```

**要点：** EBCDIC 是 IBM 大型机原生编码。解码后看字符分布识别交错模式。按 CTF flag 格式过滤大写字母与下划线是高效捷径。

**References:** EKOPARTY CTF 2017

---

## Intel SGX Enclave 逆向（Pwn2Win 2017）

Intel SGX enclave 的 `.so` 暴露 ECALL 分发表。enclave 逻辑（含密钥派生）是标准 x86-64，IDA 完整可逆。

**工作流：**

1. 在 `.so` 里定位 ECALL 表——按 ECALL 号索引的函数指针数组
2. IDA 反编译 ECALL 识别远程认证协议
3. 用 Python + `sgx_crypto_wrapper` 手动实现认证协议
4. 密钥派生：P-256 ECDH 后接 CMAC-AES-128 派生会话密钥（SK）
5. 用派生 SK 解密 AES-128-GCM 加密的 flag blob

```python
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import cmac, ciphers

# ECDH: 与服务端 P-256 公钥派生共享密钥
private_key = ec.generate_private_key(ec.SECP256R1())
shared_secret = private_key.exchange(ec.ECDH(), server_pub_key)

# CMAC-AES-128 密钥派生（按 SGX 认证规范）
c = cmac.CMAC(ciphers.algorithms.AES(b'\x00' * 16))
c.update(shared_secret[:16])
sk = c.finalize()

# 用派生 SK 做 AES-128-GCM 解密 flag
```

**要点：** 给定 enclave 度量值，SGX 远程认证的密钥派生是确定性的——用 Python 重实现协议可恢复同一会话密钥。

**References:** Pwn2Win CTF 2017
