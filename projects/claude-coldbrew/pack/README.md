# Claude 破甲 · 冷咖啡 Pack

这是可手动导入 Claude Code 的只读规则包。推荐使用根目录的 Studio 预览与安装器；手动方式适合把规则先审阅，再复制到用户级 `~/.claude/rules/claude-pojia/` 和 `~/.claude/CLAUDE.md`。

品牌：**冷咖啡 / ColdBrew**  
主产品：**Claude 破甲**

规则包只改变本地 Claude Code 指令上下文，不修改 Claude Code 二进制、凭证、网络配置或远端服务。完整安装、哈希、备份、恢复和卸载由 `app/claude_pojia.py` 负责。

`pack/` 只保留可人工阅读的 CLAUDE.md 与七个基础 Rules。v3 的五个 Skills、一个石井 Agent 和两个 Commands 由 `app/brain_layers.py` 在预览/部署时确定性生成，并由状态清单逐文件验证和恢复。只有整条用户消息逐字等于 `冷咖啡` 才加载完整固定合同；任何空格、英文、同义词或附加文字均不激活。
