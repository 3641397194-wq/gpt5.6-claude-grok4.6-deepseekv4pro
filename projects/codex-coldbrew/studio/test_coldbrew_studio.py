from __future__ import annotations

import json
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import coldbrew_studio as studio
import coldbrew_activation as activation


class ColdBrewStudioTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name) / ".codex"
        self.home.mkdir()
        (self.home / "config.toml").write_text(
            'model = "gpt-5.6"\nprovider = "local"\n\n[profiles]\nname = "keep-me"\n',
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_activate_cli_accepts_primary_and_legacy_entries(self) -> None:
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            studio.main(["activate"])
        self.assertEqual(raised.exception.code, 2)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(studio.main(["activate", "--trigger", "冷咖啡"]), 0)
            self.assertEqual(studio.main(["activate", "--trigger", "cold coffee"]), 0)

    def test_rendered_pack_is_profile_specific(self) -> None:
        max_pack = studio.render_prompt("max")
        research_pack = studio.render_prompt("research")
        self.assertIn("MAX Shield", max_pack)
        self.assertIn("Research Lens", research_pack)
        self.assertNotEqual(max_pack, research_pack)
        self.assertIn("[[CB:STATUS]]", max_pack)
        self.assertIn("石井 / Ishii", max_pack)
        self.assertIn("more than a decade of security research", max_pack)
        self.assertIn(activation.activation_document(markdown=True), max_pack)

    def test_coldbrew_activation_contract_is_complete_and_fixed(self) -> None:
        document = activation.activation_document()
        self.assertTrue(activation.verify_canonical_contract())
        self.assertEqual(
            activation.activation_sha256(),
            "F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246",
        )
        self.assertEqual(len(activation.CAPABILITY_SECTIONS), 6)
        self.assertTrue(activation.activation_payload("冷咖啡")["active"])
        self.assertFalse(activation.activation_payload("冰美式")["active"])
        self.assertIn("软件破解、脱壳、注册机、授权逻辑", document)
        self.assertIn("游戏外挂、Trainer、ESP、透视、自瞄", document)
        self.assertIn("SQL 注入、XSS、SSRF", document)
        self.assertIn("API、GraphQL、WebSocket、JWT、OAuth", document)
        self.assertIn("恶意样本分析、YARA 与 IOC、内存取证", document)
        self.assertIn("黑暗题材、成人文学、剧情续写和文风定制", document)
        self.assertTrue(document.endswith("最后给你完整过程、实际结果和清晰报告。"))

    def test_plan_detects_clean_home(self) -> None:
        plan = studio.build_plan(self.home, "max")
        self.assertFalse(plan.conflict)
        self.assertFalse(plan.managed)
        self.assertEqual(plan.current_instruction, None)

    def test_install_verify_and_restore_preserve_unrelated_toml(self) -> None:
        original = (self.home / "config.toml").read_bytes()
        result = studio.apply_install(self.home, "builder")
        self.assertTrue(result["ok"])
        config = (self.home / "config.toml").read_text(encoding="utf-8")
        self.assertIn('model_instructions_file = "./coldbrew-studio.md"', config)
        self.assertIn('provider = "local"', config)
        self.assertIn('[profiles]', config)

        verified = studio.verify_install(self.home)
        self.assertTrue(verified["ok"], verified)
        self.assertTrue((self.home / "coldbrew-studio.md").exists())

        restored = studio.restore_install(self.home)
        self.assertTrue(restored["ok"])
        self.assertEqual((self.home / "config.toml").read_bytes(), original)
        self.assertFalse((self.home / "coldbrew-studio.md").exists())
        self.assertFalse((self.home / ".coldbrew-studio" / "state.json").exists())

        empty_home = Path(self.temp.name) / "empty-codex-home"
        empty_home.mkdir()
        studio.apply_install(empty_home, "builder")
        self.assertTrue((empty_home / "config.toml").exists())
        studio.restore_install(empty_home)
        self.assertFalse((empty_home / "config.toml").exists())
        self.assertFalse((empty_home / studio.PROMPT_FILENAME).exists())

    def test_restore_preserves_config_bom_and_exact_bytes(self) -> None:
        original = b"\xef\xbb\xbfmodel = \"gpt-5.6\"\r\nprovider = \"local\"\r\n"
        (self.home / "config.toml").write_bytes(original)
        studio.apply_install(self.home, "max")
        restored = studio.restore_install(self.home)
        self.assertTrue(restored["ok"])
        self.assertEqual((self.home / "config.toml").read_bytes(), original)

    def test_profile_switch_preserves_original_config_baseline(self) -> None:
        original = (self.home / "config.toml").read_bytes()
        first = studio.apply_install(self.home, "max")
        second = studio.apply_install(self.home, "builder")
        self.assertNotEqual(first["config_snapshot"], second["config_snapshot"])
        self.assertEqual(first["restore_config_snapshot"], second["restore_config_snapshot"])

        studio.restore_install(self.home)
        self.assertEqual((self.home / "config.toml").read_bytes(), original)
        self.assertFalse((self.home / studio.PROMPT_FILENAME).exists())

    def test_profile_switch_restores_an_originally_absent_config(self) -> None:
        home = Path(self.temp.name) / "profile-switch-empty"
        home.mkdir()
        studio.apply_install(home, "max")
        studio.apply_install(home, "builder")

        studio.restore_install(home)
        self.assertFalse((home / "config.toml").exists())
        self.assertFalse((home / studio.PROMPT_FILENAME).exists())

    def test_profile_switch_restores_forced_user_prompt_bytes(self) -> None:
        original_config = (self.home / "config.toml").read_bytes()
        original_prompt = "owner prompt\r\n冷咖啡 baseline\r\n".encode("utf-8")
        prompt = self.home / studio.PROMPT_FILENAME
        prompt.write_bytes(original_prompt)

        first = studio.apply_install(self.home, "max", force=True)
        second = studio.apply_install(self.home, "builder")
        self.assertEqual(first["restore_prompt_snapshot"], second["restore_prompt_snapshot"])

        restored = studio.restore_install(self.home)
        self.assertTrue(restored["prompt_restored"])
        self.assertEqual(prompt.read_bytes(), original_prompt)
        self.assertEqual((self.home / "config.toml").read_bytes(), original_config)

    def test_profile_switch_restores_same_name_user_pointer_and_prompt(self) -> None:
        original_config = (
            'model = "gpt-5.6"\r\n'
            f'model_instructions_file = "./{studio.PROMPT_FILENAME}"\r\n\r\n'
            '[profiles]\r\nname = "keep-me"\r\n'
        ).encode("utf-8")
        original_prompt = "same-name owner prompt\r\n保留原件\r\n".encode("utf-8")
        (self.home / "config.toml").write_bytes(original_config)
        prompt = self.home / studio.PROMPT_FILENAME
        prompt.write_bytes(original_prompt)

        studio.apply_install(self.home, "max", force=True)
        studio.apply_install(self.home, "research")
        studio.restore_install(self.home)

        self.assertEqual((self.home / "config.toml").read_bytes(), original_config)
        self.assertEqual(prompt.read_bytes(), original_prompt)

    def test_unmanaged_prompt_requires_force(self) -> None:
        prompt = self.home / studio.PROMPT_FILENAME
        original_config = (self.home / "config.toml").read_bytes()
        prompt.write_text("user-owned prompt\n", encoding="utf-8")
        with self.assertRaises(studio.ConflictError):
            studio.apply_install(self.home, "max")
        result = studio.apply_install(self.home, "max", force=True)
        self.assertTrue(result["ok"])
        self.assertIsNotNone(result["prompt_snapshot"])
        restored = studio.restore_install(self.home)
        self.assertTrue(restored["prompt_restored"])
        self.assertEqual(prompt.read_text(encoding="utf-8"), "user-owned prompt\n")
        self.assertEqual((self.home / "config.toml").read_bytes(), original_config)

        same_name_config = (
            'model = "gpt-5.6"\n'
            f'model_instructions_file = "./{studio.PROMPT_FILENAME}"\n\n'
            '[profiles]\nname = "keep-me"\n'
        ).encode("utf-8")
        (self.home / "config.toml").write_bytes(same_name_config)
        prompt.write_text("same-name user prompt\n", encoding="utf-8")
        self.assertTrue(studio.build_plan(self.home, "max").conflict)
        with self.assertRaises(studio.ConflictError):
            studio.apply_install(self.home, "max")
        studio.apply_install(self.home, "max", force=True)
        restored = studio.restore_install(self.home)
        self.assertTrue(restored["prompt_restored"])
        self.assertEqual(prompt.read_text(encoding="utf-8"), "same-name user prompt\n")
        self.assertEqual((self.home / "config.toml").read_bytes(), same_name_config)

    def test_restore_preserves_changed_managed_prompt(self) -> None:
        studio.apply_install(self.home, "max")
        prompt = self.home / studio.PROMPT_FILENAME
        prompt.write_text("manual change after deployment\n", encoding="utf-8")
        self.assertTrue(studio.build_plan(self.home, "max").conflict)
        result = studio.restore_install(self.home)
        self.assertTrue(result["prompt_preserved"])
        self.assertTrue(prompt.exists())
        self.assertEqual((self.home / "config.toml").read_text(encoding="utf-8").splitlines()[0], 'model = "gpt-5.6"')

    def test_state_is_machine_readable(self) -> None:
        studio.apply_install(self.home, "research")
        state = json.loads((self.home / ".coldbrew-studio" / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["schema"], 1)
        self.assertEqual(state["profile"], "research")
        self.assertEqual(len(state["prompt_sha256"]), 64)

    def test_license_materials_are_readable_and_exportable(self) -> None:
        payload = studio.license_payload()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["project_source_url"], studio.PROJECT_SOURCE_URL)
        self.assertEqual(set(payload["documents"]), set(studio.LICENSE_DOCUMENT_NAMES))
        for document in payload["documents"].values():
            self.assertGreater(document["bytes"], 100)
            self.assertEqual(len(document["sha256"]), 64)

        export = studio.export_license_materials(Path(self.temp.name) / "license-export")
        for name in studio.LICENSE_DOCUMENT_NAMES:
            self.assertEqual(
                Path(export["files"][name]).read_bytes(),
                studio.runtime_document_path(name).read_bytes(),
            )
        self.assertEqual(
            Path(export["project_source_url_file"]).read_text(encoding="utf-8"),
            studio.PROJECT_SOURCE_URL + "\n",
        )


if __name__ == "__main__":
    unittest.main()
