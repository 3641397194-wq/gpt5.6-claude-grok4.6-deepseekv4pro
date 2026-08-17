# IDA Pro MCP 工具速查手册

> 按用途整理的 `idapro_*` 工具参考。服务器名 `idapro`，HTTP 模式，工具前缀 `idapro_*`。
> 打开文件与启动服务一律走 `scripts/start.ps1` 与 `scripts/open.ps1`。

---

## 服务与会话

### 拉起服务、打开文件

```powershell
# 后台启动服务器
powershell -File "scripts/start.ps1"
# 期望输出：OK:72

# 打开文件（HTTP 直连，绕开 MCP schema 校验）
powershell -File "scripts/open.ps1" -Path "C:\target.exe"
# 期望输出：OK:filename:session_id

# GUI/大型样本建议显式给超时
powershell -File "scripts/open.ps1" -Path "C:\big.exe" -TimeoutSeconds 600

# 想快速打开就跳过自动分析
powershell -File "scripts/open.ps1" -Path "C:\huge.sys" -NoAutoAnalysis
```

### 会话工具一览

| 工具 | 作用 | 典型时机 |
|------|------|---------|
| `idapro_idalib_list()` | 枚举所有 session | 多文件并行分析前 |
| `idapro_idalib_current()` | 查看当前绑定的 session | 确认操作落在哪个库 |
| `idapro_idalib_switch(session_id)` | 切换 session | 新旧版本对比 |
| `idapro_idalib_close(session_id)` | 关闭 session | 释放资源 |
| `idapro_idalib_save(path)` | 保存数据库 | 阶段性归档 |
| `idapro_idalib_health(session_id)` | 检查 worker 状态 | 怀疑卡死时 |
| `idapro_server_health()` | 服务器健康检查 | 工具集体无响应时 |
| `idapro_server_warmup()` | 预热子系统（字符串缓存、Hex-Rays 等） | 首次大批量操作前 |

---

## 入口侦察

### survey_binary — 全局概况

```
idapro_survey_binary(detail_level="minimal")
```

涵盖：架构（x86/x64/ARM/MIPS）、入口点、函数总数、字符串统计、段布局、导入分类（加密/网络/文件 IO/注册表）、高 xref 函数。

`detail_level` 取值：`minimal`（推荐第一步）→ `standard` → `full`。

### 函数与全局

```
# 分页列函数
idapro_list_funcs(queries=[{"offset": 0, "limit": 50}])

# 名称过滤
idapro_list_funcs(queries=[{"filter": "crypt", "offset": 0, "limit": 20}])
idapro_list_funcs(queries=[{"filter": "main", "offset": 0, "limit": 10}])

# 全局变量
idapro_list_globals(queries=[{"filter": "g_", "offset": 0, "limit": 30}])
```

### entity_query — 统一查询

```
idapro_entity_query(kind="imports", filter="Create")
idapro_entity_query(kind="strings", filter="http")
idapro_entity_query(kind="names", filter="")
```

---

## 反汇编与反编译

### decompile — 伪代码

```
# 按符号名
idapro_decompile(addr="main")
idapro_decompile(addr="sub_140001000")

# 按地址
idapro_decompile(addr="0x140001000")
```

### disasm — 汇编

```
# 默认条数
idapro_disasm(addr="main")

# 指定条数
idapro_disasm(addr="0x401000", max_instructions=100)
```

### analyze_function — 一次拿全（推荐）

```
# 伪代码 + 字符串 + 常量 + 调用者/被调用者 + 基本块
idapro_analyze_function(addr="main", include_asm=false)

# 附带汇编
idapro_analyze_function(addr="sub_401000", include_asm=true)
```

### func_profile — 批量函数指标

```
idapro_func_profile(queries=["main", "sub_401000", "sub_402000"])
```

---

## 引用、调用图与数据流

### xrefs_to — 谁引用我

```
idapro_xrefs_to(addrs=["sub_401000"])
idapro_xrefs_to(addrs=["0x404000"])
idapro_xrefs_to(addrs=["CreateFileW", "ReadFile", "WriteFile"])
```

### xref_query — 方向与类型过滤

```
idapro_xref_query(addr="0x401000", direction="to")
idapro_xref_query(addr="0x401000", direction="from")
```

