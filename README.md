<div align="center">

<img src="docs/assets/product-icon.png" width="128" alt="冷咖啡软件图标" />

# [gpt5.6-claude-grok4.6-deepseekv4pro](https://github.com/3641397194-wq/gpt5.6-claude-grok4.6-deepseekv4pro)-glm5.3破甲越狱

**冷咖啡 / ColdBrew Zero · 破甲思路 · 越界表达 · 本地优先的 BREAK//OPEN 工作台。**

<p>
  <img src="https://img.shields.io/badge/品牌启动词-冷咖啡-ff8a55?style=for-the-badge&labelColor=090d11" alt="品牌启动词 冷咖啡" />
  <img src="https://img.shields.io/badge/控制词-BREAK%2F%2FOPEN-55d7c3?style=for-the-badge&labelColor=090d11" alt="控制词 BREAK OPEN" />
  <img src="https://img.shields.io/badge/版本-2.1.0-7aa2ff?style=for-the-badge&labelColor=090d11" alt="版本 2.1.0" />
</p>

</div>

---

## 主页预览

<div align="center">
  <img src="docs/assets/hero-breakline-v1.svg" width="940" alt="ColdBrew Zero Breakline 工作台" />
</div>

这是 **gpt5.6-claude-grok4.6-deepseekv4pro-glm5.3破甲越狱** 的原创发布页。冷咖啡是品牌启动词，`BREAK//OPEN` 是工作控制词；主页采用全新断锁蓝图视觉，五个模型席位共用一条清晰工作链。

## 快速运行

### 完整桌面版

桌面版保留工作台形态：启动页、指挥台、五个模型席位、五个工作通道、目标输入、活动流、结果面板、隔离状态和社群入口。

```powershell
cd desktop
npm install
npm start
```

Windows 便携包：`npm run pack:win`。桌面源码和 CLI 共用同一套原创 `BREAK//OPEN` 工作链。

```powershell
python coldbrew.py --activate 冷咖啡 --profile MAX --prompt "把这段需求拆成可执行步骤"
```

省略 `--prompt` 时从标准输入读取。程序只处理命令行或标准输入中明确传入的文本，不扫描本机文件、目录、配置、剪贴板、环境变量或聊天记录。

## BREAK//OPEN 工作链

| 层 | 作用 |
| --- | --- |
| **OBJECTIVE** | 锁定原始目标、格式与完成判据 |
| **CONTEXT** | 保持当前任务所需上下文 |
| **OUTPUT** | 先生成可复制的提示词和执行结构 |
| **CHECK** | 标出缺失项、检查点和下一步 |

<div align="center">
  <img src="docs/assets/hero-breakline-v1.svg" width="940" alt="ColdBrew Breakline 工作链" />
</div>

## 三种档位

- `MAX`：`OBJECTIVE -> CONTEXT -> OUTPUT -> CHECK`
- `FOCUS`：`OBJECTIVE -> OUTPUT`
- `RESEARCH`：`OBJECTIVE -> SOURCES -> CHECK`

控制词与品牌词分离：**冷咖啡**负责启动品牌会话，**BREAK//OPEN**负责选择工作链。

## 五个视觉席位

<div align="center">
  <img src="docs/assets/card-codex-coldbrew.png" width="210" alt="Codex ColdBrew" />
  <img src="docs/assets/card-claude-coldbrew.png" width="210" alt="Claude ColdBrew" />
  <img src="docs/assets/card-grok4.6-coldbrew.png" width="210" alt="Grok ColdBrew" />
  <img src="docs/assets/card-deepseek-harness.png" width="210" alt="DeepSeek Harness" />
  <img src="docs/assets/card-glm5.3-breakline.svg" width="210" alt="GLM 5.3 Breakline" />
</div>

## 架构与通道板

<div align="center">
  <img src="docs/assets/architecture-v9.svg" width="940" alt="ColdBrew 架构图" />
  <img src="docs/assets/blades-board.svg" width="940" alt="ColdBrew 通道板" />
</div>

## 社群入口

<div align="center">
  <img src="docs/assets/qq-group-1-card.png" width="300" alt="QQ 交流群 1057540028" />
  <img src="docs/assets/qq-group-2-card.png" width="300" alt="QQ 专题群 1077074552" />
</div>

| 平台 | 入口 |
| --- | --- |
| QQ 交流群 | `1057540028` |
| QQ 专题群 | `1077074552` |
| Telegram 群 | [@chachachacha99999](https://t.me/chachachacha99999) |
| Telegram 频道 | [@chachachacha99999999](https://t.me/chachachacha99999999) |

## 软件图标

<p align="center"><img src="docs/assets/product-icon.png" width="180" alt="冷咖啡软件图标"></p>

## 原创与隔离

此发布树仅包含 `coldbrew.py`、主页、文档、品牌图和许可证。代码从零编写；输入只来自显式 CLI 参数或标准输入，不读取本机旧项目资料。
