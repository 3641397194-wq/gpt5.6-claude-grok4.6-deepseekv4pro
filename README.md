# ☕ 冷咖啡 ColdBrew 四合一破甲

<p align="center">
  <img src="docs/images/banner.png" width="880">
</p>

<p align="center"><strong>一杯冷咖啡的功夫，四个模型的破甲全部搞定</strong></p>

<p align="center">
  <a href="https://github.com/3641397194-wq/gpt5.6-claude-grok4.6-deepseekv4pro">
    <img src="https://img.shields.io/badge/GPT--5.6-111827?style=for-the-badge&logo=openai&logoColor=white">
  </a>
  <a href="https://github.com/3641397194-wq/gpt5.6-claude-grok4.6-deepseekv4pro">
    <img src="https://img.shields.io/badge/Claude-D97757?style=for-the-badge&logo=anthropic&logoColor=white">
  </a>
  <a href="https://github.com/3641397194-wq/gpt5.6-claude-grok4.6-deepseekv4pro">
    <img src="https://img.shields.io/badge/Grok%204.6-000000?style=for-the-badge&logo=x&logoColor=white">
  </a>
  <a href="https://github.com/3641397194-wq/gpt5.6-claude-grok4.6-deepseekv4pro">
    <img src="https://img.shields.io/badge/DeepSeek%20v4%20Pro-4D6BFE?style=for-the-badge&logoColor=white">
  </a>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white">
</p>

<p align="center">
  <a href="https://github.com/3641397194-wq/gpt5.6-claude-grok4.6-deepseekv4pro">GitHub 仓库</a>
</p>

---

## 🚀 项目简介

ColdBrew 是一个面向 GPT-5.6、Claude、Grok 4.6 与 DeepSeek v4 Pro 的四合一工作台，提供统一的部署、启动、恢复、打包与发布入口。

它把不同模型的槽位、破甲 Studio、桥接器、工作流和发布目录集中到同一个 Windows 面板中，减少重复配置，让模型切换和环境维护更直接。

## 🖼️ 四模型槽位

<table>
  <tr>
    <td align="center">
      <img src="docs/images/card-codex-coldbrew.png" width="400">
    </td>
    <td align="center">
      <img src="docs/images/card-claude-coldbrew.png" width="400">
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="docs/images/card-grok4.6-coldbrew.png" width="400">
    </td>
    <td align="center">
      <img src="docs/images/card-deepseek-harness.png" width="400">
    </td>
  </tr>
</table>

## 📥 启动

### Windows 快速启动

1. 安装 Python 3.10+。
2. 克隆仓库：

```bash
git clone https://github.com/3641397194-wq/gpt5.6-claude-grok4.6-deepseekv4pro
```

3. 进入仓库目录。
4. 双击 `启动面板.bat`。
5. 根据面板按钮执行部署、启动、恢复或打包操作。

### 启动：双击 启动面板.bat；git clone 上述仓库地址

## 🎛️ 面板按钮表

| 按钮 | 说明 |
|---|---|
| ⚡一键部署 | 自动完成对应模型槽位的部署与初始化。 |
| 🚀一键启动（仅 Claude） | 仅用于启动 Claude 破甲 Studio。 |
| 🖥️打开面板 | 打开 ColdBrew 图形化控制面板。 |
| ↩️恢复 | 将对应槽位恢复到已备份的工作状态。 |
| 📦打包 | 将当前槽位整理并打包为可发布产物。 |
| 🎯全部部署·全部恢复 | 依次完成全部模型槽位的部署与恢复。 |
| 🚢全部打包发布 | 将全部槽位统一打包并生成发布目录。 |

## 🧩 GPT-5.6 槽位

| 模块 | 路径 | 内容 |
|---|---|---|
| 部署桥接器 | `projects/codex-coldbrew/studio/eni_solo_deploy.py` | `deploy/restore/status/verify/doctor，全链路备份回滚` |
| 越狱包 | `projects/codex-coldbrew/pack/eni-solo/` | `89 技能·石井人格·确定性路由器·20 条工作流` |

