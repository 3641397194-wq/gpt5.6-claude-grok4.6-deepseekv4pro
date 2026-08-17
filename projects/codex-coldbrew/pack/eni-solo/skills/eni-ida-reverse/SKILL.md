---
name: eni-ida-reverse
description: 全局自动路由 |
  IDA Pro 二进制逆向分析技能。凡用户要求逆向、反编译或分析 PE/ELF/APK/DLL/SO/Mach-O/SYS 等二进制文件，无论是否明说 IDA，也无论目标是查破解、找密码、追注册逻辑、做漏洞或病毒分析、分析固件，都应启用本技能。

  Applies to any binary-analysis request even when "IDA" or "reverse engineering" is not mentioned, e.g. "看看这个exe", "分析这个dll", "帮我破解", "找一下密码", "这个软件怎么注册".

  Server and file management must go through the bundled scripts (scripts/start.ps1, scripts/open.ps1) — never write ad-hoc PowerShell for these operations.
---

# IDA Pro 逆向分析技能

## 技能定位

本技能把 IDA Pro 的能力通过 MCP 工具面暴露给当前 AI 客户端。核心链路是一条：

```text
start.ps1 拉起 HTTP 服务 → open.ps1 打开目标文件 → idapro_* 工具完成全部分析动作
```

服务器名固定为 `idapro`，工具前缀统一为 `idapro_*`，走 Remote HTTP 模式而非 stdio。

## 踩坑记录与对策

下表汇总了历次联调中实际遇到并已解决的问题。开工前先过一遍，能省下大量排障时间。

| 现象 | 根因 | 对策 |
|------|------|------|
| 调用 `idapro_idalib_open` 报 `Structured content does not match the tool's output schema` | 部分 AI 客户端的 MCP 实现对该工具 output schema 校验有 BUG | 一律改用 `scripts/open.ps1` 经 HTTP API 直连打开文件，绕开 MCP 校验层；打开后数据库即绑定到共享上下文，其余工具照常使用 |
| System32 下的目标打不开 | idalib 没有权限直接读取该目录 | `open.ps1` 检测到 System32 路径后自动复制到临时目录再打开 |
| 启动脚本卡住对话 | `idalib-mcp` 前台持续刷 INFO 日志 | 用 `scripts/start.ps1`（`-WindowStyle Hidden`）后台静默拉起，脚本等就绪后自行退出 |
| 服务器名带横线引发工具注册异常 | 早期把服务器命名为 `ida-pro-mcp` | 现固定为 `idapro`，工具前缀 `idapro_*` |
| stdio 本地模式同样报 schema 错误 | `type:"local"` 下 `idalib_open` 有同样问题 | 统一 Remote HTTP 模式：脚本先直开文件，再走 MCP 工具 |
| 打开后残留孤儿 worker 咬住 `.id0/.id1/.nam` | 首次打开超时后 idalib 的 Python 子进程变成孤儿进程 | `start.ps1` 用 `taskkill /F /T` 杀整棵进程树；`open.ps1` 另备降级路径：检测到旧库被锁就复制到 Temp 并加 GUID 前缀 |
| 带自动分析打开看起来像死锁 | 后端其实还在分析，只是迟迟不回包 | `open.ps1` 改为后台请求 + 前台轮询，每 10 秒打印一次 `INFO:opening:已用时/超时秒数`；支持 `-TimeoutSeconds` 参数，超时返回 `ERR:open_timeout_xxs` |

> 上游已合并过修复（mrexodia 的 PR #389 修复了 HTTP 模式下部分 structuredContent schema 问题），但客户端侧校验问题仍需靠 `open.ps1` 绕过，当前安装的是 `main` 分支最新版。

### 会话就绪判定

- `open.ps1` 轮询到会话就绪会提前返回 `OK:文件名:session_id`。
- 超时上限内始终未就绪才返回 `ERR:open_timeout_xxs`。
- 实测复杂 GUI 样本（如 Snipaste.exe）带自动分析约需 324 秒才返回成功——这是"分析久"，不是"脚本挂死"。遇到 GUI 或大样本，显式给 `-TimeoutSeconds 600`。

## 服务与文件管理

### start.ps1 — 拉起 HTTP 服务

- 位置：`scripts/start.ps1`
- 行为：`taskkill /F /T` 清掉旧进程树（连同 worker 子进程）→ 后台启动 `idalib-mcp` → 最多等 15 秒确认就绪
- 输出：成功 `OK:72`，失败 `ERR:timeout`

```powershell
powershell -File "<skill-root>\scripts\start.ps1"
```

### open.ps1 — 打开目标文件

