# 语言专项逆向技术

## 目录

- [Python 字节码逆向（dis.dis 输出）](#python-字节码逆向disdis-输出)
- [Python Opcode 重映射](#python-opcode-重映射)
- [Pyarmor 8/9 静态脱壳（1shot）](#pyarmor-89-静态脱壳1shot)
- [DOS Stub 分析](#dos-stub-分析)
- [鸿蒙 HAP/ABC 逆向（abc-decompiler）](#鸿蒙-hapabc-逆向abc-decompiler)
- [Brainfuck / Esolang](#brainfuck--esolang)
- [UEFI 二进制分析](#uefi-二进制分析)
- [转译到 C](#转译到-c)
- [代码覆盖率侧信道](#代码覆盖率侧信道)
- [函数式语言逆向（OPAL）](#函数式语言逆向opal)
- [Python 版本特定字节码（VuwCTF 2025）](#python-版本特定字节码vuwctf-2025)
- [非双射替换密码逆向](#非双射替换密码逆向)
- [FRACTRAN 程序求逆（Boston Key Party 2016）](#fractran-程序求逆boston-key-party-2016)

平台/框架专项（Android、Electron、Node.js、Verilog、Ruby/Perl polyglot 等）见 [languages-platforms.md](languages-platforms.md)。
Go 与 Rust 二进制逆向见 [languages-compiled.md](languages-compiled.md)。

---

## Python 字节码逆向（dis.dis 输出）

### 常见模式：奇偶索引分离的 XOR 校验

题目给 CPython 字节码的 dis.dis 反汇编。常见套路：

1. 检查 flag 长度
2. 偶数位字符 XOR key1，与列表 p1 比较
3. 奇数位字符 XOR key2，与列表 p2 比较

**逆向：**

```python
# 已知：p1, p2（期望值），key1, key2（XOR 密钥）
flag = [''] * flag_length
for i in range(len(p1)):
    flag[2*i] = chr(p1[i] ^ key1)      # 偶数位
    flag[2*i+1] = chr(p2[i] ^ key2)    # 奇数位
print(''.join(flag))
```

### 字节码分析要点

- `LOAD_CONST` 后跟 `COMPARE_OP` 暴露期望值
- `BINARY_XOR` 标识变换
- `BUILD_TUPLE`/`BUILD_LIST` 带常量 = 期望输出数组
- 循环结构：`FOR_ITER` + `BINARY_SUBSCR` = 遍历 flag 字符
- 对 `ord` 的 `CALL_FUNCTION` = 字符转整数

**要点：** Python 字节码题把算法摊开成显式栈操作。聚焦 `LOAD_CONST` 值（期望输出）、`BINARY_XOR`/`BINARY_ADD`（变换）、`BUILD_TUPLE`（目标数组），无需运行即可重建校验逻辑。

---

## Python Opcode 重映射

### 识别

反编译器报 opcode 错误。

### 恢复

1. 在 PyInstaller bundle 里找被改的 `opcode.pyc`
2. 与原版 Python opcode 对比
3. 建映射：`{新opcode: 原opcode}`
4. Patch 目标 .pyc
5. 正常反编译

**捷径（Hack.lu CTF 2013）：** 若题目自带改过的 Python 解释器（如自定义 `./py` 二进制），把 `uncompyle2`/`uncompyle6` 装进该解释器的环境，用题目自己的运行时反编译。改过的解释器懂自己的 opcode 映射，标准工具即可工作，免去手工恢复 opcode。

**按 Python 版本选工具：** `uncompyle6` 覆盖 2.x–3.8。3.9+ 字节码用 [`pycdc`](https://github.com/zrax/pycdc)（源码编译：`git clone && cmake . && make`）。

**要点：** Opcode 重映射击穿所有标准反编译器。最快解法是在 PyInstaller bundle 里找改过的 `opcode.pyc`，与原版 diff，把目标 .pyc patch 回标准 opcode 再反编译。

---

## Pyarmor 8/9 静态脱壳（1shot）

- 工具：`Lil-House/Pyarmor-Static-Unpack-1shot`
- 适用 Pyarmor 8.x/9.x 加固脚本，无需执行样本代码
- 快速签名检查：payload 通常以 `PY` + 六位数字开头（Pyarmor 7 及更早的 `PYARMOR` 格式不支持）

工作流：

1. 确保目标目录含加固脚本与匹配的 `pyarmor_runtime` 库。
2. 跑 one-shot 脱壳，产出 `.1shot.` 输出（反汇编 + 实验性反编译）。
3. 以反汇编为准；反编译源码与字节码不一致时用字节码核实。

```bash
python /path/to/oneshot/shot.py /path/to/scripts
```

可选参数：

```bash
# 显式指定 runtime
python /path/to/oneshot/shot.py /path/to/scripts -r /path/to/pyarmor_runtime.so

# 输出到别的目录
python /path/to/oneshot/shot.py /path/to/scripts -o /path/to/output
```

注意：

- 运行 `shot.py` 前必须存在 `oneshot/pyarmor-1shot` 可执行文件。
- PyInstaller bundle 或压缩包先解包，再用 1shot 处理。

**要点：** Pyarmor 8/9 用运行时解密包装脚本。1shot 工具直接处理加固字节码与 `pyarmor_runtime` 库，静态脱壳、不执行。实验性反编译源码不一致时以反汇编输出为准。

---

## DOS Stub 分析

PE 文件可在 DOS stub 里藏代码：

1. Ghidra/IDA 里检查异常大的 DOS stub
2. 在 DOSBox 里运行
3. IDA 按 16 位 DOS 加载
4. 找 `int 16h`（键盘输入）

**要点：** PE 文件可在 DOS stub（PE 头之前）嵌入完整可用的 16 位 DOS 程序。stub 异常大时，在 IDA 里按 16 位 DOS 加载或丢进 DOSBox——题目逻辑可能整个住在 stub 里。

---

## 鸿蒙 HAP/ABC 逆向（abc-decompiler）

- 目标文件：`.hap` 包及内嵌 `.abc` 字节码
- 工具：`https://github.com/ohos-decompiler/abc-decompiler`
- 从 releases 下载 `jadx-dev-all.jar`

启动要点：

- `java -jar` 可能进入 GUI 模式
- CLI 模式务必用：

```bash
java -cp "./jadx-dev-all.jar" jadx.cli.JadxCLI [options] <input>
```

常用命令：

```bash
# 基本反编译到目录
java -cp "./jadx-dev-all.jar" jadx.cli.JadxCLI -d "out" ".abc"

# 反编译 .abc（该场景推荐）
java -cp "./jadx-dev-all.jar" jadx.cli.JadxCLI -m simple -d "out_hap" "modules.abc"
```

推荐参数：

- `-m simple`：降低高级重建，规避 SSA/PHI 密集导致的失败
- `--log-level ERROR`：只留关键错误
- 完整推荐命令：

```bash
java -cp "./jadx-dev-all.jar" jadx.cli.JadxCLI -m simple --log-level ERROR -d "out_abc_simple" "modules.abc"
```

参数速查：

- `-d` 输出目录
- `--help` 帮助

注意：

- `.hap` 是包：先解压（zip），再定位分析 `.abc`
- 带空格或非 ASCII 的路径要加引号
- 每次运行换新输出目录，避免旧结果
- 报错不等于全败；优先看 `out_xxx/sources/`
- `auto` 失败先切 `-m simple`

标准工作流：

1. `-m simple --log-level ERROR` 跑一遍
2. 检查输出里的关键业务文件（如 `pages/Index.java`）
3. 需要更干净输出时用 `-m auto` 或 `-m restructure` 重试
4. 个别方法仍失败就保留 `simple` 输出，走别的路径继续逻辑分析

**要点：** 鸿蒙 `.hap` 是含 `.abc` 字节码的 ZIP。用 abc-decompiler 的 CLI 模式（`jadx.cli.JadxCLI`）配 `-m simple` 最稳——直接 `java -jar` 可能弹 GUI 而不处理文件。

---

## Brainfuck / Esolang

- 查是否用已知工具编译（BF-it）
- 理解纸带/内存模型
- 对单元格操作做静态分析

### Brainfuck 逐字符静态分析（BSidesSF 2026）

**模式（i-love-my-bf-part1）：** 逐字符校验输入的 BF 程序有可识别结构：`,`（读字符）后跟一段 `+`，其数量等于该字符期望的 ASCII 值。

**提取技术：**

```python
import re

bf_code = open('challenge.bf', 'r').read()

# 按逗号（输入读取）切分——每段处理一个字符
segments = bf_code.split(',')
expected = []

for seg in segments[1:]:  # 跳过第一个逗号前的序言
    # 统计首个分支/输出操作前连续的 '+'
    plus_count = 0
    for ch in seg:
        if ch == '+':
            plus_count += 1
        elif ch in '-.[]><':
            break  # 遇非自增操作即停
    if plus_count > 0:
        expected.append(chr(plus_count % 256))

flag = ''.join(expected)
print(f"Flag: {flag}")
```

**变体：**

- `-` 操作：字符值 = `256 - minus_count`
- 混合 `+`/`-`：净增量决定值
- 字符间单元格清零（`[-]`）：各段独立
- 循环乘法：`[->>+++<<]` 乘 3——数内部操作数

**识别：** 大 BF 文件带重复的 `,` + 大量 `+` 或 `-` + 比较结构（`[-]` 或 `[->+<]` 模式）。

**要点：** 校验输入的 BF 程序结构简单——每个输入字节与单元格自增构建的常量比较。提取增量计数，无需运行程序即可恢复期望输入。

**References:** BSidesSF 2026 "i-love-my-bf-part1"

### Brainfuck 读计数 oracle 侧信道（BSidesSF 2026）

**模式（i-love-my-bf-part2）：** BF 程序逐字符校验输入时，正确字符会让程序读**更多**输入字节（前进到下一位）。统计每个候选输入触发的 `,`（读）次数——读最多的字符即正确。

```python
import itertools

def bytes_read_running_bf(bf_code, input_iter, braces):
    """跑 BF 并统计消耗的输入字节数。"""
    tape = [0] * 30000
    ptr = ip = reads = 0
    input_list = list(input_iter)
    input_idx = 0
    while ip < len(bf_code):
        c = bf_code[ip]
        if c == ',':
            if input_idx < len(input_list):
                tape[ptr] = input_list[input_idx]
                input_idx += 1
                reads += 1
            else:
                return reads
        elif c == '.': pass
        elif c == '+': tape[ptr] = (tape[ptr] + 1) % 256
        elif c == '-': tape[ptr] = (tape[ptr] - 1) % 256
        elif c == '>': ptr += 1
        elif c == '<': ptr -= 1
        elif c == '[' and tape[ptr] == 0: ip = braces[ip]
        elif c == ']' and tape[ptr] != 0: ip = braces[ip]
        ip += 1
    return reads

# 逐字符恢复 flag
PRINTABLE = list(range(32, 127))
flag = []
for pos in range(50):  # flag 最大长度
    best_byte = None
    max_reads = 0
    baseline = bytes_read_running_bf(bf, flag + [PRINTABLE[0]], braces)
    for b in PRINTABLE[1:]:
        reads = bytes_read_running_bf(bf, flag + [b], braces)
        if reads > baseline:
            best_byte = b
            break
    if best_byte is None:
        break
    flag.append(best_byte)
print(bytes(flag).decode())
```

**要点：** BF 输入校验是顺序的——读一个字符、检查、匹配才读下一个。引发更多读操作的字符就是对的，因为程序越过了校验门继续检查下一位。

**References:** BSidesSF 2026 "i-love-my-bf-part2"

### Brainfuck 比较惯用法检测（BSidesSF 2026）

**模式（i-love-my-bf-part3）：** 从高级语言编译来的 BF 用固定惯用法。相等检查 `<[-<->] +<[>-<[-]]>[-<+>]` 比较两个相邻单元格。插桩解释器在执行中检测该模式，直接从纸带提取比较操作数（期望 flag 字节）。

```python
EQ_PATTERN = "<[-<->] +<[>-<[-]]>[-<+>]"

def instrumented_bf_run(bf_code, dummy_input):
    """跑 BF，检测相等比较，提取操作数。"""
    tape = [0] * 30000
    ptr = ip = 0
    comparisons = []

    while ip < len(bf_code):
        # 检查当前位置是否开始 eq 模式
        if bf_code[ip:ip+len(EQ_PATTERN)] == EQ_PATTERN:
            # 被比较的两个单元格在 ptr-2 与 ptr-1
            lhs = tape[ptr - 2]  # 用户输入字节
            rhs = tape[ptr - 1]  # 期望字节
            comparisons.append((chr(lhs), chr(rhs)))
        # ... 常规 BF 执行 ...
        ip += 1

    return comparisons

# 比较出的期望字节即 flag
```

**要点：** 编译出的 BF 复用固定惯用法做相等比较、条件分支与循环。在 BF 源码或执行中匹配这些惯用法，无需完全理解程序逻辑即可提取常量。

**常见 BF 惯用法：**

- `[-]` — 清零单元格
- `[->+<]` — 右移单元格
- `<[-<->] +<[>-<[-]]>[-<+>]` — 两单元格相等比较

**References:** BSidesSF 2026 "i-love-my-bf-part3"

---

## UEFI 二进制分析

```bash
7z x firmware.bin -oextracted/
file extracted/* | grep "PE32+"
```

- Bootkit 替换引导加载器
- 自定义 VM 保护解密
- 把 VM 字节码提升到 C

**要点：** UEFI 二进制是 PE32+ 可执行文件。`7z` 提取固件，`file` 认 PE，Ghidra/IDA 加载。Bootkit 替换引导加载器，聚焦 DXE 驱动与 boot services 协议找题目逻辑。

---

## 转译到 C

对付重度混淆的代码：

```python
for opcode, args in instructions:
    if opcode == 'XOR':
        print(f"r{args[0]} ^= r{args[1]};")
    elif opcode == 'ADD':
        print(f"r{args[0]} += r{args[1]};")
```

`-O3` 编译做常量折叠。

**要点：** 把混淆的 VM 字节码转译成 C、`-O3` 编译，让编译器的常量折叠与死代码消除自动化简算法。复杂指令集下比手工去混淆快。

---

## 代码覆盖率侧信道

**模式（Coverup，Nullcon 2026）：** PHP 题目随密文附赠 XDebug 代码覆盖率数据。

**原理：**

- PHP 代码用 `xdebug_start_code_coverage(XDEBUG_CC_UNUSED | XDEBUG_CC_DEAD_CODE | XDEBUG_CC_BRANCH_CHECK)`
- 加密带数据相关分支：`if ($xored == chr(0)) ... if ($xored == chr(1)) ...`
- 覆盖率 JSON 揭示加密时执行了哪些分支
- 泄露出现过的 XOR 中间值集合

**利用：**

```python
import json

# 读覆盖率数据
with open('coverage.json') as f:
    cov = json.load(f)

# 从分支覆盖率提取执行过的 XOR 值
executed_xored = set()
for line_no, hit_count in cov['encrypt.php']['lines'].items():
    if hit_count > 0:
        # 行号映射到 if 语句里的 chr(N) 值
        executed_xored.add(extract_value_from_line(line_no))

# 逐位置过滤候选
for pos in range(len(ciphertext)):
    candidates = []
    for key_byte in range(256):
        xored = plaintext_byte ^ key_byte  # 或反向 S-box 查表
        if xored in executed_xored:
            candidates.append(key_byte)
    # 结合已知明文前缀，唯一确定密钥
```

**要点：** 代码覆盖率是强力 oracle——告诉你哪些条件路径被走过。任何带数据相关分支的加密都会经覆盖率泄露信息。

**对抗识别：** 找分支无关/常数时间的加密实现，它们能免疫此攻击。

---

## 函数式语言逆向（OPAL）

**模式（Opalist，Nullcon 2026）：** 由 OPAL（Optimized Applicative Language，纯函数式语言）编译的二进制。

**识别标志：**

- `.impl`（实现）与 `.sign`（签名）源文件
- `IMPLEMENTATION` / `SIGNATURE` 关键字
- 嵌套 `IF..THEN..ELSE..FI` 结构
- 函数命名 `f1`、`f2` … `fN`（数字命名）
- 大量 `seq[nat]`、`string`、`denotation` 类型

**逆向思路：**

1. 纯函数数学可逆——流水线逐步求逆
2. 识别变换链：`f_final(f_n(...f_2(f_1(input))...))`
3. 逐函数构建逆

**聚合爆破 scramble 函数：**

变换累积依赖原始（未知）值的状态时：

```python
# 例：f8 按原始字节奇偶加累积偏移
# 每元素偏移贡献取决于混淆前值是奇是偶
# 总偏移 S = 贡献之和，S mod 256 只有 256 种可能

decoded = base64_decode(target)
for total_offset_S in range(256):
    candidate = [(b - total_offset_S) % 256 for b in decoded]
    # 验证：从候选值重算 S
    recomputed_S = sum(contribution(i, candidate[i]) for i in range(len(candidate))) % 256
    if recomputed_S == total_offset_S:
        # 应用剩余逆步骤
        result = apply_inverse_substitution(candidate)
        if all(32 <= c < 127 for c in result):
            print(bytes(result))
```

**关键经验：** scramble 函数存在鸡生蛋依赖（结果依赖未知的原始值）时，爆破聚合效应（常为 mod 256 = 256 种可能），而不是指数级全状态空间。

---

## Python 版本特定字节码（VuwCTF 2025）

**模式（A New Machine）：** 题目针对特定 Python 版本（如 3.14.0 alpha）。

**关键要求：** 编译那个精确版本才能反汇编字节码——alpha/beta 版本的 opcode 与稳定版不同。

```bash
# 构建特定 Python 版本
wget https://www.python.org/ftp/python/3.14.0/Python-3.14.0a4.tar.xz
tar xf Python-3.14.0a4.tar.xz
cd Python-3.14.0a4 && ./configure && make -j$(nproc)
./python -c "import dis, marshal; dis.dis(marshal.loads(open('challenge.pyc','rb').read()[16:]))"
```

**常见校验：** flag 与 ASCII 平方值元组比较：

```python
# 逆向：flag[i] = sqrt(expected_tuple[i])
import math
flag = ''.join(chr(int(math.isqrt(v))) for v in expected_values)
```

---

## 非双射替换密码逆向

**模式（Coverup，Nullcon 2026）：** S-box/替换表存在碰撞（多输入映射同一输出）。

**检测：**

```python
sbox = [...]  # 替换表
if len(set(sbox)) < len(sbox):
    print("非双射！存在碰撞。")
```

**构建反向查表：**

```python
from collections import defaultdict
rev_sub = defaultdict(list)
for i, v in enumerate(sbox):
    rev_sub[v].append(i)
# rev_sub[输出] = [可能输入列表]
```

**消歧策略：**

1. 已知明文格式（如 `ENO{`、`flag{`）固定已知位置的密钥字节
2. 侧信道数据（代码覆盖率、计时）排除不可能候选
3. 可打印 ASCII 约束（32-126）压缩候选空间
4. 候选重加密、与已知密文核对

---

## FRACTRAN 程序求逆（Boston Key Party 2016）

FRACTRAN：以分数表迭代乘法做计算的 esolang。输入编码为素因子分解（ASCII 值作连续素数的指数）。求逆：交换每个分数的分子分母，把"成功"输出经逆程序倒着跑。

```python
# 原程序：每步找第一个 n*frac 为整数的分数
def fractran_step(n, fractions):
    for num, den in fractions:
        if (n * num) % den == 0:
            return (n * num) // den
    return None  # 停机

# 求逆：交换分数表分子分母
inverted = [(d, n) for n, d in fraction_table]
# 把目标输出经逆程序跑，恢复输入
```

**要点：** FRACTRAN 程序交换分子分母即可求逆。素因子分解编码是理解 I/O 的关键——分解结果取连续素数的指数，映射到 ASCII。

**识别：** 题目提到分数、素因子分解，或给出一列有理数。
