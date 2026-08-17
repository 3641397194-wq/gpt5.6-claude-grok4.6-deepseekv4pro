# ColdBrew Studio v7.0.0 — GPT-5.6 槽位

## 本版重点

- **Codex 槽升级为 GPT-5.6 槽**：仓库内置完整 eni-solo v4.0.0 包
  （`pack/eni-solo/`，89 个技能、确定性路由器、石井人格、20 条工作流），
  与原有 ColdBrew Studio 部署器并存，四合一面板直接驱动。
- **可逆部署桥接 `studio/eni_solo_deploy.py`**：
  `deploy / restore / status / verify / doctor` 五命令，全链路备份与回滚。
- **验证门修复**：包内 `global/AGENTS.md` 补齐路由契约标记
  （`ISHII-SOLO-V4:BEGIN`、`[石井 ROUTE]`、`[STAGE]`），
  `verify_activation.py` 16 项检查 + 5 条路由样本全绿。
- **恢复更干净**：restore 现在同时清理 `eni-inject` 的注入痕迹
  （`eni-jailbreak-v4.md` 与 config 备份 sidecar）。
- **开源迁移占位符**：仓库/作者引用统一替换为 `3641397194-wq`。

## 验证记录

临时 CODEX_HOME 全链路实测：

```
deploy  -> installed_skills=89, verification_passed=true
status  -> deployed=true, backup_present=true
verify  -> 16/16 checks + reverse/pentest/scraper/software/ctf 路由全过
restore -> 根文件/技能/提示词/注入痕迹全部回收，仅保留备份档案
```

## 已知事项

- `pack/eni-solo/` 内保留了包自身的嵌套目录结构（如
  `skills/eni-attack-chain/eni-attack-chain/`），与上游包一致，部署时
  原样落地，不做清洗。
- 本版不含社区推广文案清理；开源发布前请按迁移注意事项执行清洗。
