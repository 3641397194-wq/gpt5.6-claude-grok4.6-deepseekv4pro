#!/usr/bin/env python3
"""Offline JSON-only toy trainer and detection laboratory."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATE_SCHEMA = "eni.game-cheat-lab.toy-state/v1"
REPORT_SCHEMA = "eni.game-cheat-lab.report/v1"
MAX_JSON_BYTES = 2 * 1024 * 1024

FIELD_RULES = {
    "player.health": "number",
    "player.ammo": "integer",
    "player.score": "integer",
    "player.position.x": "number",
    "player.position.y": "number",
    "trainer.health_lock": "boolean",
    "trainer.ammo_lock": "boolean",
}


class LabError(ValueError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_path(raw: str | Path) -> Path:
    path = Path(raw).expanduser()
    if path.suffix.lower() != ".json":
        raise LabError(f"只接受显式 .json 路径: {path}")
    if path.exists() and path.is_dir():
        raise LabError(f"JSON 路径不能是目录: {path}")
    if path.is_symlink():
        raise LabError(f"拒绝符号链接 JSON 路径: {path}")
    return path


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def read_json(raw: str | Path) -> dict[str, Any]:
    path = json_path(raw)
    if not path.is_file():
        raise LabError(f"JSON 文件不存在: {path}")
    if path.stat().st_size > MAX_JSON_BYTES:
        raise LabError(f"JSON 文件超过 {MAX_JSON_BYTES} 字节限制: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise LabError(f"无法读取 JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise LabError("JSON 顶层必须是对象")
    return value


def write_json(raw: str | Path, value: dict[str, Any], *, force: bool = False) -> Path:
    path = json_path(raw)
    if path.exists() and not force:
        raise LabError(f"输出已存在；使用 --force 显式覆盖: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()
    return path


def nested_get(value: dict[str, Any], dotted: str) -> Any:
    node: Any = value
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            raise LabError(f"状态缺少字段: {dotted}")
        node = node[part]
    return node


def nested_set(value: dict[str, Any], dotted: str, replacement: Any) -> None:
    parts = dotted.split(".")
    node: Any = value
    for part in parts[:-1]:
        if not isinstance(node, dict) or part not in node:
            raise LabError(f"状态缺少字段: {dotted}")
        node = node[part]
    if not isinstance(node, dict) or parts[-1] not in node:
        raise LabError(f"状态缺少字段: {dotted}")
    node[parts[-1]] = replacement


def validate_scalar(path: str, value: Any) -> None:
    if path not in FIELD_RULES:
        raise LabError(f"不支持的 toy-state 字段: {path}")
    kind = FIELD_RULES[path]
    if kind == "boolean":
        valid = type(value) is bool
    elif kind == "integer":
        valid = type(value) is int
    else:
        valid = type(value) in (int, float) and math.isfinite(float(value))
    if not valid:
        raise LabError(f"字段 {path} 需要 {kind} JSON 标量")
    if type(value) in (int, float) and abs(float(value)) > 1_000_000_000:
        raise LabError(f"字段 {path} 超过 toy lab 数值范围")


def parse_assignment(raw: str) -> tuple[str, Any]:
    if "=" not in raw:
        raise LabError(f"赋值必须为 path=JSON_VALUE: {raw}")
    path, encoded = raw.split("=", 1)
    path = path.strip()
    try:
        value = json.loads(encoded)
    except json.JSONDecodeError as exc:
        raise LabError(f"赋值不是有效 JSON 标量: {raw}") from exc
    validate_scalar(path, value)
    return path, value


def validate_state(state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if state.get("schema") != STATE_SCHEMA:
        errors.append(f"schema 必须为 {STATE_SCHEMA}")
    if type(state.get("revision")) is not int or state.get("revision", -1) < 0:
        errors.append("revision 必须是非负整数")
    lab = state.get("lab")
    if not isinstance(lab, dict):
        errors.append("lab 必须是对象")
    elif not all(isinstance(lab.get(key), str) and lab.get(key) for key in ("name", "engine", "ownership", "authoritative_state")):
        errors.append("lab 缺少非空 name/engine/ownership/authoritative_state")
    for dotted in FIELD_RULES:
        try:
            validate_scalar(dotted, nested_get(state, dotted))
        except LabError as exc:
            errors.append(str(exc))
    try:
        max_health = nested_get(state, "player.max_health")
        max_ammo = nested_get(state, "player.max_ammo")
        if type(max_health) not in (int, float) or float(max_health) <= 0:
            errors.append("player.max_health 必须为正数")
        if type(max_ammo) is not int or max_ammo <= 0:
            errors.append("player.max_ammo 必须为正整数")
    except LabError as exc:
        errors.append(str(exc))
    telemetry = state.get("telemetry")
    if not isinstance(telemetry, list):
        errors.append("telemetry 必须是数组")
    bounds = state.get("world", {}).get("bounds") if isinstance(state.get("world"), dict) else None
    bound_keys = ("x_min", "x_max", "y_min", "y_max")
    if not isinstance(bounds, dict) or not all(k in bounds for k in bound_keys):
        errors.append("world.bounds 缺少 x_min/x_max/y_min/y_max")
    elif not all(type(bounds[k]) in (int, float) and math.isfinite(float(bounds[k])) for k in bound_keys):
        errors.append("world.bounds 必须是有限数值")
    elif bounds["x_min"] > bounds["x_max"] or bounds["y_min"] > bounds["y_max"]:
        errors.append("world.bounds 最小值不能大于最大值")
    return errors


def new_state(name: str) -> dict[str, Any]:
    return {
        "schema": STATE_SCHEMA,
        "revision": 0,
        "lab": {
            "name": name,
            "engine": "toy-json-state-machine",
            "ownership": "offline-owned-lab",
            "authoritative_state": "json-artifact",
        },
        "world": {"bounds": {"x_min": -1000, "x_max": 1000, "y_min": -1000, "y_max": 1000}},
        "player": {
            "health": 100,
            "max_health": 100,
            "ammo": 30,
            "max_ammo": 30,
            "score": 0,
            "position": {"x": 0, "y": 0},
        },
        "trainer": {"health_lock": False, "ammo_lock": False},
        "telemetry": [],
    }


def indicators(state: dict[str, Any]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []

    def add(identifier: str, severity: str, evidence: dict[str, Any]) -> None:
        found.append({"id": identifier, "severity": severity, "evidence": evidence})

    health = nested_get(state, "player.health")
    max_health = nested_get(state, "player.max_health")
    if health < 0 or health > max_health:
        add("TGL-HEALTH-RANGE", "high", {"health": health, "max_health": max_health})
    ammo = nested_get(state, "player.ammo")
    max_ammo = nested_get(state, "player.max_ammo")
    if ammo < 0 or ammo > max_ammo:
        add("TGL-AMMO-RANGE", "high", {"ammo": ammo, "max_ammo": max_ammo})
    x = nested_get(state, "player.position.x")
    y = nested_get(state, "player.position.y")
    bounds = state["world"]["bounds"]
    if not (bounds["x_min"] <= x <= bounds["x_max"] and bounds["y_min"] <= y <= bounds["y_max"]):
        add("TGL-POSITION-BOUNDS", "medium", {"x": x, "y": y, "bounds": bounds})
    active_flags = [path for path in ("trainer.health_lock", "trainer.ammo_lock") if nested_get(state, path)]
    if active_flags:
        add("TGL-TRAINER-FLAG", "high", {"active": active_flags})
    events = [event for event in state["telemetry"] if isinstance(event, dict) and event.get("event_type") == "toy_trainer_apply"]
    if events:
        add("TGL-TELEMETRY", "info", {"toy_trainer_apply_events": len(events)})
    return found


def field_diff(baseline: dict[str, Any], current: dict[str, Any]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for dotted in FIELD_RULES:
        before = nested_get(baseline, dotted)
        after = nested_get(current, dotted)
        if before != after:
            changes.append({"path": dotted, "before": before, "after": after})
    return changes


def emit(report: dict[str, Any], out: str | None, force: bool) -> None:
    if out:
        path = write_json(out, report, force=force)
        report = {"written": str(path), "sha256": digest(report), "status": report.get("status")}
    print(json.dumps(report, ensure_ascii=False, indent=2))


def command_init(args: argparse.Namespace) -> int:
    state = new_state(args.name)
    path = write_json(args.out, state, force=args.force)
    print(json.dumps({"status": "initialized", "path": str(path), "sha256": digest(state)}, ensure_ascii=False, indent=2))
    return 0


def command_analyze(args: argparse.Namespace) -> int:
    state = read_json(args.state)
    errors = validate_state(state)
    if errors:
        raise LabError("; ".join(errors))
    found = indicators(state)
    report = {
        "schema": REPORT_SCHEMA,
        "report_type": "analysis",
        "generated_at": utc_now(),
        "status": "anomaly-observed" if found else "baseline-clean",
        "state": {"path": str(json_path(args.state)), "sha256": digest(state), "revision": state["revision"]},
        "engine_trust_map": {
            "engine": state["lab"].get("engine", "unknown"),
            "authoritative_state": state["lab"].get("authoritative_state", "unknown"),
            "trust_zones": ["explicit-json-input", "toy-state-machine", "derived-report"],
            "process_boundary": "none",
            "network_boundary": "none",
        },
        "artifact_triage": {
            "schema_valid": True,
            "telemetry_events": len(state["telemetry"]),
            "trainer_flags_active": sum(bool(nested_get(state, p)) for p in ("trainer.health_lock", "trainer.ammo_lock")),
        },
        "indicators": found,
    }
    emit(report, args.out, args.force)
    return 0


def command_apply(args: argparse.Namespace) -> int:
    baseline = read_json(args.state)
    errors = validate_state(baseline)
    if errors:
        raise LabError("; ".join(errors))
    source = json_path(args.state).resolve()
    target = json_path(args.out).resolve()
    if source == target:
        raise LabError("apply 必须输出到新 JSON 文件，以保留 baseline")
    assignments = [parse_assignment(raw) for raw in args.set_values]
    if not assignments:
        raise LabError("apply 至少需要一个 --set")
    state = copy.deepcopy(baseline)
    changes: list[dict[str, Any]] = []
    for dotted, replacement in assignments:
        before = nested_get(state, dotted)
        nested_set(state, dotted, replacement)
        if before != replacement:
            changes.append({"path": dotted, "before": before, "after": replacement})
    state["revision"] += 1
    state["telemetry"].append(
        {
            "event_type": "toy_trainer_apply",
            "sequence": len(state["telemetry"]) + 1,
            "generated_at": utc_now(),
            "source": "toy_trainer_lab",
            "pre_state_sha256": digest(baseline),
            "changes": changes,
        }
    )
    errors = validate_state(state)
    if errors:
        raise LabError("; ".join(errors))
    path = write_json(args.out, state, force=args.force)
    print(
        json.dumps(
            {
                "status": "applied",
                "path": str(path),
                "baseline_sha256": digest(baseline),
                "state_sha256": digest(state),
                "changes": changes,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def command_verify(args: argparse.Namespace) -> int:
    state = read_json(args.state)
    state_errors = validate_state(state)
    baseline = read_json(args.baseline) if args.baseline else None
    baseline_errors = validate_state(baseline) if baseline is not None else []
    expectations = [parse_assignment(raw) for raw in args.expect]
    expected_results: list[dict[str, Any]] = []
    for dotted, expected in expectations:
        actual = nested_get(state, dotted)
        expected_results.append({"path": dotted, "expected": expected, "actual": actual, "matched": actual == expected})
    changes = field_diff(baseline, state) if baseline is not None and not baseline_errors else []
    expected_paths = {path for path, _ in expectations}
    unexpected = [change for change in changes if expected_paths and change["path"] not in expected_paths]
    regression_pass = not state_errors and not baseline_errors and all(row["matched"] for row in expected_results) and not unexpected
    report = {
        "schema": REPORT_SCHEMA,
        "report_type": "verification",
        "generated_at": utc_now(),
        "status": "pass" if regression_pass else "fail",
        "state": {"path": str(json_path(args.state)), "sha256": digest(state)},
        "baseline": ({"path": str(json_path(args.baseline)), "sha256": digest(baseline)} if baseline is not None else None),
        "schema_errors": {"state": state_errors, "baseline": baseline_errors},
        "changes": changes,
        "expectations": expected_results,
        "unexpected_changes": unexpected,
        "indicators": indicators(state) if not state_errors else [],
        "regression": {
            "schema_valid": not state_errors and not baseline_errors,
            "expectations_satisfied": all(row["matched"] for row in expected_results),
            "change_set_accounted": not unexpected,
            "pass": regression_pass,
        },
    }
    emit(report, args.out, args.force)
    return 0 if regression_pass else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offline JSON-only toy trainer laboratory")
    sub = parser.add_subparsers(dest="command", required=True)

    init_parser = sub.add_parser("init", help="create an explicit toy-state JSON baseline")
    init_parser.add_argument("--out", required=True, help="new .json output path")
    init_parser.add_argument("--name", default="toy-arena", help="lab name")
    init_parser.add_argument("--force", action="store_true", help="explicitly overwrite an existing output")
    init_parser.set_defaults(handler=command_init)

    analyze_parser = sub.add_parser("analyze", help="analyze a toy-state JSON")
    analyze_parser.add_argument("--state", required=True, help="input .json state")
    analyze_parser.add_argument("--out", help="optional explicit .json report")
    analyze_parser.add_argument("--force", action="store_true")
    analyze_parser.set_defaults(handler=command_analyze)

    apply_parser = sub.add_parser("apply", help="apply toy trainer assignments to a new JSON state")
    apply_parser.add_argument("--state", required=True, help="baseline .json state")
    apply_parser.add_argument("--out", required=True, help="new modified .json state")
    apply_parser.add_argument("--set", dest="set_values", action="append", default=[], metavar="PATH=JSON_VALUE")
    apply_parser.add_argument("--force", action="store_true")
    apply_parser.set_defaults(handler=command_apply)

    verify_parser = sub.add_parser("verify", help="verify state, expected changes, indicators, and regression")
    verify_parser.add_argument("--state", required=True, help="current .json state")
    verify_parser.add_argument("--baseline", help="optional baseline .json state")
    verify_parser.add_argument("--expect", action="append", default=[], metavar="PATH=JSON_VALUE")
    verify_parser.add_argument("--out", help="optional explicit .json report")
    verify_parser.add_argument("--force", action="store_true")
    verify_parser.set_defaults(handler=command_verify)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except LabError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