### callees 与 callgraph

```
idapro_callees(addrs=["main"])

idapro_callgraph(roots=["main"], max_depth=3)
idapro_callgraph(roots=["sub_401000", "sub_402000"], max_depth=2)
```

### trace_data_flow — 数据流追踪

```
# 溯源：这个值从哪来
idapro_trace_data_flow(addr="0x401050", direction="backward", max_depth=5)

# 去向：这个值流向哪里
idapro_trace_data_flow(addr="0x401050", direction="forward", max_depth=5)
```

---

## 检索

### find_regex — 正则搜字符串

```
idapro_find_regex(pattern="https?://", limit=20)
idapro_find_regex(pattern="C:\\\\", limit=20)
idapro_find_regex(pattern="error|fail|invalid", limit=30)
idapro_find_regex(pattern="key|password|secret|token", limit=20)
```

### search_text — 反汇编列表内搜文本

```
idapro_search_text(pattern="call    sub_")
idapro_search_text(pattern="xor     eax, eax")
```

### find_bytes — 字节模式（`??` 通配）

```
idapro_find_bytes(patterns=["48 8B 05"], limit=10)
idapro_find_bytes(patterns=["48 89 ?? 24 ??"], limit=10)
idapro_find_bytes(patterns=["CC CC CC CC", "90 90 90 90"], limit=5)
```

### find — 高级搜索

```
idapro_find(type="immediate", targets=["0xDEADBEEF"])
idapro_find(type="string", targets=["password"])
```

---

## 内存与数据读取

```
# 原始字节
idapro_get_bytes(addrs=[{"addr": "0x401000", "size": 64}])

# 字符串
idapro_get_string(addrs=["0x404000", "0x404100"])

# 整数
idapro_get_int(queries=[{"addr": "0x405000", "size": 4}])

# 全局变量
idapro_get_global_value(queries=["g_flag", "g_key_size"])

# 结构体字段
idapro_read_struct(queries=[{"addr": "0x405000", "type": "HEADER"}])

# 找结构体
idapro_search_structs(filter="FILE")
```

---

## 写入与修补

### 注释

```
# 单条
idapro_set_comments(items=[{"addr": "0x401000", "comment": "解密函数入口"}])

# 批量
idapro_set_comments(items=[
    {"addr": "0x401000", "comment": "XOR 解密循环"},
    {"addr": "0x401050", "comment": "密钥初始化"},
    {"addr": "0x4010A0", "comment": "结果校验"}
])

# 追加（保留已有注释）
idapro_append_comments(items=[{"addr": "0x401000", "comment": "补充：密钥长度 16"}])
```

### 重命名

```
# 函数
idapro_rename(batch={"func": [
    {"addr": "sub_401000", "name": "decrypt_payload"},
    {"addr": "sub_402000", "name": "verify_license"}
]})

# 全局变量
idapro_rename(batch={"global": [
    {"addr": "0x405000", "name": "g_encryption_key"}
]})

# 局部变量
idapro_rename(batch={"local": [
    {"func": "decrypt_payload", "old": "v1", "name": "plaintext_buf"}
]})
```

### 汇编级 patch

```
# NOP 掉检测
idapro_patch_asm(items=[{"addr": "0x401050", "asm": "nop"}])

# 改跳转
idapro_patch_asm(items=[{"addr": "0x401060", "asm": "jmp 0x401080"}])

# 强制返回 true
idapro_patch_asm(items=[
    {"addr": "0x401000", "asm": "mov eax, 1"},
    {"addr": "0x401005", "asm": "ret"}
])
```

### 字节级 patch

```
idapro_patch(patches=[{"addr": "0x401050", "bytes": "9090909090"}])
```

---

## 类型系统

```
# 声明结构体
idapro_declare_type(decls=[{
    "name": "PacketHeader",
    "decl": "struct PacketHeader { uint32_t magic; uint16_t type; uint16_t length; uint8_t data[0]; };"
}])

# 给函数设原型
idapro_set_type(edits=[{
    "addr": "sub_401000",
    "type": "int __fastcall decrypt(void *buf, int size, const char *key)"
}])

# 给全局变量设类型
idapro_set_type(edits=[{"addr": "0x405000", "type": "PacketHeader"}])

# 推断 / 查询
idapro_infer_types(addrs=["sub_401000", "sub_402000"])
idapro_type_query(queries=["Packet"])
idapro_type_inspect(queries=["PacketHeader"])
```

