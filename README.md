# 冷咖啡 ColdBrew · 四模型工作台

<p align="center">
  <img src="docs/images/banner.png" width="900" alt="ColdBrew 四模型工作台">
</p>

<p align="center"><strong>一套面板，管理 GPT-5.6、Claude Code、Grok 4.6 与 DeepSeek v4 Pro</strong></p>

<p align="center">
  <a href="#快速开始windows"><img src="https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows"></a>
  <a href="#发布源码包"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <a href="#社区入口"><img src="https://img.shields.io/badge/ColdBrew-v8-80F0BC?style=for-the-badge&logoColor=07110D" alt="ColdBrew v8"></a>
</p>

> **定位**：本地配置编排、工作流管理和可回溯发布工具。所有部署动作都支持预览、验证和恢复。

## 主页导航

| 模块 | 入口 | 作用 |
| --- | --- | --- |
| 控制台 | [`coldbrew_hub.py`](coldbrew_hub.py) | 四模型卡片、环境自检、部署、验证、恢复 |
| Grok 4.6 | [`projects/grok4.6-coldbrew`](projects/grok4.6-coldbrew) | 独立适配器与深色工作台 |
| DeepSeek v4 Pro | [`projects/deepseek-harness`](projects/deepseek-harness) | Harness 适配器与导出模板 |
| 发布器 | [`pack_release.py`](pack_release.py) | 生成四个独立 ZIP、SHA-256 和总清单 |
| 社区 | [QQ群 / 微信群 / Telegram](#社区入口) | 获取更新、交流问题、扫码加入 |

## 四个模型槽位

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

## 这次升级了什么

- **ColdBrew Hub v8**：四模型卡片、状态检查、后台任务、部署后验证、全量打包和恢复。
- **统一工作台**：Grok 4.6 与 DeepSeek Harness 接入共享的深色 Tkinter UI，预览、部署、验证、恢复、导出模板一套操作完成。
- **保留原入口**：原有配置目录、事务式部署、快照和恢复逻辑保持兼容。
- **可回溯发布**：打包器按固定排序和 SHA-256 生成可复现源码 ZIP。
- **社区主页重排**：QQ群、微信群、Telegram 交流群和频道集中展示，二维码与链接分开维护。

## 快速开始（Windows）

1. 安装 Python 3.10+，确认安装包包含 `tkinter`。
2. 克隆仓库：

   ```powershell
   git clone https://github.com/3641397194-wq/gpt5.6-claude-grok4.6-deepseekv4pro.git
   cd gpt5.6-claude-grok4.6-deepseekv4pro
   ```

3. 双击 `启动面板.bat`，或运行：

   ```powershell
   python coldbrew_hub.py
   ```

4. 在面板中按这个顺序操作：

   ```text
   环境自检 → 选择模型 → 预览 → 部署 → 验证
   ```

   出现异常时，直接点击对应卡片的 **恢复** 回到快照状态。

## 命令行入口

四个适配器都支持 `preview`、`deploy`、`verify`、`restore`、`status`、`community` 和 `export`。

```powershell
python projects/grok4.6-coldbrew/app/grok_coldbrew.py --home "$env:USERPROFILE\.coldbrew\grok" preview --profile max --json
python projects/grok4.6-coldbrew/app/grok_coldbrew.py --home "$env:USERPROFILE\.coldbrew\grok" deploy --profile max --json
python projects/grok4.6-coldbrew/app/grok_coldbrew.py --home "$env:USERPROFILE\.coldbrew\grok" verify --json
```

`--home` 用来指定目标配置目录；建议先用临时目录预览，再部署到真实目录。

## 发布源码包

```powershell
python pack_release.py --all --json
```

输出位于 `release/`，包括四个项目 ZIP、每个 ZIP 的 `.sha256` 文件和总校验清单。ZIP 不包含 `.git`、缓存、日志、编译产物或旧 ZIP。

## 验证与回滚

```powershell
python -m compileall -q .
python coldbrew_hub.py --selftest
```

部署前先点 **预览变更**；出现异常时点对应卡片的 **完整恢复**。每个适配器的 `.coldbrew/` 状态目录用于保存快照和校验信息，请不要手工删除。

## 社区入口

<p align="center">
  <img src="docs/images/community-board.png" width="900" alt="冷咖啡社区入口总览">
</p>

### QQ 群

<table>
  <tr>
    <td align="center"><a href="projects/grok4.6-coldbrew/docs/images/qq-group-1.png"><img src="projects/grok4.6-coldbrew/docs/images/qq-group-1.png" width="220" alt="QQ群 1057540028"></a><br><strong>冷咖啡破甲</strong><br><code>1057540028</code></td>
    <td align="center"><a href="projects/grok4.6-coldbrew/docs/images/qq-group-2.png"><img src="projects/grok4.6-coldbrew/docs/images/qq-group-2.png" width="220" alt="QQ群 1077074552"></a><br><strong>Codex / Claude</strong><br><code>1077074552</code></td>
  </tr>
</table>

### 微信群

<p align="center">
  <a href="projects/grok4.6-coldbrew/docs/images/wechat-group.png"><img src="projects/grok4.6-coldbrew/docs/images/wechat-group.png" width="300" alt="微信群二维码"></a>
</p>

扫码后备注 **“冷咖啡”**。微信群二维码有效期以图片实际提示为准，失效后会在仓库中替换新图。

### Telegram

<table>
  <tr>
    <td align="center"><a href="https://t.me/chachachacha99999"><img src="docs/images/telegram-group.png" width="240" alt="Telegram 交流群二维码"></a><br><strong><a href="https://t.me/chachachacha99999">交流群 @chachachacha99999</a></strong></td>
    <td align="center"><a href="https://t.me/chachachacha99999999"><img src="docs/images/telegram-channel.png" width="240" alt="Telegram 频道二维码"></a><br><strong><a href="https://t.me/chachachacha99999999">频道 @chachachacha99999999</a></strong></td>
  </tr>
</table>

> Telegram 交流群和频道是两个独立入口：交流群用于讨论，频道用于发布版本和公告。

## 目录结构

```text
coldbrew_hub.py                         # 四模型控制台
pack_release.py                         # 可复现源码打包器
docs/images/                            # 主页横幅、模型卡片、社区总览和 Telegram QR
projects/shared/coldbrew_ui.py          # 共享工作台 UI
projects/codex-coldbrew/                # GPT-5.6 / Codex
projects/claude-coldbrew/               # Claude Code
projects/grok4.6-coldbrew/              # Grok 4.6
projects/deepseek-harness/              # DeepSeek v4 Pro
```

## 许可证与说明

本仓库是本地配置编排和 UI 工具集合。使用前请阅读 `AUTHORIZATION.md`、`SECURITY_AUDIT.md` 和 `THIRD_PARTY_NOTICES.md`，并自行保管账号、密钥和本地配置备份。
