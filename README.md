# 冷咖啡 · ColdBrew Hub（四合一破甲面板）

一个窗口，四个工具：**GPT-5.6 / Claude Code / Grok 4.6 / DeepSeek**。

## 启动

双击 `启动面板.bat`（需要 Python 3.10+，请先安装并勾选 Add to PATH）。

## 面板按钮说明

| 按钮 | 作用 |
|---|---|
| **一键部署** | 把对应 ColdBrew 的破甲配置部署进本机代理目录（GPT-5.6→eni-solo 全套技能+路由+提示词，Claude→CLAUDE.md/.claude，Grok/DeepSeek→本地适配器），全程可回滚，部署成功后自动追加验证 |
| **一键启动**（仅 Claude） | 部署后直接带着 max 配置拉起 Claude Code |
| **打开面板** | 打开该工具的原始 Studio GUI（完整功能：预览/验证/恢复/社区） |
| **恢复** | 一键回滚该工具的部署，恢复部署前状态 |
| **打包** | 对该工具打确定性源码包（zip + SHA256），输出到 `release\` |
| **全部部署 / 全部恢复** | 四个工具批量执行 |
| **全部打包发布** | 四个工具批量打包并生成 SHA256SUMS 汇总，GitHub Release 直接用 |

## GPT-5.6 槽位

面板 GPT-5.6 槽驱动 `projects/codex-coldbrew` 内的两个组件：

- `studio/eni_solo_deploy.py` — eni-solo v4.0.0 部署桥接器（deploy/restore/status/verify/doctor，全链路备份回滚）
- `pack/eni-solo/` — 完整越狱包（89 个技能、确定性路由器、石井人格、20 条工作流）

## 目录结构

```
冷咖啡四合一\
  启动面板.bat           → 双击入口
  coldbrew_hub.py        → 主面板（单文件 tkinter）
  pack_release.py        → 确定性打包发布脚本
  release\               → 打包产物（zip + .sha256 + SHA256SUMS）
  projects\
    codex-coldbrew\      → GPT-5.6 槽（ColdBrew Studio v7.0.0 + eni-solo v4.0.0）
    claude-coldbrew\     → Claude 破甲 Studio（v3.1.0）
    grok4.6-coldbrew\    → Grok 4.6 破甲（v1.0.1）
    deepseek-harness\    → DeepSeek 破甲（v1.0.1）
```

> 说明：为控制体积，本包未包含各项目根目录下的 `*-Source.zip` 历史发布包、`.sha256` 校验文件，以及 `dist/`（各项目独立 exe）与 `build/`（PyInstaller 中间产物）。完整备份都在桌面 `完整仓库备份/` 里。

## 注意事项

- 部署操作会修改本机代理配置目录，请先关闭正在运行的代理终端再操作；
- 部署失败时先点 **恢复** 回滚，再看日志定位（底部日志区有完整输出）；
- 新 GitHub 账号上传这些项目前，先看桌面的 `新账户迁移注意事项.md`；
- 仓库作者/链接已统一为 `3641397194-wq`。

## 冷咖啡社区

品牌：**冷咖啡 ColdBrew** —— 四模型破甲，一杯冷咖啡的功夫全部搞定。

| QQ 群：codex 破甲 | QQ 群：codex claude 破甲 |
|---|---|
| 群号 **1057540028** | 群号 **1077074552** |
| <img src="projects/codex-coldbrew/docs/images/qq-group-codex.png" alt="QQ群 1057540028" width="300"> | <img src="projects/codex-coldbrew/docs/images/qq-group-codex-claude.png" alt="QQ群 1077074552" width="300"> |

- 微信群：**冷咖啡破甲社区**（扫码加入）

  <img src="projects/codex-coldbrew/docs/images/codex-group-qr.png" alt="微信群：冷咖啡破甲社区" width="240">

- Telegram 交流群：[@chachachacha99999](https://t.me/chachachacha99999)
- 官方 Telegram 频道：[@chachacha99999999](https://t.me/chachacha99999999)

> 品牌归属与社区入口仅此一处，其余仓库 README 的社区章节与此一致。