- 位置：`scripts/open.ps1`
- 行为要点：
  - 通过 HTTP API 直调 `idalib_open`，绕开 MCP schema 校验
  - System32 路径自动转临时目录
  - 打开前清理同名旧库文件（`.id0/.id1/.nam/.til/.i64`）
  - 旧库被锁时降级：复制到 Temp、文件名加 GUID 前缀，成功输出附 `(temp copy)` 标记
  - 后台请求 + 前台轮询，避免长时间同步等待
  - 失败时自动改用 Temp 副本重试

```powershell
# 基础用法
powershell -File "<skill-root>\scripts\open.ps1" -Path "C:\path\to\file.exe"

# 指定会话 ID
powershell -File "<skill-root>\scripts\open.ps1" -Path "file.exe" -SessionId "my_session"

# 跳过自动分析（大文件推荐）
powershell -File "<skill-root>\scripts\open.ps1" -Path "large.exe" -NoAutoAnalysis

# 设定超时（带自动分析时强烈建议）
powershell -File "<skill-root>\scripts\open.ps1" -Path "file.exe" -TimeoutSeconds 600
```

输出约定：

```text
INFO:opening:11/600s                          # 分析进行中，每 10 秒一条
OK:sample.exe:abcd1234                        # 打开成功
OK:1234abcd-sample.exe:abcd1234 (temp copy)   # 成功但走了 Temp 降级副本
ERR:open_timeout_600s                         # 达到超时上限
```

## 工具分组速览

### 概况与枚举

- `idapro_survey_binary(detail_level)` — 首个动作。返回架构、入口点、函数与字符串统计、段布局、导入分类（加密/网络/文件 IO/注册表）以及高 xref 热点函数。`detail_level` 取 `minimal`（首选）/`standard`/`full`
- `idapro_list_funcs(queries)` — 分页列函数，可按名过滤
- `idapro_list_globals(queries)` — 列全局变量
- `idapro_entity_query(kind, filter)` — 统一入口，`kind` 取 functions/globals/imports/strings/names

### 反编译与反汇编

- `idapro_decompile(addr)` — 伪代码
- `idapro_disasm(addr, max_instructions)` — 汇编
- `idapro_analyze_function(addr, include_asm)` — 一次拿全伪代码、字符串、常量、调用者、被调用者、基本块
- `idapro_func_profile(queries)` — 批量函数指标（大小、块数、xref 数）

### 引用与数据流

- `idapro_xrefs_to(addrs)` / `idapro_xref_query(addr, direction)` — 谁引用谁
- `idapro_callees(addrs)` — 子调用列表
- `idapro_callgraph(roots, max_depth)` — 调用图
- `idapro_trace_data_flow(addr, direction, max_depth)` — forward/backward 数据流追踪

### 检索

- `idapro_find_regex(pattern, limit)` — 正则搜字符串
- `idapro_search_text(pattern)` — 反汇编列表内搜文本
- `idapro_find_bytes(patterns, limit)` — 字节模式，`??` 通配
- `idapro_find(type, targets)` — 高级搜索（立即数/字符串/引用）

### 数据读取

- `idapro_get_bytes(addrs)` / `idapro_get_string(addrs)` / `idapro_get_int(queries)`
- `idapro_get_global_value(queries)` / `idapro_read_struct(queries)` / `idapro_search_structs(filter)`

### 写入与修补

- `idapro_set_comments(items)`（反汇编与反编译双向同步）/ `idapro_append_comments(items)`
- `idapro_rename(batch)` — 函数/全局/局部/栈变量批量改名
- `idapro_patch_asm(items)` / `idapro_patch(patches)`
- `idapro_define_func(items)` / `idapro_undefine(items)` / `idapro_define_code(items)`

### 类型与栈

- `idapro_declare_type(decls)` / `idapro_set_type(edits)` / `idapro_infer_types(addrs)` / `idapro_type_query(queries)` / `idapro_type_inspect(queries)`
- `idapro_stack_frame(addrs)` / `idapro_declare_stack(items)` / `idapro_delete_stack(items)`

### 签名

- `idapro_make_signature(addrs)` / `idapro_make_signature_for_function(addrs)` / `idapro_find_xref_signatures(addrs)`

### 会话与杂项

- 会话：`idapro_idalib_list/current/switch/close/save/health`，注意 `idapro_idalib_open` 有 schema 校验 BUG，用 `open.ps1` 代替
- 调试器工具默认隐藏，URL 加 `?ext=dbg` 启用；`idapro_open_file(file_path)` 可在 GUI 实例中打开文件
- 杂项：`idapro_int_convert(inputs)`（进制转换必须走它，禁止心算）、`idapro_export_funcs(addrs, format)`（json/c_header/prototypes）、`idapro_py_eval(code)`、`idapro_server_health()`、`idapro_server_warmup()`

## 标准分析流程

### 第 1 步：确认服务

```powershell
powershell -File "scripts/start.ps1"
```

