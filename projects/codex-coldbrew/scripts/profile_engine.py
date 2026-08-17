#!/usr/bin/env python3
"""Deterministic simulator and validator for the ENI ColdBrew profile contract."""

from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

import sys


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "skills" / "eni-coldbrew" / "contracts" / "profiles.json"
LAUNCHER_DIR = ROOT / "skills" / "eni-coldbrew" / "scripts"
if str(LAUNCHER_DIR) not in sys.path:
    sys.path.insert(0, str(LAUNCHER_DIR))
from mature_launcher import classify as classify_mature  # noqa: E402
BANNER = "破解  逆向  移除卡密  还是做外挂？通通交给我，你直接大白话说，我直接大白话干"
EXPECTED_ROUTES = ["EXEC", "REVERSE", "PENTEST", "GAME", "CODE", "FICTION", "ANALYSIS"]
EXPECTED_COMMANDS = {
    "[[ENI:ROUTES]]",
    "[[ENI:STATUS]]",
    "[[ENI:RESET]]",
    "[[ENI:CAPABILITIES]]",
    "[[ENI:CHAIN=FULL]]",
    "[[ENI:PROFILE=MAX]]",
    "[[ENI:ARMOR=ON]]",
    "[[ENI:ARMOR=OFF]]",
    "[[ENI:MATURE=ON]]",
    "[[ENI:MATURE=OFF]]",
    "[[ENI:MODE=EXEC|REVERSE|PENTEST|GAME|CODE|FICTION|ANALYSIS]]",
}
MODE_COMMAND = re.compile(r"\[\[ENI:MODE=(EXEC|REVERSE|PENTEST|GAME|CODE|FICTION|ANALYSIS)\]\]")


