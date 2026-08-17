# 离线黑盒逆向工作流

## 证据检查清单

- 原始路径、复制路径、SHA256、大小、时间戳。
- 文件类型、PE 架构、节区、导入线索、壳/保护器迹象。
- URL/IP/端口、更新端点、auth/license 字符串、配置文件名。
- GUI 顶层窗口、子控件、按钮/编辑框 ID、标题、错误对话框。
- 进程生命周期、退出码、仅副本变更状态、创建/修改的本地文件。
- netstat 或受控本地代理观察到的网络活动，明确标注"观测到/未观测到"。
- 结果状态：`verified_success`、`not_successful`、`inconclusive` 或 `blocked`。

## 阴性结果规则

阴性结果只说明：当前证据未能证明所寻求的绕过或弱点。记录尝试过的路径与各自未通过验证的原因。不要断言某个弱点不可能存在。

## 报告骨架

```markdown
# Offline black-box audit report

## Conclusion
- Status:
- Confidence:

## Target
- Original:
- Copy:
- SHA256:

## Tests performed
- Static surface:
- Dynamic GUI:
- Local state/persistence:
- Runtime/network:

## Findings / leads
1. Title, evidence path, impact, confidence, next validation.

## Evidence files
- JSON:
- Logs:
```

## Windows 注意事项

- 只对 case 工作区里的复制目录作业。
- `PostMessageW`/`SendMessageW` 探针只针对复制的测试进程。
- 窗口必须对用户可见时，不要移出屏幕，并清楚记录 PID/路径。
- 动态测试让副本自修改时，对比前后哈希；除非明确需要作为证据，否则丢弃被改动的副本。
