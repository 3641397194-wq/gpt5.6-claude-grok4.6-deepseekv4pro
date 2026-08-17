# 符号迁移 Prompt 模板

## 标准比对 Prompt（直接复制使用）

```text
Below are two snapshots of a function — the first from a reference binary with symbols, the second from a target binary without symbols. They implement the same logic.

Reference function:

**Reference disassembly**
```c
{disasm_for_reference}
```

**Reference pseudo-code**
```c
{procedure_for_reference}
```

Target function to analyze:

**Target disassembly**
```c
{disasm_code}
```

**Target pseudo-code**
```c
{procedure}
```

Task: inside the target function, locate every reference to one of these symbols — {symbol_name_list} — and report each hit as YAML.

Output format:
```yaml
found_vcall:        # indirect call through a virtual table slot
  - insn_va: '0x180777700'          # instruction address carrying the displacement
    insn_disasm: call [rax+68h]     # the full instruction text
    vfunc_offset: '0x68'            # vtable displacement
    func_name: ILoopMode_OnLoopActivate

found_call:         # direct call to a regular function
  - insn_va: '0x180888800'
    insn_disasm: call sub_180999900
    func_name: CLoopMode_RegisterEventMapInternal

found_funcptr:      # reference to a plain function pointer (not a vtable slot)
  - insn_va: '0x180666600'          # must load/reference the pointer target
    insn_disasm: lea rdx, sub_15BC910
    funcptr_name: CLoopMode_OnClientPollNetworking

found_gv:           # reference to a global variable
  - insn_va: '0x180444400'
    insn_disasm: mov rcx, cs:qword_180666600
    gv_name: g_pNetworkMessages

found_struct_offset:  # field access with a displacement (vtables belong in found_vcall, never here)
  - insn_va: '0x1801BA12A'
    insn_disasm: mov rcx, [r14+58h]
    offset: '0x58'
    size: 8
    struct_name: CResourceService
    member_name: m_pEntitySystem
```

Rules: emit an empty YAML when nothing matches. Output nothing except the YAML. Do not include symbols that are unrelated to the list.
```

## 变量填充说明

| 变量 | 来源 | 获取方式 |
|------|------|---------|
| `{disasm_for_reference}` | 旧版 IDA | `idapro_disasm(addr="函数名")` |
| `{procedure_for_reference}` | 旧版 IDA | `idapro_decompile(addr="函数名")` |
| `{disasm_code}` | 新版 IDA | `idapro_disasm(addr="对应地址")` |
| `{procedure}` | 新版 IDA | `idapro_decompile(addr="对应地址")` |
| `{symbol_name_list}` | 旧版提取 | 从 reference 代码中提取所有非 sub_/loc_ 的符号名 |

## 批量调用脚本骨架（Python）

```python
import yaml
import httpx
import json
from pathlib import Path

PROMPT_TEMPLATE = open("prompt-template.txt").read()

def migrate_function(ref_disasm, ref_procedure, target_disasm, target_procedure, symbols, api_url, api_key, model="deepseek-chat"):
    prompt = PROMPT_TEMPLATE.format(
        disasm_for_reference=ref_disasm,
        procedure_for_reference=ref_procedure,
        disasm_code=target_disasm,
        procedure=target_procedure,
        symbol_name_list=", ".join(symbols)
    )

    resp = httpx.post(api_url, json={
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0
    }, headers={"Authorization": f"Bearer {api_key}"}, timeout=60)

    content = resp.json()["choices"][0]["message"]["content"]

    # 提取 YAML 块
    if "```yaml" in content:
        yaml_str = content.split("```yaml")[1].split("```")[0]
    elif "```" in content:
        yaml_str = content.split("```")[1].split("```")[0]
    else:
        yaml_str = content

    return yaml.safe_load(yaml_str)


def apply_results(results, ida_session):
    """将解析后的 YAML 结果应用到 IDA"""
    if not results:
        return

    renames = []
    comments = []

    if "found_call" in results:
        for item in results["found_call"]:
            # 从 insn_disasm 中提取 call target
            # call sub_XXXXXXX → 提取 sub_XXXXXXX 的地址
            renames.append({"addr": item["insn_va"], "name": item["func_name"], "type": "call_target"})

    if "found_funcptr" in results:
        for item in results["found_funcptr"]:
            renames.append({"addr": item["insn_va"], "name": item["funcptr_name"], "type": "funcptr_target"})

    if "found_gv" in results:
        for item in results["found_gv"]:
            renames.append({"addr": item["insn_va"], "name": item["gv_name"], "type": "gv"})

    if "found_vcall" in results:
        for item in results["found_vcall"]:
            comments.append({
                "addr": item["insn_va"],
                "comment": f"vcall: {item['func_name']} @ +{item['vfunc_offset']}"
            })

    if "found_struct_offset" in results:
        for item in results["found_struct_offset"]:
            comments.append({
                "addr": item["insn_va"],
                "comment": f"{item['struct_name']}.{item['member_name']} @ +{item['offset']}"
            })

    return {"renames": renames, "comments": comments}
```

## API 配置建议

```yaml
# 默认用 DeepSeek（便宜）
default:
  api_url: "https://api.deepseek.com/v1/chat/completions"
  model: "deepseek-chat"

# 超大函数回退到 GPT
fallback:
  api_url: "https://api.openai.com/v1/chat/completions"
  model: "gpt-4o"

# 或者用 Claude
alternative:
  api_url: "https://api.anthropic.com/v1/messages"
  model: "claude-sonnet-4-20250514"
```
