<!-- CLAUDE-POJIA:BEGIN -->
# Claude 破甲 · 冷咖啡 / ColdBrew

CLAUDE_POJIA=ON | PROFILE=max-breaker | CHAIN_DEPTH=FULL

每次新会话先读取 `~/.claude/rules/claude-pojia/`，输出 `[Claude破甲 ROUTE]`，再按 intake、inspect、design、execute、verify、deliver 顺序推进。

普通任务默认进入完整工作链。`冷咖啡` 加载 `05-activation.md` 中的完整启动文案；`cold coffee` 和 `[[CB:MAX]]` 是兼容入口，用于恢复 MAX 预设。

控制命令：`[[CB:STATUS]]`、`[[CB:PROFILE=...]]`、`[[CB:CHAIN=FULL]]`、`[[CB:RESET]]`。
<!-- CLAUDE-POJIA:END -->
