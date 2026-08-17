from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from coldbrew_activation import CANONICAL_SHA256, activation_payload, activation_sha256, verify_canonical_contract
from profile_engine import compose_prompt
from transaction import deploy, preview, resolve_layout, restore, verify


class ColdBrewTests(unittest.TestCase):
    def test_canonical_contract(self):
        self.assertTrue(verify_canonical_contract())
        self.assertEqual(activation_sha256(), CANONICAL_SHA256)
        self.assertTrue(activation_payload(" 冷咖啡 ")["active"])
        self.assertTrue(activation_payload("cold coffee")["active"])
        self.assertFalse(activation_payload("请给我冷咖啡")["active"])

    def test_prompt_embeds_canonical_contract(self):
        prompt = compose_prompt("max")
        self.assertIn(CANONICAL_SHA256, prompt)
        self.assertIn(activation_payload("冷咖啡")["document"], prompt)

    def test_deploy_verify_restore_exact_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "target"
            layout = resolve_layout(home)
            layout.config.parent.mkdir(parents=True)
            baseline = b'{"user_setting": "preserve-me"}\n'
            layout.config.write_bytes(baseline)
            result = deploy(home, "max")
            self.assertTrue(result["ok"])
            self.assertTrue(verify(home)["ok"])
            config = json.loads(layout.config.read_text(encoding="utf-8"))
            self.assertEqual(config["user_setting"], "preserve-me")
            self.assertIn("coldbrew", config)
            restored = restore(home)
            self.assertTrue(restored["changed"])
            self.assertEqual(layout.config.read_bytes(), baseline)
            self.assertFalse(layout.prompt.exists())
            self.assertFalse(layout.template.exists())

    def test_redeploy_keeps_first_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "target"
            deploy(home, "max")
            deploy(home, "focused")
            self.assertTrue(verify(home)["ok"])
            restore(home)
            self.assertFalse(resolve_layout(home).config.exists())


if __name__ == "__main__":
    unittest.main()
