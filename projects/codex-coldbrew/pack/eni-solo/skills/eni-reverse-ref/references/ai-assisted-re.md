# AI 辅助的逆向分析

> 神经反编译 / 多 Agent 交叉验证 / 语义级恢复
> 近年二进制分析方法论的最大变量

---

## 关键模型与框架

### LLM4Decompile

- 开源领域里最早一批把 LLM 用于「汇编 → C 源码」反编译的框架
- 架构覆盖 x86、ARM、MIPS
- 输入为汇编片段，输出为 C 代码
- 语料基于百万量级的 源码-汇编 对齐数据训练

### Decaf（2026）

- 核心思想是**编译器反馈闭环**：让 LLM 生成源码 → 重新编译 → 与原始二进制做比对，用差异反过来修正生成结果
- 在 ExeBench Real -O2 数据集上把反编译成功率从 26% 拉到 83.9%
- 最重要的启示：迭代验证的收益大于一味增大模型

### 约束引导的多 Agent 反编译（2026）

- 三段式验证流水线：
  1. 语法正确性（能否解析）
  2. 可编译性（过 GCC）
  3. 行为等价性（由 LLM 生成测试输入，对比原程序与新程序的输出）
- 84–97% 的代码可重新执行，单次二进制成本约 $0.03–0.05

### REMEND（2026）

- 定位很专：从二进制里把数学方程挖出来
- 跨 3 种 ISA × 3 档优化级别 × 2 种语言，准确率 89.8–92.4%
- 速度 0.132s/函数，参数量仅 12M

### Glaurung

- 开源 Ghidra 替代品：Rust 内核 + Python 绑定
- **AI 原生架构**：LLM Agent 嵌入每一层分析
- 证据制品输出多种格式（plain/rich/JSON/JSONL）方便 LLM 消费
- 支持 ELF/PE/Mach-O、x86/ARM/RISC-V、IOC 检测与熵分析

---

## 工作流：用 LLM 增强二进制分析

### 1. 快速侦察阶段

```text
□ strings 结果 → 交给 LLM 做语义归类（URL/密钥/路径/协议）
□ 导入表 → 让 LLM 推断功能（加密≈OpenSSL？网络≈libcurl？）
□ 反汇编片段 → 让 LLM 识别模式（密码算法、反调试、虚拟机检测）
□ 报错文案 → 让 LLM 推断语境（"Invalid license" → 授权逻辑在哪）
```

### 2. 神经反编译阶段

```bash
# LLM4Decompile
python llm4decompile.py --binary target.so --arch arm64 --output target.c

# 结果验证（重编译 + 对比行为）
gcc -O2 -o target_recompiled target.c -fPIC -shared
# → 跑相同输入，比对两个版本的输出
```

### 3. 多 Agent 校验阶段

```text
Agent 1（语法）: 生成的 C 能否被 parse
  ↓ 失败 → 把错误信息回填给 LLM 重试
Agent 2（编译）: GCC 编译 → 检查 warnings/errors
  ↓ 失败 → 把编译错误回填给 LLM
Agent 3（行为）: LLM 生成输入 → 原二进制与重编译版各跑一遍 → 对比输出
  ↓ 不一致 → 把差异回填给 LLM → 迭代修正
```

### 4. LLM 辅助静态分析

```text
□ 函数重命名: 伪代码输入 → LLM 给出语义化命名
□ 类型恢复: 结合上下文 → LLM 推断结构体/类定义
□ 算法识别: 汇编片段 → LLM 判断 AES/TEA/RC4/自定义
□ 协议逆向: 网络包序列 → LLM 推断协议格式
□ 注释生成: 反编译代码 → LLM 生成中文/英文注释
```

### 5. macOS/iOS 私有框架逆向（MOTIF）

```text
痛点: macOS 私有框架没有文档，类型信息缺失
思路: 用 LLM 分析调用模式 → 推断方法签名与参数类型
效果: ObjC 签名恢复率从静态分析的 15% 提升到 86%
```

---

## LLM Prompt 模板

### 函数语义分析

```
You are a reverse engineering expert. Analyze this decompiled function:

[伪代码]

1. What does this function do? (one sentence)
2. Suggest a meaningful function name.
3. What are the input parameters and their likely types?
4. What is the return value?
5. What external APIs/functions does it depend on?
6. Any security-relevant operations (crypto, auth, network, file I/O)?
```

### 算法识别

```
Analyze this assembly/disassembly for cryptographic operations:

[汇编代码]

1. Is this a known cryptographic algorithm? (AES/DES/RC4/TEA/ChaCha20/custom?)
2. Identify the key schedule and round structure.
3. What is the key size?
4. Are there any hardcoded constants that identify the algorithm?
```

### 协议格式推断

```
Given this network packet sequence, infer the protocol structure:

[hex dump]

1. Identify magic bytes and length fields.
2. Propose a struct definition for the packet header.
3. What field(s) appear to be checksums/CRCs?
4. Is this a known protocol or custom?
```

---

## 工具选型

| 场景 | 推荐工具 | 成本 |
|------|---------|------|
| 快速反编译 | LLM4Decompile | 免费（本地 GPU） |
| 高精度反编译 | 约束引导多 Agent | ~$0.05/二进制 |
| 数学函数提取 | REMEND | 免费 |
| 全平台 RE | Glaurung（Rust） | 免费开源 |
| 通用 LLM 交互 | Claude API / GPT-4 / DeepSeek | ~$0.01–0.10/次 |

---

## 现阶段短板

- **复杂控制流**：虚拟化/混淆代码依旧困难（平坦化、VMProtect）
- **间接调用**：虚函数表、函数指针的恢复有限
- **内联函数**：被编译器内联后边界消失
- **浮点/向量化**：SIMD 指令的语义恢复有待提升
- **上下文窗口**：超长函数（>1000 行）超出 LLM 输入限制

Source: Decaf (2026), REMEND (2026), Constraint-Guided Multi-Agent Decompilation (2026), LLM4Decompile, Glaurung