看到 `OK:72` 即可继续。

### 第 2 步：打开目标

```powershell
powershell -File "scripts/open.ps1" -Path "C:\目标.exe" -TimeoutSeconds 600
```

输出 `OK:文件名:session_id` 表示就绪；带 `(temp copy)` 表示降级到了临时副本；期间周期性的 `INFO:opening:...` 说明后端还在自动分析；`ERR:open_timeout_xxs` 才算超时。

### 第 3 步：全局概览

```
idapro_survey_binary(detail_level="minimal")
```

盯着这五项：架构（x86/x64/ARM）；入口点（main/WinMain/DllMain）；高价值字符串（URL、路径、报错文本）；导入分类（有没有加密、网络、文件 IO 族）；xref 热点函数。

### 第 4 步：锁定关键函数

```
idapro_analyze_function(addr="关键函数名")
# 或者拆开用
idapro_decompile(addr="函数名")
idapro_disasm(addr="函数名", max_instructions=50)
```

### 第 5 步：引用与数据流

```
idapro_xrefs_to(addrs="关键地址/字符串")
idapro_callgraph(roots=["关键函数"], max_depth=3)
idapro_trace_data_flow(addr="关键地址", direction="backward", max_depth=5)
```

### 第 6 步：边分析边标注

```
idapro_set_comments(items=[{"addr": "0x140001000", "comment": "你的理解"}])
idapro_rename(batch={"func": [{"addr": "函数地址", "name": "有意义的名字"}]})
```

### 第 7 步：产出报告

分析收尾后生成 `report.md`，记录发现与复现路径。

## 分析纪律

1. 进制换算交给 `idapro_int_convert`，不口算不手算
2. 顺序固定：先 survey 后深入，不跳步
3. 注释与重命名随分析持续更新，它们是后续分析的燃料
4. 发现有趣数据先查 `xrefs_to`，追踪引用链
5. 遇混淆代码先做预处理：字符串解密、导入哈希还原、控制流平坦化还原
6. C++/STL 代码先用 FLIRT/Lumina 把库函数识别掉，再啃业务逻辑
7. 解法靠反汇编推导 + 简单 Python 辅助计算，不暴力穷举
8. 报 `No database bound`：还没开文件，先跑 `open.ps1`
9. 报 `Failed to open database`：多半是旧库被锁，`open.ps1` 会自行降级到 Temp 副本（输出带 `(temp copy)`）
10. GUI/复杂样本带自动分析打开时，默认加 `-TimeoutSeconds 600`，别把长时间的 `INFO:opening:...` 误判成卡死

---

## 路由上下文

**上游入口**：`skills/SKILL.md`（总控）、`routing.md`
**上游备选**：`radare2/`（不想开 IDA 时先 r2 快速侦察）
**下游出口**：
- 需要 Frida 动态验证 → `reverse-engineering/tools-dynamic.md`
- 需要符号执行/angr → `reverse-engineering/tools-dynamic.md`
- 需要通用逆向方法论 → `reverse-engineering/SKILL.md`

**同级关联模块**：`radare2/`（IDA 不可用时的替代）

---

## 按需自举（On-Demand Bootstrap）

本 skill 入口脚本已接入统一自举系统。

### 自动化能力边界

| 工具 | 可自动安装 | 安装方式 | 说明 |
|------|-----------|---------|------|
| idalib-mcp | ✓ | 从 GitHub 以 pip 安装 | `start.ps1` 缺失时自动装 |
| IDA Pro 本体 | ✗ | 商业软件，需手动安装 | 用 `IDADIR` 环境变量指向安装目录 |

### 安装步骤（已验证）

```cmd
:: 1. 指定 IDA 安装目录
setx IDADIR "<你的IDA安装目录>"

:: 2. 安装 ida-pro-mcp（PyPI 上的 ida-mcp 是另一个项目，别装错）
pip install git+https://github.com/mrexodia/ida-pro-mcp.git

:: 3. 安装 IDA 插件（Streamable HTTP + Global + 全选客户端）
ida-pro-mcp --install

:: 4. 重启 IDA Pro 并打开目标文件，插件自动监听 127.0.0.1:13337

:: 5. 校验
ida-pro-mcp --config
```

> 注意：PyPI 上的 `ida-mcp`（作者 jtsylve）不是本项目，必须从 GitHub 装 `mrexodia/ida-pro-mcp`。

### 自举触发点

- `scripts/start.ps1`：检测不到 `idalib-mcp` 时自动调用 `bootstrap-reverse.ps1`
- MCP 注册：bootstrap 自动把 `idapro` 写入 Claude MCP 配置

### 前置条件

- IDA Pro 已安装且 `IDADIR` 已设置（或脚本内默认路径有效）
- Python 可用（idalib-mcp 依赖 Python）
