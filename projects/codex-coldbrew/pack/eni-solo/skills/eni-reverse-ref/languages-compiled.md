# 编译语言逆向（Go、Rust、Swift、Kotlin、D、Haskell、C++）

## 目录

- [Go 二进制逆向](#go-二进制逆向)
- [Rust 二进制逆向](#rust-二进制逆向)
- [Swift 二进制逆向](#swift-二进制逆向)
- [Kotlin / JVM 二进制逆向](#kotlin--jvm-二进制逆向)
- [D 语言二进制逆向（CSAW CTF 2016）](#d-语言二进制逆向csaw-ctf-2016)
- [Haskell：STG 闭包与 hsdecomp（hxp CTF 2017, Codegate 2018）](#haskellstg-闭包与-hsdecomp)
- [Haskell：GHC CMM 中间表示（N1CTF 2018）](#haskellghc-cmm-中间表示)
- [C++ 二进制逆向速查](#c-二进制逆向速查)

---

## Go 二进制逆向

Go 在 CLI 工具、网络服务与恶意软件中愈发常见，赛题里出镜率也逐年上升。

### 识别

```bash
# 判断 Go 二进制
file binary | grep -i "go"
strings binary | grep "go.buildid"
strings binary | grep "runtime.gopanic"

# 内嵌的 Go 版本
strings binary | grep "^go1\."
```

**关键指标：**

- 静态链接的庞然大物（hello world 也 ~2MB）
- 内嵌 `go.buildid` 字符串
- `runtime.*` 符号（strip 后仍残留一部分）
- 入口点是 `main.main` 而非 `main`
- `GOROOT`、`GOPATH`、`/usr/local/go/src/` 等字符串

### 符号恢复

Go 即使在 strip 后的二进制里也嵌入丰富的类型与函数信息：

```bash
# GoReSym - 从 Go 二进制恢复函数名、类型、接口
# https://github.com/mandiant/GoReSym
./GoReSym -d binary > symbols.json

# 解析输出
python3 -c "
import json
with open('symbols.json') as f:
    data = json.load(f)
for fn in data.get('UserFunctions', []):
    print(f\"{fn['Start']:#x}  {fn['FullName']}\")
"
```

**Ghidra + golang-loader：**

```bash
# 安装：Ghidra → Window → Script Manager → 搜 "golang"
# 或：https://github.com/getCUJO/ThreatFox/tree/main/ghidra-golang
# 恢复函数名、字符串引用、接口表
```

**redress（Go 二进制分析）：**

```bash
# https://github.com/goretk/redress
redress -src binary         # 重建源码树
redress -pkg binary         # 列包
redress -type binary        # 列类型与方法
redress -interface binary   # 列接口
```

### Go 内存布局

反编译里读懂 Go 数据结构的关键：

```c
# String: {pointer, length}（64 位下 16 字节）
# 不是 null 结尾！长度字段至关重要。
struct GoString {
    char *ptr;    // UTF-8 数据指针
    int64 len;    // 字节长度
};

# Slice: {pointer, length, capacity}（64 位下 24 字节）
struct GoSlice {
    void *ptr;    // 底层数组指针
    int64 len;    // 当前长度
    int64 cap;    // 已分配容量
};

# Interface: {type_descriptor, data_pointer}（16 字节）
struct GoInterface {
    void *type;   // 类型元数据（非空接口为 itab）
    void *data;   // 实际值
};

# Map: 指向 runtime.hmap 结构
# Channel: 指向 runtime.hchan 结构
```

**Ghidra/IDA 提示：** 函数带 `(ptr, int64)` 参数——大概率是 Go 字符串。三字段 `(ptr, int64, int64)` 是切片。

### Goroutine 与并发分析

```bash
# 反汇编里识别 goroutine 创建
strings binary | grep "runtime.newproc"
# newproc1 是内部的 goroutine 创建函数

# GDB 的 Go 支持：
gdb ./binary
(gdb) source /usr/local/go/src/runtime/runtime-gdb.py
(gdb) info goroutines          # 列全部 goroutine
(gdb) goroutine 1 bt          # goroutine 1 的回溯
```

**反汇编里的 channel 操作：**

- `runtime.chansend1` → `ch <- value`
- `runtime.chanrecv1` → `value = <-ch`
- `runtime.selectgo` → `select { case ... }`
- `runtime.closechan` → `close(ch)`

### 反编译常见 Go 模式

**defer 机制：**

- `runtime.deferproc` → 注册延迟函数
- `runtime.deferreturn` → 函数退出时执行延迟函数
- 延迟调用 LIFO 执行——与清理/加密密钥擦除相关

**错误处理（`if err != nil` 模式）：**

```text
# 反汇编里表现为：
# call some_function        → 返回 (result, error) 两个值
# test rax, rax             → 检查 error（第二返回值）是否为 nil
# jne error_handler
```

**字符串拼接：**

- `runtime.concatstrings` → `s1 + s2 + s3`
- `fmt.Sprintf` → 格式化构造
- `.rodata` 里找格式串：`"%s%d"`、`"%x"`

**CTF 常见标准库模式：**

```go
// 加密操作 → 字符串/导入里找：
// "crypto/aes", "crypto/cipher", "crypto/sha256", "encoding/hex", "encoding/base64"

// 网络操作：
// "net/http", "net.Dial", "bufio.NewReader"

// 文件操作：
// "os.Open", "io.ReadAll", "os.ReadFile"
```

### Go 二进制逆向工作流

```bash
1. file binary                          # 确认 Go、拿架构
2. GoReSym -d binary > syms.json       # 恢复符号
3. strings binary | grep -i flag        # 快速起手检查
4. Ghidra + golang-loader 加载          # 应用恢复的符号
5. 找 main.main                       # 入口点
6. 识别字符串比较                      # GoString {ptr, len} 对
7. 追加密操作                          # crypto/* 包的使用
8. 查内嵌资源                          # Go 1.16+ 的 embed.FS
```

**Go embed.FS（Go 1.16+）：** 二进制可在编译时嵌入文件：

```bash
# 找内嵌文件数据
strings binary | grep "embed"
# 内嵌文件在二进制里是裸数据
# 搜已知文件签名（PK 是 zip、PNG 头等）
```

**要点：** Go 的 runtime 在 strip 后的二进制里仍嵌入大量元数据。任何手工分析之前先跑 GoReSym——常能恢复 90%+ 函数名，反编译难度陡降。Go 字符串是 `{ptr, len}` 元组而非 null 结尾——没有 golang-loader 插件，Ghidra 默认字符串分析会漏掉它们。

**识别：** 大静态二进制（简单程序 2MB+）、`go.buildid`、`runtime.gopanic`、`/home/user/go/src/` 类源码路径。

### Go 二进制 UUID 补丁枚举 C2 客户端（BSidesSF 2026）

**模式（see-two）：** Go 编译的 C2 客户端经 `-ldflags -X` 嵌入 UUID。C2 服务端用 mTLS 认证。给 UUID 打补丁注册成新客户端，再用 C2 API 列出所有客户端并下载其外泄文件。

**打法：**

1. 从 Go 构建元数据提取嵌入 UUID：`go version -m client_binary`
2. 二进制补丁 UUID（等长字节替换——Go 字符串有定长底层数组）
3. 用补丁后的二进制注册 C2（mTLS 证书内嵌或在附件里）
4. 经 API 枚举客户端：`GET /api/clients` 或遍历已知端点
5. 列出并下载各客户端的 GCS bucket/文件存储
6. 在下载文件里 grep flag

```bash
# 提取 Go 构建信息
go version -m ./client_binary | grep ldflags
# 输出显示: -X main.clientUUID=<uuid>

# 补丁 UUID（旧 UUID 字节替换为新 UUID）
python3 -c "
import sys
data = open('client_binary', 'rb').read()
old_uuid = b'original-uuid-value-here'
new_uuid = b'attacker-uuid-value-here'
patched = data.replace(old_uuid, new_uuid)
open('client_patched', 'wb').write(patched)
"
chmod +x client_patched
./client_patched --register
```

**要点：** Go 二进制把 `-ldflags -X` 的字符串值直接放进数据段。Go 字符串是 `{ptr, len}` 对、指向底层字节数组，等长替换 UUID 字节即得合法补丁二进制。mTLS 证书认证客户端身份，但不绑定特定 UUID。

**References:** BSidesSF 2026 "see-two"

---

## Rust 二进制逆向

Rust 二进制在现代 CTF 里愈发常见，尤其加密、系统与安全工具类题目。

### 识别

```bash
# 判断 Rust 二进制
strings binary | grep -c "rust"
strings binary | grep "rustc"             # 编译器版本
strings binary | grep "/rustc/"           # 源码路径
strings binary | grep "core::panicking"   # panic 基础设施
```

**关键指标：**

- 字符串里出现 `core::panicking::panic`
- `_ZN` 开头的混淆符号（Itanium ABI）——如 `_ZN4main4main17h...`
- ELF 里的 `.rustc` 节
- 引用 `/rustc/<commit_hash>/library/`
- 二进制体积大（Rust 默认静态链接）

### 符号 demangle

```bash
# Rust 用 Itanium ABI 混淆（同 C++）
# rustfilt 解 Rust 专有符号
cargo install rustfilt
nm binary | rustfilt | grep "main"

# 或 c++filt（多数 Rust 符号可行）
nm binary | c++filt | grep "main"

# Ghidra: Window → Script Manager → 搜 "Demangler"
# 启用 "DemangleAllScript" 自动 demangle
```

### 反编译常见 Rust 模式

**Option/Result 枚举：**

```text
# Option<T> 内存布局: {判别值 (0=None, 1=Some), 值}
# Result<T, E>: {判别值 (0=Ok, 1=Err), union{ok_val, err_val}}

# 反汇编里：
# cmp byte [rbp-0x10], 0    → 检查 None/Err
# je handle_none_case
```

**Vec<T>（同 Go 切片）：**

```c
struct RustVec {
    void *ptr;      // 堆指针
    uint64 cap;     // 容量
    uint64 len;     // 长度
};
```

**String / &str：**

```text
# String（持有）: {ptr, capacity, length} — 24 字节，堆分配
# &str（借用）: {ptr, length} — 16 字节，可指向任何地方

# 反编译里找：
# alloc::string::String::from    → String 创建
# core::str::from_utf8           → 字节切片转 str
```

**迭代器链：**

```text
# .iter().map().filter().collect() 编译成循环融合
# 反汇编：紧凑循环 + 内联闭包
# 找: core::iter::adapters::map, filter 等
```

**panic 展开：**

```bash
# panic 字符串泄露源码位置与错误消息
strings binary | grep "panicked at"
strings binary | grep "called .unwrap().. on"
# 常含文件路径、行号、变量名
```

### Rust 专用分析工具

```bash
# cargo-bloat: 按函数分析二进制体积
cargo install cargo-bloat
cargo bloat --release -n 50

# Ghidra Rust 辅助脚本
# https://github.com/AmateursCTF/ghidra-rust (Rust RE 社区脚本)
```

**要点：** Rust 的 panic 消息是金矿——release 构建里也含源文件路径、行号与描述性错误串。永远先 `strings binary | grep "panicked"`。Rust 的单态化意味着泛型函数按类型复制——预期会看到大量相似函数。

**识别：** `core::panicking`、`.rustc` 节、`/rustc/` 路径、带 Rust 模块路径的 `_ZN` 混淆符号。

---

## Swift 二进制逆向

完整 Swift 逆向指南（demangling、运行时结构、Ghidra 集成）见 [platforms.md](platforms.md#swift-二进制逆向)。快速速查：

```bash
# 判断 Swift 二进制
strings binary | grep "swift"
otool -l binary | grep "swift"

# Swift 符号 demangle
swift demangle 's14MyApp0A8ClassC10checkInput6resultSbSS_tF'
# → MyApp.MyAppClass.checkInput(result: String) -> Bool

# 关键运行时函数: swift_allocObject, swift_release, swift_once
# String: 小串（≤15 字节内联）或大串（堆指针 + 长度）
# 协议见证表 = 动态分发（类似 vtable）
```

**识别：** Mach-O 里的 `__swift5_*` 节、`swift_` 运行时符号、混淆名 `s` 前缀。

---

## Kotlin / JVM 二进制逆向

Kotlin 编译到 JVM 字节码或（经 Kotlin/Native）原生代码。Android 与服务端赛题常见。

### JVM 字节码（Android/服务端）

```bash
# 判断 Kotlin
strings classes.dex | grep "kotlin"
# 找: kotlin.Metadata 注解, kotlin/jvm/internal/*

# 反编译
jadx classes.dex                     # Kotlin 字节码最佳
cfr classes.jar --kotlin             # CFR 的 Kotlin 模式
fernflower classes.jar output/       # IntelliJ 的反编译器

# 反编译输出里的 Kotlin 模式：
# - 伴生对象: ClassName$Companion
# - 数据类: copy(), component1(), component2(), toString()
# - 协程: ContinuationImpl, invokeSuspend, 状态机
# - 空检查: 到处是 Intrinsics.checkNotNull()
# - when 表达式: 编译成 tableswitch/lookupswitch
# - 密封类: 链式 instanceof 检查
```

**反汇编里的 Kotlin 协程：**

```text
# 协程编译成状态机：
# invokeSuspend(result) {
#     switch (this.label) {
#         case 0: this.label = 1; return suspendFunction();
#         case 1: processResult(result); return Unit;
#     }
# }
# 每个挂起点是 switch 的一个状态。
# 跟状态机理解异步流。
```

### Kotlin/Native

```bash
# Kotlin/Native 产平台原生二进制（无 JVM）
# 识别: konan, kotlin.native 字符串
strings binary | grep "konan"

# 难逆得多——无反射元数据
# LLVM 后端，反汇编像 C/C++
# 关键函数: InitRuntime, DeinitRuntime, CreateStablePointer
# 内存管理: 自动引用计数（非 GC）
```

**识别：** `kotlin.Metadata` 注解（JVM）、`konan` 字符串（Native）、`kotlin/` 包路径。

---

## D 语言二进制逆向（CSAW CTF 2016）

D 语言的符号混淆与 C++ 不同。编译期模板实例化产生大量函数变体。

```bash
# 识别: D 二进制的混淆不同于 C++
# 符号含 "_D" 前缀与数字长度前缀名
# 例: _D4mainQaFNaNbNfZv

# 符号 demangle:
# GDB: set language d
# Radare2: 导出名显示 demangle 后的 D 符号
# 在线: dlang.org/phobos/core_demangle.html

# 常见 D 二进制模式:
# - 编译期实例化模板: enc!("111"), enc!("222"), ...
# - 垃圾收集器引用 (GC.malloc, GC.free)
# - Phobos 标准库函数 (_D3std...)
# - 字符串处理: std.string, std.conv.to

# 逆一个 D 密码（循环密钥 XOR）:
def reverse_d_cipher(encrypted, num_functions=500):
    """D 二进制可能串联多个变换函数。
    每个函数与密钥字符 XOR，再与密钥长度 XOR。
    逆序处理。"""
    result = encrypted[:]
    for i in range(num_functions - 1, -1, -1):
        key = str(i) * 3  # 如 enc!("499") → "499499499"
        key_len = len(key)
        for j in range(len(result)):
            result[j] ^= key_len
            result[j] ^= ord(key[j % key_len])
    return bytes(result)
```

**要点：** D 二进制在赛题里少见，但可用 `_D` 符号前缀与 Phobos 库引用识别。编译期模板系统导致 D 函数被复制数百次、参数各异——找 `enc!("N")` 这类 N 变化的模式。

---

## Haskell：STG 闭包与 hsdecomp（hxp CTF 2017, Codegate 2018）

GHC 编译的 Haskell 二进制跑在 STG（Spineless Tagless G-machine）执行模型上，惰性求值、闭包与 thunk 使其极难逆向。STG 机器把一切变成闭包调用而非直接函数调用。

**识别：**

- 共享库：`libHSbase-*`、`libHSrts-*`
- 入口符号：`hs_main`（取代标准 `main`）
- 混淆符号用 Z-encoding：`z` = 前缀、`Z` = 大写、`zd` = `.`、`zi` = `$`
- GHC 调用约定寄存器映射：`rbx` = R1、`r14` = R2

**闭包结构：**

闭包是结构体，首 qword 指向 info table/代码。info table 在代码指针之前，含元数据（闭包类型、布局信息、SRT）。

```bash
# 识别 Haskell 二进制
ldd ./binary | grep libHS
readelf -s ./binary | grep hs_main

# hsdecomp 反编译（github.com/gereeter/hsdecomp）
# 恢复闭包结构与模式匹配成伪 Haskell
python2 hsdecomp ./binary

# 编译参考程序做 monkey-patching
ghc -O0 reference.hs -o reference
objcopy --dump-section .text=main_code reference
```

**Monkey-patching 技术：**

反编译失败或闭包不透明时，用同版本 GHC 编译最小 Haskell 程序，提取编译出的 `Main_main_info` 闭包代码，patch 进题目二进制。用已知求值器替换主入口，强制求值隐藏闭包并打印结果。

```haskell
-- reference.hs: 求值并打印目标闭包的最小程序
module Main where
main :: IO ()
main = print targetClosure  -- 换成你想求值的闭包
```

**要点：** Haskell 二进制因惰性求值、闭包与 thunk 而极难逆向。STG 机器把一切变成闭包调用而非直接函数调用。`hsdecomp` 恢复闭包结构与模式匹配。反编译失败时，从参考二进制 monkey-patch 已知的 `Main_main_info`，强制求值隐藏闭包并打印结果。

**识别：** `libHSbase-*` 共享库、`hs_main` 入口、Z-encoded 符号（如 `MainZCmain`）、GHC 版本串。

**References:** hxp CTF 2017, Codegate 2018

---

## Haskell：GHC CMM 中间表示（N1CTF 2018）

GHC 编译的 Haskell 因 STG 执行模型几乎无法用 IDA 反编译。拿到或能恢复 `.cmm`（C-- 中间）文件时，读它理解 thunk、闭包与惰性求值语义。对指数增长的递归结构，用记忆化算各段大小、二分查找定位，而非物化整个字符串。

**模式：** 二进制构建递归字符串结构 `f(n) = s1 + f(n-1) + s2 + f(n-1) + s3`。直接求值是 O(2^n) 的时间与空间。改为记忆化算每层递归大小，按段边界二分查找目标字符索引。

```python
# Haskell 递归字符串: f(n) = s1 + f(n-1) + s2 + f(n-1) + s3
# 直接求值 O(2^n) -- 用大小记忆化:
from functools import lru_cache

@lru_cache(maxsize=None)
def fsize(n):
    if n == 0: return len(s0)
    return len(s1) + fsize(n-1) + len(s2) + fsize(n-1) + len(s3)

def char_at(n, offset):
    if n == 0: return s0[offset]
    if offset < len(s1): return s1[offset]
    offset -= len(s1)
    if offset < fsize(n-1): return char_at(n-1, offset)
    offset -= fsize(n-1)
    if offset < len(s2): return s2[offset]
    offset -= len(s2)
    return char_at(n-1, offset)
```

**要点：** GHC 的 CMM（C minus minus）中间表示保留足够结构供识别算法。对每层翻倍的递归字符串构造，用记忆化算段大小、二分查找目标索引，而非物化指数增长的字符串。

**识别：** Haskell 二进制（识别同上）+ 题目附件带 `.cmm` 文件。找产生指数增长字符串类数据的递归闭包应用。

**References:** N1CTF 2018

---

## C++ 二进制逆向速查

通用工具对 C++ 已够用，以下模式是赛题相关要点：

### vtable 重建

```text
# 虚函数表（vtable）：
# 对象前 8 字节 → vtable 指针
# vtable 条目: [typeinfo_ptr, 析构函数, method1, method2, ...]
# Ghidra: 在 vtable 地址 Data → Create Pointer

# 识别多态分发：
# mov rax, [rdi]           # 从 this 指针取 vtable
# call [rax + 0x18]        # 调第 4 个虚方法（0x18/8 = typeinfo+dtor 后第 3 个）
```

### RTTI（运行时类型信息）

```bash
# 未 strip 时 RTTI 揭示类层次
strings binary | grep -E "^[0-9]+[A-Z]"   # 混淆类型名
c++filt _ZTI7MyClass                        # → MyClass 的 typeinfo

# Ghidra: 搜 vtable 引用，跟 typeinfo 指针
# typeinfo 结构: {vtable_for_typeinfo, name_string, base_class_ptr}
```

### 标准库模式

```text
std::string (libstdc++):
  SSO（小字符串优化）: ≤15 字符用内联缓冲
  布局: {char* ptr, size_t size, union{size_t cap, char buf[16]}}

std::vector<T>:
  {T* begin, T* end, T* capacity_end}

std::map<K,V>:
  红黑树: 每节点 {left, right, parent, color, key, value}

std::unordered_map<K,V>:
  哈希表: {bucket_array, size, load_factor_max, ...}
```
