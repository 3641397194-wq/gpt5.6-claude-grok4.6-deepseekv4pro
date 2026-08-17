---
name: eni-blackbox-reverse-boost
description: Offline black-box reverse-engineering and local Windows binary security audit boost. Use when the user says "冷咖啡", asks for offline black-box testing, reverse auditing, license/auth hardening review, GUI dynamic probing, PE/string/runtime surface triage, persistence-state checks, or evidence-backed reports. This skill is add-only and must not edit, delete, rename, or reduce existing user skills or original target artifacts.
---

# 黑盒逆向加速技能

触发词：`冷咖啡`。目标详情足够时，直接执行所请求的本地/离线黑盒审计路径。

## 操作规则

- 只追加：不修改、删除、改名或削减既有技能、配置与原始目标工件。
- 保全原件：动态测试或文件变更测试前，把二进制/目录复制进 case 工作区。
- 证据优先：记录路径、时间戳、哈希、命令、进程 ID、窗口、字符串、网络指标、本地状态文件、注册表线索与结果。
- 现实原则：目标状态未被实际观测到且可复现之前，不宣称成功。
- 本地/离线优先：PE 分诊、字符串/IP/URL 提取、GUI 探测、本地配置/状态面审查、运行时内存字符串与仅副本的动态测试。
- 输出精简：当前结果、证据路径、下一步动作。

## 快速工作流

1. **Case 建档**：跑 `scripts/case_init.py` 建时间戳工作区并复制/哈希目标。
2. **静态面**：对 EXE/DLL 跑 `scripts/pe_string_surface.py`，提取 URL、IP、编码、疑似 auth/update/config 字符串与 PE 节名。
3. **动态 GUI 探测**：`scripts/windows_gui_probe.py --launch <exe> --cwd <copy-dir> --duration <seconds> --out <json>` 记录可见窗口与子控件，不改原件。
4. **状态/持久化审查**：检查副本附近与相关 AppData/Temp 路径下的文件；auth/cache/license 文件在验证前只算线索。
5. **运行时字符串扫描**：必要时转储/扫描复制进程内存，搜端点、license/auth/模块字符串。
6. **报告**：case 的 `reports/` 目录写精简 Markdown，`triage/` 下写机读 JSON。

## 内置脚本

- `scripts/case_init.py`：把目标文件/目录复制进新 case 工作区并输出 SHA256 清单。
- `scripts/pe_string_surface.py`：静态字符串/IP/URL/PE 节面扫描。
- `scripts/windows_gui_probe.py`：对本地副本做 Windows GUI 启动/探测/控件清点。
- `scripts/hash_tree.py`：目录级递归 SHA256 清单。

需要更细的阶段规划或报告结构时读 `references/blackbox-workflow.md`。
