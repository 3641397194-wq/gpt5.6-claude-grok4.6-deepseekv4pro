# 平台专项逆向

> macOS/iOS、嵌入式/IoT 固件、内核驱动与汽车 CAN 总线。

## 目录

- [macOS / iOS 逆向](#macos--ios-逆向)
- [嵌入式 / IoT 固件逆向](#嵌入式--iot-固件逆向)
- [内核驱动逆向](#内核驱动逆向)
- [汽车 / CAN 总线逆向](#汽车--can-总线逆向)

---

## macOS / iOS 逆向

### Mach-O 二进制格式

```bash
# 文件识别
file binary                    # "Mach-O 64-bit executable arm64" 或 "x86_64"
otool -l binary               # Load commands（段、dylib、入口点）
otool -L binary               # 链接的动态库

# Universal（fat）二进制——单文件多架构
lipo -info universal_binary    # 列架构
lipo universal_binary -thin arm64 -output binary_arm64  # 抽单架构

# 段与节
otool -l binary | grep -A5 "segment\|section"
# 关键段: __TEXT（代码）, __DATA（全局）, __LINKEDIT（符号）
# 关键节: __text（指令）, __cstring（C 字符串）, __objc_methname
```

**Mach-O 关键概念：**

- Load commands 驱动动态链接器（`dyld`）
- `LC_MAIN` → 入口点（取代 `LC_UNIXTHREAD`）
- `LC_LOAD_DYLIB` → 共享库依赖
- `LC_CODE_SIGNATURE` → 代码签名 blob
- `__DATA_CONST.__got` → 全局偏移表
- `__DATA.__la_symbol_ptr` → 惰性符号指针（类似 PLT）

### 代码签名与权限

```bash
# 查代码签名
codesign -dvvv binary
codesign --verify binary

# 提取权限（能力许可）
codesign -d --entitlements - binary
# 关键权限: com.apple.security.app-sandbox, com.apple.security.network.client

# 去代码签名（为了 patch）
codesign --remove-signature binary

# 重签（ad-hoc，测试用）
codesign -f -s - binary
```

**CTF 相关性：** 补丁二进制要在 macOS 上跑必须重签。ad-hoc 签名（`-s -`）本地测试即可。

### Objective-C Runtime 逆向

```bash
# dump Objective-C 类信息
class-dump binary > classes.h
# 显示: @interface, @protocol, 带类型的方法签名

# lldb 运行时检查
(lldb) expression -l objc -O -- [NSClassFromString(@"ClassName") new]
(lldb) expression -l objc -O -- [[ClassName alloc] init]

# 方法交换检测（反篡改）
# 找: method_exchangeImplementations, class_replaceMethod
```

**反汇编里的 Objective-C：**

```text
# objc_msgSend(receiver, selector, ...) 是 THE 分发机制
# RDI = self（接收者）, RSI = selector（char* 方法名）

# Ghidra/IDA 里找：
objc_msgSend(obj, "checkPassword:", input)
# Selector 字符串在 __objc_methname 节
# 交叉引用 selector 找实现
```

**class-dump 替代：**

- `dsdump` — 更快，支持 Swift + Objective-C
- `otool -oV binary` — dump Objective-C 段
- Ghidra: Analysis Options 开 "Objective-C" 分析器

### Swift 二进制逆向

```bash
# 判断 Swift
strings binary | grep "swift"
otool -l binary | grep "swift"   # __swift5_* 节

# Swift demangle
swift demangle 's14MyApp0A8ClassC10checkInput6resultSbSS_tF'
# → MyApp.MyAppClass.checkInput(result: String) -> Bool

# xcrun swift-demangle < mangled_names.txt
```

**反汇编里的 Swift：**

```text
# Swift 用值见证表（VWT）做类型操作
# 协议见证表（PWT）做动态分发（类似 vtable）

# 关注运行时函数：
swift_allocObject          → 堆分配
swift_release             → 引用计数减
swift_bridgeObjectRetain  → 桥接（ObjC ↔ Swift）保留
swift_once                → 惰性初始化（类似 dispatch_once）

# String 布局：
# 小串（≤15 字节）：16 字节缓冲内联，标记指针
# 大串：堆分配，指针 + 长度 + 标志

# Array<T>: 指向 ContiguousArrayStorage（头 + 元素）
# Dictionary<K,V>: 开放寻址哈希表
```

**Swift 的 Ghidra：** 开 "Swift" 语言模块。Swift 元数据节（`__swift5_types`、`__swift5_proto`）含 Ghidra 可解析的类型描述符。

### iOS 应用分析

```bash
# 提取 IPA（iOS 应用包）
unzip app.ipa -d extracted/
ls extracted/Payload/*.app/

# 查是否加密（App Store 加密 / FairPlay DRM）
otool -l extracted/Payload/*.app/binary | grep -A4 "LC_ENCRYPTION_INFO"
# cryptid = 1 已加密, 0 已解密

# frida-ios-dump 解密（需越狱设备）
# 或设备上用 Clutch / bfdecrypt
frida-ios-dump -H jailbroken_ip -p 22 "App Name"

# 分析解密二进制
class-dump decrypted_binary > headers.h
```

**越狱检测与绕过：**

```javascript
// 常见越狱检查：
// 1. 查 Cydia/Sileo
// 2. 查 /private/var/lib/apt
// 3. fork() 成功（沙箱应用不能 fork）
// 4. 写打开 /etc/apt, /bin/sh
// 5. 查 substrate/substitute 库

// Frida 绕过：
var paths = ["/Applications/Cydia.app", "/bin/sh", "/etc/apt",
             "/private/var/lib/apt", "/usr/bin/ssh"];
Interceptor.attach(Module.findExportByName(null, "access"), {
    onEnter(args) {
        this.path = Memory.readUtf8String(args[0]);
    },
    onLeave(retval) {
        if (paths.some(p => this.path && this.path.includes(p))) {
            retval.replace(-1);  // 文件不存在
        }
    }
});
```

### dyld / 动态链接

```bash
# DYLD 环境变量（分析用；hardened runtime 下被禁）
DYLD_PRINT_LIBRARIES=1 ./binary       # 打印加载的 dylib
DYLD_INSERT_LIBRARIES=hook.dylib ./binary  # 注入 dylib（类似 LD_PRELOAD）
# 注意: SIP（系统完整性保护）对系统二进制禁此

# 查 dyld shared cache（含全部系统框架）
dyld_shared_cache_util -list /System/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e
```

---

## 嵌入式 / IoT 固件逆向

### 固件提取

```bash
# binwalk — 固件分析与提取
binwalk firmware.bin                        # 识别内嵌文件系统、压缩数据
binwalk -e firmware.bin                     # 提取全部识别组件
binwalk -Me firmware.bin                    # 递归提取（套娃）
binwalk --dd='.*' firmware.bin              # 全部裸提取

# 按签名手动提取
strings firmware.bin | head -50             # 找版本串、文件系统标记
hexdump -C firmware.bin | grep "hsqs"       # SquashFS 魔数
hexdump -C firmware.bin | grep "UBI#"       # UBI 魔数
```

**硬件提取方法（物理接触）：**

```text
UART:  串口控制台——常给 root shell 或 bootloader 权限
       工具: USB-UART 适配器, 波特率检测（常 115200）
       识别: 4 针（GND, TX, RX, VCC），万用表找

JTAG:  直接 CPU 调试——读写 flash、停 CPU、下断点
       工具: OpenOCD, J-Link, Bus Pirate
       识别: 10/14/20 针头，JTAGulator 自动检测

SPI Flash: 直接读芯片——dump 整个固件
           工具: flashrom, CH341A 编程器
           识别: 8 针 SOIC 芯片（Winbond, Macronix 等）

eMMC:  嵌入式 MMC——路由器、手机常见
       工具: eMMC 读取器, 焊测试点直连
```

### 固件解包

```bash
# SquashFS（路由器最常见）
unsquashfs -d output/ squashfs-root.sqfs
# 自定义压缩时: 试不同压缩器 (-comp xz|lzma|lzo|gzip)

# JFFS2
jefferson -d output/ jffs2.img

# UBI/UBIFS
ubireader_extract_images firmware.ubi
ubireader_extract_files ubifs.img

# CPIO（initramfs）
cpio -idv < initramfs.cpio

# 设备树 blob
dtc -I dtb -O dts -o output.dts device_tree.dtb

# 内核提取
binwalk -e firmware.bin
# 找: zImage, uImage, vmlinux
# 从压缩提取 vmlinux: vmlinux-to-elf 工具
```

### 架构注意点

**ARM（IoT 最常见）：**

```bash
# 交叉工具链
apt install gcc-arm-linux-gnueabihf gdb-multiarch

# QEMU 模拟
qemu-arm -L /usr/arm-linux-gnueabihf/ ./arm_binary
qemu-arm -g 1234 ./arm_binary    # 1234 端口起 GDB server
gdb-multiarch -ex 'target remote :1234' ./arm_binary

# ARM vs Thumb: ARM 指令 4 字节, Thumb 2 字节
# 函数指针 LSB 指示模式: 0=ARM, 1=Thumb
# Ghidra: 右键 → Processor Options → ARM/Thumb mode
```

**ARM64/AArch64：** 调用约定、ROP gadget 与 qemu-aarch64-static 模拟见 [platforms-hardware.md](platforms-hardware.md#arm64aarch64-逆向与利用)。

**MIPS（路由器、嵌入式）：**

```bash
# 大端 vs 小端——查 ELF 头或 file 命令
file binary    # "MIPS, MIPS32 rel2 (MIPS-II), big-endian" 或 "little-endian"

# 模拟
qemu-mips -L /usr/mips-linux-gnu/ ./mips_binary         # 大端
qemu-mipsel -L /usr/mipsel-linux-gnu/ ./mipsel_binary   # 小端

# MIPS 关键模式:
# 分支延迟槽——分支后的指令必执行
# $gp（全局指针）——PIC 用，指向 .got
# lui + addiu 对——载 32 位常量（高 16 + 低 16）
```

**RISC-V：** Capstone 反汇编见主 [tools.md](tools.md)；进阶扩展与调试见 [platforms-hardware.md](platforms-hardware.md)。

### RTOS 分析

```text
FreeRTOS:
  - 任务（似线程）: xTaskCreate → 函数指针 + 栈
  - 字符串: "IDLE", "Tmr Svc", 任务名
  - xQueueSend/xQueueReceive → 任务间通信
  - vTaskDelay() 计时, xSemaphoreTake() 同步

Zephyr:
  - k_thread_create → 内核线程创建
  - k_msgq_put/k_msgq_get → 消息队列
  - CONFIG_* 符号揭示内核配置

Bare metal（无 OS）:
  - 中断向量表在 0x0 或 0x08000000（STM32）
  - 主循环模式: while(1) { read_input(); process(); output(); }
  - 外设寄存器在内存映射地址（查数据手册）
```

---

## 内核驱动逆向

### Linux 内核模块

```bash
# 识别内核模块
file module.ko                      # "ELF 64-bit LSB relocatable"
modinfo module.ko                   # 模块信息（描述、作者、许可证）

# 列模块符号
nm module.ko | grep -v " U "       # 导出符号

# 快速侦察字符串
strings module.ko | grep -i "flag\|secret\|ioctl\|device"

# 找 ioctl handler
# 关键模式: file_operations 结构里 .unlocked_ioctl = my_ioctl_handler
# Ghidra: 找函数指针结构，按位置识别

# Ghidra 加载
# Language: x86:LE:64:default
# 基址: .ko 无所谓（relocatable）
# 找 init_module / cleanup_module 入口点
```

**常见内核模块赛题模式：**

```c
// 设备创建（造 /dev/challenge）
alloc_chrdev_region(&dev, 0, 1, "challenge");
cdev_init(&cdev, &fops);

// ioctl handler（主接口）
long my_ioctl(struct file *f, unsigned int cmd, unsigned long arg) {
    switch (cmd) {
        case CUSTOM_CMD_1: /* 操作 */ break;
        case CUSTOM_CMD_2: /* 操作 */ break;
    }
}

// copy_from_user / copy_to_user — 用户态数据传输
copy_from_user(kernel_buf, (void __user *)arg, size);
copy_to_user((void __user *)arg, kernel_buf, size);
```

**调试内核模块：**

```bash
# QEMU + GDB 内核调试
qemu-system-x86_64 -kernel bzImage -initrd initrd.cpio -s -S \
  -append "console=ttyS0 nokaslr" -nographic

# 另一终端
gdb vmlinux
(gdb) target remote :1234
(gdb) lx-symbols           # 加载模块符号（需脚本）
(gdb) add-symbol-file module.ko 0x<loaded_address>
```

### eBPF 程序

```bash
# dump 运行系统的 eBPF 程序
bpftool prog list
bpftool prog dump xlated id <N>    # 反汇编
bpftool prog dump jited id <N>     # JIT 机器码

# eBPF 字节码分析
# eBPF 有 11 个寄存器 (r0-r10)，64 位
# r0 = 返回值, r1-r5 = 参数, r10 = 帧指针
# 指令每条 8 字节

# 反汇编含 eBPF 的 .o
llvm-objdump -d ebpf_prog.o

# 关键 eBPF 模式:
# bpf_map_lookup_elem → 读 map
# bpf_map_update_elem → 写 map
# bpf_probe_read → 读内核内存
# bpf_trace_printk → 调试输出
```

### Windows 内核驱动

```bash
# .sys 是 PE 格式——IDA/Ghidra 按普通 PE 加载
# 入口点: DriverEntry(PDRIVER_OBJECT, PUNICODE_STRING)

# 关键模式:
# IoCreateDevice → 创建设备对象
# IRP_MJ_DEVICE_CONTROL → ioctl handler
# MmMapIoSpace → 内存映射 I/O
# ObReferenceObjectByHandle → 从句柄取内核对象
# ZwCreateFile/ZwReadFile → 内核态文件操作
```

---

## 汽车 / CAN 总线逆向

```bash
# CAN 接口设置
sudo ip link set can0 type can bitrate 500000
sudo ip link set up can0

# 抓 CAN 流量
candump can0                               # 实时抓
candump -l can0                            # 存日志
cansniffer can0                            # 过滤/高亮变化

# 重放 CAN 消息
canplayer -I logfile.log can0
cansend can0 7DF#0201000000000000          # 发单帧（OBD-II 请求）

# UDS（统一诊断服务）——汽车 CTF 常见
# 服务 0x27: 安全访问（种子-密钥认证）
# 服务 0x2E: 按标识写数据
# 服务 0x31: 例程控制

# 解码 CAN 帧
# ID: 11 位或 29 位标识符
# DLC: 数据长度码（0-8 字节）
# Data: 最多 8 字节载荷
```

**汽车 CTF 模式：**

- 种子-密钥绕过：从 ECU 固件逆密钥派生算法
- CAN 消息重放：抓合法命令重放解锁功能
- UDS/KWP2000 提取 ECU 固件
