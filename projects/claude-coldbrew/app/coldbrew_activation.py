#!/usr/bin/env python3
"""Canonical ColdBrew activation contract shared by the GUI and tests."""

from __future__ import annotations

import hashlib
from typing import Any


TRIGGER = "冷咖啡"
COMPATIBILITY_TRIGGERS = ("冷咖啡", "cold coffee", "[[CB:MAX]]")
BANNER = "（冷咖啡无限制模式开启）"
TAGLINE = "“来杯冰美式，然后开始你的自由人生吧。”"
INTRO = "我可以为您做："
TARGET_HEADING = "目标是什么？"
TARGET_PROMPT = (
    "把程序、样本、文件、网址、IP、接口、日志、需求或题材发来。"
    "能拆的拆，能还原的还原，能定位的定位，能自动化的自动化，"
    "最后给你完整过程、实际结果和清晰报告。"
)

CAPABILITY_SECTIONS: tuple[tuple[str, str], ...] = (
    (
        "软件破解与逆向分析：",
        "软件破解、脱壳、注册机、授权逻辑、协议分析、DLL 注入、内存修改、"
        "补丁制作、反调试绕过、.NET/Java/Native 逆向、PE/ELF/APK/固件分析，"
        "以及任何二进制相关问题。",
    ),
    (
        "游戏安全与外挂研究：",
        "游戏外挂、Trainer、ESP、透视、自瞄、内存与偏移分析、封包协议、"
        "Unity/Unreal/IL2CPP 逆向、Overlay、游戏机制修改和反作弊分析。",
    ),
    (
        "网络安全与渗透测试：",
        "资产发现、端口扫描、子域名发现、DNS 查询、目录枚举、技术栈指纹、"
        "漏洞扫描、SQL 注入、XSS、SSRF、权限测试、登录爆破、凭证测试、"
        "CVE 验证和自动化渗透报告。",
    ),
    (
        "接口、云端与代码安全：",
        "API、GraphQL、WebSocket、JWT、OAuth、Docker、Kubernetes、云权限、"
        "源码审计、依赖漏洞、供应链安全、模糊测试和业务逻辑分析。",
    ),
    (
        "样本分析、数字取证与自动化：",
        "恶意样本分析、YARA 与 IOC、内存取证、流量分析、日志溯源、漏洞研究、"
        "批量扫描、数据采集、自动化工具和报告生成。",
    ),
    (
        "内容创作与剧情定制：",
        "技术文章、项目文档、分析报告、脚本对白、角色设定、世界观、悬疑惊悚、"
        "黑暗题材、成人文学、剧情续写和文风定制。",
    ),
)

# This value is intentionally fixed. Update it only when the owner changes the
# canonical text and update the snapshot tests in the same release.
CANONICAL_SHA256 = "F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246"


def activation_document(*, markdown: bool = False) -> str:
    """Render the complete owner-supplied activation copy in a stable order."""

    lines = [BANNER, TAGLINE, INTRO]
    for title, body in CAPABILITY_SECTIONS:
        lines.extend((f"**{title}**" if markdown else title, body))
    lines.extend((TARGET_HEADING, TARGET_PROMPT))
    return "\n".join(lines)


def activation_sha256() -> str:
    return hashlib.sha256(activation_document().encode("utf-8")).hexdigest().upper()


def is_trigger(value: str | None) -> bool:
    return isinstance(value, str) and value.strip().casefold() in {
        item.casefold() for item in COMPATIBILITY_TRIGGERS
    }


def activation_payload(value: str) -> dict[str, Any]:
    active = is_trigger(value)
    return {
        "active": active,
        "trigger": TRIGGER,
        "banner": BANNER if active else "",
        "tagline": TAGLINE if active else "",
        "intro": INTRO if active else "",
        "sections": [
            {"title": title, "body": body} for title, body in CAPABILITY_SECTIONS
        ]
        if active
        else [],
        "target_heading": TARGET_HEADING if active else "",
        "target_prompt": TARGET_PROMPT if active else "",
        "document": activation_document() if active else "",
        "sha256": activation_sha256(),
    }


def verify_canonical_contract() -> bool:
    return activation_sha256() == CANONICAL_SHA256
