# ColdBrew Suite v8 升级记录

## 改动范围

- 根控制台 `coldbrew_hub.py` 重写为 v8 控制台：四模型卡片、后台任务、部署后验证、全量打包、环境自检和恢复入口。
- 新增 `projects/shared/coldbrew_ui.py`，统一 Grok 4.6 与 DeepSeek Harness 的 Tkinter 工作台。
- Grok 与 DeepSeek 的原有 CLI、profile、快照、部署和恢复函数保持不变，只替换 GUI 入口。
- 共享 UI 依赖已由 `pack_release.py` 自动随 Grok/DeepSeek 项目 ZIP 打包，单独解压也能运行。
- README 改为 UTF-8 简体中文，并补齐安装、命令行、打包、验证和回滚说明。

## 验证记录

```text
python -m compileall -q .                         PASS
python coldbrew_hub.py --selftest                  PASS (4/4 CLI + GUI)
9 个项目 unittest 文件逐一执行                    PASS (54 tests)
Grok/DeepSeek 临时目录 preview/deploy/verify/restore PASS
Grok/DeepSeek standalone ZIP --help                PASS
python pack_release.py --all --json                PASS
```

最新发布目录：`release-20260818b/`

```text
claude-coldbrew-v3.1.0-source.zip       SHA256 166f2c4128b1e5bfb9f5e279f9fe27311db9443c979afeaa69c57892172dc092
codex-coldbrew-v7.0.0-source.zip        SHA256 42daac08f34267f5b30da744e4013ce8df2f27d651b41b1da59bedbe2a844fe3
deepseek-harness-v1.0.1-source.zip      SHA256 5f76294bc557bdbb5415c49dfbba2425a6b0c0b5863b7d8b9cb88fc766742eba
grok4.6-coldbrew-v1.0.1-source.zip      SHA256 3b2f22367ad43c46507f964c27735089b7153af49897af0eb54a5fdea7629732
```

## 回滚

1. 升级前保留原仓库目录或旧 ZIP。
2. 仅回滚界面时，用旧版 `coldbrew_hub.py` 和两个适配器入口替换对应文件。
3. 运行对应适配器的 `restore`，例如：

   ```powershell
   python projects/grok4.6-coldbrew/app/grok_coldbrew.py restore --profile max
   python projects/deepseek-harness/app/deepseek_harness.py restore --profile max
   ```

4. 运行 `verify`，确认快照和托管文件校验恢复正常。
