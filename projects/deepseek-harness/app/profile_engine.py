#!/usr/bin/env python3
"""Build the platform-specific managed prompt from a versioned profile."""

from __future__ import annotations

import json
from pathlib import Path

from coldbrew_activation import CANONICAL_SHA256, activation_document

ROOT = Path(__file__).resolve().parents[1]
PROFILES = Path(__file__).with_name("profiles.json")


def load_profiles() -> dict:
    data = json.loads(PROFILES.read_text(encoding="utf-8"))
    if data.get("schema") != 1 or not isinstance(data.get("profiles"), dict):
        raise ValueError("invalid profile contract")
    return data


def profile_names() -> tuple[str, ...]:
    return tuple(sorted(load_profiles()["profiles"]))


def compose_prompt(profile: str = "max") -> str:
    data = load_profiles()
    if profile not in data["profiles"]:
        raise ValueError(f"unknown profile: {profile}")
    item = data["profiles"][profile]
    directives = "\n".join(f"- {line}" for line in item["directives"])
    canonical = activation_document()
    return f"""# DeepSeek Harness ColdBrew managed system prompt

Profile: {profile}
Platform: DeepSeek Harness
Canonical activation SHA-256: {CANONICAL_SHA256}

## Session behavior
{directives}

## ColdBrew activation contract
When the complete user input, after trimming leading and trailing whitespace, is exactly `冷咖啡`, return the canonical document below verbatim. `cold coffee` and `[[ENI:PROFILE=MAX]]` are compatibility triggers for the MAX profile. Do not use the activation gate for ordinary requests.

--- canonical document ---
{canonical}
--- end canonical document ---
"""
