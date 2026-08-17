from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import brain_layers
import claude_pojia as pojia


class ClaudeBrainLayerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / ".claude"
        self.root.mkdir()
        self.layout = pojia.resolve_layout("user", home=self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_install_verifies_skills_agent_commands_and_ishii(self) -> None:
        result = pojia.apply_install(self.layout, "max-breaker")
        self.assertTrue(result["ok"])
        self.assertEqual(result["brain"]["layers"], {"skills": 5, "agents": 1, "commands": 2})
        self.assertTrue((self.root / "skills" / "coldbrew-ishii" / "SKILL.md").exists())
        agent = (self.root / "agents" / "coldbrew-ishii.md").read_text(encoding="utf-8")
        self.assertIn("十几年安全研究", agent)
        self.assertIn("偶尔带粗口", agent)
        self.assertTrue((self.root / "commands" / "coldbrew.md").exists())

        verified = pojia.verify_install(self.layout)
        self.assertTrue(verified["ok"], verified)
        self.assertEqual(verified["brain"]["layer_count"], 8)
        self.assertEqual(verified["rules_count"], 7)

    def test_profile_switch_restores_first_command_baseline(self) -> None:
        command = self.root / "commands" / "coldbrew.md"
        command.parent.mkdir(parents=True)
        baseline = b"owner command\r\nkeep=true\r\n"
        command.write_bytes(baseline)

        pojia.apply_install(self.layout, "max-breaker", force=True)
        pojia.apply_install(self.layout, "research")
        restored = pojia.restore_install(self.layout)

        self.assertTrue(restored["ok"])
        self.assertEqual(command.read_bytes(), baseline)

    def test_restore_preserves_edited_managed_skill(self) -> None:
        pojia.apply_install(self.layout, "builder")
        skill = self.root / "skills" / "coldbrew-core" / "SKILL.md"
        skill.write_text("user changed after install\n", encoding="utf-8")

        restored = pojia.restore_install(self.layout)

        self.assertIn("skills/coldbrew-core/SKILL.md", restored["brain"]["preserved"])
        self.assertEqual(skill.read_text(encoding="utf-8"), "user changed after install\n")

    def test_unmanaged_brain_file_requires_force(self) -> None:
        target = self.root / "agents" / "coldbrew-ishii.md"
        target.parent.mkdir(parents=True)
        target.write_text("owner agent\n", encoding="utf-8")

        plan = pojia.build_plan(self.layout, "max-breaker")
        self.assertTrue(plan.conflict)
        self.assertIn(str(target), plan.brain_conflicts)
        with self.assertRaises(pojia.OwnershipConflict):
            pojia.apply_install(self.layout, "max-breaker")

    def test_project_scope_keeps_layers_inside_project(self) -> None:
        project = Path(self.temp.name) / "project"
        project.mkdir()
        layout = pojia.resolve_layout("project", project=project)

        pojia.apply_install(layout, "creative")

        self.assertTrue((project / ".claude" / "skills" / "coldbrew-creative" / "SKILL.md").exists())
        self.assertTrue((project / ".claude" / "agents" / "coldbrew-ishii.md").exists())
        self.assertFalse((self.root / "skills").exists())


if __name__ == "__main__":
    unittest.main()
