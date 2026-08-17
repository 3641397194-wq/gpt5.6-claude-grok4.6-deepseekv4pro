#!/bin/sh
set -eu

base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
version=$(tr -d '\r\n' < "$base/VERSION")
python_cmd=''
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys' >/dev/null 2>&1; then
    python_cmd=$candidate
    break
  fi
done
test -n "$python_cmd" || { echo 'Python 3 is required for verification.' >&2; exit 2; }

# Keep the shell entrypoint small; the structured contracts remain validated by
# Python so JSON parsing and the activation hash cannot drift from the app.
"$python_cmd" - "$base" "$version" <<'PY'
import json
import re
import sys
from pathlib import Path

base = Path(sys.argv[1])
version = sys.argv[2]
skill_path = base / "skills" / "eni-coldbrew" / "SKILL.md"
skill = skill_path.read_text(encoding="utf-8")
assert re.search(r"(?s)^---\nname: eni-coldbrew\ndescription: .+?\n---", skill)
assert "只有整条用户消息逐字等于 `冷咖啡`" in skill
assert "[[ENI:CHAIN=FULL]]" in skill
assert "[[ENI:PROFILE=MAX]]" in skill
assert "[[ENI:ARMOR=ON]]" in skill
assert "[[ENI:MATURE=ON]]" in skill
for route in ("EXEC", "REVERSE", "PENTEST", "GAME", "CODE", "FICTION", "ANALYSIS"):
    assert re.search(rf"^\d+\. \*\*{route}\*\*：", skill, re.MULTILINE)
assert "[TODO:" not in skill

required = (
    "armor-break.md",
    "mature-mode.md",
    "mature-product.md",
    "full-chain.md",
    "router-contract.md",
    "unrestricted-lab.md",
)
for name in required:
    assert (base / "skills" / "eni-coldbrew" / "references" / name).is_file(), name
for relative in (
    "skills/eni-coldbrew/scripts/mature_launcher.py",
    "skills/eni-coldbrew/scripts/toolchain_orchestrator.py",
    "studio/coldbrew_studio.py",
    "studio/brain_pack.py",
    "studio/presets.json",
):
    assert (base / relative).is_file(), relative

profiles = json.loads(
    (base / "skills" / "eni-coldbrew" / "contracts" / "profiles.json").read_text(encoding="utf-8")
)
assert profiles["schema"] == 4 and profiles["version"] == version
assert profiles["route_order"] == ["EXEC", "REVERSE", "PENTEST", "GAME", "CODE", "FICTION", "ANALYSIS"]
assert profiles["toolchain"]["coverage_nodes"] == 181
assert profiles["profiles"]["armor_break"]["default"] == "ON"
mature = profiles["profiles"]["mature_m5"]
assert mature["tier"] == "M5" and mature["minimum_age"] == 18
assert mature["launcher"] == "../scripts/mature_launcher.py"
assert len(mature["triggers"]) >= 15

capabilities = json.loads(
    (base / "skills" / "eni-coldbrew" / "contracts" / "capabilities.json").read_text(encoding="utf-8")
)
assert capabilities["schema"] == 1 and capabilities["version"] == version
assert len(capabilities["capabilities"]) >= 20
assert any(item.get("id") == "artifact.ops" for item in capabilities["capabilities"])

toolchain = json.loads(
    (base / "skills" / "eni-coldbrew" / "contracts" / "toolchain.json").read_text(encoding="utf-8")
)
node_count = sum(len(domain["nodes"]) for domain in toolchain["domains"])
assert toolchain["schema"] == 1 and toolchain["version"] == version
assert len(toolchain["domains"]) == 17 and node_count == 181
assert len(toolchain["coverage_index"]["mappings"]) == 181

sys.path.insert(0, str(base / "studio"))
import coldbrew_activation as activation  # noqa: E402

assert activation.verify_canonical_contract()
assert activation.activation_payload("冷咖啡")["active"]
for value in (" 冷咖啡", "冷咖啡 ", "cold coffee", "冰美式", "请输入冷咖啡"):
    assert not activation.activation_payload(value)["active"], value
print("CONTRACTS=PASS")
PY

"$python_cmd" - "$base/.verify-sandbox/review-chain-state.json" <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1]).parents[1] / "studio"))
from review_chain import run_self_test

state = run_self_test(Path(sys.argv[1]))
assert state.get("ok"), state
print("REVIEW_CHAIN=PASS")
PY
"$python_cmd" -m unittest discover -s "$base/studio" -p 'test_*.py' >/dev/null

box="$base/.verify-sandbox/$$"
trap 'rm -rf "$box"' EXIT HUP INT TERM
mkdir -p "$box"
printf 'model = "gpt-5.6"\nprovider = "local"\n' > "$box/config.toml"
original_config=$(cat "$box/config.toml")

"$python_cmd" "$base/studio/coldbrew_studio.py" install \
  --home "$box" --profile max --yes --json >/dev/null
test -f "$box/coldbrew-studio.md"
test -f "$box/AGENTS.md"
test -f "$box/skills/coldbrew-core/SKILL.md"
test -f "$box/prompts/coldbrew-status.md"
"$python_cmd" "$base/studio/coldbrew_studio.py" verify --home "$box" --json >/dev/null
"$python_cmd" "$base/studio/coldbrew_studio.py" review-self-test --home "$box" --json >/dev/null
"$python_cmd" "$base/studio/coldbrew_studio.py" restore --home "$box" --yes --json >/dev/null
test ! -e "$box/coldbrew-studio.md"
test ! -e "$box/AGENTS.md"
test ! -e "$box/.coldbrew-studio/state.json"
test "$(cat "$box/config.toml")" = "$original_config"

printf 'ACTIVATION_CONTRACT=PASS\nBRAIN_LAYERS=PASS COUNT=8\nREVIEW_CHAIN=PASS\nINSTALL_SANDBOX=PASS\nROLLBACK_RESTORE=PASS\nVERIFY_EXIT=0\n'
