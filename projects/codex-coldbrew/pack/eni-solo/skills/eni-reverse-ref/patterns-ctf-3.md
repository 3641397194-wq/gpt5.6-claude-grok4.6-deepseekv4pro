# 赛题逆向模式（第三部分）

## 目录

- [Z3 解单行 Python 布尔电路（BearCatCTF 2026）](#z3-解单行-python-布尔电路)
- [滑窗 popcount 差分递推（BearCatCTF 2026）](#滑窗-popcount-差分递推)
- [键盘 LED 摩斯码（PlaidCTF 2013）](#键盘-led-摩斯码)
- [C++ 析构函数隐藏校验（Defcamp 2015）](#c-析构函数隐藏校验)
- [系统调用副作用内存破坏（Hack.lu 2015）](#系统调用副作用内存破坏)
- [MFC 对话框事件定位（WhiteHat 2015）](#mfc-对话框事件定位)
- [VM 顺序密钥链爆破（Midnight Flag 2026）](#vm-顺序密钥链爆破)
- [无终结符的 Burrows-Wheeler 逆变换（ASIS CTF Finals 2016）](#无终结符的-burrows-wheeler-逆变换)
- [OpenType 连字利用（Hack The Vote 2016）](#opentype-连字利用)
- [GLSL 着色器 VM 自修改代码（ApoorvCTF 2026）](#glsl-着色器-vm-自修改代码)
- [指令计数器作加密状态（MetaCTF Flash 2026）](#指令计数器作加密状态)
- [线程竞态 + 有符号整数溢出（Codegate 2017）](#线程竞态--有符号整数溢出)
- [ESP32/Xtensa 固件 + ROM 符号图（Insomni'hack 2017）](#esp32xtensa-固件--rom-符号图)
- [objdump 批量 crackme 自动化（DEF CON 2017）](#objdump-批量-crackme-自动化)
- [fork + pipe + 死分支反分析（RCTF 2017）](#fork--pipe--死分支反分析)
- [时间锁二进制（Hack.lu 2017）](#时间锁二进制)
- [图像像素里的 ARM 代码（Hack.lu 2017）](#图像像素里的-arm-代码)
- [x86 16 位 MBR psadbw 约束求解（CSAW 2017）](#x86-16-位-mbr-psadbw-约束求解)
- [TensorFlow DNN 逐层求逆（N1CTF 2018）](#tensorflow-dnn-逐层求逆)
- [内核 JIT 导出 BPF 分析（Midnight Sun CTF 2018）](#内核-jit-导出-bpf-分析)

---

## Z3 解单行 Python 布尔电路（BearCatCTF 2026）

**模式（Captain Morgan）：** 2000+ 分号的单行 Python，海象运算符链把输入当大端整数分解，位运算构成布尔电路校验 flag。

**识别：**

- 分号分隔语句的单行 Python
- 海象 `:=` 链：`(x := expr)`
- 混淆 XOR：`(x | i) & ~(x & i)` 替代 `x ^ i`
- 输入当单个大整数处理，经位移分解

**Z3 解法：**

```python
from z3 import *

n_bytes = 29  # Flag 长度
ari = BitVec('ari', n_bytes * 8)

# 解析分号分隔语句
# 海象链建模为 LShR(ari, shift_amount)
# 布尔表达式符号化求值
# 最终断言: result_var == 0

s = Solver()
s.add(bfu == 0)  # 最终校验变量
if s.check() == sat:
    m = s.model()
    val = m[ari].as_long()
    flag = val.to_bytes(n_bytes, 'big').decode('ascii')
```

**要点：** 单行 Python 混淆构造输入位上的布尔电路。海象链只是变量赋值——按分号拆分、逐条翻译成 Z3 符号。混淆 XOR `(a | b) & ~(a & b)` 就是 `a ^ b`。Z3 一秒内解掉这类电路。找 `__builtins__` 访问或 `ord()`/`chr()` 调用识别输入→整数转换。

**识别：** 1000+ 分号的单行 Python、海象运算符、位运算、最后与 0 或 True 比较。

---

## 滑窗 popcount 差分递推（BearCatCTF 2026）

**模式（Treasure Hunt 4）：** 二进制按输入位上 16 位滑窗的期望 popcount（置位计数）逐位置校验输入。

**差分递推：**

窗口滑过 1 位时：

```text
popcount(window[i+1]) - popcount(window[i]) = bit[i+16] - bit[i]
```

所以：`bit[i+16] = bit[i] + (data[i+1] - data[i])`

```python
expected = [...]  # 337 个期望 popcount 值
total_bits = 337 + 15  # = 352

# 爆破初始 16 位窗口（popcount 必须等于 expected[0]）
for start_val in range(0x10000):
    if bin(start_val).count('1') != expected[0]:
        continue

    bits = [0] * total_bits
    for j in range(16):
        bits[j] = (start_val >> (15 - j)) & 1

    valid = True
    for i in range(len(expected) - 1):
        new_bit = bits[i] + (expected[i + 1] - expected[i])
        if new_bit not in (0, 1):
            valid = False
            break
        bits[i + 16] = new_bit

    if valid:
        # 位转字节
        flag_bytes = bytes(int(''.join(map(str, bits[i:i+8])), 2)
                          for i in range(0, total_bits, 8))
        if b'BCCTF' in flag_bytes or flag_bytes[:5].isascii():
            print(flag_bytes.decode(errors='replace'))
            break
```

**要点：** 滑窗 popcount 差分形成递推：每个新位由 16 位前的位加 popcount 增量决定。只有前 16 位自由（受初始 popcount 约束）。爆破约 4000-8000 个合法初始窗口——每个窗口决定整个位序列。一秒内跑完。

**识别：** 二进制对固定大小窗口算 popcount/汉明重量。期望值数组长度 ≈ 输入位数 - 窗口大小 + 1。数组值是小整数（0 到窗口大小）。

---

## 键盘 LED 摩斯码（PlaidCTF 2013）

**模式：** 二进制用 `ioctl(fd, KDSETLED, value)` 闪烁键盘 LED（Num/Caps/Scroll Lock）。时序模式编码摩斯码。

```bash
# 第一步: 绕 ptrace 反调试
# 偏移处 NOP（0x90）掉 ptrace 调用
python3 -c "
data = open('binary','rb').read()
data = data[:0x72b] + b'\x90'*5 + data[:0x730]  # NOP ptrace 调用
open('patched','wb').write(data)
"

# 第二步: strace 下跑，抓 ioctl 调用
strace -e ioctl ./patched 2>&1 | grep KDSETLED > leds.txt

# 第三步: 解码时序模式
# 短闪（250ms）= 点 (.), 长闪（750ms）= 划 (-)
# 字符间停顿 = 3x, 词间停顿 = 7x
```

```python
# 解析 strace 输出提取摩斯
import re
morse_map = {'.-':'A', '-...':'B', '-.-.':'C', '-..':'D', '.':'E',
             '..-.':'F', '--.':'G', '....':'H', '..':'I', '.---':'J',
             '-.-':'K', '.-..':'L', '--':'M', '-.':'N', '---':'O',
             '.--.':'P', '--.-':'Q', '.-.':'R', '...':'S', '-':'T',
             '..-':'U', '...-':'V', '.--':'W', '-..-':'X', '-.--':'Y',
             '--..':'Z', '-----':'0', '.----':'1'}
# LED 亮时长短映射点划，按停顿分组
```

**要点：** `KDSETLED` 控制 Linux 上物理键盘 LED（`/dev/console`）。二进制必须有控制台访问权限。`strace -e ioctl` 无需物理观察即可捕获全部 LED 状态变化。调用间时序决定点与划。

---

## C++ 析构函数隐藏校验（Defcamp 2015）

校验逻辑可藏在 `main()` 返回后执行的 C++ 析构函数里。`__cxa_atexit` 机制注册析构回调：

1. **定位析构：** 在 `.init_array`/构造节里搜 `__cxa_atexit` 调用
2. **静态分析：** 找出析构里做 flag 检查的全局对象
3. **动态验证：** 断在 `__cxa_finalize` 追 main 之后的执行

```asm
# IDA/Ghidra 里找 atexit 注册
__cxa_atexit(destructor_func, object_ptr, dso_handle);

# 析构含真实校验：
# - 4 字节块上的正则模式匹配（8 道顺序检查）
# - 算术: v2 += -3 * s[i] + 36 + (s[i] ^ 0x2FCFBA)
# - 累积和的模校验
```

**要点：** `main()` 看着平凡或不完整时，查 C++ 全局/静态对象的析构。`.fini_array` 节与 `__cxa_atexit` 注册暴露隐藏的 main 之后逻辑。

---

## 系统调用副作用内存破坏（Hack.lu 2015）

`rt_sigprocmask` 系统调用把 `sigset_t` 结构写到输出指针。输入解析传了指向安全关键变量附近的指针时：

1. 某些输入字符（如 `:` 到 `@` 范围，值 0x3A-0x40）触发 `rt_sigprocmask` 副作用
2. 系统调用清零输出地址处的字节，可能覆盖相邻变量
3. 小端布局下，清零相邻整数变量的 MSB 等效把它设成小值

```c
// 内存布局（无 ASLR）：
// 0x603390: input_buffer[4]
// 0x603394: security_check_var

// 输入 ':' 触发: rt_sigprocmask(SIG_BLOCK, NULL, (sigset_t*)0x603397, ...)
// 这清零 0x603397+ 的字节，破坏 security_check_var 的高字节
```

**要点：** 审计输入校验函数与系统调用的交互。hex 转换例程里的字符→系统调用映射可经内核态操作产生意外的内存写。

---

## MFC 对话框事件定位（WhiteHat 2015）

在 MFC（Microsoft Foundation Class）应用里找事件 handler：

1. **断 SendMessageW：** 断在 `user32!SendMessageW` 拦截对话框消息
2. **滤 WM_COMMAND：** 消息 ID 0x111 是按钮点击与控制事件
3. **追消息映射：** 沿 MFC 消息分发 `CWnd::OnWndMsg` → `CCmdTarget::OnCmdMsg` → handler 函数
4. **OnInitDialog：** 常含解密或校验初始化；由 WM_INITDIALOG（0x110）触发

```asm
# WinDbg/x64dbg:
bp user32!SendMessageW ".if (poi(@esp+8)==0x111) {} .else {gc}"
# 或 IDA 里: 找 AFX_MSGMAP_ENTRY 结构的交叉引用
```

**要点：** MFC 应用经分发表路由消息。识别 `AFX_MSGMAP` 结构即可无运行时分析枚举全部处理的消息。

---

## VM 顺序密钥链爆破（Midnight Flag 2026）

**模式（67）：** 自定义 VM 按 N 字节块校验输入。每块输出密钥喂作下一块输入，无法并行求解。每块搜索空间小到可爆破（3 字节块 = 2^24）。

**识别信号：**

- XOR 混淆 opcode 的字节码（全字节 XOR 常量，产出像 ASCII 的字节码）
- 迭代变换循环（xorshift + 乘法，重复 1000+ 次）使代数求逆不现实
- CHECK opcode 把累积状态与内嵌常量比较
- 大 `.data` 节带重复字节码模式

**求解打法：**

1. 解析字节码提取 CHECK 值（每块后的期望密钥）
2. 逐块顺序爆破产出期望密钥的输入字节
3. CHECK 值作下一块的密钥

```c
// OpenMP 并行逐块爆破
uint32_t process(uint32_t val) {
    for (int i = 0; i < 1000; i++) {
        val ^= (val << 13);
        val ^= (val >> 17);
        val ^= (val << 5);
        val *= 0x2545f491;
    }
    return val;
}

int solve_block(uint32_t old_key, uint32_t expected_key, unsigned char *out) {
    int found = 0;
    #pragma omp parallel for shared(found)
    for (int v = 0; v < 0x1000000; v++) {
        if (found) continue;
        uint32_t input_val = ((v >> 16) << 16) | (v & 0xFF) | ((v >> 8 & 0xFF) << 8);
        uint32_t saved = input_val ^ old_key;
        uint32_t final_val = process(saved);
        if ((final_val ^ saved) == expected_key) {
            #pragma omp critical
            { if (!found) { out[0]=v>>16; out[1]=(v>>8)&0xFF; out[2]=v&0xFF; found=1; } }
        }
    }
    return found;
}
// 编译: gcc -O3 -march=native -fopenmp -o solve solve.c
```

**要点：** 变换刻意不可逆（迭代类哈希函数）时，爆破就是出题人的本意。OpenMP 并行是关键——287 块 × 16.7M 候选并行跑分钟级，单线程小时级。顺序密钥依赖意味着必须按序解块，但每块的搜索本身是尴尬的并行。

---

## 无终结符的 Burrows-Wheeler 逆变换（ASIS CTF Finals 2016）

BWT 应用于二进制表示、无标准终结符。需试全部可能原始串暴力求逆。

```python
def bwt_inverse_bruteforce(bwt_string):
    """无终结符时的 BWT 求逆。
    标准 BWT 逆变换需要终结符位置。
    没有它，就试全部 n 种旋转。"""
    n = len(bwt_string)

    # 标准 BWT 逆变换产一张表
    table = [''] * n
    for _ in range(n):
        table = sorted([bwt_string[i] + table[i] for i in range(n)])

    # 无终结符时 n 行都是合法候选
    # 按已知约束过滤（如二进制以 '1' 开头、匹配 XOR 模式）
    candidates = []
    for row in table:
        # 施加题目特定校验
        if is_valid_plaintext(row):
            candidates.append(row)

    return candidates

def bwt_with_xor_rounds(encrypted_hex, num_rounds):
    """多轮 BWT + 轮索引派生 XOR 密钥"""
    data = bytes.fromhex(encrypted_hex)
    for round_idx in range(num_rounds - 1, -1, -1):
        # 每轮: 二进制表示的 BWT，再与轮密钥 XOR
        binary_str = ''.join(format(b, '08b') for b in data)
        candidates = bwt_inverse_bruteforce(binary_str)
        # 选匹配约束的候选（前导 '1'、尾位规则）
        data = select_valid_candidate(candidates, round_idx)
    return data
```

**要点：** 标准 BWT 用终结符（如 '$'）标记原始串位置。没有它，BWT 求逆产出 n 个候选（每种旋转一个）。用领域特定约束（二进制格式、XOR 轮结构、flag 前缀）识别正确候选。

---

## OpenType 连字利用（Hack The Vote 2016）

带自定义 OpenType 连字的字体文件把可见字符映射到隐藏字形。GSUB（Glyph Substitution）表定义这些映射。

```python
from fontTools.ttLib import TTFont

def decode_font_ligatures(font_path, encoded_text):
    """提取连字替换表并解码消息"""
    font = TTFont(font_path)

    # 提取 GSUB 表的连字替换
    gsub = font['GSUB']

    # 导航到连字 lookup
    ligature_map = {}
    for lookup in gsub.table.LookupList.Lookup:
        for subtable in lookup.SubTable:
            if hasattr(subtable, 'ligatures'):
                for glyph_name, ligatures in subtable.ligatures.items():
                    for lig in ligatures:
                        # 映射: 输入序列 -> 输出字形
                        input_seq = [glyph_name] + lig.Component
                        output = lig.LigGlyph
                        ligature_map[tuple(input_seq)] = output

    print("找到的连字映射:")
    for inp, out in ligature_map.items():
        print(f"  {inp} -> {out}")

    # 备选: TTF 转 XML 手工分析
    # font.saveXML('font_dump.xml')
    # 搜 <LigatureSubst> 条目

# 命令行打法:
# pip install fonttools
# ttx font.otf  # 转 XML
# grep -A5 'LigatureSubst' font.ttx
```

**要点：** 带 GSUB 连字表的自定义字体构成密码——显示字符与其字形映射不同。`fonttools` 的 `ttx` 命令把字体 dump 成 XML，连字替换表一目了然。每个连字把输入字符序列映射到不同输出字形。

---

## GLSL 着色器 VM 自修改代码（ApoorvCTF 2026）

**模式（Draw Me）：** WebGL2 片段着色器在 256x256 RGBA 纹理上实现图灵完备 VM。纹理既是程序内存又是显示输出。

**纹理布局：**

- **第 0 行：** 寄存器（像素 0 = 指令指针，像素 1-32 = 通用）
- **第 1-127 行：** 程序内存（RGBA = opcode, arg1, arg2, arg3）
- **第 128-255 行：** 显存（显示输出）

**Opcodes：** NOP(0)、SET(1)、ADD(2)、SUB(3)、XOR(4)、JMP(5)、JNZ(6)、VRAM-写(7)、STORE(8)、LOAD(9)。每帧 16 步。

**自修改代码：** 阶段 1（解密）用 STORE opcode XOR-patch 程序内存，阶段 2（绘制）再执行。解密在绘制代码运行前把 SET 指令覆写为正确像素颜色值。

**为何 GPU 渲染失败：** GPU 每帧并行跑全部像素，但着色器每帧每像素只跟踪一个写目标。一帧多次 VRAM 写只有最后一次存活——丢失 75%+ 像素。同理 STORE 补丁在并行解密中冲突。

**顺序模拟求解：**

```python
from PIL import Image
import numpy as np

img = Image.open('program.png').convert('RGBA')
state = np.array(img, dtype=np.int32).copy()
regs = [0] * 33

# 阶段 1: 迹解密——顺序应用全部 STORE 补丁
x, y = start_x, start_y
while True:
    r, g, b, a = state[y][x]
    opcode = int(r)
    if opcode == 1: regs[g] = b & 255           # SET
    elif opcode == 4: regs[g] = regs[b] ^ regs[a]  # XOR
    elif opcode == 8:                              # STORE——patch 程序内存
        tx, ty = regs[g], regs[b]
        state[ty][tx] = [regs[a], regs[a+1], regs[a+2], regs[a+3]]
    elif opcode == 5: break                        # JMP 到绘制阶段
    x += 1
    if x > 255: x, y = 0, y + 1

# 阶段 2: 执行绘制代码——保留全部 VRAM 写
vram = np.zeros((128, 256), dtype=np.uint8)
# ... 迹 opcode 7: vram[ty][tx] = color
Image.fromarray(vram, mode='L').save('output.png')
```

**要点：** GLSL 着色器图灵完备，但 GPU 并行引发写冲突。自修改代码（STORE 补丁）雪上加霜——并行执行的补丁互相覆写。Python 顺序模拟恢复完整输出。program.png 文件本身就是字节码。

**识别：** WebGL/着色器题带 PNG "程序"文件，题目说"渲染不出来"或输出花屏。GLSL 源码里找自定义 opcode 表。

---

## 指令计数器作加密状态（MetaCTF Flash 2026）

**模式（Who's Counting?）：** 手写汇编二进制用专用寄存器（如 `r12`）作指令计数器，几乎每条指令后自增。计数器值喂进每个输入字节的 XOR、ROL、乘法变换，使整个变换路径相关——依赖处理每个字节前执行过的指令数。

**识别：**

- 手写汇编（无编译器模式、异常寄存器用法）
- 一个只自增的寄存器（`inc r12` 或 `add r12, 1`）出现在多数指令后
- 引用该计数寄存器的变换（`xor rax, r12`、`rol al, cl` 且 `cl` 派生自计数器）
- 状态前传的顺序字节处理循环

**求解打法：**

```python
# 逐字节爆破 + 模拟
# 每个字节的变换依赖计数器（依赖之前全部指令），状态路径相关。

from unicorn import *
from unicorn.x86_const import *

def try_byte(known_prefix, candidate_byte):
    """模拟二进制跑已知前缀 + 候选，检查输出。"""
    uc = Uc(UC_ARCH_X86, UC_MODE_64)
    # 映射代码、栈、数据段
    uc.mem_map(CODE_BASE, 0x10000)
    uc.mem_write(CODE_BASE, binary_code)
    uc.mem_map(STACK_BASE, 0x10000)
    uc.mem_map(DATA_BASE, 0x10000)

    # 写输入: known_prefix + candidate
    test_input = known_prefix + bytes([candidate_byte])
    uc.mem_write(DATA_BASE, test_input + b'\x00' * (64 - len(test_input)))

    # 设寄存器（rsp、指向输入的 rdi、r12 = 0）
    uc.reg_write(UC_X86_REG_RSP, STACK_BASE + 0x8000)
    uc.reg_write(UC_X86_REG_R12, 0)  # 指令计数器从 0 开始

    try:
        uc.emu_start(CODE_BASE + ENTRY_OFFSET, CODE_BASE + EXIT_OFFSET)
        # 读变换输出，与期望比对
        output = uc.mem_read(OUTPUT_ADDR, len(test_input))
        return output[:len(test_input)] == expected[:len(test_input)]
    except:
        return False

# 逐字节恢复 flag
flag = b''
for pos in range(FLAG_LEN):
    for b in range(256):
        if try_byte(flag, b):
            flag += bytes([b])
            print(f"Position {pos}: {chr(b)} -> {flag}")
            break
```

**要点：** 寄存器作指令计数器喂进字节变换时，字节 N 的变换依赖处理字节 0 到 N-1 时执行的确切指令数。解析求逆不现实——每个字节位置的计数器值依赖此前全部字节的执行路径。逐字节爆破 + 完整模拟（Unicorn 或 GDB 脚本）最可靠——每位置试 256 个值，保留正确前缀的状态。

**识别：** 二进制无标准库调用、一致使用异常寄存器、存在只自增的寄存器。每字节变换涉及引用该计数器的操作（XOR、旋转、乘法）。题目名暗示 "counting" 或 "instructions"。

**替代打法：**

- GDB 脚本：每字节变换后断点，比对输出
- 静态分析：手工数指令算计数器值，再代数求逆（计数器累积易错）

**References:** MetaCTF Flash CTF 2026 "Who's Counting?"

---

## 线程竞态 + 有符号整数溢出（Codegate 2017）

**模式（Hunting）：** 战斗模拟二进制用线程不安全的技能选择。攻击线程用有符号比较查 `skill_id <= 4`，睡一小会儿后施加伤害。睡眠期间切到别的技能。火球技能用 `cdqe`（EAX 符号扩展 RAX），把 `0xFFFFFFFF`（冰剑伤害）转成 -1（有符号 64 位）。从 BOSS HP（`0x7FFFFFFFFFFFFFFF`）减 -1 引发有符号溢出到负值，杀死 BOSS。

```python
# 竞态利用:
# 线程 A: 选火球 (skill_id=2, 过 <= 4 检查)
# 线程 A: 睡动画帧
# Main: 切到冰剑 (skill_id=5, damage=0xFFFFFFFF)
# 线程 A: 醒, 从冰剑槽读伤害
# cdqe: 0xFFFFFFFF -> 0xFFFFFFFFFFFFFFFF (-1 有符号)
# boss_hp -= (-1) -> boss_hp = 0x7FFFFFFFFFFFFFFF + 1 = 负值 -> 死

import time, threading
def race():
    select_skill(2)  # 火球——过边界检查
    time.sleep(0.001)
    select_skill(5)  # 冰剑——竞进伤害计算
```

**要点：** `cdqe`（Convert Doubleword to Quadword Extension）把 32 位 EAX 符号扩展成 64 位 RAX。攻击代码读 32 位伤害值再符号扩展时，`0xFFFFFFFF` 变成 -1。减负数等于加，但 HP 已在 `INT64_MAX` 时加法溢出到负值，击杀目标。

---

## ESP32/Xtensa 固件 + ROM 符号图（Insomni'hack 2017）

**模式（Internet of Fail）：** ESP32 固件（Xtensa 架构）无 IDA 原生支持。用 radare2 + ESP32 ROM 链接脚本（`esp32.rom.ld`）把函数地址映射成名称。对照公开 ESP32 HTTP server 源码识别密码检查逻辑——由约 20 个操作全局状态变量的条件 XOR 函数组成。

```bash
# radare2 加载 ESP32 固件
r2 -a xtensa -b 32 firmware.bin

# 应用 ESP-IDF 的 ROM 符号映射
# esp32.rom.ld 映射如：
# 0x40000000 = ets_printf
# 0x400013A0 = cache_Read_Enable
# 加载为 flags: . esp32.rom.ld.r2

# 交叉引用识别 HTTP 请求处理器
# 对照 esp-idf/examples/protocols/http_server
# 找 URI 处理器注册模式
```

**要点：** ESP32 的 Xtensa 架构缺主流 RE 工具支持，但 ESP-IDF SDK 提供 ROM 链接脚本映射每个 ROM 函数地址到名称。把它们加载为 radare2 符号立即解析数百个函数调用。对照公开 ESP-IDF 示例代码，即使 strip 固件也能识别应用级模式（HTTP 处理器、WiFi 回调）。

---

## objdump 批量 crackme 自动化（DEF CON 2017）

用脚本化 `objdump` 提取比较值与算术操作，无需执行即可算出数百个同构 crackme 的密钥。

```bash
# 简单变体: 直接提取 CMP 立即数
objdump -M intel -d $binary | grep -P "cmp\s+rdi" | \
    grep -oP "0x\w{1,2}" | xxd -r -p

# 复杂变体: 解析 add/sub/cmp 链反推
# 每个二进制: 一串 add/sub rdi,N 再 cmp rdi,target
# 逆向: 从 target 出发，倒序撤销操作
python3 <<'EOF'
import subprocess, re, glob
for binary in sorted(glob.glob("crackmes/*")):
    asm = subprocess.check_output(["objdump", "-M", "intel", "-d", binary]).decode()
    ops = re.findall(r'(add|sub)\s+rdi,(0x\w+)', asm)
    target = int(re.search(r'cmp\s+rdi,(0x\w+)', asm).group(1), 16)
    # 逆操作
    for op, val in reversed(ops):
        val = int(val, 16)
        target = (target - val) if op == 'add' else (target + val)
    print(chr(target & 0xff), end='')
EOF
```

**要点：** 批量 crackme 题（数百上千个二进制）结构一致、仅常量不同。脚本化 `objdump` 反汇编解析提取立即数与算术序列，代数反推密钥。无需执行或模拟。

---

## fork + pipe + 死分支反分析（RCTF 2017）

二进制用 fork/pipe IPC：父进程写数据后退出，子进程读管道继续。密钥校验在死分支（恒假比较）里，需二进制补丁才能到达。

```bash
# 检测: main 里 fork() + pipe() + read()/write()
# 子进程读管道，需要知道自己的 PID

# 死分支模式:
# cmp DWORD PTR [ebp-0xc], 0x1  ; 0 与 1 比较, 恒假
# je  real_flag_computation      ; 永不到达

# 补丁: 比较值 0x1 改 0x0
# 找: 83 7d f4 01 → 改: 83 7d f4 00
python3 -c "
data = open('binary','rb').read()
data = data.replace(b'\x83\x7d\xf4\x01', b'\x83\x7d\xf4\x00')
open('binary_patched','wb').write(data)
"
```

**要点：** fork+pipe 构造父供数据、子继续的关系。死分支（恒假比较）藏真实校验逻辑。`strace` 揭示 fork/pipe/read 模式；patch 比较常量到达隐藏代码路径。

---

## 时间锁二进制（Hack.lu 2017）

二进制读系统日期，只在特定日期正确执行（如 2012 年 12 月 21 日）。日期常量在二进制里是 Unix 时间戳或结构化日期比较。

**检测：** 找与可识别日期区间大整数常量的比较（Unix 时间戳：2012 = ~1.35B，2017 = ~1.5B）。文化意义有帮助：末日日期、CTF 发布日、历史事件。

```bash
# 系统时钟设到所需日期
sudo date -s "2012-12-21 00:00:00"
./binary

# 或 faketime 免系统级改动
LD_PRELOAD=/usr/lib/faketime/libfaketime.so.1 FAKETIME="2012-12-21 00:00:00" ./binary

# 之后恢复系统时间
sudo ntpdate pool.ntp.org
```

**IDA/Ghidra 里：** 搜 `time()` 或 `localtime()` 调用。看 `tm` 结构字段：`tm_year`（1900 起年数）、`tm_mon`（0 基）、`tm_mday`。

**要点：** 时间密钥用文化意义日期。逆向代码里永远查日期比较，深入分析前先试改系统时钟或 faketime。

**References:** Hack.lu CTF 2017

---

## 图像像素里的 ARM 代码（Hack.lu 2017）

JavaScript 题把 ARM 字节码内嵌图像像素数据。图像 base64 编码在 HTML/JS 源码里。像素 RGBA 值编码 ARM 指令。捆绑的 UnicornJS 库（JavaScript 的 ARM CPU 模拟器）提取并执行字节码。

**识别流程：**

1. JS 源码里找 base64 blob → 解码 → PNG/BMP 文件
2. 识别 UnicornJS 导入（`unicorn.js`、`uc.js` 等）→ 确认 ARM 模拟
3. 像素提取循环：光栅序拼接 RGBA 字节构成 ARM 指令流
4. 提取字节喂给 ARM 反汇编器

```python
from PIL import Image
import capstone

img = Image.open('decoded.png').convert('RGBA')
pixels = list(img.getdata())

# 从像素提取 ARM 字节码（每像素 4 字节: R, G, B, A）
arm_code = bytes([channel for pixel in pixels for channel in pixel])

# 按 ARM Thumb 或 ARM32 反汇编
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
for insn in md.disasm(arm_code, 0x0):
    print(f"0x{insn.address:04x}: {insn.mnemonic} {insn.op_str}")
```

**要点：** 多层混淆：ARM 码在图像像素里、base64 编码、运行时经 UnicornJS 模拟。先识别模拟器库才知道逆哪个 ISA——库名揭示架构。

**References:** Hack.lu CTF 2017

---

## x86 16 位 MBR psadbw 约束求解（CSAW 2017）

可引导 MBR 用 SSE2 `psadbw`（Packed Sum of Absolute Differences of Bytes）在 xmm 寄存器上校验 flag。每轮掩 2 个输入字节，与已知常量算 `psadbw`，和与期望值比较。

**`psadbw` 语义：**

```asm
psadbw xmm0, xmm1
; 8 个字节对每对: sum += |xmm0[i] - xmm1[i]|
; 结果以 16 位整数存 xmm0 低 qword
```

这生成绝对差之和方程：

```text
|a[0] - k[0]| + |a[1] - k[1]| + ... + |a[7] - k[7]| = C
```

**解法：**

```python
import numpy as np
from itertools import product

# 每个 2 字节掩码组，提取常量与期望和
# 方程非纯线性（绝对值），但可打印 ASCII
# 把每字节约束到 [0x20, 0x7e]，限制爆破空间

def solve_psadbw_group(known_constants, expected_sum, printable_range=(0x20, 0x7e)):
    """给定绝对差和约束，爆破 2 个未知字节。"""
    solutions = []
    for a, b in product(range(*printable_range), repeat=2):
        pair = [a, b]
        sad = sum(abs(pair[i] - known_constants[i]) for i in range(len(pair)))
        if sad == expected_sum:
            solutions.append(bytes([a, b]))
    return solutions

# 多解歧义: 施加附加约束
# (flag 格式前缀、字符频率、后续迭代)
```

**要点：** `psadbw` 生成绝对差之和方程——非纯线性，但字节限于可打印 ASCII 时约束爆破可解。每 2 字节组独立，搜索空间 95^2 = ~9000 候选/组。

**References:** CSAW CTF 2017

---

## TensorFlow DNN 逐层求逆（N1CTF 2018）

**模式：** 二进制实现 5 层 sigmoid 激活深度神经网络。输入（flag 字符）在进网络前变换为 `1.0/char_value`。从二进制提取权重与偏置，逐层求逆：逆 sigmoid、减偏置、乘权重矩阵逆。

```python
import numpy as np

def sigmoid_inv(x):
    return -np.log(1.0/x - 1.0)

# 从输出到输入逐层求逆
v = target_output
for i in range(num_layers - 1, -1, -1):
    v = np.dot(sigmoid_inv(v) - biases[i], np.linalg.inv(weights[i]))

# 输入是 1.0/char，flag 字符是乘法逆
flag = ''.join(chr(int(round(1.0 / v[j]))) for j in range(len(v)))
```

**要点：** 激活可逆（sigmoid、tanh）且权重矩阵方阵的神经网络可逐层数学求逆。逆 sigmoid、减偏置、乘权重逆。留意输入变换（如 1/x）也要逆。

**识别：** TensorFlow 或自定义 DNN 实现的二进制。找 sigmoid/tanh 调用、矩阵乘法、`.rodata` 里硬编码浮点数组（权重/偏置）。方阵权重矩阵（N x N）说明网络可逆。

**References:** N1CTF 2018

---

## 内核 JIT 导出 BPF 分析（Midnight Sun CTF 2018）

**模式：** 二进制创建带 BPF（Berkeley Packet Filter）的裸 socket。标准 BPF 反汇编器输出不可读时，开内核 BPF JIT 编译器把 BPF 字节码转原生 x64 汇编，再从 dmesg 读编译代码。

```bash
# 开 BPF JIT 编译
echo 1 > /proc/sys/net/core/bpf_jit_enable

# 跑二进制，从内核日志读 JIT 编译的 BPF
dmesg | grep -A 100 "flen="

# 分析揭示: 期望 UDP 3333 端口的 DNS TXT 查询
dig @target -p 3333 'M4d!bKn3~l' TXT
```

**要点：** Linux 可把 BPF 过滤器 JIT 编译成原生 x64 机器码。标准 BPF 反汇编器失败或输出不可读时，开 `bpf_jit_enable` 从 dmesg 读编译汇编。原生代码常比 BPF 字节码好懂。

**识别：** 二进制用 `setsockopt` 带 `SO_ATTACH_FILTER`、裸 socket 创建（`socket(AF_PACKET, ...)`）或内嵌 `struct sock_fprog` 结构。BPF 程序是 `struct sock_filter` 数组（每 8 字节：opcode, jt, jf, k）。

**References:** Midnight Sun CTF 2018

---

关联阅读：[patterns-ctf.md](patterns-ctf.md)（第一部分）；[patterns-ctf-2.md](patterns-ctf-2.md)（第二部分：多层自解密、内嵌 ZIP+XOR 许可证、栈字符串脱混淆、前缀哈希爆破、CVP/LLL 格、决策树混淆、GF(2^8) 高斯消元）。
