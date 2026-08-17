# 赛题逆向模式（第二部分）

## 目录

- [多层自解密二进制（DiceCTF 2026）](#多层自解密二进制)
- [内嵌 ZIP + XOR 许可证解密（MetaCTF 2026）](#内嵌-zip--xor-许可证解密)
- [.rodata XOR Blob 的栈字符串脱混淆（Nullcon 2026）](#rodata-xor-blob-的栈字符串脱混淆)
- [前缀哈希爆破（Nullcon 2026）](#前缀哈希爆破)
- [CVP/LLL 格约束整数校验（HTB ShadowLabyrinth）](#cvplll-格约束整数校验)
- [决策树函数混淆（HTB WonderSMS）](#决策树函数混淆)
- [GF(2^8) 高斯消元恢复 flag（ApoorvCTF 2026）](#gf28-高斯消元恢复-flag)
- [修改二进制里的 ROP 链混淆（PlaidCTF 2016）](#修改二进制里的-rop-链混淆)

---

## 多层自解密二进制（DiceCTF 2026）

**模式（another-onion）：** N 层（如 256 层）二进制，每层读 2 个密钥字节，经 SHA-256 NI 指令派生密钥流，XOR 解密下一层后跳过去。须在时限内解出（如 30 分钟）。

**正确密钥的 oracle：** 错密钥产生垃圾代码。正确密钥产生恰好含 2 条 `call read@plt` 指令的代码（下一层的读取）。用此 oracle 每层爆破全部 65536 候选。

**JIT 执行打法（最快）：**

```c
// 把二进制内存按原虚拟地址映射进求解进程
// 求解器编到不重叠地址: -Wl,-Ttext-segment=0x10000000
void *text = mmap((void*)0x400000, text_size, PROT_RWX, MAP_FIXED|MAP_PRIVATE, fd, 0);
void *bss = mmap((void*)bss_addr, bss_size, PROT_RW, MAP_FIXED|MAP_SHARED, shm_fd, 0);

// Patch read@plt 注入候选字节而非读 stdin
// Patch 层间尾 jmp/call 为 ret/NOP 以便从层返回

// fork-per-candidate: COW 免 memcpy 提供内存隔离
for (int candidate = 0; candidate < 65536; candidate++) {
    pid_t pid = fork();
    if (pid == 0) {
        // 子进程: BSS 改 MAP_PRIVATE 重映射（COW 自共享文件）
        mmap(bss_addr, bss_size, PROT_RW, MAP_FIXED|MAP_PRIVATE, shm_fd, 0);
        inject_key(candidate >> 8, candidate & 0xff);
        ((void(*)())layer_addr)();  // 层当函数调用执行
        // 检查: 解密代码是否恰含 2 条 call read@plt?
        if (count_read_calls(next_layer_addr) == 2) signal_found(candidate);
        _exit(0);
    }
}
```

**性能档位：**

| 打法 | 速度 | 256 层估算 |
|----------|-------|--------------------|
| Python subprocess | ~2/s | 数天 |
| Ptrace fork 注入 | ~119/s | 6+ 小时 |
| JIT + fork-per-candidate | ~1000/s | 140 分钟 |
| JIT + 共享 BSS + 32 工作进程 | ~3500/s | **~17 分钟** |

**共享 BSS 优化：** BSS（16MB+）以 `MAP_SHARED` 放 `/dev/shm`。子进程 `MAP_PRIVATE` 重映射做 COW。fork 开销从 16MB 页表建立降到 ~4KB。

**要点：** 多层解密题本质是造快速爆破引擎。JIT 执行（二进制内存映射进求解器、代码直接当函数跑）比 ptrace 快几个数量级。fork 的 COW 免费提供每候选的内存隔离。

**坑：**

- 真二进制层间可能用 `call`（0xe8）而非 `jmp`（0xe9）——调整尾部 patch
- BSS 可能经内核 brk 映射超出 ELF MemSiz——多映射点空间
- SHA-NI 指令在 `/proc/cpuinfo` 未声明时也可用

---

## 内嵌 ZIP + XOR 许可证解密（MetaCTF 2026）

**模式（License To Rev）：** 二进制要求许可证文件作参数。内嵌 ZIP 存期望许可证，另有 XOR 加密的 flag。

**识别：**

- `strings` 显示 `EMBEDDED_ZIP` 与 `ENCRYPTED_MESSAGE` 符号
- 二进制未 strip——`nm` 或 `readelf -s` 显示 `.rodata` 里的数据符号
- `file` 显示 PIE 可执行，源文件名 `licensed.c`

**分析工作流：**

1. **找数据符号：**

```bash
readelf -s binary | grep -E "EMBEDDED|ENCRYPTED|LICENSE"
# EMBEDDED_ZIP 在偏移 0x2220，384 字节
# ENCRYPTED_MESSAGE 在偏移 0x21e0，35 字节
```

2. **提取内嵌 ZIP：**

```python
import struct
with open('binary', 'rb') as f:
    data = f.read()
# .rodata 里找 PK\x03\x04 魔数
zip_start = data.find(b'PK\x03\x04')
# 提取 ZIP（大小取自符号表或到下个符号）
open('embedded.zip', 'wb').write(data[zip_start:zip_start+384])
```

3. **从 ZIP 取许可证：**

```bash
unzip embedded.zip  # 含 license.txt
```

4. **XOR 解密 flag：**

```python
license = open('license.txt', 'rb').read()
enc_msg = open('encrypted_msg.bin', 'rb').read()  # 从 .rodata 提取
flag = bytes(a ^ b for a, b in zip(enc_msg, license))
print(flag.decode())
```

**要点：** 无需运行二进制或绕过到期检查。内嵌 ZIP 与加密消息都在 `.rodata`——提取后离线 XOR。

**反汇编佐证：**

- `memcmp(user_license, decompressed_embedded_zip, size)` — 许可证校验
- 对 `EXPIRY_DATE=` 字段的 `sscanf("%d-%d-%d")` 日期解析
- XOR 循环：`ENCRYPTED_MESSAGE[i] ^ license[i]` → 逐字节 `putc()`

**经验：** 二进制带命名符号（`EMBEDDED_*`、`ENCRYPTED_*`）时，直接从不执行提取数据。与已知明文（许可证）XOR 平凡可逆。

---

## .rodata XOR Blob 的栈字符串脱混淆（Nullcon 2026）

**模式（stack_strings_1/2）：** 二进制 mmap `.rodata` 的 blob，XOR 脱混淆后用于校验输入。重实现校验循环恢复 flag。

**识别：**

- `mmap()` 调用后跟 `.rodata` 数据的 XOR 循环
- 校验循环带运行态（`eax`、`ebx`、`r9`），用 `0x9E3779B9`、`0x85EBCA6B`、`0xA97288ED` 等常量更新
- 位置相关移位的 `rol32()` 操作
- 期望字节存于脱混淆缓冲区

**打法：**

1. pyelftools 提取 `.rodata` blob：

   ```python
   from elftools.elf.elffile import ELFFile
   with open(binary, "rb") as f:
       elf = ELFFile(f)
       ro = elf.get_section_by_name(".rodata")
       blob = ro.data()[offset:offset+size]
   ```

2. 用反汇编里的已知密钥 XOR 恢复内嵌常量（长度、魔数值）
3. 重实现逐字节校验循环：
   - 每轮：从运行态算两个类哈希值
   - 两者 XOR 再与期望字节 XOR 恢复输入字节
   - 常量加法更新运行态

**变体（stack_strings_2）：** 加位置置换 + 前一字符的状态依赖：

- 位置置换：字节 `i` 可能放到输出位置 `pos[i]`
- 状态依赖：`need = (expected - rol8(prev_char, 1)) & 0xFF`
- 必须跟踪每轮更新为当前字符的 `state` 变量

**留意常量：**

- `0x9E3779B9`（黄金比例小数，哈希函数常见）
- `0x85EBCA6B`（MurmurHash3 finalizer 常量）
- `0xA97288ED`（关联哈希常量）
- 移位 `i & 7` 的 `rol32()`

---

## 前缀哈希爆破（Nullcon 2026）

**模式（Hashinator）：** 二进制对输入的每个前缀独立哈希、逐前缀输出摘要。给 N 个输出摘要，flag 有 N-1 个字符。

**攻击：** 逐字符恢复输入：

```python
for pos in range(1, len(target_hashes)):
    for ch in charset:
        candidate = known_prefix + ch + padding
        hashes = run_binary(candidate)
        if hashes[pos] == target_hashes[pos]:
            known_prefix += ch
            break
```

**要点：** 每个前缀哈希独立（无链式/HMAC）时，问题分解成 `N × |字符集|` 次二进制执行。这就是逐字节分组密码攻击的哈希等价物。

**识别：** 二进制输出多行哈希。改最后一个字符只改最后一行哈希。不同输入长度产生不同行数。

---

## CVP/LLL 格约束整数校验（HTB ShadowLabyrinth）

**模式：** 二进制用矩阵乘法校验 flag——分组的输入字符与系数矩阵相乘，与硬编码 64 位结果比对。普通代数失效，因为解必须是可打印 ASCII（32-126）。LLL 规约 + CVP（最近向量问题）高效求解。

**识别：**

1. 二进制分组输入字符（如每 4 个一组）
2. 每组与系数矩阵相乘
3. 结果与硬编码 64 位值比较
4. 需要约束区间（可打印 ASCII）内的整数解

**SageMath CVP 求解器：**

```python
from sage.all import *

def solve_constrained_matrix(coefficients, targets, char_range=(32, 126)):
    """
    coefficients: 系数行列表（如每组 4 值）
    targets: 期望输出值
    char_range: 合法字符区间（可打印 ASCII）
    """
    n = len(coefficients[0])  # 每组字符数
    mid = (char_range[0] + char_range[1]) // 2

    # 建格: [coeff_matrix | I*scale]
    # 目标向量含调整后的 targets
    M = matrix(ZZ, n + len(targets), n + len(targets))
    scale = 1000  # 约束字符区间的权重

    for i, row in enumerate(coefficients):
        for j, c in enumerate(row):
            M[j, i] = c
        M[n + i, i] = 1  # padding

    for j in range(n):
        M[j, len(targets) + j] = scale

    target_vec = vector(ZZ, [t - sum(c * mid for c in row)
                              for row, t in zip(coefficients, targets)]
                        + [0] * n)

    # LLL + CVP
    L = M.LLL()
    closest = L * L.solve_left(target_vec)  # 或 Babai
    solution = [closest[len(targets) + j] // scale + mid for j in range(n)]
    return bytes(solution)
```

**两阶段校验模式：**

1. **阶段 1（矩阵运算）：** CVP/LLL 解 → 恢复前 N 字符
2. 前 N 字符作 AES 密钥 → 解密 `file.bin`（末 16 字节 XOR + AES-256-CBC + zlib 解压）
3. **阶段 2（自定义 VM）：** 解密字节码在自定义 VM 里跑，经另一线性系统（mod 2^32）校验剩余字符

**模线性系统求解（阶段 2——VM 校验）：**

```python
import numpy as np
from sympy import Matrix

# M * x = v (mod 2^32)
M_mod = Matrix(coefficients) % (2**32)
v_mod = Matrix(targets) % (2**32)
# Z/(2^32) 里高斯消元
solution = M_mod.solve(v_mod)  # 返回 flag 字符
```

**要点：** 二进制用大系数线性组合校验输入、解必须落在小区间（可打印 ASCII）时，这是披着伪装格的题。LLL 规约 + CVP 找最近格点，恢复约束解。交叉参考：LLL/CVP 基础走 `/ctf-crypto`（ctf-crypto 里的 advanced-math.md）。

**识别：** 二进制对分组输入做矩阵式运算、与 64 位常量比对，爆破空间过大（如 256^4/组 × 12 组）。

---

## 决策树函数混淆（HTB WonderSMS）

**模式：** 二进制把输入路由进约 200+ 自动生成的函数，每个从输入位置计算多项式、与常量比较、左右分支。无脚本化提取时静态分析不现实。

**识别：**

1. 大量相似函数、随机名（如 `f315732804`）
2. 每个函数对特定输入位置做算术
3. 函数调其他树函数或最终校验函数
4. 反编译显示 `if (expr cmp constant) call_left() else call_right()`

**Ghidra headless 批量提取：**

```python
# 提取全部树函数的比较常量
# 运行: analyzeHeadless project/ tmp -import binary -postScript extract_tree.py
from ghidra.program.model.listing import *
from ghidra.program.model.symbol import *

fm = currentProgram.getFunctionManager()
results = []
for func in fm.getFunctions(True):
    name = func.getName()
    if name.startswith('f') and name[1:].isdigit():
        # 找 CMP 指令提取立即数常量
        inst_iter = currentProgram.getListing().getInstructions(func.getBody(), True)
        for inst in inst_iter:
            if inst.getMnemonicString() == 'CMP':
                operand = inst.getOpObjects(1)
                if operand:
                    results.append((name, int(operand[0].getValue())))
```

**从已知输出格式做约束传播：**

1. 从已知输出字节出发（如 `http://HTB{...}`）→ 固定若干输入位置
2. 固定位置沿算术约束级联 → 确定依赖位置
3. 树根方程钉住剩余自由变量
4. 部分 flag 里认出英文单词消歧多解

**要点：** 自动生成的决策树看着吓人但结构上重复。脚本化提取（Ghidra、Binary Ninja、radare2）而不是手工逐个逆。树只是分发器——真实逻辑在叶函数与其约束里。

**识别：** 数百个结构相似的函数、每函数 3-5 个输入位置引用、分支到另外两个函数或公共叶。

---

## GF(2^8) 高斯消元恢复 flag（ApoorvCTF 2026）

**模式（Forge）：** strip 二进制在 GF(2^8)（256 元素伽罗瓦域，用 AES 多项式）上做高斯消元。矩阵与增广向量内嵌 `.rodata`。解向量即 flag。

**AES 多项式（x^8+x^4+x^3+x+1 = 0x11b）的 GF(2^8) 算术：**

```python
def gf_mul(a, b):
    """AES 归约多项式下的 GF(2^8) 乘法。"""
    p = 0
    for _ in range(8):
        if b & 1:
            p ^= a
        hi = a & 0x80
        a = (a << 1) & 0xff
        if hi:
            a ^= 0x1b  # 归约: x^8 = x^4+x^3+x+1
        b >>= 1
    return p

def gf_inv(a):
    """暴力求乘法逆元（256 元素足够）。"""
    if a == 0: return 0
    for x in range(1, 256):
        if gf_mul(a, x) == 1:
            return x
    return 0
```

**解线性系统：**

```python
# 从二进制 .rodata 提取 N×N 矩阵 + N 字节增广向量
N = 56  # Flag 长度
# 建增广矩阵: N 行 × (N+1) 列

for col in range(N):
    # 找非零主元
    pivot = next((r for r in range(col, N) if aug[r][col] != 0), -1)
    if pivot != col:
        aug[col], aug[pivot] = aug[pivot], aug[col]
    # 主元行乘逆元归一
    inv = gf_inv(aug[col][col])
    aug[col] = [gf_mul(v, inv) for v in aug[col]]
    # 消去其他行的该列
    for row in range(N):
        if row == col: continue
        factor = aug[row][col]
        if factor == 0: continue
        aug[row] = [v ^ gf_mul(factor, aug[col][j]) for j, v in enumerate(aug[row])]

flag = bytes(aug[i][N] for i in range(N))
```

**要点：** GF(2^8) 不是普通整数算术——加法是 XOR，乘法带多项式归约。AES 多项式（0x11b）最常见；反汇编里找常量 `0x1b`。二进制可能事后用 AES-GCM 加密结果，但裸解向量（加密前）就是 flag。

**识别：** `.rodata` 里大矩阵（N² 字节）、XOR 行操作、常量 `0x1b` 或 `0x11b`、flag 长度等于矩阵边长的平方根。

---

## 修改二进制里的 ROP 链混淆（PlaidCTF 2016）

**模式（quite quixotic quest）：** 改过的 `curl` 二进制带自定义 `--pctfkey KEY` 选项。密钥校验把 `esp` 换成缓冲区地址，返回进 `magic_buf` 符号里存的约 250KB ROP 链。ROP 链经 XOR、MD5 与常量比较校验密钥。

**分析打法：**

1. **检测 ROP 分发：** 找 `mov esp, eax; ret` 之类栈枢轴——重定向执行进 ROP 链
2. **dump ROP 链：** GDB 脚本反汇编链中每个返回地址后的指令：

```python
# GDB 脚本迹 ROP gadget
import gdb

magic_buf = 0x080b0000  # 符号地址
buf_size = 0x40000       # 四分之一兆
offset = 0

while offset < buf_size:
    addr = int.from_bytes(gdb.selected_inferior().read_memory(magic_buf + offset, 4), 'little')
    gdb.execute(f'x/3i {addr}')
    # 前进过 gadget（一般每返回地址 4 字节）
    offset += 4
```

3. **识别链中模式：** 找展开循环（重复 gadget 序列）、跳数据的 `pop` 指令、跳大块的 `ret imm16`
4. **重建算法：** 链通常执行：
   - 密钥长度检查（与常量比较）
   - 字符级操作（ASCII 值求和、与常量 XOR）
   - 哈希计算（派生值的 MD5）
   - 哈希前缀比较
   - 输入与哈希作密钥流 XOR
   - 与内嵌常量比较

5. **提取求解：** dump 内嵌常量，爆破中间值（如字符和 → 匹配前缀的 MD5），再 XOR 恢复密钥：

```python
import hashlib

# 爆破产生正确 MD5 前缀的和
target_prefix = 0xc0050bdd  # 从 ROP 链提取
for s in range(128 * 0x35):  # 可打印字符最大和 * 密钥长度
    h = hashlib.md5(str(s ^ xor_constant).encode()).hexdigest()
    if int(h[:8], 16) == target_prefix:
        md5_key = bytes.fromhex(h)
        break

# 内嵌值与 MD5 密钥流 XOR 得 flag
flag = bytes(v ^ md5_key[i % 16] for i, v in enumerate(embedded_values))
```

**要点：** ROP 链混淆（"ROPfuscation"）把算法藏进返回导向 gadget 链。裸地址序列不可读，但 (a) dump 每个 gadget 的反汇编、(b) 滤重复与跳过区域、(c) 标注寄存器效应后即可分析。链功能等价于普通代码——只是用 `ret` 替代顺序执行。大链（100K+ gadget）常含展开循环，压缩成约 1000 行伪代码。

关联阅读：[patterns-ctf.md](patterns-ctf.md)（第一部分：隐藏模拟器 opcode、SPN 静态提取、图像 XOR 平滑度、逐字节密码、数学收敛位图、Windows PE XOR 位图 OCR、RC4+VM 两级 loader、内核模块走迷宫、多线程 VM 通道）。[patterns-ctf-3.md](patterns-ctf-3.md)（第三部分：Z3 单行 Python 电路、滑窗 popcount、键盘 LED 摩斯码、C++ 析构隐藏校验、系统调用副作用内存破坏、MFC 对话框事件、VM 顺序密钥链爆破、Burrows-Wheeler 逆变换、OpenType 连字利用、GLSL 着色器 VM 自修改代码、指令计数器作加密状态）。
