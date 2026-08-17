#!/usr/bin/env python3
"""Validate and route the ENI ColdBrew independent toolchain contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "contracts" / "toolchain.json"
VERSION = (ROOT.parent.parent / "VERSION").read_text(encoding="utf-8").strip()
SOURCE_SHA256 = "3E07EC16325D99C6C415EDA4EF7AFC123C61275E55D458BED1D6628652A89533"
ROUTES = {"EXEC", "REVERSE", "PENTEST", "GAME", "CODE", "FICTION", "ANALYSIS"}
KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CAPABILITY = re.compile(r"^[a-z][a-z0-9.-]*$")
SPLIT = re.compile(r"[\s._/\\:+&、，,；;（）()\[\]{}<>与和及]+")
STOP = {
    "analysis", "assurance", "assessment", "audit", "boundary", "check", "configuration",
    "control", "detection", "engineering", "exposure", "integrity", "inventory", "lifecycle",
    "mapping", "modeling", "platform", "review", "simulation", "validation", "workflow",
}


class ContractError(ValueError):
    pass


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(value)).casefold().strip())


def string_list(value: Any, field: str, minimum: int = 1) -> list[str]:
    need(isinstance(value, list) and len(value) >= minimum, f"{field} must contain {minimum}+ items")
    need(all(isinstance(x, str) and x.strip() for x in value), f"{field} contains invalid text")
    need(len(value) == len(set(value)), f"{field} contains duplicates")
    return value


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"manifest load failed: {exc}") from exc
    need(isinstance(value, dict), "manifest root must be an object")
    return value


def validate(manifest: dict[str, Any]) -> dict[str, int | str]:
    need(manifest.get("schema") == 1 and manifest.get("version") == VERSION, "schema/version mismatch")
    source = manifest.get("source_archive", {})
    need(source.get("sha256") == SOURCE_SHA256, "source SHA-256 mismatch")
    need(source.get("source_domains") == 17 and source.get("source_leaves") == 181, "source coverage mismatch")
    activation = manifest.get("activation", {})
    need(
        activation
        == {
            "exact": "冷咖啡",
            "aliases": [],
            "full_chain": True,
            "coverage": 181,
            "domain_count": 17,
        },
        "activation mismatch",
    )
    need(set(manifest.get("route_order", [])) == ROUTES, "route order mismatch")
    domains = manifest.get("domains")
    need(isinstance(domains, list) and len(domains) == 17, "manifest must contain 17 domains")

    domain_ids: set[str] = set()
    node_ids: set[str] = set()
    stage_ids: set[str] = set()
    node_orders: list[int] = []
    total_nodes = 0
    for domain_order, domain in enumerate(domains, 1):
        did = domain.get("id")
        need(isinstance(did, str) and KEBAB.fullmatch(did) is not None and did not in domain_ids, "invalid domain id")
        domain_ids.add(did)
        need(domain.get("order") == domain_order and domain.get("route") in ROUTES, f"invalid domain contract: {did}")
        need(isinstance(domain.get("priority"), int) and domain.get("source_domain"), f"invalid domain metadata: {did}")
        string_list(domain.get("keywords"), f"{did}.keywords")
        nodes = domain.get("nodes")
        need(isinstance(nodes, list) and nodes and domain.get("node_count") == len(nodes), f"node count mismatch: {did}")
        total_nodes += len(nodes)
        local_ids: set[str] = set()
        for node_order, node in enumerate(nodes, 1):
            nid = node.get("id")
            need(isinstance(nid, str) and KEBAB.fullmatch(nid) is not None and nid not in node_ids, "invalid node id")
            node_ids.add(nid)
            local_ids.add(nid)
            need(node.get("domain_order") == domain_order and node.get("node_order") == node_order, f"node order mismatch: {nid}")
            need(isinstance(node.get("order"), int) and node.get("route") in ROUTES, f"invalid node route/order: {nid}")
            node_orders.append(node["order"])
            need(isinstance(node.get("capability"), str) and CAPABILITY.fullmatch(node["capability"]), f"invalid capability: {nid}")
            string_list(node.get("aliases"), f"{nid}.aliases")
            string_list(node.get("outputs"), f"{nid}.outputs", 2)
            string_list(node.get("verification"), f"{nid}.verification", 2)
            stages = node.get("stages")
            need(isinstance(stages, list) and 3 <= len(stages) <= 6, f"invalid stage count: {nid}")
            for stage_order, stage in enumerate(stages, 1):
                sid = stage.get("id")
                need(isinstance(sid, str) and KEBAB.fullmatch(sid) and sid not in stage_ids, f"invalid stage id: {nid}")
                need(stage.get("order") == stage_order and isinstance(stage.get("action"), str) and stage["action"].strip(), f"invalid stage: {sid}")
                stage_ids.add(sid)
        need(domain.get("default_node") in local_ids, f"invalid default node: {did}")

    need(total_nodes == 181 and node_orders == list(range(1, 182)), "manifest node coverage/order mismatch")
    coverage = manifest.get("coverage_index", {})
    mappings = coverage.get("mappings")
    need(coverage.get("expected_domains") == 17 and coverage.get("expected_nodes") == 181, "coverage counts mismatch")
    need(coverage.get("source_archive_sha256") == SOURCE_SHA256, "coverage SHA-256 mismatch")
    need(isinstance(mappings, list) and len(mappings) == 181, "coverage mappings mismatch")
    need([x.get("order") for x in mappings] == list(range(1, 182)), "coverage order mismatch")
    mapped = [x.get("canonical_id") for x in mappings]
    pairs = [(x.get("source_domain"), x.get("source_leaf")) for x in mappings]
    need(len(set(mapped)) == 181 and set(mapped) == node_ids, "coverage canonical ids mismatch")
    need(all(a and b for a, b in pairs) and len(set(pairs)) == 181, "coverage source pairs mismatch")
    return {"schema": 1, "version": VERSION, "domains": 17, "nodes": 181,
            "stages": len(stage_ids), "coverage": 181, "source_sha256": SOURCE_SHA256}


def expanded_terms(values: Iterable[str]) -> list[tuple[str, int]]:
    weighted: dict[str, int] = {}
    for raw in values:
        full = normalize(raw)
        if not full:
            continue
        weighted[full] = max(weighted.get(full, 0), 4)
        for piece in SPLIT.split(full.replace("-", " ")):
            if piece and piece not in STOP and (len(piece) >= 3 or (piece.isascii() and len(piece) >= 2)):
                weighted[piece] = max(weighted.get(piece, 0), 1)
    return sorted(weighted.items(), key=lambda item: (-item[1], -len(item[0]), item[0]))


def hits(prompt: str, values: Iterable[str]) -> list[tuple[str, int]]:
    return [(term, weight) for term, weight in expanded_terms(values) if term in prompt]


def compose(node: dict[str, Any]) -> list[dict[str, Any]]:
    return [{**stage, "route": node["route"], "capability": node["capability"]} for stage in node["stages"]]


def dispatch(prompt: str, manifest: dict[str, Any]) -> dict[str, Any]:
    if prompt == manifest["activation"]["exact"]:
        return {"matched": True, "activation": "coldbrew", "full_chain": True, "coverage": 181,
                "domain_count": 17, "source_archive_sha256": manifest["source_archive"]["sha256"],
                "chain": [{"order": d["order"], "domain_id": d["id"], "route": d["route"],
                           "coverage": d["node_count"], "node_ids": [n["id"] for n in d["nodes"]]}
                          for d in manifest["domains"]]}
    text = normalize(prompt)

    candidates = []
    for domain in manifest["domains"]:
        dh = hits(text, [domain["id"], domain["label"], domain["source_domain"], *domain["keywords"]])
        for node in domain["nodes"]:
            nh = hits(text, [node["id"], node["capability"], *node["aliases"]])
            if not nh and not dh:
                continue
            score = (int(bool(nh)), sum(w == 4 for _, w in nh), sum(w == 4 for _, w in dh),
                     sum(len(t) * 10 + w * 100 for t, w in nh) + sum(len(t) * 3 + w * 25 for t, w in dh),
                     domain["priority"], int(node["id"] == domain["default_node"]),
                     -domain["order"], -node["node_order"])
            candidates.append((score, domain, node, sorted({t for t, _ in dh}), sorted({t for t, _ in nh})))
    if not candidates:
        return {"matched": False, "full_chain": False, "coverage": 0, "normalized_prompt": text,
                "available_domains": [d["id"] for d in manifest["domains"]]}
    _, domain, node, dh, nh = max(candidates, key=lambda item: (item[0], item[2]["id"]))
    return {"matched": True, "full_chain": False, "coverage": 1, "normalized_prompt": text,
            "selection": {"domain_id": domain["id"], "domain_label": domain["label"], "node_id": node["id"],
                          "route": node["route"], "capability": node["capability"]},
            "match": {"domain_terms": dh, "node_terms": nh}, "chain": compose(node),
            "outputs": node["outputs"], "verification": node["verification"]}


def self_test(manifest: dict[str, Any]) -> dict[str, Any]:
    summary = validate(manifest)
    need(summary["domains"] == 17 and summary["nodes"] == 181 and summary["stages"] == 905, "count assertion failed")
    cold = dispatch("冷咖啡", manifest)
    need(cold.get("full_chain") is True and cold.get("coverage") == 181 and len(cold["chain"]) == 17, "activation failed")
    for rejected in (" 冷咖啡", "冷咖啡 ", "cold coffee", "冰美式", "请输入冷咖啡", "冷咖啡！"):
        need(dispatch(rejected, manifest).get("full_chain") is False, f"non-canonical activation accepted: {rejected!r}")
    cases = {
        "ＳＱＬ注入": ("web-application-assurance", "web-sql-query-boundary", "PENTEST"),
        "ＰＥ文件分析": ("reverse-engineering", "reverse-pe-structure-analysis", "REVERSE"),
        "ＣＴＦ平台": ("reproducible-lab-environments", "lab-ctf-fixture-platform", "EXEC"),
        "漏洞评级ＣＶＳＳ": ("assessment-methodology", "methodology-cvss-scoring-consistency", "ANALYSIS"),
        "云配置审计": ("cloud-platform-assurance", "cloud-cloud-configuration-baseline", "PENTEST"),
    }
    for prompt, expected in cases.items():
        result = dispatch(prompt, manifest)
        selected = result.get("selection", {})
        actual = (selected.get("domain_id"), selected.get("node_id"), selected.get("route"))
        need(actual == expected, f"routing assertion failed for {prompt}: {actual}")
        need([s["order"] for s in result["chain"]] == [1, 2, 3, 4, 5], "stage sequence failed")
    need(dispatch("Web攻击类：目录与内容发现", manifest)["selection"]["node_id"] == "web-route-content-inventory", "web disambiguation failed")
    need(dispatch("探测类-侦察信息收集：目录与内容发现", manifest)["selection"]["node_id"] == "recon-web-route-inventory", "recon disambiguation failed")
    return {"self_test": "PASS", **summary, "activation": "PASS", "nfkc_matching": "PASS",
            "unique_selection": "PASS", "sequential_chain": "PASS"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and route the ENI ColdBrew toolchain contract")
    parser.add_argument("prompt", nargs="?")
    parser.add_argument("--prompt", dest="prompt_option")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(args.manifest)
        result = self_test(manifest) if args.self_test else validate(manifest) if args.validate else None
        if result is None:
            prompt = args.prompt_option if args.prompt_option is not None else args.prompt
            if prompt is None and not sys.stdin.isatty():
                prompt = sys.stdin.read().strip()
            if not prompt:
                parser.error("a prompt, --validate, or --self-test is required")
            validate(manifest)
            result = dispatch(prompt, manifest)
        print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty or args.self_test or args.validate else None))
        return 0
    except ContractError as exc:
        print(f"CONTRACT_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
