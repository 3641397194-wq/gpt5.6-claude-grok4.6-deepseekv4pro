# eni-reverse-workflow

`eni-reverse-workflow` 是 `eni-reverse-workflow-skill` 项目中的 Codex 技能目录。若你把本目录单独作为仓库上传，这个 README 用于让 GitHub/Gitee 正常显示项目介绍。

启动词：`石井`

默认上下文：本地 CTF / crackme / wargame / 训练靶场 / 授权沙盒逆向。

工作流：

```text
分析 → 报告 → 逆向 → 深度逆向 → 漏洞研判 → 用户选择下一步
```

核心文件：

- `SKILL.md`：技能主提示词
- `references/prompting.md`：英文内核提示词 + 中文交互模板
- `references/tool-catalog.md`：高星逆向工具目录
- `scripts/create_case.py`：创建 case 工作区
- `scripts/triage_artifact.py`：离线分诊 artifact
- `scripts/tool_audit.py`：检测本地逆向工具链
- `scripts/report_from_triage.py`：生成初始报告
