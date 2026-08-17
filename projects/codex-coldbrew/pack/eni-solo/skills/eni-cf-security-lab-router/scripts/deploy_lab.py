from __future__ import annotations

import argparse
import json
import pathlib
import shutil


ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "cf-style-fps-lab"


def versioned_destination(parent: pathlib.Path, base: str) -> pathlib.Path:
    candidate = parent / base
    if not candidate.exists():
        return candidate
    index = 2
    while (parent / f"{base}-v{index}").exists():
        index += 1
    return parent / f"{base}-v{index}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy the bundled CF-style FPS lab")
    parser.add_argument("--out", type=pathlib.Path, default=pathlib.Path.cwd())
    parser.add_argument("--name", default="cf-style-fps-lab")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    destination = versioned_destination(args.out.resolve(), args.name)
    shutil.copytree(SOURCE, destination)

    result = {
        "source": str(SOURCE),
        "destination": str(destination),
        "entry": str(destination / "index.html"),
        "files": sum(1 for path in destination.rglob("*") if path.is_file()),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
