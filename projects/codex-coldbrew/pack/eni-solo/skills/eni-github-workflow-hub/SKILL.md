---
name: eni-github-workflow-hub
description: "Official GitHub workflow source catalog and local tool readiness adapter. Use when selecting upstream methods for reverse engineering, web testing, fuzzing, code security, cloud, mobile, memory, or scraping."
---

# 石井 GitHub Workflow Hub

## 定位

官方工作流来源目录与本地工具就绪适配器。为逆向、Web 测试、模糊测试、代码安全、云、移动、内存与采集等工作流提供方法来源索引。

## 使用方式

- 选型矩阵：读 `references/github-sources.md`
- 按工作流过滤来源：

```bash
python scripts/source_catalog.py --workflow reverse --json
```

- 检测本地可用适配器：

```bash
python scripts/tool_adapter.py --workflow fuzzing --json
```

## 收录原则

- 只记录已审阅并锁定的 commit，方法结构按需吸收
- 不 vendor 上游仓库代码
- 安装工具时优先稳定 release 或不可变 commit

## 工作流覆盖

| 工作流 | 主要来源 |
|------|---------|
| reverse | ghidra, frida, capa |
| pentest | nuclei, nuclei-templates, owasp-asvs, owasp-wstg, zaproxy |
| fuzzing | oss-fuzz, aflplusplus |
| code-security | semgrep, trivy, osv-scanner |
| supply-chain | trivy, osv-scanner |
| cloud-container | prowler, trivy |
| scraper | scrapy, playwright-python |
| memory / malware-ir | volatility3, capa |
| mobile | frida, mobsf |

## 工具就绪检查

- `scripts/tool_adapter.py` 输出本机已装适配器清单
- 缺工具时按对应工作流的 bootstrap 路径补齐
- 来源 commit 锁定信息与许可证在引入前确认兼容性

## 衔接

- 上游：`eni-unified-router` 路由结果中标注来源需求的任务
- 下游：各工作流技能按本目录选取方法来源与工具
