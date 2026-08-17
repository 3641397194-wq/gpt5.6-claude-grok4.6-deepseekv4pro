# ColdBrew Studio

ColdBrew Studio is the product layer for the ColdBrew project. It gives a
new user one place to detect a Codex home, preview a deployment, install an
instruction profile, verify the result, and restore the previous configuration.

The implementation is intentionally standard-library only:

- `coldbrew_studio.py gui` opens the desktop window;
- `coldbrew_studio.py plan` previews the exact managed files;
- `coldbrew_studio.py install --profile max --yes` performs a one-click-style deployment;
- `coldbrew_studio.py verify` checks the prompt hash and root TOML pointer;
- `coldbrew_studio.py restore --yes` returns the previous pointer and removes the managed prompt when its hash still matches.

Studio owns only `coldbrew-studio.md`, the root-level
`model_instructions_file` entry, and `.coldbrew-studio/state.json`. Existing
provider, model, authentication, and unrelated project settings remain outside
its managed surface. Every write is atomic and every replacement creates a
timestamped snapshot under `.coldbrew-studio/snapshots/`.

The profile contract is in `presets.json`. The profiles are independently
written product presets; the existing `eni-coldbrew` Skill and its contracts
remain available for users who prefer direct Skill installation.
