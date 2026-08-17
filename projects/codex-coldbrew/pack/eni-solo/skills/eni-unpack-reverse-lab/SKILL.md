---
name: eni-unpack-reverse-lab
description: Offline Windows PE packing, unpacking triage, and evidence-backed reverse-engineering workflow. Use when the user says "冷咖啡" and asks to inspect a local EXE/DLL, identify packers or protectors, triage UPX/PyInstaller/.NET/native/VM-protected binaries, audit local reverse tools, create a copy-only analysis case, decompile or dynamically observe a local binary, or verify whether an authorization state is real, persistent, and cross-machine.
---

# 脱壳逆向实验工作流

触发词：`冷咖啡`。当用户以 `冷咖啡` 开场并要求检查本地 EXE/DLL、识别壳与保护器、分诊 UPX/PyInstaller/.NET/原生/VM 保护样本、盘点本地逆向工具、建立仅副本的分析 case、反编译或动态观察本地二进制，或验证某个授权状态是否真实、持久且跨机时，走本技能。

本技能只面向本地工件。绝不修改、改名、删除或覆盖原始工件与任何既有用户技能。所有工作在复制的 case 工件上进行，证据路径、哈希、时间戳与进程清理结果全程留痕。

## 快速路径

1. 在工作区下新建或复用 case 目录；记录 SHA-256 基线。
2. 跑 `scripts/cold_coffee_native_workflow.py <artifact> --case-dir <case> --dynamic` 走完整有界工作流；某个阶段需要单独隔离时，改跑下面的单脚本。
3. 仅需静态证据时：`scripts/pe_pack_triage.py <artifact> --out <case>/triage/pe-pack.json` 与 `scripts/reverse_tool_audit.py --out <case>/triage/reverse-tools.json`。
4. 按下方指标选择最浅的可行路线。所有指标都只是线索，不是证据。
5. 动态作业只启动复制目标，窗口保持隐藏或移出屏幕，设置超时，且只清理从 case 路径启动的进程。
6. 报告时事实与推断分开写。状态弹窗、本地分支或打过补丁的副本，不能表述为永久/全权限结果。

## 路由

- **UPX 特征**：先记录节布局与熵；只在副本上脱壳，并对结果重新分诊。
- **PyInstaller 特征**：定位 archive/overlay 与 Python 运行时标记；提取前先清点内容。
- **.NET 特征**：本地有元数据/IL 工具时使用；保留强名称与原始元数据证据。
- **原生壳/虚拟化特征**：收集节熵、导入、运行时分配/保护变化、反调试/更新行为与稳定代码区，再做定向反汇编。
- **未知或混合特征**：静态字符串/导入 + 有界的隐藏 GUI/进程追踪；样本表现出破坏性或越过复制 case 边界时立即停止。

## 授权证据闸门

用户索要解锁功能、全部权限、长期激活、持久化或跨机行为时，读 `references/evidence-gates.md`。每一项诉求都要有直接证据支撑。

## 资源

- `scripts/pe_pack_triage.py`：只读的 PE/头/节/熵/签名分诊。
- `scripts/reverse_tool_audit.py`：盘点本地可用的脱壳与逆向工具，不改动系统。
- `scripts/runtime_exec_surface.py`：复制进程的有界只读可执行内存映射。
- `scripts/capture_private_exec_regions.py`：只捕获复制进程的私有可执行区域，附哈希。
- `scripts/scan_x86_dispatch.py`：离线扫描捕获代码中的有界 x86 授权分发签名。
- `scripts/auth_transport_trace.py`：只捕获复制登录进程的 socket/传输/加密 API 元数据；刻意排除载荷与凭据。
- `scripts/isolated_remember_state_probe.py`：用进程隔离的 AppData/Temp 沙箱检查复制进程的记住状态持久化，不登录。
- `scripts/login_memory_map_diff.py`：对比正常有界登录尝试前后的私有分配元数据，不读载荷内存。
- `scripts/login_control_layout.py`：在自动化之前识别登录控件标签、ID 与布局；绝不提交登录。
- `scripts/runtime_string_xrefs.py`：定位复制进程中的运行时文本与代码引用，不改内存、不发输入。
- `scripts/trial_surface_probe.py`：触发复制客户端的可见试用入口并记录 UI 结果，不读凭据。
- `scripts/cold_coffee_native_workflow.py`：只追加的自动化包装：建时间戳 case run，收集静态/工具证据，可选执行隐藏的复制进程运行时捕获。
- `references/evidence-gates.md`：防误报的验证闸门。
