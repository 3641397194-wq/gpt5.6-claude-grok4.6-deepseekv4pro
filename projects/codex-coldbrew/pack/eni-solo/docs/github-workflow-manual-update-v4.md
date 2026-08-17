# GitHub 工作流手动刷新说明

仅在用户明确要求更新时执行：

```bash
python scripts/github_workflow_upgrade.py refresh --package-root . --out-dir <evidence-dir>
```

刷新产出证据目录（diff 与测试记录）。先人工审阅 diff 与测试结果，
确认无误后再运行该脚本输出的显式安装命令。未审阅不安装。
