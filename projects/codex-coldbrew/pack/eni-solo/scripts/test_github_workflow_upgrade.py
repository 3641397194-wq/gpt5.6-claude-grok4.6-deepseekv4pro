#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().with_name("github_workflow_upgrade.py")
SPEC = importlib.util.spec_from_file_location("github_workflow_upgrade", SCRIPT)
upgrade = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(upgrade)
SHA_A, SHA_B = "a" * 40, "b" * 40


class UpgradeTests(unittest.TestCase):
    def package(self, base: Path, commit: str = SHA_A) -> Path:
        root = base / "package"
        for relative in ("manifest", "docs", "scripts", "skills/eni-github-workflow-hub/scripts"):
            (root / relative).mkdir(parents=True, exist_ok=True)
        (root / "manifest/package.json").write_text(json.dumps({"version": "4.0.0"}), encoding="utf-8")
        data = {"sources": [{
            "id": "example", "repository": "https://github.com/example/example",
            "branch_reviewed": "main", "commit": commit, "reviewed_at": "2026-07-15",
            "license": "MIT", "workflow_lanes": ["software"], "patterns_absorbed": "test",
            "vendored": False, "integration": "method adapter and source reference only",
        }]}
        (root / "manifest/github-workflow-sources.json").write_text(json.dumps(data), encoding="utf-8")
        (root / "docs/github-workflow-manual-update-v4.md").write_text("test\n", encoding="utf-8")
        (root / "scripts/github_workflow_upgrade.py").write_text("# test\n", encoding="utf-8")
        (root / "skills/eni-github-workflow-hub/scripts/source_catalog.py").write_text("# test\n", encoding="utf-8")
        return root

    def test_build_lock(self):
        with tempfile.TemporaryDirectory() as value:
            root = self.package(Path(value))
            result = upgrade.build_lock(root)
            allow = upgrade.read_json(root / "manifest/github-workflow-allowlist.json")
            lock = upgrade.read_json(root / "manifest/github-revision-lock.json")
            self.assertEqual(result["source_count"], 1)
            self.assertEqual(allow["sources"][0]["repo_path"], "example/example")
            self.assertEqual(lock["sources"]["example"]["commit"], SHA_A)

    def test_known_heads_never_calls_network(self):
        with tempfile.TemporaryDirectory() as value:
            base = Path(value); root = self.package(base); upgrade.build_lock(root)
            known = base / "known.json"
            known.write_text(json.dumps({"example": {"url": "https://github.com/example/example", "branch": "main", "commit": SHA_A, "ok": True}}), encoding="utf-8")
            with mock.patch.object(upgrade, "github_api_head", side_effect=AssertionError("network")), mock.patch.object(upgrade, "git_head", side_effect=AssertionError("git")):
                result, code = upgrade.refresh(root, base / "refresh", known, 1)
            self.assertEqual(code, 0)
            self.assertEqual(result["summary"]["unchanged"], 1)

    def test_api_failure_uses_git_fallback(self):
        with tempfile.TemporaryDirectory() as value:
            base = Path(value); root = self.package(base); upgrade.build_lock(root)
            with mock.patch.object(upgrade, "github_api_head", side_effect=RuntimeError("offline")), mock.patch.object(upgrade, "git_head", return_value=SHA_B):
                result, code = upgrade.refresh(root, base / "refresh", None, 1)
            metadata = upgrade.read_json(base / "refresh/github-upstream-metadata.json")
            self.assertEqual(code, 0)
            self.assertEqual(result["summary"]["changed"], 1)
            self.assertEqual(metadata["records"][0]["resolution"], "git-ls-remote")

    def test_atomic_install_and_rollback(self):
        with tempfile.TemporaryDirectory() as value:
            base = Path(value); root = self.package(base); upgrade.build_lock(root); home = base / "home"
            first = upgrade.atomic_install(root, home, "4.0.0")
            target = Path(first["target"])
            self.assertTrue((target / "install-index.json").is_file())
            (target / "sentinel.txt").write_text("previous", encoding="utf-8")
            second = upgrade.atomic_install(root, home, "4.0.0")
            result = upgrade.rollback(Path(second["rollback_manifest"]))
            self.assertTrue(result["restored_previous_backup"])
            self.assertEqual((Path(result["target"]) / "sentinel.txt").read_text(encoding="utf-8"), "previous")

    def test_rejects_non_github_source(self):
        with tempfile.TemporaryDirectory() as value:
            root = self.package(Path(value))
            data = upgrade.read_json(root / "manifest/github-workflow-sources.json")
            data["sources"][0]["repository"] = "https://example.com/a/b"
            (root / "manifest/github-workflow-sources.json").write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                upgrade.build_lock(root)

    def test_discover_scores_pins_and_promotes_verified_source(self):
        with tempfile.TemporaryDirectory() as value:
            base = Path(value); root = self.package(base)
            fixture = base / "search.json"
            fixture.write_text(json.dumps({"items": [{
                "name": "ultimate-parser", "full_name": "official-labs/ultimate-parser",
                "html_url": "https://github.com/official-labs/ultimate-parser",
                "description": "maintained binary parser workflow and harness",
                "topics": ["binary", "parser", "workflow", "harness"],
                "default_branch": "main", "head_commit": SHA_B,
                "stargazers_count": 100000, "forks_count": 9000, "open_issues_count": 12,
                "pushed_at": upgrade.now(), "archived": False, "fork": False,
                "owner": {"type": "Organization"}, "license": {"spdx_id": "Apache-2.0"},
            }]}), encoding="utf-8")
            found = upgrade.discover(root, base / "discovery", "software", "binary parser workflow harness", 5, 1, fixture)
            report = upgrade.read_json(Path(found["report"]))
            self.assertEqual(found["channel"], "local-search-results")
            self.assertEqual(found["staged_count"], 1)
            self.assertEqual(report["candidates"][0]["head_commit"], SHA_B)
            promoted = upgrade.promote_source(
                root, Path(found["report"]), "official-labs/ultimate-parser", "software",
                ["PASS:focused", "PASS:regression"], "verifier-B",
                "https://official.example/project", True,
            )
            self.assertEqual(promoted["computed_score"], 100)
            self.assertIn("official-labs-ultimate-parser", upgrade.read_json(root / "manifest/github-revision-lock.json")["sources"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
