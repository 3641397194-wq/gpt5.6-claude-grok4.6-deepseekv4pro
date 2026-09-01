# 冷咖啡 / ColdBrew Zero

从零原创的本地优先提示词工作台。品牌启动词保留为 **冷咖啡**，新版控制词改为 **BREAK//OPEN**。

## 运行

```powershell
python coldbrew.py --activate 冷咖啡 --profile MAX --prompt "把这段需求拆成可执行步骤"
```

程序只处理命令行中明确传入的文本，不扫描本机文件、目录、配置、剪贴板、环境变量或聊天记录。

## 控制词

- `冷咖啡`：启动品牌会话
- `BREAK//OPEN`：进入开放工作流
- `MAX`：OBJECTIVE → CONTEXT → OUTPUT → CHECK
- `FOCUS`：OBJECTIVE → OUTPUT
- `RESEARCH`：OBJECTIVE → SOURCES → CHECK

输出是可复制的会话提示词，不绑定任何模型供应商，也不改写模型权重或客户端设置。

## 社群

- QQ 交流群：`1057540028`
- QQ 专题群：`1077074552`
- Telegram 群：[@chachachacha99999](https://t.me/chachachacha99999)
- Telegram 频道：[@chachachacha99999999](https://t.me/chachachacha99999999)

## 原创与隔离

此发布树由 `coldbrew.py`、`docs/index.html` 和品牌文档组成，未从本机旧仓库复制文件。所有输入只来自显式 CLI 参数或标准输入。