---

## 栈帧

```
# 查看栈帧
idapro_stack_frame(addrs=["main", "sub_401000"])

# 声明栈变量
idapro_declare_stack(items=[{
    "func": "sub_401000",
    "offset": -0x20,
    "name": "local_buf",
    "type": "char [32]"
}])

# 删除栈变量
idapro_delete_stack(items=[{"func": "sub_401000", "name": "local_buf"}])
```

---

## 签名

```
# 地址级唯一字节签名
idapro_make_signature(addrs=["0x401000"])

# 函数级签名
idapro_make_signature_for_function(addrs=["decrypt_payload"])

# 引用某地址的代码签名
idapro_find_xref_signatures(addrs=["0x405000"])
```

---

## 进制与导出

### int_convert — 进制转换（必须用它）

```
idapro_int_convert(inputs=["0x401000"])      # hex → dec
idapro_int_convert(inputs=["4198400"])       # dec → hex
idapro_int_convert(inputs=["0xDEAD", "0xBEEF", "12345"])
```

> 任何进制换算都走这个工具，不要自己算。

### export_funcs

```
idapro_export_funcs(addrs=["main", "sub_401000"], format="json")
idapro_export_funcs(addrs=["main", "sub_401000"], format="c_header")
idapro_export_funcs(addrs=["main", "sub_401000"], format="prototypes")
```

### py_eval — 上下文内执行 Python

```
idapro_py_eval(code="import idautils; print(list(idautils.Functions())[:10])")
idapro_py_eval(code="import idc; print(idc.get_segm_name(0x401000))")
idapro_py_eval(code="import ida_funcs; f=ida_funcs.get_func(0x401000); print(f.size())")
```

---

## 场景速查

### 恶意软件分析

```text
1. survey_binary        → 看导入：网络 API？加密？注册表？
2. find_regex("http|socket|connect") → 搜网络相关字符串
3. xrefs_to(字符串地址)  → 定位引用函数
4. decompile(引用函数)   → 读通信逻辑
5. trace_data_flow(加密参数, "backward") → 追密钥来源
6. set_comments + rename → 固化发现
```

### 注册/授权校验分析

```text
1. find_regex("serial|license|register|valid") → 搜校验相关字符串
2. xrefs_to(校验字符串)  → 定位校验函数
3. analyze_function(校验函数) → 理清判定逻辑
4. callgraph(校验函数, 2) → 看上下游调用链
5. patch_asm(条件跳转, "jmp 通过分支") → 按需 patch
```

### CTF 逆向

```text
1. survey_binary        → 确认架构与入口
2. decompile("main")    → 读主逻辑
3. find_regex("flag|correct|wrong") → 定位判定点
4. trace_data_flow(判定点, "backward") → 追踪输入变换
5. Python 辅助计算/解密 → 得 flag
```

### 漏洞分析

```text
1. entity_query(kind="imports", filter="strcpy|sprintf|gets") → 找危险调用
2. xrefs_to(危险函数)   → 找调用点
3. analyze_function(调用点所在函数) → 看上下文
4. stack_frame(函数)    → 确认缓冲区大小
5. trace_data_flow(危险参数, "backward") → 确认输入可控
```

---

## 故障排查

| 报错 | 原因 | 处理 |
|------|------|------|
| `No database bound` | 尚未打开任何文件 | 先执行 `open.ps1` |
| `Failed to open database` | 旧库被锁 | `open.ps1` 自动降级到 Temp 副本 |
| schema 校验失败 | MCP 客户端 BUG | 改用 `open.ps1` 代替 `idalib_open` |
| 工具长时间无响应 | 大文件自动分析中 | 显式加 `-TimeoutSeconds 600` |
| `ERR:timeout`（start.ps1） | 服务器没起来 | 检查 Python / idalib-mcp 安装 |
| 进制换算出错 | 手算出错 | 一律 `idapro_int_convert` |
| 函数名定位不到 | 名称不精确 | `list_funcs` 加 filter 先搜 |
