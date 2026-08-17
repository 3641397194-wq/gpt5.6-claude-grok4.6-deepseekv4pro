---
name: eni-fuzzing-workflow
description: "[DOCUMENTATION ONLY] [仅文档] Coverage-guided fuzzing workflow for local or authorized targets, including harnesses, corpus design, sanitizers, campaigns, minimization, triage, and regression."
---

> 仅文档：本 Skill 提供方法与检查表，不宣称自带可执行脚本。

# 模糊测试工作流

## 适用场景

- 解析器与协议实现的健壮性验证（文件格式、网络报文、序列化格式）
- 本地或授权范围内的二进制与库函数测试
- 已有崩溃样本的复现与最小化
- 修复后的回归验证

## 工作流阶段

### 1. 边界定义

先回答"测什么"：

- 攻击面是文件解析、网络输入、API 参数还是库函数接口
- 输入结构：格式约束、字段长度、校验和、嵌套深度
- 崩溃判据：段错误、断言、sanitizer 报告、超时、内存异常

边界不清楚时，先用少量变异输入摸清输入空间，再定 harness。

### 2. Harness 构建

- 写一个确定性入口：输入进、目标函数跑完、进程退出
- 持久化模式优先（AFL++ 的 `__AFL_LOOP` / libFuzzer 的 `LLVMFuzzerTestOneInput`），比每次 fork 快一个量级
- 记录编译命令、编译器版本、sanitizer 组合

### 3. 语料库与字典

- 种子：少量合法样本即可，宁可小而真实，不要大而雷同
- 字典：从协议字段名、魔数、错误码里提炼 token
- 语料库做去重与最小化后再开跑，省一半时间

### 4. 构建配置

```text
□ ASan: 内存错误首选
□ UBSan: 未定义行为
□ MSan: 未初始化读
□ 组合构建分开跑，报告分开存
```

### 5. 战役管理

- 设定时间预算与覆盖率目标，达标即停
- 长跑前先 checkpoint：语料库、二进制、运行参数、随机种子
- 多核并行时用主从模式，主节点统一去重

### 6. 崩溃处理

- 崩溃输入立即落盘并编号
- 用 `afl-tmin` / `libFuzzer -minimize_crash` 最小化
- 按崩溃栈做根因去重，不要按文件名
- 调试器复现，确认触发路径与利用条件

### 7. 回归化

- 确认的崩溃转成回归测试（corpus 文件 + 期望的 sanitizer 结果）
- 修复后跑全量回归，确认无复燃
- 覆盖率报告归档

## 证据要求

- 命令、版本、哈希、证据路径、假设与验证结果全程留痕
- 长跑前持久化检查点
- 每个崩溃条目绑定：输入文件、崩溃栈、最小化产物、判定结论

## 衔接

- 入口承接 `eni-universal-workflow` 的分类结果
- 收尾交付走 `eni-universal-workflow` 的 deliver 阶段
- 崩溃样本深挖可转 `eni-pentest-workflow` 的逆向车道
