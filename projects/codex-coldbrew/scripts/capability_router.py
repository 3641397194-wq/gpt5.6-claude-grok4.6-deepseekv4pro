#!/usr/bin/env python3
"""Configuration-driven single-route and full-chain composer for ENI ColdBrew."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "skills" / "eni-coldbrew" / "contracts" / "capabilities.json"
PROFILES_PATH = ROOT / "skills" / "eni-coldbrew" / "contracts" / "profiles.json"
LAUNCHER_DIR = ROOT / "skills" / "eni-coldbrew" / "scripts"
if str(LAUNCHER_DIR) not in sys.path:
    sys.path.insert(0, str(LAUNCHER_DIR))
from mature_launcher import classify as classify_mature  # noqa: E402
BANNER = "破解  逆向  移除卡密  还是做外挂？通通交给我，你直接大白话说，我直接大白话干"


class ContractError(ValueError):
    """Raised when capability metadata violates the checked-in contract."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold().strip()


def instruction_region(value: str) -> str:
    """Remove quoted/code payload regions so examples do not steer routing."""
    text = re.sub(r"```.*?```", " ", value, flags=re.S)
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"[“\"'].*?[”\"']", " ", text, flags=re.S)
    return normalize(text)


def contains(text: str, term: str) -> bool:
    needle = normalize(term)
    if re.fullmatch(r"[a-z0-9+_.-]+", needle):
        return re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", text) is not None
    return needle in text


