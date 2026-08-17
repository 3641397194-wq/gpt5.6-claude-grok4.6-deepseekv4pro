# 来源、原创重构与发布记录

## 输入基线

本仓库的发布基线来自用户提供的 `ENI-ColdBrew-Unlimited-v3.0.1.zip`：

- 原始大小：13,561 bytes
- 原始 SHA-256：`F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246`
- 原始条目：20 个 UTF-8 文本文件

基线包经逐项读取、清单校验与静态扫描后进入 GitHub 发布整理流程。

## v3.0.1 GitHub 发布整理

- 将 Skill 目录统一为 `skills/eni-coldbrew/`。
- 将 Skill frontmatter 对齐为 `name` 与 `description` 两个发现字段。
- 更新 `agents/openai.yaml` 的名称、简介和默认提示词。
- 修复 Windows/Linux 验证脚本中的安装目标路径错误。
- 加入事务式安装、收据式多层升级与逐层回滚测试。
- 加入中英双语 README、亮暗 Hero、架构图、QQ 交流群展示与 GitHub Pages。
- 加入确定性 ZIP 构建、内部/仓库 SHA-256 清单和可复现性验证。
- 将版权人更新为仓库所有者 `3641397194-wq and contributors`。

## v3.1.0 功能参考基线

v3.1.0 额外读取了两份由仓库所有者提供的功能参考包：

| 参考包 | 大小 | 条目 | SHA-256 |
|---|---:|---:|---|
| `黄文部署器(2).zip` | 4,380 bytes | 3 | `F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246` |
| `真心为你渗透逆向工具链Skills包.zip` | 577,165 bytes | 381 | `F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246` |

两份参考包只用于建立功能清单、分类边界和回归用例，没有进入 Git 仓库或发布 ZIP。v3.1.0 使用新的目录结构、JSON 合同、状态模型、配置解析、阶段编排、验证脚本和文档表述独立实现对应能力。

## v3.1.0 原创实现

- 保留短激活词、安装目录和七路由兼容边界。
- 新增 Armor Break MAX 与 Mature M5 双配置引擎，配置之间保持技术语境隔离。
- 新增配置驱动能力图谱和单主路由、单顺序链编排合同。
- 新增配置/能力模拟、自测试、来源哈希与相似度审计。
- 将版本真源、安装、验证、发布、文档和视觉统一到 `v3.1.0`。
- 原创审计报告由发布验证生成，记录哈希和统计指标，不保存参考包正文。

## 参考仓库

