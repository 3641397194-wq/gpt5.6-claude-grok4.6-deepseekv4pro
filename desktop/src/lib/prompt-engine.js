const ACTIVATION_WORD = "冷咖啡";
const CONTROL_WORD = "BREAK//OPEN";

const PROFILES = [
  { id: "max", label: "MAX / 全开", tone: "完整、直接、可继续", stages: ["OBJECTIVE", "CONTEXT", "OUTPUT", "CHECK"] },
  { id: "focused", label: "FOCUS / 聚焦", tone: "短链路、少噪声", stages: ["OBJECTIVE", "OUTPUT"] },
  { id: "builder", label: "BUILDER / 构建", tone: "实现、打包、可复现", stages: ["OBJECTIVE", "BUILD", "CHECK"] },
  { id: "research", label: "RESEARCH / 研究", tone: "来源、证据、分层", stages: ["OBJECTIVE", "SOURCES", "CHECK"] },
  { id: "creative", label: "CREATIVE / 创作", tone: "角色、语气、连续性", stages: ["OBJECTIVE", "VOICE", "OUTPUT"] },
];

const SEATS = [
  { id: "codex", tag: "GPT-5.6", name: "Codex", accent: "#80f0bc", short: "指令层与工作流编排", mark: "01" },
  { id: "claude", tag: "Claude Code", name: "Claude", accent: "#ff9e7a", short: "长会话与规则组织", mark: "02" },
  { id: "grok", tag: "Grok 4.6", name: "Grok", accent: "#5ee7ff", short: "实时信息流与模板", mark: "03" },
  { id: "deepseek", tag: "DeepSeek v4 Pro", name: "DeepSeek", accent: "#7aa2ff", short: "深度推理与会话导出", mark: "04" },
];

const CHANNELS = [
  { id: "REVERSE", label: "拆解", hint: "结构还原 · 依赖 / 伪代码", color: "#e8a872" },
  { id: "UNLOCK", label: "开锁", hint: "校验定位 · 规则 / 状态", color: "#f5d76e" },
  { id: "INFIL", label: "深入", hint: "路径分析 · 入口 / 反馈", color: "#ff6ba8" },
  { id: "HARVEST", label: "采集", hint: "数据整理 · 验证 / 续接", color: "#5ee7ff" },
  { id: "TRAIN", label: "训练", hint: "本地工作流 · 实体 / 视图", color: "#80f0bc" },
];

function profileById(id) {
  return PROFILES.find((item) => item.id === id) || PROFILES[0];
}

function compose({ profile = "max", channel = "ALL", prompt = "" }) {
  const clean = String(prompt).trim();
  if (!clean) throw new Error("请先输入明确目标");
  const selected = profileById(profile);
  const channelLabel = CHANNELS.find((item) => item.id === channel)?.label || "自动选择";
  return {
    ok: true,
    activation: ACTIVATION_WORD,
    control: CONTROL_WORD,
    profile: selected.id,
    channel,
    channelLabel,
    stages: selected.stages,
    text: `${CONTROL_WORD} / ${selected.id.toUpperCase()}\n工作链：${selected.stages.join(" -> ")}\n通道：${channelLabel}\n语气：${selected.tone}\n\n保持用户目标、格式和完成判据；缺失项使用占位符；先输出可执行产物，再列出检查点。\n\n用户目标：${clean}`,
  };
}

function activate({ word, profile, channel, prompt }) {
  if (word !== ACTIVATION_WORD) return { ok: false, error: "启动词不匹配" };
  return compose({ profile, channel, prompt });
}

module.exports = { ACTIVATION_WORD, CONTROL_WORD, PROFILES, SEATS, CHANNELS, compose, activate };