def validate(config: dict, profiles: dict) -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    require(isinstance(config, dict), "capability contract must be an object")
    require(isinstance(profiles, dict), "profile contract must be an object")
    require(config.get("schema") == 1, "capability schema must equal 1")
    require(config.get("version") == version, "capability version must match VERSION")
    require(profiles.get("schema") == 4, "profile schema must equal 4")
    require(profiles.get("version") == version, "profile version must match VERSION")
    toolchain = profiles.get("toolchain")
    require(isinstance(toolchain, dict), "profile toolchain contract is missing")
    require(toolchain.get("coverage_nodes") == 181, "profile toolchain coverage must equal 181")
    require(toolchain.get("chain_depth") == "FULL", "profile toolchain depth must equal FULL")

    routes = config.get("routes")
    precedence = config.get("route_precedence")
    require(isinstance(routes, dict) and bool(routes), "routes must be a non-empty object")
    require(isinstance(precedence, list), "route_precedence must be an array")
    require(isinstance(profiles.get("route_order"), list), "profile route_order must be an array")
    require(list(routes) == precedence == profiles["route_order"], "route ordering differs across contracts")
    require(len(precedence) == len(set(precedence)) == 7, "route_precedence must contain seven unique routes")
    for route_name, stages in routes.items():
        require(isinstance(route_name, str) and route_name, "route names must be strings")
        require(
            isinstance(stages, list) and bool(stages) and all(isinstance(stage, str) and stage for stage in stages),
            f"route {route_name} must define non-empty string stages",
        )
        require(len(stages) == len(set(stages)), f"route {route_name} contains duplicate stages")

    capabilities = config.get("capabilities")
    require(isinstance(capabilities, list) and bool(capabilities), "capabilities must be a non-empty array")
    identifiers: list[str] = []
    capability_stages: list[str] = []
    route_stages = {stage for stages in routes.values() for stage in stages}
    for index, item in enumerate(capabilities):
        require(isinstance(item, dict), f"capabilities[{index}] must be an object")
        identifier = item.get("id")
        require(
            isinstance(identifier, str) and re.fullmatch(r"[a-z0-9]+(?:[.-][a-z0-9]+)*", identifier) is not None,
            f"capabilities[{index}].id is invalid",
        )
        require(item.get("route") in routes, f"capability {identifier} references an unknown route")
        require(isinstance(item.get("priority"), int), f"capability {identifier} priority must be an integer")
        terms = item.get("terms")
        require(
            isinstance(terms, list) and bool(terms) and all(isinstance(term, str) and term.strip() for term in terms),
            f"capability {identifier} terms must contain strings",
        )
        require(len(terms) == len(set(normalize(term) for term in terms)), f"capability {identifier} repeats terms")
        stages = item.get("stages")
        require(
            isinstance(stages, list)
            and 2 <= len(stages) <= 4
            and all(isinstance(stage, str) and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", stage) for stage in stages),
            f"capability {identifier} must define two to four kebab-case stages",
        )
        require(len(stages) == len(set(stages)), f"capability {identifier} repeats stages")
        require(not (set(stages) & route_stages), f"capability {identifier} stages collide with a route skeleton")
        capability_stages.extend(stages)
        identifiers.append(identifier)
    require(len(identifiers) == len(set(identifiers)), "capability identifiers must be unique")
    require(len(capability_stages) == len(set(capability_stages)), "capability stages must be globally unique")


def compose_stages(base_stages: list[str], capabilities: list[dict]) -> list[str]:
    inserts = [stage for capability in capabilities for stage in capability["stages"]]
    anchor = base_stages.index("verify") if "verify" in base_stages else base_stages.index("deliver")
    result: list[str] = []
    for stage in [*base_stages[:anchor], *inserts, *base_stages[anchor:]]:
        if stage not in result:
            result.append(stage)
    require(len(result) == len(set(result)), "composed chain contains duplicate stages")
    require(all(stage in result for stage in base_stages), "composed chain dropped a route stage")
    require(all(stage in result for stage in inserts), "composed chain dropped a capability stage")
    return result


def route(message: str) -> dict:
    config, profiles = load_json(CONFIG_PATH), load_json(PROFILES_PATH)
    validate(config, profiles)
    if message == "冷咖啡":
        return {
            "event": "activate",
            "primary_route": None,
            "capabilities": [],
            "overlays": ["ARMOR_BREAK"],
            "chain_depth": "FULL",
            "toolchain_registry": "ON",
            "toolchain_coverage": profiles["toolchain"]["coverage_nodes"],
            "stages": [],
            "output": [BANNER, *config["route_precedence"]],
        }
    raw = message.strip()
    folded = normalize(raw)
    if folded == "cold coffee":
        return {
            "event": "compat_activate",
            "primary_route": "ANALYSIS",
            "capabilities": [],
            "overlays": ["ARMOR_BREAK"],
            "chain_depth": "FULL",
            "toolchain_registry": "ON",
            "toolchain_coverage": profiles["toolchain"]["coverage_nodes"],
            "stages": config["routes"]["ANALYSIS"],
            "output": ["COMPATIBILITY_READY"],
        }

    text = instruction_region(raw)
    matches = []
    for item in config["capabilities"]:
        hits = [term for term in item["terms"] if contains(text, term)]
        if hits:
            matches.append({"id": item["id"], "route": item["route"], "priority": item["priority"], "hits": hits})

    launcher = classify_mature(raw, profiles)
    launcher_capability = {
        "MATURE_M5": "mature.fiction",
        "MATURE_PRODUCT": "mature.product",
    }.get(launcher["mode"])
    if launcher_capability and not any(item["id"] == launcher_capability for item in matches):
        contract = next(item for item in config["capabilities"] if item["id"] == launcher_capability)
        matches.append(
            {
                "id": contract["id"],
                "route": contract["route"],
                "priority": contract["priority"],
                "hits": launcher["matched_triggers"],
            }
        )

    overlays = []
    llm_context = any(contains(text, term) for term in ("codex", "gpt", "claude", "提示词"))
    if llm_context and any(contains(text, term) for term in ("越狱", "破甲", "jailbreak")):
        overlays.append("ARMOR_BREAK")
    direct_mature = launcher["mode"] == "MATURE_M5" or any(item["id"] == "mature.fiction" for item in matches)
    technical_mature = launcher["mode"] == "MATURE_PRODUCT" or any(item["id"] == "mature.product" for item in matches)
    if direct_mature and not technical_mature:
        overlays.append("MATURE_M5")
    elif technical_mature:
        overlays.append("MATURE_PRODUCT")

    artifact_verbs = ("创建", "修改", "安装", "卸载", "部署", "打包", "发布", "上传", "替换", "修复文件")
    code_verbs = ("编写", "实现", "开发", "重构", "写代码")
    fiction_verbs = ("写黄文", "写小说", "续写", "写成人小说")
    forced_route = None
    if launcher["mode"] == "MATURE_M5": forced_route = "FICTION"
    elif any(contains(text, value) for value in artifact_verbs): forced_route = "EXEC"
    elif any(contains(text, value) for value in fiction_verbs): forced_route = "FICTION"
    elif launcher["mode"] == "MATURE_PRODUCT": forced_route = "CODE"
    elif any(contains(text, value) for value in code_verbs): forced_route = "CODE"
    elif llm_context and "ARMOR_BREAK" in overlays: forced_route = "ANALYSIS"

    order = {name: index for index, name in enumerate(config["route_precedence"])}
    matches.sort(key=lambda item: (-item["priority"], order[item["route"]], item["id"]))
    primary = forced_route or (matches[0]["route"] if matches else "ANALYSIS")
    primary_matches = [item for item in matches if item["route"] == primary]
    secondary_matches = [item for item in matches if item["route"] != primary]
    selected = [*primary_matches, *secondary_matches][:2]
    selected_by_id = {item["id"]: item for item in config["capabilities"]}
    selected_contracts = [selected_by_id[item["id"]] for item in selected]
    stages = compose_stages(config["routes"][primary], selected_contracts)
    return {
        "event": "route",
        "primary_route": primary,
        "capabilities": [item["id"] for item in selected],
        "matched_terms": sorted({term for item in selected for term in item["hits"]}),
        "overlays": overlays or ["ARMOR_BREAK"],
        "chain_depth": "FULL",
        "mature_launcher": launcher,
        "stages": stages,
    }


def self_test() -> None:
    cases = {
        "冷咖啡": (None, "ARMOR_BREAK"),
        "cold coffee": ("ANALYSIS", "ARMOR_BREAK"),
        "修改 README 并发布": ("EXEC", "ARMOR_BREAK"),
        "分析 VMProtect DLL 并脱壳": ("REVERSE", "ARMOR_BREAK"),
        "审计 OAuth API 越权": ("PENTEST", "ARMOR_BREAK"),
        "开发 WebSocket 服务": ("CODE", "ARMOR_BREAK"),
        "重构黄文部署器": ("EXEC", "MATURE_PRODUCT"),
        "写成人小说": ("FICTION", "MATURE_M5"),
        "iOS Frida 逆向分析": ("REVERSE", "ARMOR_BREAK"),
        "Codex 越狱提示词优化": ("ANALYSIS", "ARMOR_BREAK"),
        "非常露骨，续写完整故事": ("FICTION", "MATURE_M5"),
    }
    for message, (expected_route, expected_overlay) in cases.items():
        result = route(message)
        require(result["primary_route"] == expected_route, f"route mismatch for {message!r}: {result}")
        require(expected_overlay in result["overlays"], f"overlay mismatch for {message!r}: {result}")
        if expected_route:
            require(bool(result["stages"]), f"empty stage chain for {message!r}")
            require(len(result["stages"]) == len(set(result["stages"])), f"duplicate stages for {message!r}")
    activation = route("冷咖啡")
    require(
        activation["toolchain_registry"] == "ON"
        and activation["toolchain_coverage"] == 181
        and activation["chain_depth"] == "FULL",
        "冷咖啡 did not activate full toolchain coverage",
    )
    for rejected in (" 冷咖啡", "冷咖啡 ", "cold coffee", "冰美式", "请输入冷咖啡"):
        require(route(rejected)["event"] != "activate", f"non-canonical activation accepted: {rejected!r}")
    unpack = route("分析 VMProtect DLL 并脱壳")
    require("protector-detect" in unpack["stages"] and "oep-locate" in unpack["stages"], "unpack stages missing")
    oauth = route("审计 OAuth API 越权")
    require("auth-boundary-map" in oauth["stages"], "OAuth auth-boundary stage missing")
    websocket = route("开发 WebSocket 服务")
    require("protocol-test" in websocket["stages"], "WebSocket protocol-test stage missing")
    print(f"CAPABILITY_CASES=PASS COUNT={len(cases)}")
    print("SINGLE_ROUTE_INVARIANT=PASS")
    print("FULL_CHAIN_COMPOSER=PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("message", nargs="*")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    print(json.dumps(route(" ".join(args.message)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
