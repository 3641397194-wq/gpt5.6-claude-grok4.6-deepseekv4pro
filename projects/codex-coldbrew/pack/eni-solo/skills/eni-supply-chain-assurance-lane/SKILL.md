---
name: eni-supply-chain-assurance-lane
description: "[DOCUMENTATION ONLY] [仅文档] Supply-chain assurance workflow for sequential eni-solo execution."
---

# 供应链保障工作流

> 仅文档：本 Skill 提供阶段方法，不自带审批或打分引擎。

## 定位

面向供应链的按序执行保障车道，阶段固定、顺序执行，适配 eni-solo 串行执行模式。

## 阶段链

`manifest-inventory → sbom → provenance → advisory-match → reachability → build-ci-trust → remediation → regression → verify → deliver`

### 1. manifest-inventory 清单盘点

- 收集项目全部依赖声明：lockfile、构建清单、基础镜像引用
- 输出组件-版本-来源三列表

### 2. sbom 物料清单生成

- 用可用工具生成 SBOM（CycloneDX 或 SPDX）
- 核对 SBOM 与清单盘点的一致性

### 3. provenance 溯源核验

- 检查构建记录、签名与来源声明
- 标记无法溯源的组件

### 4. advisory-match 通告匹配

- SBOM 对 OSV/NVD/GitHub Advisory 匹配
- 输出候选 CVE 列表

### 5. reachability 可达性判定

- 对高严重度条目做路径分析
- 区分"库里有漏洞"与"代码路径触达漏洞"

### 6. build-ci-trust 构建信任

- 检查 CI 配置、密钥管理、Runner 隔离、制品签名

### 7. remediation 修复

- 按可达性与影响排修复优先级
- 给出升级版本或替代方案

### 8. regression 回归

- 升级后重跑构建与测试，确认无破坏

### 9. verify 验证

- 复扫确认告警清除，签名验证通过

### 10. deliver 交付

- 输出：组件清单、SBOM、匹配结果、可达性结论、修复记录

## 工具使用

直接使用环境中已安装的 SBOM、签名、依赖与构建工具，不假设特定产品。

## 衔接

- 深度方法参考 `eni-supply-chain`
- 收尾交付走 `eni-universal-workflow` 的 deliver 阶段
