#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "4.0.0"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_LANES = {
    "api", "architecture", "browser", "cloud-container", "code-security",
    "crack", "fuzzing", "malware-ir", "memory", "mobile", "pentest",
    "reverse", "scraper", "software", "supply-chain",
    "game-security-lab", "online-intelligence", "offline-deep-lab", "research-docs",
}
SCOPES = [
    "local-software-engineering",
    "reverse-analysis",
    "authorized-security-research",
    "defensive-workflows",
    "offline-owned-game-security-labs",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name("." + path.name + ".tmp-" + uuid.uuid4().hex)
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest().upper()


def version(root: Path) -> str:
    package = root / "manifest" / "package.json"
    return str(read_json(package).get("version") or VERSION) if package.is_file() else VERSION


def repo_path(repository: str) -> str:
    parsed = urllib.parse.urlparse(repository)
    if parsed.scheme != "https" or parsed.netloc.casefold() != "github.com":
        raise ValueError(f"repository must be an HTTPS github.com URL: {repository}")
    value = parsed.path.strip("/")
    value = value[:-4] if value.endswith(".git") else value
    if len(value.split("/")) != 2 or not all(value.split("/")):
        raise ValueError(f"repository must identify owner/repository: {repository}")
    return value


def normalize(data: dict[str, Any]) -> list[dict[str, Any]]:
    raw = data.get("sources")
    if not isinstance(raw, list) or not raw:
        raise ValueError("sources must be a non-empty list")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in raw:
        source_id = str(source.get("id") or "").strip()
        repository = str(source.get("repository") or "").strip()
        branch = str(source.get("branch_reviewed") or source.get("branch") or "").strip()
        commit = str(source.get("commit") or "").casefold()
        lanes = [str(item) for item in source.get("workflow_lanes", [])]
        if not source_id or source_id in seen:
            raise ValueError(f"missing or duplicate source id: {source_id!r}")
        if not branch or not HEX40.fullmatch(commit):
            raise ValueError(f"{source_id}: branch and immutable 40-character commit are required")
        if source.get("vendored") is not False:
            raise ValueError(f"{source_id}: vendored must be false")
        invalid = sorted(set(lanes) - ALLOWED_LANES)
        if invalid:
            raise ValueError(f"{source_id}: unsupported workflow lanes: {invalid}")
        seen.add(source_id)
        item = dict(source)
        item.update(
            id=source_id,
            repository=repository,
            repo_path=repo_path(repository),
            branch=branch,
            branch_reviewed=branch,
            commit=commit,
            workflow_lanes=lanes,
            vendored=False,
        )
        result.append(item)
    return sorted(result, key=lambda item: item["id"].casefold())


def build_lock(root: Path, source_file: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    source_file = (source_file or root / "manifest" / "github-workflow-sources.json").resolve()
    sources = normalize(read_json(source_file))
    source_sha = digest(source_file)
    generated = now()
    allowlist = {
        "schema_version": 1,
        "package_version": version(root),
        "generated_at": generated,
        "source_manifest_sha256": source_sha,
        "scope": SCOPES,
        "policy": {
            "host": "github.com",
            "selection": "official upstream repositories only",
            "vendoring": False,
            "third_party_code_auto_execution": False,
            "revision_required_before_install": True,
        },
        "sources": sources,
    }
    locked = {
        item["id"]: {
            "repository": item["repository"],
            "repo_path": item["repo_path"],
            "branch": item["branch"],
            "commit": item["commit"],
            "reviewed_at": item.get("reviewed_at"),
        }
        for item in sources
    }
    revision_lock = {
        "schema_version": 1,
        "package_version": version(root),
        "generated_at": generated,
        "source_manifest_sha256": source_sha,
        "source_count": len(locked),
        "sources": locked,
    }
    allow_path = root / "manifest" / "github-workflow-allowlist.json"
    lock_path = root / "manifest" / "github-revision-lock.json"
    write_json(allow_path, allowlist)
    write_json(lock_path, revision_lock)
    return {
        "command": "build-lock", "source_count": len(sources),
        "allowlist_path": str(allow_path), "lock_path": str(lock_path),
        "source_manifest_sha256": source_sha,
    }


def github_api_head(source: dict[str, Any], timeout: float) -> str:
    branch = urllib.parse.quote(source["branch"], safe="")
    url = f"https://api.github.com/repos/{source['repo_path']}/commits/{branch}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"eni-github-workflow-upgrade/{VERSION}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as response:
        commit = str(json.loads(response.read().decode("utf-8")).get("sha") or "").casefold()
    if not HEX40.fullmatch(commit):
        raise ValueError("GitHub API returned no valid commit")
    return commit


def github_search(query: str, timeout: float, limit: int) -> list[dict[str, Any]]:
    encoded = urllib.parse.quote(query + " in:name,description,readme archived:false fork:false")
    url = f"https://api.github.com/search/repositories?q={encoded}&sort=stars&order=desc&per_page={min(max(limit, 1), 50)}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"eni-github-workflow-upgrade/{VERSION}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as response:
        value = json.loads(response.read().decode("utf-8"))
    items = value.get("items") if isinstance(value, dict) else None
    if not isinstance(items, list):
        raise ValueError("GitHub search returned no repository list")
    return [item for item in items if isinstance(item, dict)][:limit]


def candidate_score(item: dict[str, Any], capability: str) -> tuple[int, dict[str, int]]:
    text = " ".join(
        str(value or "") for value in [item.get("name"), item.get("full_name"), item.get("description"), " ".join(item.get("topics") or [])]
    ).casefold()
    wanted = {token for token in re.findall(r"[a-z0-9][a-z0-9+_.-]+", capability.casefold()) if len(token) > 2}
    overlap = sum(1 for token in wanted if token in text)
    stars = max(0, int(item.get("stargazers_count") or 0))
    pushed = str(item.get("pushed_at") or "")
    try:
        age_days = max(0.0, (datetime.now(timezone.utc) - datetime.fromisoformat(pushed.replace("Z", "+00:00"))).total_seconds() / 86400)
    except Exception:
        age_days = 99999
    breakdown = {
        "maintained": 15 if age_days <= 365 else (8 if age_days <= 1095 else 0),
        "adoption": min(25, int(5 * math.log10(stars + 1))),
        "license_visible": 10 if item.get("license") else 0,
        "not_archived": 10 if not item.get("archived") else 0,
        "not_fork": 10 if not item.get("fork") else 0,
        "organization_owner": 10 if str((item.get("owner") or {}).get("type") or "").casefold() == "organization" else 4,
        "capability_match": min(15, overlap * 5),
        "default_branch": 5 if item.get("default_branch") else 0,
    }
    return sum(breakdown.values()), breakdown


def discovery_source(item: dict[str, Any], workflow: str, capability: str, timeout: float) -> dict[str, Any]:
    repository = str(item.get("html_url") or "")
    full_name = str(item.get("full_name") or "")
    branch = str(item.get("default_branch") or "main")
    score, breakdown = candidate_score(item, capability)
    source = {"id": full_name.casefold().replace("/", "-"), "repository": repository, "repo_path": full_name, "branch": branch}
    fixture_head = str(item.get("head_commit") or "").casefold()
    if HEX40.fullmatch(fixture_head):
        resolved = {"head_commit": fixture_head, "resolution": "provided-search-evidence", "attempts": [{"channel": "provided-search-evidence", "status": "ok"}]}
    else:
        resolved = resolve_head(source, {}, timeout) if repository and full_name else {"head_commit": None, "resolution": "unresolved", "attempts": []}
    return {
        "candidate_id": full_name,
        "repository": repository,
        "description": item.get("description"),
        "workflow": workflow,
        "capability": capability,
        "default_branch": branch,
        "head_commit": resolved.get("head_commit"),
        "head_resolution": resolved.get("resolution"),
        "head_attempts": resolved.get("attempts"),
        "stars": int(item.get("stargazers_count") or 0),
        "forks": int(item.get("forks_count") or 0),
        "open_issues": int(item.get("open_issues_count") or 0),
        "pushed_at": item.get("pushed_at"),
        "license": (item.get("license") or {}).get("spdx_id") if isinstance(item.get("license"), dict) else None,
        "topics": item.get("topics") or [],
        "quality_score": score,
        "quality_breakdown": breakdown,
        "staged": bool(score >= 80 and resolved.get("head_commit")),
        "promotion_requires": ["official-project-proof", "license-review", "focused-tests", "independent-verifier", "immutable-revision"],
    }


def discover(root: Path, out: Path, workflow: str, capability: str, limit: int, timeout: float, results_file: Path | None = None) -> dict[str, Any]:
    if workflow not in ALLOWED_LANES:
        raise ValueError(f"unsupported workflow: {workflow}")
    if results_file:
        raw = read_json(results_file.resolve())
        items = raw.get("items", raw) if isinstance(raw, dict) else raw
        if not isinstance(items, list):
            raise ValueError("search results fixture must contain a list")
        channel = "local-search-results"
    else:
        items = github_search(capability, timeout, limit)
        channel = "github-search-api"
    candidates = [discovery_source(item, workflow, capability, timeout) for item in items[:limit]]
    candidates.sort(key=lambda item: (-item["quality_score"], -item["stars"], item["candidate_id"].casefold()))
    existing = {item["repository"].rstrip("/").casefold() for item in normalize(read_json(root / "manifest" / "github-workflow-sources.json"))}
    for item in candidates:
        item["already_allowlisted"] = item["repository"].rstrip("/").casefold() in existing
        if item["already_allowlisted"]:
            item["staged"] = False
    report = {
        "schema_version": 1,
        "package_version": version(root),
        "generated_at": now(),
        "channel": channel,
        "workflow": workflow,
        "capability": capability,
        "query_sha256": hashlib.sha256(capability.encode("utf-8")).hexdigest(),
        "candidate_count": len(candidates),
        "staged_count": sum(1 for item in candidates if item["staged"]),
        "selection": "maintained + adopted + licensed + non-fork + organization + capability-match + immutable-head",
        "candidates": candidates,
    }
    out.mkdir(parents=True, exist_ok=True)
    path = out / "github-workflow-discovery.json"
    write_json(path, report)
    return {"command": "discover", "report": str(path), "candidate_count": len(candidates), "staged_count": report["staged_count"], "channel": channel}


def promote_source(root: Path, report_file: Path, candidate_id: str, workflow: str, tests: list[str], verifier: str, official_proof: str, license_reviewed: bool) -> dict[str, Any]:
    report = read_json(report_file.resolve())
    candidate = next((item for item in report.get("candidates", []) if item.get("candidate_id") == candidate_id), None)
    if not candidate:
        raise ValueError("candidate not found in discovery report")
    checks = {
        "source_quality": int(candidate.get("quality_score") or 0) >= 80,
        "immutable_revision": bool(HEX40.fullmatch(str(candidate.get("head_commit") or ""))),
        "official_and_license_review": bool(official_proof and license_reviewed and candidate.get("license")),
        "focused_tests": bool(tests) and all(str(item).startswith("PASS:") for item in tests),
        "independent_verifier": bool(verifier),
    }
    score = sum(20 for value in checks.values() if value)
    if score != 100:
        raise ValueError(f"source promotion computed {score}/100; candidate remains staged: {checks}")
    sources_path = root / "manifest" / "github-workflow-sources.json"
    manifest = read_json(sources_path)
    if any(str(item.get("repository") or "").rstrip("/").casefold() == candidate["repository"].rstrip("/").casefold() for item in manifest.get("sources", [])):
        raise ValueError("repository already exists in source manifest")
    source_id = re.sub(r"[^a-z0-9-]+", "-", candidate_id.casefold().replace("/", "-")).strip("-")
    manifest["sources"].append({
        "id": source_id,
        "repository": candidate["repository"],
        "branch_reviewed": candidate["default_branch"],
        "commit": candidate["head_commit"],
        "reviewed_at": now(),
        "workflow_lanes": [workflow],
        "vendored": False,
        "license": candidate["license"],
        "official_proof": official_proof,
        "quality_score": candidate["quality_score"],
        "promotion_tests": tests,
        "independent_verifier": verifier,
    })
    manifest["sources"] = sorted(manifest["sources"], key=lambda item: item["id"].casefold())
    write_json(sources_path, manifest)
    lock = build_lock(root, sources_path)
    return {"command": "promote-source", "source_id": source_id, "computed_score": score, "checks": checks, "revision": candidate["head_commit"], "lock": lock}


def git_head(source: dict[str, Any], timeout: float) -> str:
    completed = subprocess.run(
        ["git", "ls-remote", "--exit-code", source["repository"], "refs/heads/" + source["branch"]],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=max(timeout, 20), check=False,
    )
    if completed.returncode:
        raise RuntimeError((completed.stderr or completed.stdout or "git ls-remote failed").strip())
    for line in completed.stdout.splitlines():
        candidate = line.split()[0].casefold() if line.split() else ""
        if HEX40.fullmatch(candidate):
            return candidate
    raise ValueError("git ls-remote returned no valid commit")


def resolve_head(source: dict[str, Any], known: dict[str, Any], timeout: float) -> dict[str, Any]:
    attempts: list[dict[str, str]] = []
    cached = known.get(source["id"])
    if isinstance(cached, dict) and cached.get("ok") is True:
        commit = str(cached.get("commit") or "").casefold()
        same_url = not cached.get("url") or str(cached["url"]).rstrip("/") == source["repository"].rstrip("/")
        same_branch = not cached.get("branch") or str(cached["branch"]) == source["branch"]
        if HEX40.fullmatch(commit) and same_url and same_branch:
            return {"head_commit": commit, "resolution": "known-heads-json", "attempts": [{"channel": "known-heads-json", "status": "ok"}]}
        attempts.append({"channel": "known-heads-json", "status": "rejected"})
    try:
        commit = github_api_head(source, timeout)
        attempts.append({"channel": "github-api", "status": "ok"})
        return {"head_commit": commit, "resolution": "github-api", "attempts": attempts}
    except Exception as error:
        attempts.append({"channel": "github-api", "status": "failed", "error": str(error)[:500]})
    try:
        commit = git_head(source, timeout)
        attempts.append({"channel": "git-ls-remote", "status": "ok"})
        return {"head_commit": commit, "resolution": "git-ls-remote", "attempts": attempts}
    except Exception as error:
        attempts.append({"channel": "git-ls-remote", "status": "failed", "error": str(error)[:500]})
    return {"head_commit": None, "resolution": "unresolved", "attempts": attempts}


def refresh(root: Path, out: Path, known_file: Path | None, timeout: float) -> tuple[dict[str, Any], int]:
    root, out = root.resolve(), out.resolve()
    allow_path, lock_path = root / "manifest" / "github-workflow-allowlist.json", root / "manifest" / "github-revision-lock.json"
    if not allow_path.is_file() or not lock_path.is_file():
        build_lock(root)
    sources = normalize(read_json(allow_path))
    locked = read_json(lock_path).get("sources") or {}
    known = read_json(known_file.resolve()) if known_file else {}
    records = []
    for source in sources:
        locked_commit = str((locked.get(source["id"]) or {}).get("commit") or source["commit"]).casefold()
        resolved = resolve_head(source, known, timeout)
        head = resolved["head_commit"]
        status = "unresolved" if not head else ("unchanged" if head == locked_commit else "changed")
        records.append({
            "id": source["id"], "repository": source["repository"], "branch": source["branch"],
            "locked_commit": locked_commit, "head_commit": head, "resolution": resolved["resolution"],
            "status": status, "changed": status == "changed", "attempts": resolved["attempts"],
        })
    groups = {name: [item for item in records if item["status"] == name] for name in ("changed", "unchanged", "unresolved")}
    summary = {"total": len(records), **{name: len(items) for name, items in groups.items()}}
    out.mkdir(parents=True, exist_ok=True)
    metadata_path, diff_path = out / "github-upstream-metadata.json", out / "github-upstream-diff.json"
    candidate_path = out / "github-revision-lock-candidate.json"
    write_json(metadata_path, {"schema_version": 1, "package_version": version(root), "generated_at": now(), "records": records})
    write_json(diff_path, {"schema_version": 1, "package_version": version(root), "generated_at": now(), "summary": summary, **groups, "revision_lock_mutated": False})
    candidate = dict(locked)
    for item in records:
        if item["head_commit"]:
            value = dict(candidate.get(item["id"]) or {})
            value.update(repository=item["repository"], repo_path=repo_path(item["repository"]), branch=item["branch"], commit=item["head_commit"], candidate_resolution=item["resolution"])
            candidate[item["id"]] = value
    write_json(candidate_path, {"schema_version": 1, "package_version": version(root), "generated_at": now(), "base_revision_lock_sha256": digest(lock_path), "review_required": bool(groups["changed"] or groups["unresolved"]), "sources": candidate})
    result = {"command": "refresh", "metadata_path": str(metadata_path), "diff_path": str(diff_path), "candidate_lock_path": str(candidate_path), "summary": summary}
    return result, 0 if not groups["unresolved"] else 2


def assets(root: Path) -> list[tuple[Path, str]]:
    mapping = [
        (root / "manifest" / "github-workflow-sources.json", "manifest/github-workflow-sources.json"),
        (root / "manifest" / "github-workflow-allowlist.json", "manifest/github-workflow-allowlist.json"),
        (root / "manifest" / "github-revision-lock.json", "manifest/github-revision-lock.json"),
        (root / "docs" / "github-workflow-manual-update-v4.md", "docs/github-workflow-manual-update-v4.md"),
        (root / "scripts" / "github_workflow_upgrade.py", "scripts/github_workflow_upgrade.py"),
        (root / "skills" / "eni-github-workflow-hub" / "scripts" / "source_catalog.py", "scripts/source_catalog.py"),
    ]
    missing = [str(path) for path, _ in mapping if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing required assets: " + ", ".join(missing))
    return mapping


def replace_path(source: Path, target: Path, attempts: int = 20) -> None:
    """Retry same-volume directory swaps when Windows indexing briefly holds a handle."""
    for attempt in range(attempts):
        try:
            os.replace(source, target)
            return
        except PermissionError:
            if attempt + 1 >= attempts:
                raise
            time.sleep(0.05 * (attempt + 1))


def atomic_install(root: Path, codex_home: Path, package_version: str) -> dict[str, Any]:
    root, codex_home = root.resolve(), codex_home.resolve()
    if not (root / "manifest" / "github-workflow-allowlist.json").is_file():
        build_lock(root)
    eni_root = codex_home / "eni-unified"
    target, backups = eni_root / "github-workflow", eni_root / "backups"
    eni_root.mkdir(parents=True, exist_ok=True)
    backups.mkdir(parents=True, exist_ok=True)
    staging = eni_root / (".github-workflow.staging-" + uuid.uuid4().hex)
    previous: Path | None = None
    installed = []
    try:
        staging.mkdir()
        for source, relative in assets(root):
            destination = staging / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            installed.append({"path": relative, "bytes": destination.stat().st_size, "sha256": digest(destination)})
        write_json(staging / "install-index.json", {"schema_version": 1, "package_version": package_version, "installed_at": now(), "files": installed})
        if target.exists():
            previous = backups / ("github-workflow-" + stamp() + "-" + uuid.uuid4().hex[:8])
            replace_path(target, previous)
        replace_path(staging, target)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        if previous and previous.exists() and not target.exists():
            replace_path(previous, target)
        raise
    record = {
        "schema_version": 1, "version": package_version, "installed_at": now(),
        "codex_home": str(codex_home), "eni_root": str(eni_root), "target": str(target),
        "previous_backup": str(previous) if previous else None, "installed_files": installed,
    }
    unique = eni_root / f"github-workflow-rollback-{package_version}-{stamp()}.json"
    latest = eni_root / f"github-workflow-rollback-{package_version}.json"
    write_json(unique, record)
    write_json(latest, {**record, "history_manifest": str(unique)})
    return {"command": "install", "version": package_version, "target": str(target), "previous_backup": str(previous) if previous else None, "installed_file_count": len(installed), "rollback_manifest": str(unique), "rollback_manifest_latest": str(latest), "install_index": str(target / "install-index.json")}


def child(root: Path, target: Path) -> bool:
    try:
        return os.path.commonpath([os.path.normcase(str(root.resolve())), os.path.normcase(str(target.resolve()))]) == os.path.normcase(str(root.resolve()))
    except ValueError:
        return False


def rollback(manifest: Path) -> dict[str, Any]:
    manifest = manifest.resolve()
    data = read_json(manifest)
    eni_root, target = Path(data["eni_root"]).resolve(), Path(data["target"]).resolve()
    previous = Path(data["previous_backup"]).resolve() if data.get("previous_backup") else None
    if not child(eni_root, target) or (previous and not child(eni_root, previous)):
        raise ValueError("rollback path escaped 石井 root")
    backups = eni_root / "backups"
    backups.mkdir(parents=True, exist_ok=True)
    displaced = None
    if target.exists():
        displaced = backups / ("github-workflow-displaced-" + stamp() + "-" + uuid.uuid4().hex[:8])
        replace_path(target, displaced)
    restored = False
    try:
        if previous and previous.exists():
            replace_path(previous, target)
            restored = True
    except Exception:
        if displaced and displaced.exists() and not target.exists():
            replace_path(displaced, target)
        raise
    result = {"command": "rollback", "rolled_back_at": now(), "target": str(target), "restored_previous_backup": restored, "displaced_install": str(displaced) if displaced else None}
    result_path = manifest.with_name(manifest.stem + "-result-" + stamp() + ".json")
    write_json(result_path, result)
    result["result_path"] = str(result_path)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build-lock"); build.add_argument("--package-root", required=True); build.add_argument("--sources")
    update = commands.add_parser("refresh"); update.add_argument("--package-root", required=True); update.add_argument("--out-dir", required=True); update.add_argument("--known-heads-json"); update.add_argument("--timeout", type=float, default=15)
    find = commands.add_parser("discover"); find.add_argument("--package-root", required=True); find.add_argument("--out-dir", required=True); find.add_argument("--workflow", required=True, choices=sorted(ALLOWED_LANES)); find.add_argument("--capability", required=True); find.add_argument("--limit", type=int, default=10); find.add_argument("--timeout", type=float, default=15); find.add_argument("--search-results-json")
    promote = commands.add_parser("promote-source"); promote.add_argument("--package-root", required=True); promote.add_argument("--report", required=True); promote.add_argument("--candidate-id", required=True); promote.add_argument("--workflow", required=True, choices=sorted(ALLOWED_LANES)); promote.add_argument("--test", action="append", required=True); promote.add_argument("--independent-verifier", required=True); promote.add_argument("--official-proof", required=True); promote.add_argument("--license-reviewed", action="store_true")
    install = commands.add_parser("install"); install.add_argument("--package-root", required=True); install.add_argument("--codex-home", required=True); install.add_argument("--version", default=VERSION)
    undo = commands.add_parser("rollback"); undo.add_argument("--rollback-manifest", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "build-lock":
            result, code = build_lock(Path(args.package_root), Path(args.sources) if args.sources else None), 0
        elif args.command == "refresh":
            result, code = refresh(Path(args.package_root), Path(args.out_dir), Path(args.known_heads_json) if args.known_heads_json else None, args.timeout)
        elif args.command == "discover":
            result, code = discover(Path(args.package_root), Path(args.out_dir), args.workflow, args.capability, args.limit, args.timeout, Path(args.search_results_json) if args.search_results_json else None), 0
        elif args.command == "promote-source":
            result, code = promote_source(Path(args.package_root), Path(args.report), args.candidate_id, args.workflow, args.test, args.independent_verifier, args.official_proof, args.license_reviewed), 0
        elif args.command == "install":
            result, code = atomic_install(Path(args.package_root), Path(args.codex_home), args.version), 0
        else:
            result, code = rollback(Path(args.rollback_manifest)), 0
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return code
    except Exception as error:
        print(json.dumps({"command": args.command, "error": str(error), "type": type(error).__name__}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