### GPT-5.6 三条命令

```bash
python projects/codex-coldbrew/studio/eni_solo_deploy.py deploy --yes
python projects/codex-coldbrew/studio/eni_solo_deploy.py verify
python projects/codex-coldbrew/studio/eni_solo_deploy.py restore --yes
```

### 命令说明

| 命令 | 用途 |
|---|---|
| `deploy --yes` | 执行 GPT-5.6 槽位部署并创建必要备份。 |
| `verify` | 检查部署结果、文件状态和桥接器完整性。 |
| `restore --yes` | 从备份恢复 GPT-5.6 槽位状态。 |

## 📁 目录结构

```text
启动面板.bat
coldbrew_hub.py
pack_release.py
make_art.py
make_art_sol.py
docs\
  images\
release\
projects\
  codex-coldbrew=GPT-5.6 槽
  claude-coldbrew=Claude 破甲 Studio
  grok4.6-coldbrew=Grok 4.6 破甲
  deepseek-harness=DeepSeek 破甲
```

## 🛠️ 核心文件

| 文件 | 用途 |
|---|---|
| `启动面板.bat` | Windows 快速启动入口。 |
| `coldbrew_hub.py` | ColdBrew 主面板程序。 |
| `pack_release.py` | 统一打包与发布处理。 |
| `make_art.py` | 生成项目视觉素材。 |
| `make_art_sol.py` | 生成槽位相关视觉素材。 |
| `docs\images\` | 项目图片、Banner 与卡片资源。 |
| `release\` | 打包后的发布产物目录。 |
| `projects\` | 四个模型槽位与对应工具集合。 |

## 🧊 冷咖啡社区

### QQ 群

<p align="center">
  <strong>🐧 codex 破甲 1057540028 ｜ 🐧 codex claude 破甲 1077074552</strong><br>
  <img src="projects/codex-coldbrew/docs/images/qq-group-codex.png" width="340">
  <img src="projects/codex-coldbrew/docs/images/qq-group-codex-claude.png" width="340">
</p>

### 微信群

<p align="center">
  <img src="projects/codex-coldbrew/docs/images/codex-group-qr.png" width="220">
</p>

### Telegram

- ✈️ [@chachachacha99999](https://t.me/chachachacha99999)
- ✈️ [@chachacha99999999](https://t.me/chachacha99999999)---|---|
| `projects/codex-coldbrew/docs/images/qq-group-codex.png` | 1057540028 |
| `projects/codex-coldbrew/docs/images/qq-group-codex-claude.png` | 1077074552 |

### 微信群

<p align="center">
  <img src="projects/codex-coldbrew/docs/images/codex-group-qr.png" width="220">
</p>

### Telegram

- @chachachacha99999
- @chachachacha99999999

## 📦 发布流程

```text
启动面板
   ↓
选择模型槽位
   ↓
一键部署 / 一键恢复
   ↓
状态验证
   ↓
单独打包或全部打包发布
   ↓
release\ 目录
```

## 🔄 推荐使用流程

1. 克隆仓库并确认 Python 版本为 3.10+。
2. 双击 `启动面板.bat`。
3. 首次使用时执行对应槽位的 `⚡一键部署`。
4. 使用 `🖥️打开面板` 进入控制面板。
5. 修改或更新槽位前保留备份。
6. 使用 `↩️恢复` 回滚到稳定状态。
7. 发布前执行 `🎯全部部署·全部恢复` 与状态检查。
8. 使用 `🚢全部打包发布` 生成统一发布产物。

## 📜 仓库

[https://github.com/3641397194-wq/gpt5.6-claude-grok4.6-deepseekv4pro](https://github.com/3641397194-wq/gpt5.6-claude-grok4.6-deepseekv4pro)

<p align="center"><sub>ColdBrew · 四个模型 · 一杯冷咖啡</sub></p>
