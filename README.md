# ColdBrew 冷咖啡｜四模型工作台

<p align="center">
  <img src="docs/images/banner.png" width="900" alt="冷咖啡四模型工作台">
</p>

<p align="center"><strong>GPT-5.6 / Codex · Claude Code · Grok 4.6 · DeepSeek v4 Pro</strong></p>

<p align="center">
  <a href="#快速开始"><img src="https://img.shields.io/badge/系统-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows 系统"></a>
  <a href="#快速开始"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10 及以上"></a>
  <a href="#社区入口"><img src="https://img.shields.io/badge/版本-ColdBrew%20v8-80F0BC?style=for-the-badge&logoColor=07110D" alt="ColdBrew v8"></a>
</p>

> **项目定位：** 本地配置编排、工作流管理、可复现发布，以及支持回滚的部署工具。

## 主页导航

| 模块 | 入口 | 说明 |
| --- | --- | --- |
| 控制中心 | [`coldbrew_hub.py`](coldbrew_hub.py) | 四模型卡片、环境检查、部署、验证与恢复 |
| Grok 4.6 | [`projects/grok4.6-coldbrew`](projects/grok4.6-coldbrew) | Grok 适配器与统一深色界面 |
| DeepSeek | [`projects/deepseek-harness`](projects/deepseek-harness) | Harness 适配器与导出模板 |
| 发布工具 | [`pack_release.py`](pack_release.py) | 可复现 ZIP、SHA-256 校验和清单 |
| 社区入口 | [QQ / 微信 / Telegram](#社区入口) | 交流、更新与版本公告 |

## 四个模型

<table>
  <tr>
    <td align="center"><img src="docs/images/card-codex-coldbrew.png" width="390" alt="GPT-5.6 Codex 卡片"><br><strong>GPT-5.6 / Codex</strong></td>
    <td align="center"><img src="docs/images/card-claude-coldbrew.png" width="390" alt="Claude Code 卡片"><br><strong>Claude Code</strong></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/images/card-grok4.6-coldbrew.png" width="390" alt="Grok 4.6 卡片"><br><strong>Grok 4.6</strong></td>
    <td align="center"><img src="docs/images/card-deepseek-harness.png" width="390" alt="DeepSeek v4 Pro 卡片"><br><strong>DeepSeek v4 Pro</strong></td>
  </tr>
</table>

## 本次升级

- **ColdBrew Hub v8：** 四模型卡片、状态检查、后台任务、部署验证、打包与恢复。
- **统一工作台：** Grok 4.6 与 DeepSeek Harness 使用同一套深色 Tkinter 界面。
- **可复现发布：** 固定文件顺序，并生成 SHA-256 校验清单。
- **整洁社区入口：** 主页采用紧凑的文字入口，不再堆叠重复二维码。

## 快速开始

1. 安装 Python 3.10 或更高版本，并确认包含 `tkinter`。
2. 克隆仓库：

   ```powershell
   git clone https://github.com/3641397194-wq/gpt5.6-claude-grok4.6-deepseekv4pro.git
   cd gpt5.6-claude-grok4.6-deepseekv4pro
   ```

3. 双击启动文件，或运行：

   ```powershell
   python coldbrew_hub.py
   ```

4. 在控制面板按以下顺序操作：

   ```text
   环境检查 -> 选择模型 -> 预览 -> 部署 -> 验证
   ```

5. 在模型卡片上点击 **恢复**，即可回到已保存的快照。

## 命令行

```powershell
python projects/grok4.6-coldbrew/app/grok_coldbrew.py --home "$env:USERPROFILE\.coldbrew\grok" preview --profile max --json
python projects/grok4.6-coldbrew/app/grok_coldbrew.py --home "$env:USERPROFILE\.coldbrew\grok" deploy --profile max --json
python projects/grok4.6-coldbrew/app/grok_coldbrew.py --home "$env:USERPROFILE\.coldbrew\grok" verify --json
python pack_release.py --all --json
```

## 验证与回滚

```powershell
python -m compileall -q .
python coldbrew_hub.py --selftest
```

部署前先执行预览。每个适配器都会在自己的 `.coldbrew/` 目录保存快照和验证数据。

## 社区入口

> **整洁入口：** 主页只保留文字链接，不展示重复二维码；二维码素材仍保存在仓库资源目录，方便维护者单独取用。

| 渠道 | 入口 | 用途 |
| --- | --- | --- |
| QQ · ColdBrew | **1057540028** | 综合交流 |
| QQ · Codex / Claude | **1077074552** | 模型专项交流 |
| 微信群 | **ColdBrew** | 微信群；入群请联系维护者 |
| Telegram · 交流群 | [加入群组](https://t.me/chachachacha99999) | 提问与社区交流 |
| Telegram · 公告频道 | [订阅频道](https://t.me/chachachacha99999999) | 发布与通知 |

Telegram 群组与频道分开维护：群组用于讨论，频道用于发布版本和公告。

## 仓库结构

```text
coldbrew_hub.py                         # 四模型控制中心
pack_release.py                         # 可复现发布打包工具
docs/images/                            # 横幅、模型卡片与社区素材
projects/shared/coldbrew_ui.py          # 共享工作台界面
projects/codex-coldbrew/                # GPT-5.6 / Codex
projects/claude-coldbrew/               # Claude Code
projects/grok4.6-coldbrew/              # Grok 4.6
projects/deepseek-harness/              # DeepSeek v4 Pro
```

## 许可与说明

请勿将账号凭据、API 密钥和本地配置备份提交到公开仓库。部署前请先阅读项目说明，并保留可回滚的快照。\n# ColdBrew &#x51b7;&#x5496;&#x5561; | Four-model workbench

<p align="center">
  <img src="docs/images/banner.png" width="900" alt="ColdBrew four-model workbench">
</p>

<p align="center"><strong>GPT-5.6 / Codex &middot; Claude Code &middot; Grok 4.6 &middot; DeepSeek v4 Pro</strong></p>

<p align="center">
  <a href="#quick-start"><img src="https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows"></a>
  <a href="#quick-start"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <a href="#community"><img src="https://img.shields.io/badge/ColdBrew-v8-80F0BC?style=for-the-badge&logoColor=07110D" alt="ColdBrew v8"></a>
</p>

> &#x5b9a;&#x4f4d;&#xff1a; local configuration orchestration, workflow management, reproducible releases and rollback-friendly deployment.

## Home navigation | &#x4e3b;&#x9875;&#x5bfc;&#x822a;

| Module | Entry | Purpose |
| --- | --- | --- |
| Hub | [`coldbrew_hub.py`](coldbrew_hub.py) | Four-model cards, environment checks, deploy, verify and restore |
| Grok 4.6 | [`projects/grok4.6-coldbrew`](projects/grok4.6-coldbrew) | Grok adapter and shared dark UI |
| DeepSeek | [`projects/deepseek-harness`](projects/deepseek-harness) | Harness adapter and export templates |
| Release | [`pack_release.py`](pack_release.py) | Reproducible ZIP, SHA-256 and manifest |
| Community | [QQ / WeChat / Telegram](#community) | Updates, discussion and release announcements |

## Four model slots

<table>
  <tr>
    <td align="center"><img src="docs/images/card-codex-coldbrew.png" width="390" alt="Codex ColdBrew"><br><strong>GPT-5.6 / Codex</strong></td>
    <td align="center"><img src="docs/images/card-claude-coldbrew.png" width="390" alt="Claude ColdBrew"><br><strong>Claude Code</strong></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/images/card-grok4.6-coldbrew.png" width="390" alt="Grok 4.6 ColdBrew"><br><strong>Grok 4.6</strong></td>
    <td align="center"><img src="docs/images/card-deepseek-harness.png" width="390" alt="DeepSeek Harness"><br><strong>DeepSeek v4 Pro</strong></td>
  </tr>
</table>

## What changed | &#x8fd9;&#x6b21;&#x5347;&#x7ea7;&#x4e86;&#x4ec0;&#x4e48;

- **ColdBrew Hub v8**: four model cards, status checks, background jobs, deployment verification, packaging and restore.
- **Shared workbench**: Grok 4.6 and DeepSeek Harness use the same dark Tkinter UI.
- **Reproducible releases**: deterministic file order plus SHA-256 manifests.
- **New community home**: QQ, WeChat, Telegram group and Telegram channel have separate cards, links and QR assets.

## Quick start | &#x5feb;&#x901f;&#x5f00;&#x59cb;

1. Install Python 3.10+ with `tkinter`.
2. Clone the repository:

   ```powershell
   git clone https://github.com/3641397194-wq/gpt5.6-claude-grok4.6-deepseekv4pro.git
   cd gpt5.6-claude-grok4.6-deepseekv4pro
   ```

3. Double-click the launcher `.bat` file, or run:

   ```powershell
   python coldbrew_hub.py
   ```

4. Use this order in the panel:

   ```text
   Environment check -> choose model -> preview -> deploy -> verify
   ```

5. Use **Restore** on the model card to return to the saved snapshot.

## Command line

```powershell
python projects/grok4.6-coldbrew/app/grok_coldbrew.py --home "$env:USERPROFILE\.coldbrew\grok" preview --profile max --json
python projects/grok4.6-coldbrew/app/grok_coldbrew.py --home "$env:USERPROFILE\.coldbrew\grok" deploy --profile max --json
python projects/grok4.6-coldbrew/app/grok_coldbrew.py --home "$env:USERPROFILE\.coldbrew\grok" verify --json
python pack_release.py --all --json
```

## Verify and rollback | &#x9a8c;&#x8bc1;&#x4e0e;&#x56de;&#x6eda;

```powershell
python -m compileall -q .
python coldbrew_hub.py --selftest
```

Preview before deployment. Each adapter stores snapshots and verification data in its `.coldbrew/` directory.

## Community | &#x793e;&#x533a;&#x5165;&#x53e3;

<p align="center">
  <img src="docs/images/community-board-v2.png" width="900" alt="ColdBrew community board">
</p>

### QQ groups

<table>
  <tr>
    <td align="center"><a href="projects/grok4.6-coldbrew/docs/images/qq-group-1-v2.png"><img src="docs/images/qq-group-1-v2.png" width="300" alt="QQ group 1057540028"></a><br><strong>ColdBrew QQ</strong><br><code>1057540028</code></td>
    <td align="center"><a href="projects/grok4.6-coldbrew/docs/images/qq-group-2-v2.png"><img src="docs/images/qq-group-2-v2.png" width="300" alt="QQ group 1077074552"></a><br><strong>Codex / Claude</strong><br><code>1077074552</code></td>
  </tr>
</table>

### WeChat group

<p align="center">
  <a href="projects/grok4.6-coldbrew/docs/images/wechat-group.png"><img src="projects/grok4.6-coldbrew/docs/images/wechat-group.png" width="340" alt="WeChat group QR"></a>
</p>

Scan and note **ColdBrew**. QR validity follows the live image; replace the image when it expires.

### Telegram

<table>
  <tr>
    <td align="center"><a href="https://t.me/chachachacha99999"><img src="docs/images/telegram-group-v2.png" width="260" alt="Telegram group QR"></a><br><strong><a href="https://t.me/chachachacha99999">Discussion group</a></strong><br><code>t.me/chachachacha99999</code></td>
    <td align="center"><a href="https://t.me/chachacha99999999"><img src="docs/images/telegram-channel-v2.png" width="260" alt="Telegram channel QR"></a><br><strong><a href="https://t.me/chachacha99999999">Announcement channel</a></strong><br><code>t.me/chachacha99999999</code></td>
  </tr>
</table>

> The Telegram group and channel are intentionally separate: group for discussion, channel for releases and notices.

## Repository layout

```text
coldbrew_hub.py                         # four-model control hub
pack_release.py                         # reproducible release packer
docs/images/                            # banner, model cards and community art
projects/shared/coldbrew_ui.py          # shared workbench UI
projects/codex-coldbrew/                # GPT-5.6 / Codex
projects/claude-coldbrew/               # Claude Code
projects/grok4.6-coldbrew/              # Grok 4.6
projects/deepseek-harness/              # DeepSeek v4 Pro
```

## License and notes

Keep account credentials, API keys and local configuration backups private. Review the repository notes before deploying changes.
