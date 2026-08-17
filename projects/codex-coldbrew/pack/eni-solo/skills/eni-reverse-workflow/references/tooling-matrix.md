# 工具矩阵

优先选用环境里已有的工具。除非确实有用且被允许，否则不装重型工具。

## 通用分诊

- 哈希：`Get-FileHash`、`sha256sum`、Python `hashlib`
- 文件类型：`file`，缺失时用 Python magic-bytes 兜底
- 字符串：`strings`、FLOSS、Python 兜底
- 元数据：ExifTool、Detect It Easy、TrID
- 十六进制：`xxd`、`hexdump`、HxD、010 Editor

## 原生二进制静态分析

- 主力：Ghidra、IDA Free/Pro、Binary Ninja、Radare2/rizin、objdump、readelf、nm、dumpbin
- PE 侧：PE-bear、CFF Explorer、pefile、sigcheck
- ELF 侧：readelf、checksec（仅安全上下文）、eu-readelf
- Mach-O 侧：otool、jtool2、class-dump/objc 工具

## 动态分析

- 调试器：x64dbg、WinDbg、gdb/lldb、Frida
- 追踪：Procmon、Process Explorer、API Monitor、strace/ltrace、dtruss、ETW/xperf
- 网络：Wireshark、tcpdump、mitmproxy（授权实验环境）
- 沙箱：本地 VM 快照、Linux 工具容器、移动端模拟器

## 托管/移动

- .NET：dnSpyEx、ILSpy、dotnet 元数据工具
- Java/Android：jadx、apktool、dex2jar、Android Studio profiler、adb
- iOS/macOS：class-dump、Hopper/Ghidra、lldb、Frida（自有测试设备）

## 固件

- binwalk、unblob、jefferson/sasquatch、unsquashfs、qemu-user/system、FirmAE（适用时）

## 漏洞证据

- Sanitizers：可重编译时用 ASAN/UBSAN/MSAN
- 模糊测试：libFuzzer/AFL++/honggfuzz（自有代码或实验靶标）
- 崩溃分诊：调试器栈回溯、寄存器、故障地址、输入偏移关联
- 补丁对比：bindiff、Diaphora、Ghidra version tracking、git diff/源码 diff

## 每次工具运行的取证要求

记录命令、版本、输入哈希、输出路径、时间戳与解读。原始日志 + 简短的结论摘要并存。
