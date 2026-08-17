# 硬件与高级架构逆向

> HD44780 LCD 的 GPIO 重建、RISC-V 进阶扩展与调试、ARM64/AArch64 逆向与利用。

## 目录

- [HD44780 LCD 控制器 GPIO 重建（32C3 2015）](#hd44780-lcd-控制器-gpio-重建)
- [RISC-V（进阶）](#risc-v进阶)
- [ARM64/AArch64 逆向与利用](#arm64aarch64-逆向与利用)
- [MIPS64 Cavium OCTEON 协处理器 2 加密（SEC-T CTF 2017）](#mips64-cavium-octeon-协处理器-2-加密)
- [EFM32 ARM 微控制器 MMIO AES（SEC-T CTF 2017）](#efm32-arm-微控制器-mmio-aes)
- [MBR/Bootloader 逆向：QEMU + GDB（Square CTF 2017）](#mbrbootloader-逆向qemu--gdb)

---

## HD44780 LCD 控制器 GPIO 重建（32C3 2015）

从原始树莓派 GPIO 记录恢复 HD44780 LCD 显示的文字：

1. **识别信号线：** GPIO 针映射到 HD44780 信号（RS、CLK、4 位模式的 D4-D7）
2. **时钟沿检测：** 下降沿（1→0 跳变）采样数据线
3. **半字节拼装：** 两个 4 位样本拼一个 8 位命令/数据字节
4. **DRAM 地址映射：** HD44780 多行显示用非连续寻址：
   - 第 0 行：0x00-0x27
   - 第 1 行：0x40-0x67
   - 第 2 行：0x14-0x3B
   - 第 3 行：0x54-0x7B

```python
display = [' '] * 80  # 4 行 x 20 字符
cursor = 0

for timestamp, gpio_state in sorted(gpio_log):
    if falling_edge(gpio_state, CLK_PIN):
        nibble = extract_data_bits(gpio_state)
        byte = assemble_nibble(nibble)  # 每字节两个半字节
        if rs_high(gpio_state):  # RS=1: 数据写
            display[dram_to_position(cursor)] = chr(byte)
            cursor += 1
        else:  # RS=0: 命令（设光标、清屏等）
            cursor = parse_command(byte)
```

**要点：** GPIO 针到信号的映射少有文档；找 CLK 靠跳变最多的针，找 RS 靠与数据模式的相关性（命令/数据交替相位）。

---

## RISC-V（进阶）

基础反汇编见 [tools.md](tools.md#risc-v-二进制分析)。进阶内容：

### 自定义扩展

```text
Bitmanip 扩展（Zbb, Zbc, Zbs）:
  clz, ctz, cpop         -> 数前导/尾随零, popcount
  orc.b, rev8            -> 字节级位操作
  andn, orn, xnor        -> 取反逻辑运算
  clmul, clmulh, clmulr  -> 无进位乘法（加密）
  bset, bclr, binv, bext -> 单位操作

加密扩展（Zk*）:
  aes32esi, aes32dsmi     -> AES 轮操作
  sha256sig0, sha512sum0  -> SHA 哈希加速
  sm3p0, sm4ed            -> 中国密码标准
```

### 特权级

```text
Machine 模式（M）:  最高特权，固件/bootloader
Supervisor 模式（S）: OS 内核
User 模式（U）:      应用

关注的 CSR 寄存器:
  mstatus/sstatus    -> 特权级, 中断使能
  mtvec/stvec       -> 陷阱处理器地址
  mepc/sepc         -> 异常返回地址
  mcause/scause     -> 陷阱原因
  satp              -> 页表根（虚拟内存）
```

### RISC-V 调试

```bash
# OpenOCD + GDB 硬件调试
openocd -f interface/jlink.cfg -f target/riscv.cfg

# RISC-V 的 GDB
riscv64-unknown-elf-gdb binary
(gdb) target remote :3333

# QEMU 带 GDB server
qemu-riscv64 -g 1234 -L /usr/riscv64-linux-gnu/ ./binary
riscv64-linux-gnu-gdb -ex 'target remote :1234' ./binary
```

---

## ARM64/AArch64 逆向与利用

AArch64（ARM 64 位）出现在移动应用、云服务器（AWS Graviton）、Apple Silicon 与 CTF 题里。与 x86-64 的关键差异同时影响逆向与利用。

**环境与模拟：**

```bash
# 装交叉工具链与模拟器
apt install gcc-aarch64-linux-gnu gdb-multiarch qemu-user-static

# x86 主机跑 AArch64 二进制
qemu-aarch64-static -L /usr/aarch64-linux-gnu/ ./arm64_binary

# GDB 调试
qemu-aarch64-static -g 12345 -L /usr/aarch64-linux-gnu/ ./arm64_binary &
gdb-multiarch -ex 'set arch aarch64' -ex 'target remote :1234' ./arm64_binary

# 库预加载（题目自带 libc 时）
qemu-aarch64-static -g 12345 -E LD_PRELOAD=./libc.so.6 -L ./lib ./arm64_binary
```

**AArch64 调用约定（与 x86-64 的关键差异）：**

```text
寄存器:
  x0-x7    -- 函数参数兼返回值（x0 = 第一参数 / 返回）
  x8       -- 间接结果位置（结构体返回）
  x9-x15   -- 调用者保存临时
  x19-x28  -- 被调用者保存（跨调用保留）
  x29 (fp) -- 帧指针
  x30 (lr) -- 链接寄存器（返回地址，默认不在栈上）
  sp       -- 栈指针（须 16 字节对齐）
  xzr      -- 零寄存器（读为 0，写丢弃）

利用关键差异:
  - 返回地址在 LR (x30) 不在栈上——只有函数调别人时才压栈
  - 无 x86 式 RIP 相对寻址——ADRP+ADD 对做 PC 相对加载
  - 固定 4 字节指令宽——无变长 gadget 技巧
  - NOP = 0xD503201F（不是 0x90）
  - BLR x8 / BR x30 -- 间接调用/跳转用寄存器操作数
```

**Ghidra/IDA 常见 AArch64 模式：**

```text
# PC 相对地址加载（等价 x86 LEA）:
ADRP  x0, #0x411000      ; 载页地址（4KB 对齐）
ADD   x0, x0, #0x8       ; 加页内偏移 -> x0 = 0x411008

# 函数序言:
STP   x29, x30, [sp, #-0x30]!  ; 压 fp + lr, 减 sp
MOV   x29, sp                   ; 设帧指针

# 函数尾声:
LDP   x29, x30, [sp], #0x30    ; 弹 fp + lr, 增 sp
RET                              ; 转 x30 (lr)

# Switch/跳转表:
ADR   x1, jump_table
LDRB  w2, [x1, x0]       ; 载偏移字节
ADD   x1, x1, w2, SXTB   ; 符号扩展相加
BR    x1                   ; 间接分支
```

**AArch64 上的 ROP：**

```python
from pwn import *

# AArch64 gadget 不同于 x86:
# - "pop {x0}; ret" 等价: LDP x0, x1, [sp], #0x10; RET
# - 序言 gadget: LDP x29, x30, [sp, #0x20]; ... RET
# - system() 调用: x0 = "/bin/sh" 指针, BLR 到 system

context.arch = 'aarch64'
elf = ELF('./arm64_binary')

# AArch64 libc 常见 gadget 模式:
# LDP X19, X20, [SP,#var_s10]
# LDP X29, X30, [SP+var_s0],#0x20
# RET
# 控制 x19, x20, x29, x30 且 sp 前进 0x20
```

**要点：** AArch64 的固定指令宽与寄存器返回地址（`lr`/`x30`）使 ROP gadget 比 x86 更受限。找从栈弹多寄存器的 `LDP`（load pair）gadget。函数序言/尾声保存/恢复被调用者寄存器的 `STP`/`LDP` 指令对是主要 gadget 来源。

**识别：** `file` 显示 "ELF 64-bit LSB ... ARM aarch64"。Ghidra 自动检测，但裸二进制可能要手动选处理器。x86 主机用 `qemu-aarch64-static` 模拟。

**工具：** radare2（`r2 -AA -a arm -b 64`）、Ghidra（自动检测）、`aarch64-linux-gnu-objdump -d`、Unicorn Engine（`UC_ARCH_ARM64`）

**References:** Google CTF 2016 "Forced Puns", Insomni'hack 2018 "onecall"

---

## MIPS64 Cavium OCTEON 协处理器 2 加密（SEC-T CTF 2017）

Cavium OCTEON 网络处理器经 MIPS 协处理器 2（CP2）用 `dmtc2`（move to CP2）与 `dmfc2`（move from CP2）指令实现硬件 AES 与 SHA256。反汇编器眼里像普通寄存器移动，实际驱动硬件加密引擎。

**CP2 关键寄存器布局（OCTEON）：**

```text
AES 密钥寄存器:
  0x0104 – AES 密钥 quadword 0
  0x0105 – AES 密钥 quadword 1
  0x0106 – AES 密钥 quadword 2
  0x0107 – AES 密钥 quadword 3

SHA256 哈希寄存器:
  0x400E–0x4012 – SHA256 中间哈希字
  0x404F        – SHA256 控制/结果

dmtc2  rN, 0x0104   ; 载 64 位 AES 密钥进 CP2 寄存器 0x104
dmtc2  rN, 0x0105   ; ...下一 quadword
```

**打法：**

1. IDA/Ghidra 反汇编——`dmtc2`/`dmfc2` 选择子在 0x100-0x40FF 区间即 OCTEON CP2
2. 交叉参考 Cavium OCTEON 硬件参考手册查寄存器语义
3. 迹密钥加载序列恢复 AES 或 HMAC 密钥材料

**要点：** MIPS 上的硬件加密加速器表现为 CP2 寄存器写（`dmtc2`/`dmfc2`）。识别基寄存器地址并对照厂商文档。

**References:** SEC-T CTF 2017

---

## EFM32 ARM 微控制器 MMIO AES（SEC-T CTF 2017）

Silicon Labs EFM32 Cortex-M 二进制——0x1000 加载的 Thumb 模式裸二进制。

**IDA 设置：**

```text
处理器: ARM Little-endian (ARMv7-M)
加载地址: 0x1000
设 T 寄存器 = 1（强制 Thumb 解码）
```

**AES 加速器 MMIO 布局（EFM32 AES 外设在 0x400E0000）：**

```text
0x400E0000 + 0x000  CTRL   – 使能, 解密模式
0x400E0000 + 0x004  CMD    – 启动/停止
0x400E0000 + 0x010  KEYLA  – 密钥低字 0
0x400E0000 + 0x014  KEYLB  – 密钥低字 1
0x400E0000 + 0x018  KEYLC  – 密钥低字 2
0x400E0000 + 0x01C  KEYLD  – 密钥低字 3
```

二进制加载两个独立值、XOR 后写成 AES 密钥。用合成密钥 ECB 模式解密内嵌密文块。

```python
from Crypto.Cipher import AES

key_part_a = bytes.fromhex("...")  # 从 IDA .data 节提取
key_part_b = bytes.fromhex("...")  # 第二个值
key = bytes(a ^ b for a, b in zip(key_part_a, key_part_b))

cipher = AES.new(key, AES.MODE_ECB)
plaintext = cipher.decrypt(ciphertext)
```

**要点：** 微控制器上的硬件 AES 加速器表现为特定基址的 MMIO 寄存器写——对照厂商参考手册（Silicon Labs 外设查 EFM32 Reference Manual）。

**References:** SEC-T CTF 2017

---

## MBR/Bootloader 逆向：QEMU + GDB（Square CTF 2017）

QEMU 开 GDB stub 引导软盘/磁盘镜像，挂 GDB 对 16 位实模式或 32 位保护模式 bootloader 做源码级调试。

```bash
# 带 GDB stub 引导，端口 1234; -S 启动即暂停
qemu-system-x86_64 -fda disk.img -s -S

# 另一终端挂 GDB
gdb -ex "set architecture i8086" \
    -ex "target remote :1234" \
    -ex "break *0x7c00" \
    -ex "continue"

# MBR 常驻入口 0x7c00（BIOS 把 MBR 载到这里）
# 步过 bootloader，查寄存器与内存:
(gdb) x/20i $pc
(gdb) info registers
(gdb) x/16xb 0x7c00
```

绕过密码检查：找比较后的条件跳转，在镜像文件里 NOP 掉，或 patch 比较恒成立。

```bash
# 在镜像里找比较偏移并 patch
python3 -c "
data = open('disk.img', 'rb').read()
# JNZ (0x75) 换成短 JMP 恒跳或 NOP
data = data[:offset] + b'\x90\x90' + data[offset+2:]
open('disk_patched.img', 'wb').write(data)
"
```

**要点：** QEMU 的 `-s` 在 1234 端口开 GDB stub，MBR/bootloader 调试与用户态调试完全同流程。

**References:** Square CTF 2017
