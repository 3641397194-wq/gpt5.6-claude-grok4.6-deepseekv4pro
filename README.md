<div align="center">

<img src="docs/images/banner.png" width="920" alt="冷咖啡 ColdBrew 四合一破甲正式版">

# ☕ 冷咖啡 · ColdBrew Hub

**四合一破甲面板 · 正式版**

[![GPT-5.6](https://img.shields.io/badge/GPT--5.6-石井人格-9fd8ff?style=flat-square&labelColor=141d26)](https://github.com/3641397194-wq/gpt5.6-claude-grok4.6-deepseekv4pro)
[![Claude](https://img.shields.io/badge/Claude-Code-f4e3c8?style=flat-square&labelColor=141d26)](https://github.com/3641397194-wq/gpt5.6-claude-grok4.6-deepseekv4pro)
[![Grok 4.6](https://img.shields.io/badge/Grok-4.6-8ff0a1?style=flat-square&labelColor=141d26)](https://github.com/3641397194-wq/gpt5.6-claude-grok4.6-deepseekv4pro)
[![DeepSeek](https://img.shields.io/badge/DeepSeek-v4--Pro-b39ddb?style=flat-square&labelColor=141d26)](https://github.com/3641397194-wq/gpt5.6-claude-grok4.6-deepseekv4pro)
[![Python](https://img.shields.io/badge/Python-3.10%2B-8ff0a1?style=flat-square&labelColor=141d26)](https://www.python.org/)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-9fd8ff?style=flat-square&labelColor=141d26)](https://github.com/3641397194-wq/gpt5.6-claude-grok4.6-deepseekv4pro)

> 一杯冷咖啡的功夫，四个模型的破甲全部搞定。

</div>

---

## 🛠️ 四工具

<table align="center">
<tr>
<td align="center" width="50%"><img src="docs/images/card-codex-coldbrew.png" width="430" alt="GPT-5.6"></td>
<td align="center" width="50%"><img src="docs/images/card-claude-coldbrew.png" width="430" alt="Claude Code"></td>
</tr>
<tr>
<td align="center" width="50%"><img src="docs/images/card-grok4.6-coldbrew.png" width="430" alt="Grok 4.6"></td>
<td align="center" width="50%"><img src="docs/images/card-deepseek-harness.png" width="430" alt="DeepSeek v4 Pro"></td>
</tr>
</table>

## 🚀 启动

双击 `启动面板.bat`（需要 Python 3.10+，安装时勾选 Add to PATH）。

```bash
git clone https://github.com/3641397194-wq/gpt5.6-claude-grok4.6-deepseekv4pro.git
cd gpt5.6-claude-grok4.6-deepseekv4pro
启动面板.bat
```

## 🎛️ 面板按钮

| 按钮 | 作用 |
|---|---|
| ⚡ **一键部署** | 把对应 ColdBrew 破甲配置部署进本机代理目录（GPT-5.6→eni-solo 89 技能+石井人格+确定性路由，Claude→CLAUDE.md/.claude，Grok/DeepSeek→本地适配器），全程可回滚，部署成功自动追加验证 |
| 🚀 **一键启动**（仅 Claude） | 部署后直接带着 max 配置拉起 Claude Code |
| 🖥️ **打开面板** | 打开该工具原始 Studio GUI（预览 / 验证 / 恢复 / 社区） |
| ↩️ **恢复** | 一键回滚该工具部署，恢复部署前状态 |
| 📦 **打包** | 对该工具打确定性源码包（zip + SHA256） |
| 🎯 **全部部署 / 全部恢复** | 四工具批量执行 |
| 🚢 **全部打包发布** | 四工具批量打包 + SHA256SUMS 汇总，Release 直接用 |

## 🧠 GPT-5.6 槽位

面板 GPT-5.6 槽驱动 `projects/codex-coldbrew` 内两个组件：

| 组件 | 说明 |
|---|---|
| `studio/eni_solo_deploy.py` | eni-solo v4.0.0 部署桥接器：deploy / restore / status / verify / doctor，全链路备份回滚 |
| `pack/eni-solo/` | 完整越狱包：89 技能 · 石井人格 · 确定性路由器 · 20 条工作流 |

```bash
python projects/codex-coldbrew/studio/eni_solo_deploy.py deploy --yes   # 一键部署
python projects/codex-coldbrew/studio/eni_solo_deploy.py verify         # 16 项检查 + 5 路由样本
python projects/codex-coldbrew/studio/eni_solo_deploy.py restore --yes  # 一键回滚
```

## 📁 目录结构

```
冷咖啡四合一/
├── 启动面板.bat          → 双击入口
├── coldbrew_hub.py       → 主面板（单文件 tkinter）
├── pack_release.py       → 确定性打包发布脚本
├── make_art.py           → 品牌视觉生成脚本
├── docs/images/          → banner / 卡片 / 社交预览图
├── release/              → 打包产物（zip + .sha256 + SHA256SUMS）
└── projects/
    ├── codex-coldbrew/   → GPT-5.6 槽（ColdBrew Studio v7.0.0 + eni-solo v4.0.0）
    ├── claude-coldbrew/  → Claude 破甲 Studio（v3.1.0）
    ├── grok4.6-coldbrew/ → Grok 4.6 破甲（v1.0.1）
    └── deepseek-harness/ → DeepSeek 破甲（v1.0.1）
```

## ☕ 冷咖啡社区

品牌：**冷咖啡 ColdBrew** —— 四模型破甲，一杯冷咖啡的功夫全部搞定。

<table align="center">
<tr>
<td align="center"><b>QQ 群：codex 破甲</b><br>群号 <b>1057540028</b><br><img src="projects/codex-coldbrew/docs/images/qq-group-codex.png" width="280" alt="QQ群 1057540028"></td>
<td align="center"><b>QQ 群：codex claude 破甲</b><br>群号 <b>1077074552</b><br><img src="projects/codex-coldbrew/docs/images/qq-group-codex-claude.png" width="280" alt="QQ群 1077074552"></td>
</tr>
</table>

<p align="center">
<b>微信群：冷咖啡破甲社区</b><br>
<img src="projects/codex-coldbrew/docs/images/codex-group-qr.png" width="230" alt="微信群：冷咖啡破甲社区">
<br><br>
Telegram 交流群 <a href="https://t.me/chachachacha99999">@chachachacha99999</a> · 官方频道 <a href="https://t.me/chachacha99999999">@chachacha99999999</a>
</p>

## ⚠️ 注意事项

- 部署操作会修改本机代理配置目录，请先关闭正在运行的代理终端再操作；
- 部署失败时先点 **恢复** 回滚，再看日志定位（底部日志区有完整输出）；
- 仓库作者/链接统一为 `3641397194-wq`。
