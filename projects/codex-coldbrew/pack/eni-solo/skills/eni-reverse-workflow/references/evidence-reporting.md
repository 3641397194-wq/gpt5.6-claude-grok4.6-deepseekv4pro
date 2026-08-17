# 证据与报告

## 初始报告模板

```markdown
# Reverse Engineering Initial Report

## Summary
- Artifact:
- Scope:
- Current phase:
- Overall risk:

## Artifact inventory
| Name | Path | Size | SHA-256 | Type | Notes |
|---|---|---:|---|---|---|

## Verified facts
| ID | Evidence | Source/offset/tool | Interpretation | Confidence |
|---|---|---|---|---|

## Key findings
### Finding 1: <title>
- Evidence:
- Impact:
- Confidence:
- Validation status:

## Unknowns
-

## Recommended next steps
1.
2.
3.
```

## 深度逆向报告模板

```markdown
# Deep Reverse Engineering Report

## Executive summary
## Scope and artifacts
## Methodology
## Architecture and behavior model
## Function/module map
## Data-flow and trust boundaries
## Dynamic observations
## Vulnerability candidates
## Evidence appendix
## Reproducibility notes
## Recommended next steps
```

## 漏洞通报模板

```markdown
# Vulnerability Report: <title>

## Summary
## Affected product/version/component
## Severity and rationale
## Preconditions
## Root cause
## Technical details
## Safe reproduction evidence
## Impact
## Remediation guidance
## Detection/mitigation
## Evidence appendix
## Timeline/status
```

## 置信度用语

- **High**：代码或运行时直接观测到，且可复现。
- **Medium**：多条静态指标支撑，但未完整执行验证。
- **Low**：证据有限的合理假设。

## 证据表规范

使用稳定标识符。附上偏移、函数名、命令输出、哈希、日志摘录、截图或追踪记录。原始日志留在 case 目录，报告里只摘录相关行。
