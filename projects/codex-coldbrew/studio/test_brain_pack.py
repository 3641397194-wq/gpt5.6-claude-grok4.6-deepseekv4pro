from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import brain_pack
import coldbrew_activation as activation
import coldbrew_studio as studio


class CodexBrainPackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name) / ".codex"
        self.home.mkdir()
        (self.home / "config.toml").write_text('model = "gpt-5.6"\n', encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_primary_and_legacy_activation_entries(self) -> None:
        self.assertTrue(activation.is_trigger("冷咖啡"))
        for value in (" 冷咖啡", "冷咖啡 ", "cold coffee", "[[ENI:PROFILE=MAX]]"):
            self.assertTrue(activation.is_trigger(value), value)
        for value in ("冰美式", "请输入冷咖啡"):
            self.assertFalse(activation.is_trigger(value), value)

    def test_install_verifies_all_brain_layers_and_ishii_persona(self) -> None:
        result = studio.apply_install(self.home, "max")
        self.assertTrue(result["ok"])
        self.assertEqual(result["brain"]["layers"]["skills"], 5)
        self.assertEqual(result["brain"]["layers"]["prompts"], 2)
        agents = (self.home / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn(brain_pack.BEGIN_MARKER, agents)
        self.assertIn("十几年安全研究", agents)
        self.assertIn("允许少量粗口", agents)
        self.assertTrue((self.home / "skills" / "coldbrew-ishii" / "SKILL.md").exists())
        self.assertTrue((self.home / "prompts" / "coldbrew-status.md").exists())

        verified = studio.verify_install(self.home)
        self.assertTrue(verified["ok"], verified)
        self.assertEqual(verified["brain"]["layer_count"], 8)

    def test_restore_removes_marker_and_preserves_outside_agents_edits(self) -> None:
        agents = self.home / "AGENTS.md"
        agents.write_text("# Owner rules\nkeep-before=true\n", encoding="utf-8")
        studio.apply_install(self.home, "builder")
        agents.write_text(
            agents.read_text(encoding="utf-8") + "\nkeep-after=true\n",
            encoding="utf-8",
        )

        restored = studio.restore_install(self.home)
        self.assertTrue(restored["ok"])
        text = agents.read_text(encoding="utf-8")
        self.assertIn("keep-before=true", text)
        self.assertIn("keep-after=true", text)
        self.assertNotIn(brain_pack.BEGIN_MARKER, text)

    def test_profile_switch_retains_first_skill_baseline(self) -> None:
        target = self.home / "skills" / "coldbrew-core" / "SKILL.md"
        target.parent.mkdir(parents=True)
        baseline = b"owner skill\r\nkeep=true\r\n"
        target.write_bytes(baseline)

        studio.apply_install(self.home, "max", force=True)
        studio.apply_install(self.home, "research")
        restored = studio.restore_install(self.home)

        self.assertTrue(restored["ok"])
        self.assertEqual(target.read_bytes(), baseline)

    def test_restore_preserves_edited_managed_skill(self) -> None:
        studio.apply_install(self.home, "max")
        target = self.home / "skills" / "coldbrew-core" / "SKILL.md"
        target.write_text("user changed this after install\n", encoding="utf-8")

        result = studio.restore_install(self.home)

        self.assertIn("skills/coldbrew-core/SKILL.md", result["brain"]["preserved"])
        self.assertEqual(target.read_text(encoding="utf-8"), "user changed this after install\n")

    def test_unmanaged_namespaced_file_requires_force(self) -> None:
        target = self.home / "prompts" / "coldbrew.md"
        target.parent.mkdir(parents=True)
        target.write_text("owner prompt\n", encoding="utf-8")
        plan = studio.build_plan(self.home, "max")
        self.assertTrue(plan.conflict)
        self.assertIn(str(target), plan.brain_conflicts)
        with self.assertRaises(studio.ConflictError):
            studio.apply_install(self.home, "max")


if __name__ == "__main__":
    unittest.main()
