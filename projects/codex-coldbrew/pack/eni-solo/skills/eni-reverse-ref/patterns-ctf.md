# 赛题逆向模式（第一部分）

## 目录

- [隐藏模拟器 opcode + LD_PRELOAD 提密钥（0xFun 2026）](#隐藏模拟器-opcode)
- [Spectre-RSB SPN 密码——静态参数提取（0xFun 2026）](#spectre-rsb-spn-密码)
- [图像 XOR 掩码平滑度恢复（VuwCTF 2025）](#图像-xor-掩码平滑度恢复)
- [数据段 shellcode 经 mmap RWX（VuwCTF 2025）](#数据段-shellcode)
- [递归 execve 减法（VuwCTF 2025）](#递归-execve-减法)
- [逐字节分组密码攻击（UTCTF 2024）](#逐字节分组密码攻击)
- [数学收敛位图（EHAX 2026）](#数学收敛位图)
- [Windows PE XOR 位图提取 + OCR（srdnlenCTF 2026）](#windows-pe-xor-位图提取--ocr)
- [两级 loader：RC4 门 + VM 约束（srdnlenCTF 2026）](#两级-loader)
- [内核模块走迷宫（DiceCTF 2026）](#内核模块走迷宫)
- [多线程 VM 与通道同步（DiceCTF 2026）](#多线程-vm-与通道同步)
- [字符串 diff 识别被植入共享库（Hack.lu CTF 2012）](#字符串-diff-识别被植入共享库)
- [自定义 binfmt 内核模块 + RC4 裸二进制（BSidesSF 2026）](#自定义-binfmt-内核模块)
- [哈希解析导入 / 无导入勒索软件（BSidesSF 2026）](#哈希解析导入)
- [ELF 节头损坏反分析（BSidesSF 2026）](#elf-节头损坏反分析)

---

## 隐藏模拟器 opcode + LD_PRELOAD 提密钥（0xFun 2026）

**模式（CHIP-8）：** 非标准 opcode `FxFF` 触发隐藏的 `superChipRendrer()` → AES-256-CBC 解密。密钥由二进制常量派生。

**技术：**

1. 检查全部指令分发分支里的非标准 opcode
2. 隐藏 opcode 可能触发加密函数（OpenSSL）
3. 用 `LD_PRELOAD` hook `EVP_DecryptInit_ex` 运行时抓 AES 密钥：

```c
#include <openssl/evp.h>
int EVP_DecryptInit_ex(EVP_CIPHER_CTX *ctx, const EVP_CIPHER *type,
                       ENGINE *impl, const unsigned char *key,
                       const unsigned char *iv) {
    // 记录密钥
    for (int i = 0; i < 32; i++) printf("%02x", key[i]);
    printf("\n");
    // 调原函数
    return ((typeof(EVP_DecryptInit_ex)*)dlsym(RTLD_NEXT, "EVP_DecryptInit_ex"))
           (ctx, type, impl, key, iv);
}
```

```bash
gcc -shared -fPIC -ldl -lssl hook.c -o hook.so
LD_PRELOAD=./hook.so ./emulator rom.ch8
```

---

## Spectre-RSB SPN 密码——静态参数提取（0xFun 2026）

**模式：** 二进制用缓存侧信道实现 S-box，但全部密码参数（轮密钥、S-box 表、置换）都在二进制数据段。

**要点：** 不必在特殊硬件上跑。静态提取参数：

- 8 个 S-box × 8 输出位，每个 256 项
- 值 `0x340` = 位 1，`0x100` = 位 0
- 64 字节置换表、8 个轮密钥

```python
# 从二进制数据段提取
import struct
sbox = [[0]*256 for _ in range(8)]
for i in range(8):
    for j in range(256):
        val = struct.unpack('<I', data[sbox_offset + (i*256+j)*4 : ...])[0]
        sbox[i][j] = 1 if val == 0x340 else 0
```

**经验：** 侧信道实现把查找表嵌在内存里。静态提取即可。

---

## 图像 XOR 掩码平滑度恢复（VuwCTF 2025）

**模式（Trianglification）：** 图像被分成三角区域，各区域用 `key = (mask * x - y) & 0xFF` XOR 加密，mask 未知（0-255）。

**恢复：** 自然图像有平滑梯度。爆破 mask（每区域 256 个值），用相邻像素差分打分：

```python
import numpy as np
from PIL import Image

img = np.array(Image.open('encrypted.png'))

def score_smoothness(region_pixels, mask, positions):
    decrypted = []
    for (x, y), pixel in zip(positions, region_pixels):
        key = (mask * x - y) & 0xFF
        decrypted.append(pixel ^ key)
    # 打分：相邻像素绝对差之和
    return -sum(abs(decrypted[i] - decrypted[i+1]) for i in range(len(decrypted)-1))

for region in regions:
    best_mask = max(range(256), key=lambda m: score_smoothness(region, m, positions))
```

**搜索空间：** 256 候选 × N 区域 = 微不足道。平滑度是自然图像可靠的打分指标。

---

## 数据段 shellcode 经 mmap RWX（VuwCTF 2025）

**模式（Missing Function）：** 二进制把数据搬迁到 RWX 内存（mmap 带 PROT_READ|PROT_WRITE|PROT_EXEC）并跳过去。

**检测：** 找带 PROT_EXEC 的 `mmap`。内嵌 shellcode 常用旋转密钥 XOR。

**分析：** 提取数据段，试 3 字节旋转 XOR 密钥，反汇编结果。

---

## 递归 execve 减法（VuwCTF 2025）

**模式（String Inspector）：** 二进制经 `execve` 递归调用自身，每次减常量。

**解法：** 找基准情形倒推。常是 `N * M + remainder` 这类数学关系。

---

## 逐字节分组密码攻击（UTCTF 2024）

**模式（PES-128）：** 首个输出字节只依赖首个输入字节（零扩散）。

**攻击：** 逐位置试全部 256 字节值，输出字节与目标密文比对。每字节一匹配 = 无需密钥的完整明文恢复。

**检测：** 改一个输入字节 → 只有对应输出字节变。零跨字节扩散 = 平凡可破。

---

## 数学收敛位图（EHAX 2026）

**模式（Compute It）：** 二进制用牛顿法收敛性分类复平面坐标。分类结果排成栅格，拼出 ASCII art flag。

**识别：**

- 输入文件是坐标对（x, y）
- 二进制迭代数学函数（如 z^3 - 1 = 0）输出通过/失败
- 栅格维度由点数暗示（如 2600 = 130×20）
- CTF 常见 5 像素高 ASCII art 字体

**z^3 - 1 的牛顿法：**

```python
def newton_converges_to_one(px, py, max_iter=50, target_count=12):
    """牛顿法恰在 target_count 步收敛到 z=1 时返回 True。"""
    x, y = px, py
    count = 0
    for _ in range(max_iter):
        f_real = x**3 - 3*x*y**2 - 1.0
        f_imag = 3*x**2*y - y**3
        J_rr = 3.0 * (x**2 - y**2)
        J_ri = 6.0 * x * y
        det = J_rr**2 + J_ri**2
        if det < 1e-9:
            break
        x -= (f_real * J_rr + f_imag * J_ri) / det
        y -= (f_imag * J_rr - f_real * J_ri) / det
        count += 1
        if abs(x - 1.0) < 1e-6 and abs(y) < 1e-6:
            break
    return count == target_count

# 读坐标渲染位图
points = [(float(x), float(y)) for x, y in ...]
bits = [1 if newton_converges_to_one(px, py) else 0 for px, py in points]
WIDTH = 130  # 2600 / 20 行
for r in range(len(bits) // WIDTH):
    print(''.join('#' if bits[r*WIDTH+c] else '.' for c in range(WIDTH)))
```

**要点：** 二进制是数学分类器，不是 flag checker。flag 在分类结果的视觉图案里，不在二进制的输出里。逆数学、对全部坐标应用、按位图可视化。

---

## Windows PE XOR 位图提取 + OCR（srdnlenCTF 2026）

**模式（Artistic Warmup）：** 二进制渲染输入文本，把渲染位图与 `.rdata` 里 XOR 常量保护的期望像素比较。无需计算——直接提取期望像素。

**攻击：**

1. 逆核心检查函数识别渲染与比较逻辑
2. 在 `.rdata` 找期望像素 blob（比较附近的大数据块）
3. 与常量（如 0xAA）XOR 恢复期望渲染 DIB
4. 存成图像 OCR 出 flag 文本

```python
import numpy as np
from PIL import Image

with open("binary.exe", "rb") as f:
    data = f.read()

# 从 .rdata 节提取（偏移来自逆向）
blob_offset = 0xC3620  # .rdata 里 XOR blob 的偏移
blob_size = 0x15F90     # 450 * 50 * 4 (BGRA)
blob = np.frombuffer(data[blob_offset:blob_offset + blob_size], dtype=np.uint8)
expected = blob ^ 0xAA  # XOR 常量密钥

# 重塑为 BGRA 图像（维度来自逆向）
img = expected.reshape(50, 450, 4)
channel = img[:, :, 0]  # 取一个通道（灰度文本）
Image.fromarray(channel, "L").save("target.png")

# 带字符白名单 OCR
import subprocess
result = subprocess.run(
    ["tesseract", "target.png", "stdout", "-c",
     "tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789{}_"],
    capture_output=True, text=True)
print(result.stdout)
```

**要点：** 二进制渲染文本再比像素时，期望像素数据就是渲染成图像的 flag。直接从二进制数据段提取，无需理解渲染逻辑。字符白名单 OCR 提升 CTF flag 字符的准确率。

---

## 两级 loader：RC4 门 + VM 约束（srdnlenCTF 2026）

**模式（Cornflake v3.5）：** 两级恶意 loader——第一级 RC4 用户名门，第二级从 C2 下载、含 VM 密码校验。

**第一级——RC4 用户名恢复：**

```python
def rc4(key, data):
    s = list(range(256))
    j = 0
    for i in range(256):
        j = (j + s[i] + key[i % len(key)]) & 0xFF
        s[i], s[j] = s[j], s[i]
    i = j = 0
    out = bytearray()
    for b in data:
        i = (i + 1) & 0xFF
        j = (j + s[i]) & 0xFF
        s[i], s[j] = s[j], s[i]
        out.append(b ^ s[(s[i] + s[j]) & 0xFF])
    return bytes(out)

# 密钥来自二进制字符串，密文来自存储的 hex
username = rc4(b"s3cr3t_k3y_v1", bytes.fromhex("46f5289437bc009c17817e997ae82bfbd065545d"))
```

**第二级——VM 约束提取：**

1. 从 C2 端点下载第二级（如 `/updates/check.php`）
2. 逆 VM 字节码解释器（通常 15-20 opcode）
3. 提取 flag 字符上的线性等式约束
4. 解约束系统（Z3 或手解）

**要点：** 多级 loader 常用简单加密（RC4）做第一道门，更复杂的校验（自定义 VM）做第二道。VM 内存可能未初始化（全零），极大简化约束提取——依赖内存的操作变成常量。

---

## 内核模块走迷宫（DiceCTF 2026）

**模式（Explorer）：** Rust 内核模块经 `/dev/challenge` ioctl 实现 3D 迷宫。走迷宫、避开诱饵出口（status=2）、找真出口（status=1）、读 flag。

**ioctl 枚举：**

| 命令 | 说明 |
|---------|-------------|
| `0x80046481-83` | 取迷宫维度（3 轴，各 8-16） |
| `0x80046485` | 取状态：0=进行中, 1=WIN, 2=诱饵 |
| `0x80046486` | 取墙位域（6 方向） |
| `0x80406487` | 取 flag（64 字节，仅 status=1 时） |
| `0x40046488` | 移动（方向 0-5） |
| `0x6489` | 复位位置 |

**带诱饵规避的 DFS 求解器：**

```c
// 最小静态二进制用裸系统调用（无 libc）缩小上传体积
// gcc -nostdlib -static -Os -fno-builtin -o solve solve.c -Wl,--gc-sections && strip solve

int visited[16][16][16];
int bad[16][16][16];   // 跨复位记录的诱饵位置

void dfs(int fd, int x, int y, int z) {
    if (visited[x][y][z] || bad[x][y][z]) return;
    visited[x][y][z] = 1;

    int status = ioctl_get_status(fd);
    if (status == 1) { read_flag(fd); exit(0); }
    if (status == 2) { bad[x][y][z] = 1; return; }  // 诱饵——标坏

    int walls = ioctl_get_walls(fd);
    int dx[] = {1,-1,0,0,0,0}, dy[] = {0,0,1,-1,0,0}, dz[] = {0,0,0,0,1,-1};
    int opp[] = {2,3,0,1,5,4};  // 回溯用反方向

    for (int dir = 0; dir < 6; dir++) {
        if (!(walls & (1 << dir))) continue;  // 有墙
        ioctl_move(fd, dir);
        dfs(fd, x+dx[dir], y+dy[dir], z+dz[dir]);
        ioctl_move(fd, opp[dir]);  // 回溯
    }
}
// 撞诱饵后：ioctl 0x6489 复位，清 visited，重跑 DFS
```

**远程部署：** 经 netcat shell 按 base64 块上传二进制，解码执行。

**要点：** 内核模块题往 initramfs 里注入测试二进制、动态探测 ioctl，比静态逆向 strip 内核模块快。求解器保持最小（裸系统调用、无 libc）以便快速上传。

---

## 多线程 VM 与通道同步（DiceCTF 2026）

**模式（locked-in）：** 自定义栈式 VM 跑 16 个并发线程校验 30 字符 flag。线程经 futex 通道通信。流水线：输入 → XOR 打乱 → 变换 → 四进制状态机 → 最终检查。

**分析打法：**

1. **GDB 里追踪通道读写模式识别线程角色**
2. **断在特定 opcode 提取常量**（XOR 打乱值、查找表）
3. **留意反转逻辑：** 有效性检查对合法返回 0、对阻塞返回非零（与直觉相反）
4. **察觉 futex 怪癖：** 无主 mutex 上的 `unlock_pi` 返回 EPERM=1，会改变所有计算

**约束状态机的 BFS 搜索：**

```python
from collections import deque

def solve_flag(scramble_vals, lookup_table, initial_state, target_state):
    """BFS 状态机找合法 flag 字节。"""
    flag = [None] * 30
    # flag 格式的已知前缀/后缀
    flag[0:5] = list(b'dice{')
    flag[29] = ord('}')

    # 每个未知位置试全部可打印 ASCII
    states = {initial_state}
    for pos in range(28, 4, -1):  # 倒序处理
        next_states = {}
        for state in states:
            for ch in range(32, 127):
                transformed = transform(ch, scramble_vals[pos])
                digits = to_base4(transformed)
                new_state = apply_digits(state, digits, lookup_table)
                if new_state is not None:  # 存在合法路径
                    next_states.setdefault(new_state, []).append((state, ch))
        states = set(next_states.keys())

    # 从 target_state 回溯恢复 flag
```

**要点：** 多线程 VM 要求跨线程边界追数据流。通道通信构成流水线——看每个线程读写哪些通道即可识别其角色（输入、变换、校验、输出）。影响计算的常量可能来自意想不到的地方（futex 返回值、线程 ID）。

---

## 字符串 diff 识别被植入共享库（Hack.lu CTF 2012）

**模式（Zombie Lockbox）：** setuid 二进制用 `strcmp` 校验密码。期望密码经 `strings` 可见、GDB 下可用（GDB 会丢 suid），但正常运行失败。二进制链接了非标准 libc，它按 suid 状态 patch 函数行为。

**检测步骤：**

1. `ldd` 查非标准库路径：

```bash
ldd ./binary
# 可疑: libc.so.6 => /lib/libc/libc.so.6  (非标准路径)
# 正常:    libc.so.6 => /lib32/libc.so.6
```

2. 可疑库与系统 libc 的字符串 diff：

```bash
strings /lib/libc/libc.so.6 > suspicious_strings
strings /lib32/libc-2.15.so > normal_strings
diff suspicious_strings normal_strings
```

3. 反汇编被 patch 的函数（如 `puts`）找注入代码：

```bash
gdb /lib/libc/libc.so.6
(gdb) disas puts
# 找意外的调用或分支
# 注入代码可能查 suid 状态（getuid/geteuid 系统调用）
# 并在运行时换掉期望密码
```

**要点：** 二进制在 GDB 下与正常执行行为不一致时，`ldd` 查非标准库路径。suid 二进制在调试器下丢权限，被植入的 libc 可经 `getuid`/`geteuid` 检测并改变程序行为。`strings | diff` 无需完整反汇编即可快速暴露注入数据。

---

## 自定义 binfmt 内核模块 + RC4 裸二进制（BSidesSF 2026）

**模式（Private Binary）：** 自定义 Linux 内核模块（`.ko`）为非标准二进制格式注册 `binfmt` 处理器。带特定魔数的文件被执行时，内核模块拦截、内存中解密内容、跳到入口点。

**逆向打法：**

1. **分析 `.ko`：** 找 `register_binfmt()` 调用——注册带 `load_binary` 回调的 `struct linux_binfmt`
2. **找魔数：** `load_binary` 函数比对文件头几字节的特定魔数识别格式
3. **提取加密密钥：** 找加载 8 字节常量的 `movabs` 指令——常是 RC4 密钥字节
4. **识别加密方案：** 常见 RC4、XOR 或 AES-ECB。RC4 靠 S-box 初始化循环识别（256 字节数组、交换模式）
5. **解密裸二进制：** 密钥作用于加密文件内容，跳过头部

```python
from Crypto.Cipher import ARC4

# 从内核模块提取 RC4 密钥（经 movabs 指令找到）
key = bytes([0x41, 0x42, 0x43, ...])  # .ko 反汇编里的密钥字节

with open('encrypted.bin', 'rb') as f:
    header = f.read(HEADER_SIZE)  # 跳过 binfmt 头
    encrypted = f.read()

cipher = ARC4.new(key)
decrypted = cipher.decrypt(encrypted)

# 解密输出是裸二进制（无 ELF 头）
# 按内核模块指定的固定虚拟地址加载
# 反汇编: objdump -b binary -m i386:x86-64 -D decrypted.bin
# 或 Ghidra: 按 "Raw Binary" 导入，基址取自 .ko
```

**内核模块检测：**

- `register_binfmt` / `unregister_binfmt` 调用
- `vm_mmap()` 或 `vm_brk()` 固定地址分配
- 直接跳进映射内存（入口点执行）
- S-box 初始化模式（RC4）：0-255 循环、`S[i]` 与 `S[j]` 交换

**要点：** 裸二进制没有 ELF 头，标准工具不认识。必须从内核模块提取加载地址（看 `vm_mmap` 调用的地址参数），把解密 blob 按该地址导入反汇编器。内核模块里的 RC4 密钥常以 `mov`/`movabs` 立即数形式存储，而非数据节。

**References:** BSidesSF 2026 "Private Binary"

---

## 哈希解析导入 / 无导入勒索软件（BSidesSF 2026）

**模式（Ran Somewhere）：** 恶意二进制零可见导入——全部 API 调用在运行时经符号名哈希与预计算哈希比对解析。二进制用 `dlopen` + 自定义哈希表找 libc 与 libcrypto 函数。

**识别：**

- `readelf -d` 显示无动态符号或极少（只有 `dlopen`/`dlsym`）
- strings 无标准 API 名
- 反汇编显示哈希计算循环后跟间接调用
- RC4 加密的内嵌字符串（RSA 公钥、文件路径、口令）

**分析捷径——LD_PRELOAD 提密钥：**

与其逆向整套哈希解析与密钥派生，不如 hook 恶意软件最终调用的加密函数：

```c
// hook_crypto.c — 抓勒索软件用的 AES 密钥
#define _GNU_SOURCE
#include <dlfcn.h>
#include <openssl/evp.h>
#include <stdio.h>

int EVP_CipherInit_ex(EVP_CIPHER_CTX *ctx, const EVP_CIPHER *type,
                       ENGINE *impl, const unsigned char *key,
                       const unsigned char *iv) {
    if (key) {
        FILE *f = fopen("/tmp/aes_key.bin", "wb");
        fwrite(key, 1, 32, f);  // AES-256
        fclose(f);
        fprintf(stderr, "[HOOK] AES key captured\n");
    }
    typedef int (*orig_t)(EVP_CIPHER_CTX*, const EVP_CIPHER*, ENGINE*,
                          const unsigned char*, const unsigned char*);
    orig_t orig = (orig_t)dlsym(RTLD_NEXT, "EVP_CipherInit_ex");
    return orig(ctx, type, impl, key, iv);
}
```

```bash
# 编译并运行
gcc -shared -fPIC -o hook.so hook_crypto.c -ldl
# 在 Docker 容器里跑（勒索软件有破坏性！）
docker run --rm -v $(pwd):/work -w /work ubuntu:22.04 \
  bash -c "LD_PRELOAD=./hook.so ./ransomware; xxd /tmp/aes_key.bin"
```

**哈希解析模式：**

- **SipHash 变体：** 两个 64 位种子，与符号名字节迭代混合
- **DJB2/FNV 变体：** 更简单的哈希，带可识别常量（`5381`、`0xcbf29ce484222325`）
- **ROR13 系：** Windows 恶意软件最爱：`hash = (hash >> 13) | (hash << 19); hash += c`

**拿密钥后的解密：**

```python
from Crypto.Cipher import AES

key = open('/tmp/aes_key.bin', 'rb').read()
iv = open('/tmp/aes_iv.bin', 'rb').read()  # 同样可 hook
cipher = AES.new(key, AES.MODE_CBC, iv)

with open('flag.txt.enc', 'rb') as f:
    ct = f.read()
pt = cipher.decrypt(ct)
# 去 PKCS7 填充
pt = pt[:-pt[-1]]
print(pt.decode())
```

**要点：** 二进制用哈希解析全部导入时，别浪费时间去逆哈希函数、建彩虹表。让恶意软件自己解析——在沙箱里跑，`LD_PRELOAD` hook 你关心的函数（OpenSSL 加密函数、文件 I/O、网络调用）。AES 密钥跨运行确定——一次成功，永远成功。

**安全：** 疑似勒索软件永远在 Docker 容器或 VM 里跑。只挂载加密文件的副本，绝不挂原件。

**References:** BSidesSF 2026 "Ran Somewhere"

---

## ELF 节头损坏反分析（BSidesSF 2026）

**模式（stubborn-elf）：** ELF 二进制故意损坏节头表条目，让标准分析工具（`readelf`、`objdump`、IDA、Ghidra）崩溃或报错。但 **程序头**（OS 加载器用的）完好，二进制照常执行。flag 附在损坏节之后，带魔数标记。

```python
import sys

# 标准工具在损坏节头上失败
# 手动解析完全绕过节头

with open("stubborn_elf", "rb") as f:
    data = f.read()

# 搜 ELF 节后附着的魔法标记
magic = b"\xDE\xAD\xBE\xEF\xCA\xFE\xBA\xBE"
idx = data.find(magic)
if idx >= 0:
    # 魔数后的数据是 XOR 加密的
    encrypted = data[idx + len(magic):]
    decrypted = bytes(b ^ 0x42 for b in encrypted)
    print(decrypted.decode(errors='ignore'))
```

**要点：** ELF 执行需要 **程序头**（PT_LOAD 段），不是节头。节头是调试器与分析工具的元数据——运行时可选。损坏 ELF 头里的 `e_shoff`、`e_shnum` 或 `e_shstrndx` 击穿工具但不影响执行。工具失败时手动解析，或把 ELF 头里的节头引用清零再进反汇编器。

**恢复打法：**

```bash
# 节头偏移 patch 成 0（去掉节表）
printf '\x00\x00\x00\x00\x00\x00\x00\x00' | dd of=binary bs=1 seek=40 conv=notrunc
# 现在 Ghidra/IDA 可以只用程序头加载

# 或 readelf -l（只看程序头，忽略节）
readelf -l stubborn_elf
```

**识别：** `readelf -S` 崩溃或显示垃圾。`file` 认它是 ELF。`readelf -l`（小写 L，程序头）正常。工具失败但二进制照常运行。

**References:** BSidesSF 2026 "stubborn-elf"

---

关联阅读：[patterns-ctf-2.md](patterns-ctf-2.md)（第二部分：多层自解密、内嵌 ZIP+XOR 许可证、栈字符串脱混淆、前缀哈希爆破、CVP/LLL 格、决策树混淆、GF(2^8) 高斯消元）；[patterns-ctf-3.md](patterns-ctf-3.md)（第三部分：Z3 布尔电路、滑窗 popcount、键盘 LED 摩斯码、C++ 析构隐藏校验、VM 顺序密钥链爆破、BWT 逆变换、OpenType 连字利用、GLSL 着色器 VM 自修改代码）。
