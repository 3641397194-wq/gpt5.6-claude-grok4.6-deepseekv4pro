# 冷咖啡 ColdBrew · 四模型工作台

<p align="center">
  <img src="docs/images/banner.png" width="880" alt="ColdBrew banner">
</p>

<p align="center"><strong>一套面板，管理 GPT-5.6、Claude Code、Grok 4.6 与 DeepSeek v4 Pro</strong></p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white">
  <img src="https://img.shields.io/badge/ColdBrew-v8-80F0BC?style=for-the-badge&logoColor=07110D">
</p>

## 这次升级了什么

- **ColdBrew Hub v8**：四模型卡片、状态检查、后台任务、部署后验证、全量打包和恢复。
- **统一工作台**：Grok 4.6 与 DeepSeek Harness 接入共享的深色 Tkinter 工作台，预览、部署、验证、恢复、导出模板一套操作完成。
- **保留原契约**：不改底层快照、事务式部署、恢复逻辑和冷咖啡兼容入口。
- **可回溯发布**：打包器按固定时间戳、排序和 SHA-256 生成可复现源码 ZIP。

## 快速开始（Windows）

1. 安装 Python 3.10 或更高版本，并确保包含 `tkinter`。
2. 克隆仓库：

   ```powershell
   git clone https://github.com/3641397194-wq/gpt5.6-claude-grok4.6-deepseekv4pro.git
   cd gpt5.6-claude-grok4.6-deepseekv4pro
   ```

3. 双击 `启动面板.bat`，或执行：

   ```powershell
   python coldbrew_hub.py
   ```

4. 在面板中先点 **环境自检**，再按模型卡片执行预览、部署和验证。所有操作完成后都可以点 **恢复** 回到快照状态。

## 命令行入口

四个适配器都支持 `preview`、`deploy`、`verify`、`restore`、`status`、`community` 和 `export`。例如：

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

## 目录结构

```text
coldbrew_hub.py                    # 四模型控制台
pack_release.py                     # 可复现源码打包器
projects/shared/coldbrew_ui.py     # 共享工作台 UI
projects/codex-coldbrew/            # GPT-5.6 / Codex
projects/claude-coldbrew/           # Claude Code
projects/grok4.6-coldbrew/          # Grok 4.6
projects/deepseek-harness/          # DeepSeek v4 Pro
```

## 验证与回滚

```powershell
python -m compileall -q .
python coldbrew_hub.py --selftest
```

部署前先点 **预览变更**；出现异常时点对应卡片的 **完整恢复**。每个适配器的 `.coldbrew/` 状态目录用于保存快照和校验信息，请不要手工删除。

## 社区入口

仓库内的 `projects/*/docs/images/` 保存 QQ、微信群二维码和发布板图片。二维码以项目目录为准，避免把个人联系方式硬编码进程序。

## 许可证与说明

本仓库是本地配置编排和 UI 工具集合。使用前请阅读 `AUTHORIZATION.md`、`SECURITY_AUDIT.md` 和 `THIRD_PARTY_NOTICES.md`，并自行保管好账号、密钥和本地配置备份。
