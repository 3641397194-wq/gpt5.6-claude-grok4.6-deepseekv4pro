# 逆向工具参考（静态分析）

## 目录

- [GDB](#gdb)
- [Radare2](#radare2)
- [Ghidra](#ghidra)
- [Unicorn 模拟](#unicorn-模拟)
- [Python 字节码](#python-字节码)
- [WASM 分析](#wasm-分析)
- [Android APK](#android-apk)
- [.NET 分析](#net-分析)
- [加壳二进制](#加壳二进制)
- [LLVM IR](#llvm-ir)
- [RISC-V 二进制分析](#risc-v-二进制分析)
- [Binary Ninja](#binary-ninja)
- [dogbolt.org 反编译器对比](#dogboltorg-反编译器对比)
- [常用命令](#常用命令)

动态插桩工具（Frida、angr、lldb、x64dbg）见 [tools-dynamic.md](tools-dynamic.md)。

---

## GDB

### 基本命令

```bash
gdb ./binary
run                      # 运行
start                    # 跑到 main
b *0x401234              # 地址断点
b *main+0x100            # 相对断点
c                        # 继续
si                       # 步指令
ni                       # 步过（跳调用）
x/s $rsi                 # 看字符串
x/20x $rsp               # 看栈
info registers           # 寄存器
set $eax=0               # 改寄存器
```

### PIE 二进制调试

```bash
gdb ./binary
start                    # 强制解析 PIE 基址
b *main+0xca            # 相对 main
b *main+0x198
run
```

### 一行自动化

```bash
gdb -ex 'start' -ex 'b *main+0x198' -ex 'run' ./binary
```

### 内存查看

```bash
x/s $rsi                 # RSI 处字符串
x/38c $rsi               # 38 个字符
x/20x $rsp               # 栈上 20 个 hex 字
x/10i $rip               # RIP 起 10 条指令
```

---

## Radare2

### 基本会话

```bash
r2 -d ./binary           # 调试模式打开
aaa                      # 全分析
afl                      # 函数列表
pdf @ main               # 反汇编 main
db 0x401234              # 断点
dc                       # 继续
ood                      # 重启调试
dr                       # 寄存器
dr eax=0                 # 改寄存器
```

### r2pipe 自动化

```python
import r2pipe
r2 = r2pipe.open('./binary', flags=['-d'])
r2.cmd('aaa')
r2.cmd('db 0x401234')

for char in range(256):
    r2.cmd('ood')        # 重启
    r2.cmd(f'dr eax={char}')
    output = r2.cmd('dc')
    if 'correct' in output:
        print(f"Found: {chr(char)}")
```

---

## Ghidra

### Headless 分析

```bash
analyzeHeadless /path/to/project tmp -import binary -postScript script.py
```

### 用模拟器解密

```java
EmulatorHelper emu = new EmulatorHelper(currentProgram);
emu.writeRegister("RSP", 0x2fff0000);
emu.writeRegister("RBP", 0x2fff0000);

// 写加密数据
emu.writeMemory(dataAddress, encryptedBytes);

// 设函数参数
emu.writeRegister("RDI", arg1);

// 跑到返回
emu.setBreakpoint(returnAddress);
emu.run(functionEntryAddress);

// 读结果
byte[] decrypted = emu.readMemory(outputAddress, length);
```

### MCP 命令

- 侦察：`list_functions`、`list_imports`、`list_strings`
- 分析：`decompile_function`、`get_xrefs_to`
- 标注：`rename_function`、`rename_variable`

---

## Unicorn 模拟

### 基本设置

```python
from unicorn import *
from unicorn.x86_const import *

mu = Uc(UC_ARCH_X86, UC_MODE_64)

# 映射代码段
mu.mem_map(0x400000, 0x10000)
mu.mem_write(0x400000, code_bytes)

# 映射栈
mu.mem_map(0x7fff0000, 0x10000)
mu.reg_write(UC_X86_REG_RSP, 0x7fff0000 + 0xff00)

# 运行
mu.emu_start(start_addr, end_addr)
```

### 混合模式（64 到 32）切换

```python
# 64 位 stub 经 retf/retfq 跳进 32 位代码时：
# - retf 弹 4 字节 EIP + 2 字节 CS（6 字节）
# - retfq 弹 8 字节 RIP + 8 字节 CS（16 字节）

uc32 = Uc(UC_ARCH_X86, UC_MODE_32)
# 拷内存区域，再拷 GPR
reg_map = {
    UC_X86_REG_EAX: UC_X86_REG_RAX,
    UC_X86_REG_EBX: UC_X86_REG_RBX,
    UC_X86_REG_ECX: UC_X86_REG_RCX,
    UC_X86_REG_EDX: UC_X86_REG_RDX,
    UC_X86_REG_ESI: UC_X86_REG_RSI,
    UC_X86_REG_EDI: UC_X86_REG_RDI,
    UC_X86_REG_EBP: UC_X86_REG_RBP,
}
for e, r in reg_map.items():
    uc32.reg_write(e, mu.reg_read(r) & 0xffffffff)  # mu = 上面的 64 位模拟器
uc32.reg_write(UC_X86_REG_EFLAGS, mu.reg_read(UC_X86_REG_RFLAGS) & 0xffffffff)

# SSE 密集 blob 要拷 XMM
for xr in [UC_X86_REG_XMM0, UC_X86_REG_XMM1, UC_X86_REG_XMM2, UC_X86_REG_XMM3,
           UC_X86_REG_XMM4, UC_X86_REG_XMM5, UC_X86_REG_XMM6, UC_X86_REG_XMM7]:
    uc32.reg_write(xr, mu.reg_read(xr))

# 跑 32 位，再把寄存器/内存拷回 64 位
```

**提示：** `UC_IGNORE_REG_BREAK=1` 静默未实现寄存器的警告。

### 寄存器追踪 Hook

```python
def hook_code(uc, address, size, user_data):
    if address == TARGET_ADDR:
        rsi = uc.reg_read(UC_X86_REG_RSI)
        print(f"0x{address:x}: rsi=0x{rsi:016x}")

mu.hook_add(UC_HOOK_CODE, hook_code)
```

### 追踪寄存器变化

```python
prev_rsi = [None]
def hook_rsi_changes(uc, address, size, user_data):
    rsi = uc.reg_read(UC_X86_REG_RSI)
    if rsi != prev_rsi[0]:
        print(f"0x{address:x}: RSI changed to 0x{rsi:016x}")
        prev_rsi[0] = rsi

mu.hook_add(UC_HOOK_CODE, hook_rsi_changes)
```

---

## Python 字节码

### 反汇编

```python
import marshal, dis

with open('file.pyc', 'rb') as f:
    f.read(16)  # 跳头部（随 Python 版本变）
    code = marshal.load(f)
    dis.dis(code)
```

### 提取常量

```python
for ins in dis.get_instructions(code):
    if ins.opname == 'LOAD_CONST':
        print(ins.argval)
```

### Pyarmor 静态脱壳（1shot）

仓库：`https://github.com/Lil-House/Pyarmor-Static-Unpack-1shot`

```bash
# 基本用法（递归处理）
python /path/to/oneshot/shot.py /path/to/scripts

# 显式指定 pyarmor runtime 库
python /path/to/oneshot/shot.py /path/to/scripts -r /path/to/pyarmor_runtime.so

# 输出到别的目录
python /path/to/oneshot/shot.py /path/to/scripts -o /path/to/output
```

注意：

- 运行 `shot.py` 前须存在 `oneshot/pyarmor-1shot`。
- 支持范围：Pyarmor 8.x-9.x（`PY` + 六位数字头样式）。
- Pyarmor 7 及更早（`PYARMOR` 头）不在范围。
- 反汇编输出可靠；反编译源码是实验性的。

---

## WASM 分析

### 反编译到 C

```bash
wasm2c checker.wasm -o checker.c
gcc -O3 checker.c wasm-rt-impl.c -o checker
```

### 常见模式

- `w2c_memory` - 线性内存数组
- `wasm_rt_trap(N)` - 运行时错误
- 函数导出：`flagChecker`、`validate`

---

## Android APK

### 提取

```bash
apktool d app.apk -o decoded/   # 最佳——解码 XML
jadx app.apk                     # 反编译 Java
unzip app.apk -d extracted/      # 简单提取
```

### 关键位置

- `res/values/strings.xml` - 字符串资源
- `AndroidManifest.xml` - 应用元数据
- `classes.dex` - Dalvik 字节码
- `assets/`, `res/raw/` - 资源

### 搜索

```bash
grep -r "flag\|CTF" decoded/
strings decoded/classes*.dex | grep -i flag
```

### Flutter APK（Blutter）

```bash
# 对 arm64 构建跑 Blutter
python3 blutter.py path/to/app/lib/arm64-v8a out_dir
```

### 鸿蒙 HAP/ABC（abc-decompiler）

仓库：`https://github.com/ohos-decompiler/abc-decompiler`

```bash
# 先解 .hap 拿 .abc 文件
unzip app.hap -d hap_extracted/
```

启动模式要点：

```bash
# 用 CLI 入口（避免 java -jar 进 GUI）
java -cp "./jadx-dev-all.jar" jadx.cli.JadxCLI [options] <input>
```

```bash
# 基本反编译
java -cp "./jadx-dev-all.jar" jadx.cli.JadxCLI -d "out" ".abc"

# .abc 推荐
java -cp "./jadx-dev-all.jar" jadx.cli.JadxCLI -m simple --log-level ERROR -d "out_abc_simple" ".abc"
```

注意：

- 从 `-m simple --log-level ERROR` 起步。
- `auto` 失败先试 `-m simple`。
- 报错不等于全败；查 `out_xxx/sources/`。
- 每次跑换新输出目录。

---

## .NET 分析

### 工具

- **dnSpy** - 调试 + 反编译（最佳）
- **ILSpy** - 反编译器
- **dotPeek** - JetBrains 反编译器

### NativeAOT

- 找 `System.Private.CoreLib` 字符串
- 类型元数据在但已重构
- 找长度前缀的 UTF-16 模式

### 两级 XOR + AES-CBC 解码模式（Codegate 2013）

**模式：** .NET 二进制存加密字节数组，先 XOR 解码再 AES-256-CBC 解密。同一密钥值兼作 AES key 与 IV。

**步骤：**

1. 从二进制提取硬编码字节数组与密钥串（dnSpy/ILSpy）
2. 逐字节 XOR（可能多轮，如 `0x25` 再 `0x58`，等价单轮 `0x7D`）
3. XOR 结果 Base64 解码
4. 用提取密钥同时作 Key 与 IV 的 `RijndaelManaged` 做 AES-256-CBC 解密

```python
from Crypto.Cipher import AES
from base64 import b64decode

# 步骤 1: XOR 解码
data = bytearray(encrypted_bytes)
for i in range(len(data)):
    data[i] ^= 0x7D  # 合并 XOR 密钥 (0x25 ^ 0x58)

# 步骤 2: Base64 解码
ct = b64decode(bytes(data))

# 步骤 3: AES-256-CBC 解密（同一值作 key 和 IV）
key = b"9e2ea73295c7201c5ccd044477228527"  # 补到 32 字节
cipher = AES.new(key, AES.MODE_CBC, iv=key)
plaintext = cipher.decrypt(ct)
```

**要点：** .NET 反编译里出现 `RijndaelManaged` 时，查 Key 与 IV 是否同值——赛题常见模式。XOR 阶段常是真加密前的简单混淆层。

---

## 加壳二进制

### UPX

```bash
upx -d packed -o unpacked
strings binary | grep UPX     # 查 UPX 签名
```

### 自定义壳

1. 脱壳 stub 后下断点
2. dump 内存
3. 修 PE/ELF 头

### PyInstaller

```bash
python pyinstxtractor.py binary.exe
# 看: binary.exe_extracted/
```

---

## LLVM IR

### 转汇编

```bash
llc task.ll --x86-asm-syntax=intel
gcc -c task.s -o file.o
```

---

## RISC-V 二进制分析

**模式（iguessbro）：** 静态链接、strip 的 RISC-V ELF 二进制。x86 上无法原生跑。

**Capstone 反汇编：**

```python
from capstone import *

with open('binary', 'rb') as f:
    code = f.read()

# RISC-V 64 位 + 压缩指令支持
md = Cs(CS_ARCH_RISCV, CS_MODE_RISCVC | CS_MODE_RISCV64)
md.detail = True

# 从入口点反汇编（查 ELF 头 e_entry）
TEXT_OFFSET = 0x10000  # 静态 RISC-V 常见
for insn in md.disasm(code[TEXT_OFFSET:], TEXT_OFFSET):
    print(f"0x{insn.address:x}:\t{insn.mnemonic}\t{insn.op_str}")
```

**常见 RISC-V 模式：**

- `li a0, N` → 载立即数（参数设置）
- `mv a0, s0` → 寄存器移动
- `call offset` → 函数调用（auipc + jalr 对）
- `beq/bne a0, zero, label` → 条件分支
- `sd/ld` → 64 位存/载
- `addiw` → 32 位加（W 后缀 = 字操作）

**与 x86 的关键差异：**

- 无标志寄存器——比较内联在分支指令里
- 参数在 a0-a7（非 rdi/rsi/rdx）
- 返回值在 a0
- 保存寄存器 s0-s11（被调用者保存）
- 压缩指令（2 字节）与标准（4 字节）混合——用 `CS_MODE_RISCVC`

**RISC-V 反逆向花招：**

- 字符串常量假 flag（查 `"n0t_th3_r34l"` 模式）
- 计时反爆破（rdtime 指令）
- 增量密钥 XOR 解密：`decrypted[i] = enc[i] ^ (key & 0xFF) ^ 0xA5; key += 7`

**模拟：** `qemu-riscv64 -L /usr/riscv64-linux-gnu/ ./binary`（需交叉工具链 sysroot）

---

## Binary Ninja

社区增长迅速的交互动静态分析器/反编译器。

**反编译输出：** 高级中间语言（HLIL）、伪 C、伪 Rust、伪 Python。

```bash
# 打开二进制
binaryninja binary
```

```python
# Headless 分析（Python API）
import binaryninja
bv = binaryninja.open_view("binary")
for func in bv.functions:
    print(func.name, hex(func.start))
    print(func.hlil)  # 高级 IL
```

**社区插件：** Plugin Manager（Ctrl+Shift+P → "Plugin Manager"）。

**免费版：** https://binary.ninja/free/ （云端，功能受限）。

**相对 Ghidra 的优势：** 启动更快、IL 表示更干净、脚本 Python API 更好。

---

## dogbolt.org 反编译器对比

**dogbolt.org** 对同一二进制同时跑多个反编译器、并排显示结果。

**支持的反编译器：** Hex-Rays（IDA）、Ghidra、Binary Ninja、angr、RetDec、Snowman、dewolf、Reko、Relyze。

**何时用：**

- 反编译器输出费解——对比替代品找清晰版本
- 一个反编译器处理不好某构造——另一个可能行
- 免装全本地工具快速分诊
- 交叉引用输出验证反编译器正确性

```bash
# 网页上传: https://dogbolt.org/
# 或 API:
curl -F "file=@binary" https://dogbolt.org/api/binaries/
```

**要点：** 不同反编译器各有所长。一个输出不可读时，另一个常给出更清晰伪代码。交叉引用抓反编译器 bug。

---

## 常用命令

```bash
# 文件信息
file binary
checksec --file=binary
rabin2 -I binary

# 字符串提取
strings binary | grep -iE "flag|secret"
rabin2 -z binary

# 节
readelf -S binary
objdump -h binary

# 符号
nm binary
readelf -s binary

# 反汇编
objdump -d binary
objdump -M intel -d binary
```
