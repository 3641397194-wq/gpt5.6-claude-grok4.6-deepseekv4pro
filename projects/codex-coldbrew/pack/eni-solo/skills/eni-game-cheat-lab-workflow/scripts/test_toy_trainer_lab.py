#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("toy_trainer_lab.py")


class ToyTrainerLabTests(unittest.TestCase):
    def run_cli(self, *args: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(expected, result.returncode, msg=f"stdout={result.stdout}\nstderr={result.stderr}")
        return result

    @staticmethod
    def file_hash(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_complete_toy_trainer_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = root / "baseline.json"
            analysis = root / "analysis.json"
            trained = root / "trained.json"
            verification = root / "verification.json"

            self.run_cli("init", "--out", str(baseline), "--name", "unittest-arena")
            baseline_hash = self.file_hash(baseline)
            self.run_cli("analyze", "--state", str(baseline), "--out", str(analysis))
            analysis_data = json.loads(analysis.read_text(encoding="utf-8"))
            self.assertEqual("baseline-clean", analysis_data["status"])
            self.assertEqual("none", analysis_data["engine_trust_map"]["process_boundary"])

            self.run_cli(
                "apply",
                "--state",
                str(baseline),
                "--out",
                str(trained),
                "--set",
                "player.health=999",
                "--set",
                "trainer.health_lock=true",
            )
            self.assertEqual(baseline_hash, self.file_hash(baseline), "apply must preserve the baseline")
            trained_data = json.loads(trained.read_text(encoding="utf-8"))
            self.assertEqual(999, trained_data["player"]["health"])
            self.assertTrue(trained_data["trainer"]["health_lock"])
            self.assertEqual("toy_trainer_apply", trained_data["telemetry"][-1]["event_type"])

            self.run_cli(
                "verify",
                "--state",
                str(trained),
                "--baseline",
                str(baseline),
                "--expect",
                "player.health=999",
                "--expect",
                "trainer.health_lock=true",
                "--out",
                str(verification),
            )
            result = json.loads(verification.read_text(encoding="utf-8"))
            self.assertTrue(result["regression"]["pass"])
            indicator_ids = {row["id"] for row in result["indicators"]}
            self.assertTrue({"TGL-HEALTH-RANGE", "TGL-TRAINER-FLAG", "TGL-TELEMETRY"}.issubset(indicator_ids))

    def test_rejects_non_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            bad = Path(temp) / "state.txt"
            result = self.run_cli("init", "--out", str(bad), expected=2)
            self.assertIn(".json", result.stderr)
            self.assertFalse(bad.exists())

    def test_rejects_unknown_field_and_preserves_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = root / "baseline.json"
            output = root / "modified.json"
            self.run_cli("init", "--out", str(baseline))
            baseline_hash = self.file_hash(baseline)
            result = self.run_cli(
                "apply",
                "--state",
                str(baseline),
                "--out",
                str(output),
                "--set",
                "system.process=1",
                expected=2,
            )
            self.assertIn("不支持", result.stderr)
            self.assertEqual(baseline_hash, self.file_hash(baseline))
            self.assertFalse(output.exists())

    def test_failed_expectation_returns_nonzero_and_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = root / "baseline.json"
            report = root / "failed.json"
            self.run_cli("init", "--out", str(baseline))
            self.run_cli(
                "verify",
                "--state",
                str(baseline),
                "--expect",
                "player.health=999",
                "--out",
                str(report),
                expected=2,
            )
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual("fail", data["status"])
            self.assertFalse(data["regression"]["expectations_satisfied"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

