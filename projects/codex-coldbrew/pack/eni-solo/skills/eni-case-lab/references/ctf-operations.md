# CTF 作战规范

## 案件启动

1. 用 `scripts/new_case.py` 建案件。
2. 未改动的题目输入进 `artifacts/original/`。
3. 每个文件用 `scripts/hash_artifact.py` 登记哈希。
4. `notes.md` 记录：分类、flag 格式、远端端点、架构、保护机制、运行环境与工具版本。

## 分类分诊

- Reverse: 文件类型、架构、字符串、导入、入口、壳、关键函数、常量。
- Pwn: `file`、`checksec`、崩溃复现、cyclic 偏移、libc/loader、原语与稳定性。
- Web: 路由、请求、JavaScript、框架、认证状态、对象 ID、解析器差异、自动化矩阵。
- Crypto: 参数、关系、oracle 行为、已知明文、nonce/IV 复用、候选攻击分类。
- Forensics: 原始哈希、时间线、分区、进程、网络流、carving 目标、提取的指标。
- Mobile: 包元数据、清单、Java/native 分工、导出组件、目标方法、运行跟踪。

## 求解工程

- 完整脚本存 `scripts/`，捕获输出存 `evidence/`。
- 脚本带本地/远程开关、超时、重试、断言、确定性解析与 flag 格式检查。
- 失败的假设简短记录，避免重复尝试。
- 精确命令与环境依赖原样保存。

## 收尾

`output/` 存放：flag/结果、最终求解脚本、验证命令、证据索引与简明 Writeup。