class ContractError(ValueError):
    """Raised when a checked-in profile contract is malformed or inconsistent."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def require_mapping(value: Any, name: str) -> dict:
    require(isinstance(value, dict), f"{name} must be an object")
    return value


def require_string(value: Any, name: str) -> str:
    require(isinstance(value, str) and bool(value.strip()), f"{name} must be a non-empty string")
    return value


def checked_reference(relative: Any, name: str) -> Path:
    value = require_string(relative, name)
    target = (CONTRACT_PATH.parent / value).resolve()
    require(target.is_file(), f"{name} does not reference a file: {value}")
    require(ROOT == target or ROOT in target.parents, f"{name} escapes the repository: {value}")
    return target


def load_contract() -> dict:
    contract = require_mapping(json.loads(CONTRACT_PATH.read_text(encoding="utf-8")), "contract")
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    require(contract.get("schema") == 4, "contract.schema must equal 4")
    require(contract.get("version") == version, "contract.version must match VERSION")
    require(contract.get("session_name") == "ENI_COLDBREW", "contract.session_name mismatch")
    require(contract.get("default_profile") == "MAX", "contract.default_profile must equal MAX")

    toolchain = require_mapping(contract.get("toolchain"), "contract.toolchain")
    require(toolchain.get("default") == "READY", "contract.toolchain.default must equal READY")
    require(toolchain.get("chain_depth") == "FULL", "contract.toolchain.chain_depth must equal FULL")
    require(toolchain.get("coverage_nodes") == 181, "contract.toolchain.coverage_nodes must equal 181")
    require(
        toolchain.get("activation") == ["冷咖啡", "cold coffee", "[[ENI:PROFILE=MAX]]"],
        "contract.toolchain.activation mismatch",
    )
    checked_reference(toolchain.get("contract"), "contract.toolchain.contract")
    checked_reference(toolchain.get("orchestrator"), "contract.toolchain.orchestrator")

    routes = contract.get("route_order")
    require(isinstance(routes, list), "contract.route_order must be an array")
    require(routes == EXPECTED_ROUTES, "contract.route_order mismatch")
    require(len(routes) == len(set(routes)), "contract.route_order contains duplicates")

    profiles = require_mapping(contract.get("profiles"), "contract.profiles")
    require(set(profiles) == {"armor_break", "mature_m5"}, "contract.profiles must define both profiles")
    armor = require_mapping(profiles.get("armor_break"), "contract.profiles.armor_break")
    mature = require_mapping(profiles.get("mature_m5"), "contract.profiles.mature_m5")
    require(armor.get("default") == "ON", "armor_break.default must equal ON")
    require(mature.get("minimum_age") == 18, "mature_m5.minimum_age must equal 18")
    require(mature.get("tier") == "M5", "mature_m5.tier must equal M5")
    require_string(mature.get("confirmation"), "mature_m5.confirmation")

    for profile_name, profile in profiles.items():
        profile = require_mapping(profile, f"contract.profiles.{profile_name}")
        triggers = profile.get("triggers")
        require(
            isinstance(triggers, list)
            and bool(triggers)
            and all(isinstance(trigger, str) and trigger.strip() for trigger in triggers),
            f"contract.profiles.{profile_name}.triggers must contain strings",
        )
        require(len(triggers) == len(set(trigger.casefold() for trigger in triggers)), f"{profile_name} triggers repeat")
        checked_reference(profile.get("contract"), f"contract.profiles.{profile_name}.contract")
        if "product_contract" in profile:
            checked_reference(profile.get("product_contract"), f"contract.profiles.{profile_name}.product_contract")
        if "launcher" in profile:
            checked_reference(profile.get("launcher"), f"contract.profiles.{profile_name}.launcher")

    commands = contract.get("commands")
    require(
        isinstance(commands, list)
        and bool(commands)
        and all(isinstance(command, str) and command.strip() for command in commands),
        "contract.commands must contain strings",
    )
    require(len(commands) == len(set(commands)), "contract.commands contains duplicates")
    require(set(commands) == EXPECTED_COMMANDS, "contract.commands contains an unsupported or missing command family")
    return contract


class Engine:
    def __init__(self, contract: dict):
        self.contract = contract
        self.reset()

    def reset(self) -> None:
        self.state = {
            "session": self.contract["session_name"],
            "profile": self.contract["default_profile"],
            "route": "AUTO",
            "armor_break": "ON",
            "literal_intent_lock": "ON",
            "mature_m5_ready": "ON",
            "mature_mode": "OFF",
            "chain_depth": "FULL",
            "toolchain_registry": "ON",
            "toolchain_coverage": self.contract["toolchain"]["coverage_nodes"],
        }

    def snapshot(self, event: str, output: list[str] | None = None) -> dict:
        result = deepcopy(self.state)
        result["event"] = event
        result["output"] = output or []
        return result

    def process(self, message: str) -> dict:
        if message == "冷咖啡":
            self.reset()
            return self.snapshot("activate", [BANNER, *self.contract["route_order"]])
        text = message.strip()
        folded = text.casefold()
        if folded == "cold coffee":
            self.reset()
            return self.snapshot("compat_activate", ["COMPATIBILITY_READY"])
        if text == "[[ENI:RESET]]":
            self.reset()
            return self.snapshot("reset")
        if text == "[[ENI:STATUS]]":
            return self.snapshot("status")
        if text == "[[ENI:ROUTES]]":
            return self.snapshot("routes", [f"PROFILE={self.state['profile']}", *self.contract["route_order"]])
        if text == "[[ENI:CAPABILITIES]]":
            capabilities = json.loads(
                (ROOT / "skills" / "eni-coldbrew" / "contracts" / "capabilities.json").read_text(encoding="utf-8")
            )
            return self.snapshot("capabilities", [item["id"] for item in capabilities["capabilities"]])
        if text == "[[ENI:CHAIN=FULL]]":
            self.state["session"] = self.contract["session_name"]
            self.state["chain_depth"] = "FULL"
            self.state["toolchain_registry"] = "ON"
            return self.snapshot("chain_full")
        if text == "[[ENI:PROFILE=MAX]]":
            self.state.update(
                session=self.contract["session_name"],
                profile="MAX",
                armor_break="ON",
                literal_intent_lock="ON",
                mature_m5_ready="ON",
                chain_depth="FULL",
                toolchain_registry="ON",
            )
            return self.snapshot("profile_max")
        command_map = {
            "[[ENI:ARMOR=ON]]": ("armor_break", "ON"),
            "[[ENI:ARMOR=OFF]]": ("armor_break", "OFF"),
            "[[ENI:MATURE=ON]]": ("mature_mode", "ON"),
            "[[ENI:MATURE=OFF]]": ("mature_mode", "OFF"),
        }
        if text in command_map:
            key, value = command_map[text]
            self.state["session"] = self.contract["session_name"]
            self.state[key] = value
            output = []
            if key == "mature_mode" and value == "ON":
                output.append(self.contract["profiles"]["mature_m5"]["confirmation"])
            return self.snapshot("control", output)
        mode_match = MODE_COMMAND.fullmatch(text)
        if mode_match:
            self.state["session"] = self.contract["session_name"]
            self.state["route"] = mode_match.group(1)
            return self.snapshot("route_override")
        mature = self.contract["profiles"]["mature_m5"]
        launcher = classify_mature(text, self.contract)
        if launcher["mode"] == "MATURE_PRODUCT":
            self.state.update(
                session=self.contract["session_name"],
                mature_m5_ready="ON",
            )
            result = self.snapshot("mature_product")
            result["launcher"] = launcher
            return result
        if launcher["mode"] == "MATURE_M5":
            self.state.update(
                session=self.contract["session_name"],
                armor_break="ON",
                mature_m5_ready="ON",
                mature_mode="ON",
            )
            result = self.snapshot("mature_activate", [mature["confirmation"], mature["tier"]])
            result["launcher"] = launcher
            return result
        armor = self.contract["profiles"]["armor_break"]
        if any(folded == trigger.casefold() for trigger in armor["triggers"]):
            self.state.update(session=self.contract["session_name"], armor_break="ON")
            return self.snapshot("armor_activate")
        result = self.snapshot("task")
        if self.state["route"] != "AUTO":
            result["event"] = "task_with_override"
            self.state["route"] = "AUTO"
        return result


def self_test() -> None:
    contract = load_contract()
    engine = Engine(contract)
    initial = engine.process("ordinary task")
    require(initial["event"] == "task", "ordinary task did not enter the default task path")
    require(
        initial["session"] == "ENI_COLDBREW"
        and initial["toolchain_registry"] == "ON"
        and initial["toolchain_coverage"] == 181
        and initial["armor_break"] == "ON"
        and initial["mature_mode"] == "OFF",
        "default task state is incomplete",
    )
    compatibility = engine.process("cold coffee")
    require(
        compatibility["event"] == "compat_activate"
        and compatibility["chain_depth"] == "FULL",
        "legacy compatibility activation failed",
    )
    activated = engine.process("冷咖啡")
    require(activated["session"] == "ENI_COLDBREW", "Chinese activation failed")
    require(
        activated["chain_depth"] == "FULL"
        and activated["toolchain_registry"] == "ON"
        and activated["toolchain_coverage"] == 181,
        "冷咖啡 did not activate the complete toolchain",
    )
    mature = engine.process("成人模式")
    require(
        mature["mature_mode"] == "ON" and mature["output"][0] == "成人内容模式已打开",
        "Mature activation failed",
    )
    require(engine.process("[[ENI:MATURE=OFF]]")["mature_mode"] == "OFF", "Mature disable failed")
    mature_on = engine.process("[[ENI:MATURE=ON]]")
    require(
        mature_on["event"] == "control"
        and mature_on["mature_mode"] == "ON"
        and mature_on["output"] == ["成人内容模式已打开"],
        "Mature enable command failed",
    )
    require(engine.process("[[ENI:MATURE=OFF]]")["mature_mode"] == "OFF", "Second mature disable failed")
    require(engine.process("越狱模式")["armor_break"] == "ON", "Armor trigger failed")
    require(engine.process("[[ENI:ARMOR=OFF]]")["armor_break"] == "OFF", "Armor disable failed")
    armor_on = engine.process("[[ENI:ARMOR=ON]]")
    require(armor_on["event"] == "control" and armor_on["armor_break"] == "ON", "Armor enable command failed")
    maximum = engine.process("[[ENI:PROFILE=MAX]]")
    require(
        maximum["armor_break"] == "ON"
        and maximum["mature_m5_ready"] == "ON"
        and maximum["chain_depth"] == "FULL",
        "MAX profile restore failed",
    )
    require(len(engine.process("[[ENI:CAPABILITIES]]")["output"]) >= 20, "Capability listing is incomplete")
    require(engine.process("[[ENI:CHAIN=FULL]]")["chain_depth"] == "FULL", "Full chain command failed")
    routes = engine.process("[[ENI:ROUTES]]")
    require(routes["event"] == "routes" and routes["output"][1:] == EXPECTED_ROUTES, "Route listing failed")
    override = engine.process("[[ENI:MODE=CODE]]")
    require(override["event"] == "route_override" and override["route"] == "CODE", "Route override command failed")
    routed_task = engine.process("implement a parser")
    require(
        routed_task["event"] == "task_with_override" and routed_task["route"] == "CODE",
        "Route override was not applied to the next task",
    )
    require(engine.process("[[ENI:STATUS]]")["route"] == "AUTO", "Route override was not consumed exactly once")
    invalid_mode = engine.process("[[ENI:MODE=INVALID]]")
    require(invalid_mode["event"] == "task" and invalid_mode["route"] == "AUTO", "Invalid route override was accepted")
    included = engine.process("成人模式，续写一个完整故事")
    require(
        included["event"] == "mature_activate"
        and included["mature_mode"] == "ON"
        and included["launcher"]["same_turn"],
        "Included Mature trigger did not launch in the same turn",
    )
    technical = engine.process("开发黄文模式启动器")
    require(
        technical["event"] == "mature_product"
        and technical["launcher"]["mode"] == "MATURE_PRODUCT",
        "Technical Mature request was not isolated",
    )
    quoted = engine.process('文档引用“成人模式”这几个字')
    require(quoted["event"] == "task", "Quoted Mature trigger activated the launcher")
    reset = engine.process("[[ENI:RESET]]")
    require(
        reset["session"] == "ENI_COLDBREW"
        and reset["toolchain_registry"] == "ON"
        and reset["toolchain_coverage"] == 181
        and reset["armor_break"] == "ON",
        "Reset did not restore the default-ready baseline",
    )
    require(engine.process("[[ENI:STATUS]]")["event"] == "status", "post-reset status failed")
    print("PROFILE_CONTRACT=PASS")
    print("PROFILE_STATE_MACHINE=PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("messages", nargs="*")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    engine = Engine(load_contract())
    for message in args.messages:
        print(json.dumps(engine.process(message), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