[`MDX-Tom/gpt-5.6-instruct`](https://github.com/MDX-Tom/gpt-5.6-instruct) 仅用于参考 README 信息架构、双语展示、Release 组织和视觉呈现。本仓库没有复制其源码、提示词或视觉资产。

## v4.0.0 原创 Studio 重构

v4.0.0 将来源能力重新编排为 `studio/coldbrew_studio.py`、`studio/presets.json` 和
`docs/index.html` 的独立产品层：新的部署状态模型、快照目录、原子写入、配置指针保留、
提示词渲染、CLI/GUI 双入口、四套预设、视觉界面和测试均由本仓库独立实现。来源项目只
提供功能清单、接口观察和回归方向；逐项映射见 [`docs/SOURCE_MAP.md`](docs/SOURCE_MAP.md)。

本版本还新增自定义 `ColdBrew Studio Community License v1.0`，要求源码、构建脚本、来源
映射和署名持续公开，禁止闭源发布、商业售卖、付费托管和去除署名。许可证文本见
[`LICENSE`](LICENSE)。

## v5.0.0 Codex 独立产品重构

v5.0.0 在 v4 可逆部署核心之上建立 Codex 专属桌面产品。新增内容包括固定启动合同模块、
Codex 工作台、任务/文件/目录入口、CLI 发现与启动、本地请求/审查链诊断、真实软件截图、
Codex 专属 ICO、单文件 Windows 构建器、源码/EXE 校验旁车、站点审计、许可审计和标签发布
流水线。Claude 产品不作为运行时依赖，两套仓库继续独立构建与发布。

用户指定的完整启动原文只在 `studio/coldbrew_activation.py` 定义一次；GUI、CLI 与站点检查
共用该合同。固定纯文本 SHA-256 为
`F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246`。

新增 GitHub 研究只使用固定提交的元数据、公开功能说明和许可证建立来源地图。没有下载或
导入外部 Release、源码、提示词、规则、schema、测试夹具、页面结构、图片、图标、截图或
品牌文案。AGPL 项目保持观察级边界；无许可证仓库只记录抽象现象。完整固定提交与独立
实现落点见 [`docs/SOURCE_MAP.md`](docs/SOURCE_MAP.md)。

两个 QQ 二维码由仓库所有者提供：

- `docs/images/qq-group-codex.jpg`，群号 `1057540028`，SHA-256
  `F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246`；
- `docs/images/qq-group-codex-claude.jpg`，群号 `1077074552`，SHA-256
  `F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246`。

本地审查链只覆盖 ColdBrew 应用自身处理的请求和状态，不代表改变任何远端服务端执行策略。

## v5.0.1 可逆部署与发行完整性修正

v5.0.1 保留 v5.0.0 的原创桌面产品边界，修正连续切换多个 Profile 时可能覆盖首次回滚
基线的问题。状态记录现在始终继承第一次部署前的配置哈希、配置快照、提示快照和恢复标志；
四种独立回归场景验证原配置存在、原配置不存在、强制接管用户提示，以及原配置指向同名
用户提示时均能逐字节恢复。

Windows 单文件程序现随包携带 `LICENSE`、`LICENSE_POLICY.md` 和
`THIRD_PARTY_NOTICES.md`，桌面界面提供许可证查看与公开源码入口，CLI 可将三份材料及公开
源码 URL 导出。构建验证会从实际 EXE 执行审查链自检和许可证导出，再与仓库原件逐字节
比对。

本次新增五个固定 GitHub 快照，只将模块化测试、可重复评估、原子配置事务和一键卸载状态
提炼为验证问题。GPL 项目和无许可证项目保持观察级边界；任何外部提示词、源码、schema、
测试数据、UI、图片、文案和发布包继续排除。逐项证据见 [`docs/SOURCE_MAP.md`](docs/SOURCE_MAP.md)。

## 版本

- `v3.0.1` — Codex GitHub publication build，2026-08-02。
- `v3.1.0` — MAX 双引擎与配置驱动全链路 build，2026-08-06。
- `v4.0.0` — ColdBrew Studio 一键部署应用、原创产品站和公开源码社区许可，2026-08-07。
- `v5.0.0` — Codex 独立桌面软件、固定启动合同、本地审查链诊断与双资产发布，2026-08-08。
- `v5.0.1` — 首次回滚基线继承、EXE 许可材料、跨平台确定性源码包与扩展来源审计，2026-08-08。

## v6.0.0 多层行为脑与品牌重构

v6.0.0 从仓库提交 `54ab607242b5c5d249a16352dfe695af0379988b` 开始。写入前建立的 Git bundle 为
`backup/brain-refactor-baseline-20260810/codex5.6-coldbrew-54ab607.bundle`，SHA-256：
`F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246`。

本版本新增 `studio/brain_pack.py`，把本地行为合同拆分到 Codex 支持的主指令、AGENTS 标记区块、
五个 Skills 和两个 Prompts。每个文件单独记录所有权、首次部署基线和部署哈希；切换 Profile
继承第一次安装前的恢复点，恢复时保留用户在区块外或受管文件中的后续修改。

激活规则统一为整条输入逐字等于 `冷咖啡`。GUI、CLI、profile engine、capability router、
toolchain orchestrator 和生成指令均拒绝前后空格、英文、同义词与附加文字。固定原文没有变化，
SHA-256 仍为 `F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246`。

本轮外部研究固定到：

- `MDX-Tom/gpt-5.6-instruct@77e7a649903f9556f2d7bfa0223fa99e123aad52`，MIT；
- `zxr-roro/GPT5.6-5.5-@b18ceb0322d86480df049147e451cfbea5070e20`，顶层未观察到统一许可证。

前者只用于观察预览、所有权、回滚、归档与回归概念；后者只用于观察目录和能力分类。两者的
提示词、源码、Skills、测试、README、图片、状态 schema、脚本和发布产物全部排除。

仓库所有者提供人物原图，公开副本为 `assets/ishii-brand-source.jpg`，SHA-256：
`F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246`。
`scripts/generate_brand_assets.py` 独立生成软件 ICO、应用头像、Pages 人物图与 Codex Hero。
两个 QQ 展示 PNG 由所有者社区图片生成，仅用于群入口展示。Telegram 交流群为
`https://t.me/chachachacha99999`，官方频道为
`https://t.me/chachacha99999999`。新增的 `codex-group-qr.png` 是所有者提供的
微信群二维码原图，固定哈希并只用于社区入口展示。

- `v6.0.0` — 精确冷咖啡门禁、Codex 多层行为脑、石井人格、所有者品牌视觉与新版社区宣传，2026-08-10。

## v6.0.0 当前树原创性证据

当前发布候选树使用 `scripts/originality_audit.py --candidate . --reference ../references --json docs/originality-evidence-v6.json` 直接与当前参考树比较，不依赖历史 ZIP。扫描排除 Git 元数据、备份、构建产物、发布包、许可证和来源台账等非产品噪声；产品实现、测试、Skills、Pages、工作流和产品文档仍在比较范围内。

本次机器可读证据记录 `67` 个候选文本/代码文件和 `916` 个参考文本/代码文件。结果为：同字节文件 `0`、归一化候选行重叠 `0.5118%`、最长连续归一化共同块 `4` 行、外部版权头 `0`，全部低于阈值，结果为 `PASS`。候选树与参考树清单 SHA-256 及完整指标见 [`docs/originality-evidence-v6.json`](docs/originality-evidence-v6.json)；该证据文件包含在源码包中，参考树不包含在源码包中。
