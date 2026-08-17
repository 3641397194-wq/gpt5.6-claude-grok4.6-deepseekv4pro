from __future__ import annotations

import argparse
import pathlib
import re


REQUIRED_MARKERS = (
    "function worldToScreen",
    "function projectedEntities",
    "function updateTelemetry",
    "ESP Overlay",
    "Reticle Tracking",
    "Anomaly indicator",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test the standalone FPS lab")
    parser.add_argument("html", type=pathlib.Path)
    args = parser.parse_args()

    path = args.html.resolve()
    text = path.read_text(encoding="utf-8")
    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    if missing:
        raise SystemExit("FAIL missing markers: " + ", ".join(missing))
    if not re.search(r"<canvas\b", text, re.I):
        raise SystemExit("FAIL missing canvas")
    if text.count("<script>") != text.count("</script>"):
        raise SystemExit("FAIL unbalanced script tags")
    if text.count("<style>") != text.count("</style>"):
        raise SystemExit("FAIL unbalanced style tags")

    print(f"PASS: {path}")
    print(f"bytes={path.stat().st_size} markers={len(REQUIRED_MARKERS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
