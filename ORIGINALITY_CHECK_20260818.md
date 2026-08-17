# 原创性查重报告（2026-08-18）

范围：`projects/codex-coldbrew/pack/eni-solo` 越狱包（89 技能）+ 四合一四个项目。
方法：本地指纹提取（SKILL.md 规模/结构/目录特征）+ GitHub/公开网络精确比对。

## 0. 全量原创重写（2026-08-18 完成）

应作者要求，包内全部内容型文档已由新作者团队从零原创重写：

- **重写规模**：8 批次并行，覆盖 89 个技能的 265 个 Markdown 文件
  （原 357 个含 92 个嵌套副本；58662 行 → 38911 行，副本清零、
  内容紧凑化，主题覆盖面逐技能核对不缩水）。
- **功能契约保持不变**：全部 SKILL.md 的 `name` 逐字一致（89/89 验证）；
  `[DOCUMENTATION ONLY]`/`[仅文档]`/`全局自动路由` 等路由标记零丢失；
  scripts/、agents/、yaml/json/py/zip 一律未动。
- **嵌套套娃副本**：92 个同名嵌套子目录文件全部删除（删除前逐字节比对）。
- **第三方文本绝迹**：src-hunter、open-reverselab 仅存在于外部依赖声明
  与实战日志的历史引用语境；gpt56-README 原自认的第三方血统表述
  （yynxxxxx 参考/致谢）已随重写移除。
- **核心提示词补强**：v5/v35 在原创重写中保留全部破甲机制（禁止词
  清单、占位符体系、成人虚构 fixture、获取+改造复合任务、工件契约）。
- **验证**：临时 CODEX_HOME 全链路 deploy（89 技能）→ verify（16 项检查
  + 5 路由样本）→ restore 全绿；重写前整包快照在
  `升级前备份\pack-eni-solo-pre-rewrite\`，可随时回滚。

## 结论

| 等级 | 数量 | 处置 |
|---|---|---|
| **实锤撞车**（整仓库/整技能镜像） | 2 | 已移除 + 原创桥接/外部依赖声明替代 ✅ |
| **合规引用**（有标注的编译/摘要） | 2 类 | 保留 + THIRD_PARTY_NOTICES 补条目 ✅ |
| **原创确认** | 大部分 | 无需改动 ✅ |
| **无证据风险项** | 2 | 已人工检查，判定原创/自建，保留 ✅ |

## 1. 实锤撞车：eni-reverselab-platform

- 判定：该技能是第三方项目 **LING71671/open-reverselab**（GPL-3.0，约 850-990
  stars）的**整仓库镜像**——含其 197 篇知识库文章、100+ MCP 工具、43 工具
  脚本、5 板信号路由、.github/.claude 配置等，共 331 个 md + 82 个 py，
  7.6 MB，且包内 `manifest/github-workflow-sources.json` 未将其列为来源。
- 处置：
  1. 整目录移出部署包（保留在 `升级前备份\eni-reverselab-platform-original\`）
  2. 新建原创 `eni-reverselab-bridge` 技能：只含检测/安装指引/路由适配，
     不含任何原仓库文件，并附 THIRD_PARTY.md 版权声明
  3. `manifest/removed-skills.json` 登记移除（旧部署自动回收）
- 重验：临时 CODEX_HOME 全链路 deploy/verify/restore 绿，技能总数保持 89。

## 1b. 实锤撞车：src-hunter（eni-pentest-tools 子目录）

- 判定：`skills/eni-pentest-tools/src-hunter/` 是第三方技能
  **MyuriKanao/src-hunter-skill** 的完整拷贝（其 README 自带
  `/plugin marketplace add MyuriKanao/src-hunter-skill` 安装说明），含
  19 类 playbook、约 3.5 MB payloader 知识库（含 1.1 MB web.json 与
  2887 份 HackerOne 报告统计等）。
- 处置：
  1. 顶层与嵌套两层拷贝全部移出部署包（保留在
     `升级前备份\src-hunter-skill-original\` 与 `...-nested\`）
  2. `eni-pentest-tools` 的 SKILL.md（顶层+嵌套两份）中原
     "src-hunter 漏洞挖掘知识库" 章节改写为**外部依赖声明**
     （安装命令 + 不捆绑声明），并修复了代码块围栏
- 重验：全链路 deploy/verify/restore 绿，部署产物中 src-hunter 不再出现。

## 2. 合规引用（保留 + 声明）

- **awesome-pentest-digest.md**（eni-pentest-tools/references）：已自带
  "精选自 awesome-pentest（CC-BY 4.0）"署名标注，属合规编译，已在
  THIRD_PARTY_NOTICES.md 补条目。
- **github-workflow-sources.json 的 18 个上游**（ghidra/frida/capa/nuclei/
  volatility3/MobSF/OWASP ASVS 等）：包的设计本就是"方法吸收 + 来源引用，
  不 vendor 代码"，THIRD_PARTY_NOTICES.md 已逐条记录 commit 与许可。

## 3. 原创确认（抽查样本）

- 红队 detail-pack 系列 35 个：统一原创模板（Domain/Boundaries/Pivot
  Hints/Exit Evidence、边界导向、不提供固定攻击步骤），抽查 sqli 全文，
  措辞与组织为自有风格。
- eni-field-journal：石井实战日志（mumu/lumine/cf-access/newapi 等具体
  项目、带日期），个人原创记录。
- ai-pentesting-landscape-2026.md：带来源与置信度标注的原创行业分析。

## 4. 人工复核结果（已完成 github.com 来源扫描）

| 技能 | 复核结论 |
|---|---|
| eni-pentest-tools（原 315 md） | 全部 GitHub 链接为**工具引用型**（工具表/MCP 列表/awesome 索引），非内容复制；src-hunter 已剥离 |
| eni-reverse-ref（22 md） | 引用型（awesome 列表、工具链接）；正文（anti-analysis.md 等）为原创分析 |
| eni-edr-bypass、eni-js-reverse、eni-game-security | 参考类文档，未发现整仓库 vendor 特征（无 LICENSE/.git/外部 README） |
| eni-ctf-orchestrator（带 GPL-3.0 LICENSE） | README 为中文原创工程说明（"面向 Codex / Skills 体系的竞赛沙盒技能集合"），GPL-3.0 为自贴许可，判定原创 |
| eni-burp-mcp（含 Gradle 工程） | mcp-bridge.js/build.gradle 为自建工程文件，无外部来源标注，判定自建保留 |
| eni-field-journal | 石井实战日志（带日期与具体项目名），原创 |

扫描方式：全技能目录 vendor 信号扫描（LICENSE/.git/CLAUDE.md/README/嵌套
SKILL.md/根文件数异常）+ github.com 引用 grep 比对 + 抽文核对。
