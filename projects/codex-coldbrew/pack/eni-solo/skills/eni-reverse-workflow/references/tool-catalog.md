# 精选逆向工具目录

快照说明：GitHub star 数据查询于 2026-07-01。数字为近似值，正式对外引用前应重新核对。

## 高星工具按用途分类

### 反编译与静态分析主力

| 工具 | 仓库 | Stars | 一句话评价 | 本地命令 |
|---|---|---:|---|---|
| Ghidra | https://github.com/NationalSecurityAgency/ghidra | 70,306 | 反编译质量与可脚本化兼备的开源标杆，原生与固件通吃 | `ghidraRun`, `analyzeHeadless` |
| RetDec | https://github.com/avast/retdec | 8,566 | 全自动机器码反编译，适合无人值守批量出伪代码 | `retdec-decompiler` |
| radare2 | https://github.com/radareorg/radare2 | 24,225 | CLI 交互灵活，脚本化能力强，侦察首选 | `r2`, `rabin2`, `rahash2` |
| Rizin | https://github.com/rizinorg/rizin | 3,693 | radare2 的社区分支，接口更现代 | `rizin`, `rz-bin` |

### 动态插桩与调试

| 工具 | 仓库 | Stars | 一句话评价 | 本地命令 |
|---|---|---:|---|---|
| x64dbg | https://github.com/x64dbg/x64dbg | 48,770 | Windows 用户态调试的事实标准 | `x64dbg`, `x32dbg` |
| Frida | https://github.com/frida/frida | 21,168 | 跨平台运行时插桩，移动端逆向的核心武器 | `frida`, `frida-trace` |
| pwndbg | https://github.com/pwndbg/pwndbg | 10,609 | GDB 的体验增强层，pwn 场景顺手 | `gdb` 插件 |
| GEF | https://github.com/hugsy/gef | 8,251 | 另一款 GDB 增强，可视化友好 | `gdb` 插件 |
| PEDA | https://github.com/longld/peda | 6,130 | 老牌 GDB 辅助，exploit 开发常用 | `gdb` 插件 |

### Android 专项

| 工具 | 仓库 | Stars | 一句话评价 | 本地命令 |
|---|---|---:|---|---|
| jadx | https://github.com/skylot/jadx | 49,250 | DEX/APK 转 Java 源码的首选，界面与 CLI 都可用 | `jadx`, `jadx-gui` |
| Apktool | https://github.com/iBotPeaches/Apktool | 24,904 | APK 资源与 smali 的解包/重建标准件 | `apktool` |

### 固件与文件识别

| 工具 | 仓库 | Stars | 一句话评价 | 本地命令 |
|---|---|---:|---|---|
| Binwalk | https://github.com/ReFirmLabs/binwalk | 14,083 | 固件切割与提取的常青树 | `binwalk` |
| Detect It Easy | https://github.com/horsicq/Detect-It-Easy | 11,062 | 壳/编译器/文件类型识别，快且准 | `diec`, `die` |

### 符号执行与仿真

| 工具 | 仓库 | Stars | 一句话评价 | 本地命令 |
|---|---|---:|---|---|
| angr | https://github.com/angr/angr | 8,921 | 符号执行与 CFG 分析的开源头牌 | Python 模块 |
| Unicorn | https://github.com/unicorn-engine/unicorn | 9,126 | 轻量 CPU 仿真内核，适合自建分析框架 | Python 模块 |
| Qiling | https://github.com/qilingframework/qiling | 5,986 | 基于 Unicorn 的全系统仿真框架，跨平台 | Python 模块 |
| Manticore | https://github.com/trailofbits/manticore | 3,857 | Trail of Bits 出品的符号执行平台 | `manticore` |

### 规则与特征检测

| 工具 | 仓库 | Stars | 一句话评价 | 本地命令 |
|---|---|---:|---|---|
| YARA | https://github.com/VirusTotal/yara | 9,721 | 二进制模式匹配的事实标准 | `yara` |
| capa | https://github.com/mandiant/capa | 6,080 | 从二进制里直接提取"能干什么"的能力检测 | `capa` |
| FLOSS | https://github.com/mandiant/flare-floss | 4,066 | 静态提取被混淆/加密的字符串 | `floss` |

### 内存取证

| 工具 | 仓库 | Stars | 一句话评价 | 本地命令 |
|---|---|---:|---|---|
| Volatility 3 | https://github.com/volatilityfoundation/volatility3 | 4,223 | 内存镜像取证框架的标准 | `vol`, `vol.py` |

### 漏洞验证与模糊测试

| 工具 | 仓库 | Stars | 一句话评价 | 本地命令 |
|---|---|---:|---|---|
| hashcat | https://github.com/hashcat/hashcat | 26,241 | 离线哈希恢复性能之王（授权场景） | `hashcat` |
| John the Ripper | https://github.com/openwall/john | 13,318 | 多格式离线哈希审计经典 | `john` |
| Google Sanitizers | https://github.com/google/sanitizers | 12,407 | 编译器插桩系内存错误检测 | 编译选项 |
| OSS-Fuzz | https://github.com/google/oss-fuzz | 12,398 | 持续模糊测试的工程范本 | 模板参考 |
| AFL++ | https://github.com/AFLplusplus/AFLplusplus | 6,628 | 覆盖率引导模糊测试主力 | `afl-fuzz` |
| syzkaller | https://github.com/google/syzkaller | 6,249 | 内核模糊测试框架 | `syz-manager` |

### 二进制解析库与实验环境

| 工具 | 仓库 | Stars | 一句话评价 | 本地命令 |
|---|---|---:|---|---|
| Capstone | https://github.com/capstone-engine/capstone | 8,872 | 反汇编库，自家工具链的底座 | Python 模块 / 库 |
| LIEF | https://github.com/lief-project/LIEF | 5,460 | 格式解析与改写一体，PE/ELF/Mach-O 通吃 | Python 模块 |
| FLARE-VM | https://github.com/mandiant/flare-vm | 8,809 | Windows 逆向实验环境一键配齐 | PowerShell 安装器 |
| Bloaty | https://github.com/google/bloaty | 5,496 | 二进制体积剖析，定位膨胀来源 | `bloaty` |

## 场景选型建议

- **原生逆向**：Ghidra 主力 + radare2/Rizin 侦察 + Detect It Easy 识别 + capa 能力分诊 + FLOSS 提字符串；调试上 x64dbg（Windows）/ GDB + pwndbg/GEF（Linux）。
- **Android**：jadx 读 Java 层、Apktool 动资源与 smali、Frida 做动态插桩、Ghidra 处理 native 库。
- **固件**：Binwalk 提取 + Ghidra 分析 + Qiling/Unicorn 局部仿真 + YARA 特征扫描。
- **动态侧**：x64dbg/WinDbg/gdb/lldb/Frida，配合 Procmon/strace/tcpdump/Wireshark。
- **漏洞向**：AFL++ 与 sanitizers 打头，内核用 syzkaller，崩溃后用调试器做根因分诊。
- **内存取证**：Volatility 3 + YARA + 字符串与时间线工具。

## 选型原则

从"能回答用户问题的最小本地工具集"起步，不要求全装。优先用已安装的，缺的作为可选的下一步建议。
