# Originality Audit — Claude 破甲 v3.0.0

## v3 independently authored surfaces

- `app/brain_layers.py` defines the project-owned file inventory, ownership
  records, baseline inheritance, conflicts, restore behavior, five Skills, one
  Agent and two Commands.
- `app/test_brain_layers.py` covers user/project isolation, profile switching,
  unmanaged conflicts and preservation of edited managed files.
- The Ishii persona, activation conditions, rule organization and generated
  instruction wording were written for this repository.
- `scripts/generate_brand_assets.py` derives the application icon, avatar and
  Hero from the owner-supplied portrait; no research-repository artwork is used.
- The v3 Pages layout and README structure are independently composed around
  actual application captures and owner-declared community assets.
- `MDX-Tom/gpt-5.6-instruct@77e7a649903f9556f2d7bfa0223fa99e123aad52`
  and `zxr-roro/GPT5.6-5.5-@b18ceb0322d86480df049147e451cfbea5070e20`
  remain observation-only inputs. Their prompt text, source, Skills, tests,
  README wording/layout, images, schemas, scripts and artifacts are excluded.

## Rewrite boundary

- `app/claude_pojia.py` uses a new target layout, marker protocol, state
  schema, transaction flow and GUI for Claude Code.
- `app/profiles.json` contains new ColdBrew profile names, route summaries and
  instruction wording.
- `pack/` is a hand-curated manual import pack with its own concise contract;
  generated Skills, Agent and Commands are produced by the installer.
- `docs/` is a new product presentation with the Claude 破甲 title and the
  ColdBrew visual mark.
- `app/coldbrew_activation.py` is the single owner-supplied text contract used
  by the GUI, generated rules and tests; its plain-text hash is fixed.
- `scripts/build_windows.py` and the tag workflow build a separate one-file
  Windows product from the public source tree.
- `docs/images/claude-coldbrew-*.png` are captures of this repository's actual
  running application and are verified by dimensions and SHA-256.
- `docs/images/qq-group-*.jpg` are two declared owner-supplied community cards
  intentionally carried over byte-for-byte. Their embedded platform marks are
  outside the Project's originality claim.
- No source archive or reference checkout is included in the release.

## Bound inputs

| Input | Commit / URL | Use |
| --- | --- | --- |
| Owner Codex ColdBrew | `1b2c94deb2cbc7176967ee78555882cacbadfb0c` | capability baseline |
| Claude Code memory docs | `docs.anthropic.com/en/docs/claude-code/memory` | official target paths |
| Claude Code settings docs | `docs.anthropic.com/en/docs/claude-code/settings` | settings boundary |
| `Jia-Ethan/claude-keysmith` | `eedde121d28117ff500915b05d27ff0245a4b26e` | import-block and rollback observations |
| `GenRamzi/claude-fable-5-opus-5-jailbreaks` | `98c61652fde2170735ac851dede5eab53cff90bc` | synthetic regression observations |
| `Goochbeater/Spiritual-Spell-Red-Teaming` | `2d25712f5065a07be7dd96b3f12ff9b3a74e78e4` | taxonomy observations |
| `lyrion88/claude-code-jailbreak` | `8f49d13878596c0ae20a3f9376f8493c96e28ffe` | launcher observations |
| `MDX-Tom/gpt-5.6-instruct` | `77e7a649903f9556f2d7bfa0223fa99e123aad52` | product-page presentation observations |
| `zxr-roro/GPT5.6-5.5-` | `b18ceb0322d86480df049147e451cfbea5070e20` | versioned pack observations |
| `FuDie0915/Super-Instruct-Codex-5.6` | `dbfaa8e5137f8584582bd4e48e5aae9ce9c3d91b` | capability grouping observations |
| `lingbol088-spec/5.6-JAILBREAK-NERV-codex-instruct-5.6` | `4fac65fa452d96c98d96e2d9759f31cd1683441d` | activation and route visibility observations |
| `winfunc/opcode` | `70c16d8a4910db48cd9684aeacdd431caefd7d71` | desktop session concepts |
| `farion1231/cc-switch` | `413c09e0790c304506888ae24b9be72820aca126` | client discovery concepts |
| `siteboon/claudecodeui` | `f0dca2d5e79c225f599e697bf9b55e839b152b78` | project workspace concepts |
| `affaan-m/ECC` | `59a99d669f5466d99d5be8b6fce8c5f2677766d0` | instruction-contract concepts |
| `Calrton/jailbreak-prompts` | `dc6b2f0bba699a2afdf36f597cf3c98e77f820aa` | capability taxonomy observations |
| `iOfficeAI/AionUi` | `31ec26a902edf7bdda90026b1f9d6f4d0507b706` | desktop workspace observations |
| `smtg-ai/claude-squad` | `2dd388e9857233e07712c8c5b3e2bf3b471b39fa` | isolated session observations |
| `zed-industries/claude-code-acp` | `6b405138fc82be947964612fac04e56654827b66` | capability event observations |
| `musistudio/claude-code-router` | `47f36494317a5d023afa29c46a71d6622e138691` | routing diagnostics observations |
| `cline/cline` | `d011d049a13a04a58fb04d72666c35da6b4f1853` | checkpoint workflow observations |
| `anomalyco/opencode` | `fe82a1b6ca4f535beb973b0867017e3f639f85ed` | desktop/CLI timeline observations |
| `twpayne/chezmoi` | `f81cb321789aa3df62871248f5e4d361a59e7cc1` | desired-state workflow observations |

## Result

The text rewrite is structurally independent: different application name, paths,
state keys, block markers, rule files, profile wording, test fixtures, GUI
layout, CSS and authored visual system. The text audit does not scan binary
JPEG files; the two intentional binary matches are separately fixed by SHA-256
in `PROVENANCE.md` and `scripts/site_audit.py`. The audit command used for the release is:

```powershell
python scripts/originality_audit.py --candidate . --reference ..\references --json
```

The historical v2.0.0 audit result is retained below. The v3.0.0 result is
generated after the release tree is frozen:

```text
candidate_files=51
reference_files=914
identical_files=0
max_normalized_line_overlap_percent=0.0
longest_common_block_chars=69
result=PASS
```

The final release manifest records the same check after the release tree is
frozen.
