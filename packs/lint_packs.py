#!/usr/bin/env python3
"""Pack linter: mechanical consistency checks for every country pack.

For each packs/<continent>/<country>/ folder this verifies what a
human auditor should never have to check by eye again:

- pack.json parses and passes the runner's schema validation,
- README.md exists and faithfully covers the pack's data: every
  feed URL, every hunting-ground URL, every search term, and the
  first GDELT preset's query, verbatim.

Usage:
    python3 packs/lint_packs.py            # all packs
    python3 packs/lint_packs.py packs/europe/france

Exit code 0 when every checked pack is clean, 1 otherwise.
Pure standard library.
"""
import json
import sys
from pathlib import Path

PACKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PACKS_DIR))
import pack_runner  # noqa: E402


def discover_packs():
    return sorted(p.parent for p in PACKS_DIR.glob("*/*/pack.json"))


def check_pack(pack_dir):
    """Return a list of problems for one pack folder."""
    problems = []
    try:
        pack = json.loads((pack_dir / "pack.json").read_text())
    except (OSError, json.JSONDecodeError) as e:
        return [f"pack.json unreadable: {e}"]
    problems += pack_runner.validate_pack(pack)
    readme_path = pack_dir / "README.md"
    if not readme_path.exists():
        return problems + ["README.md is missing"]
    readme = readme_path.read_text(encoding="utf-8")
    for f in pack.get("feeds", []):
        if f.get("url") and f["url"] not in readme:
            problems.append(f"README does not mention feed url "
                            f"of {f.get('id')}")
    for g in pack.get("hunting_grounds", []):
        if g.get("url") and g["url"] not in readme:
            problems.append(f"README does not mention ground url "
                            f"of {g.get('id')}")
    for group, terms in (pack.get("terms") or {}).items():
        for t in terms:
            if t not in readme:
                problems.append(f"README does not carry term {t!r} "
                                f"from terms.{group}")
    presets = pack.get("gdelt_presets") or []
    if presets and presets[0].get("query") not in readme:
        problems.append("README does not carry the first GDELT "
                        "preset's query verbatim")
    return problems


def main():
    targets = [Path(a) for a in sys.argv[1:]] or discover_packs()
    if not targets:
        print("no packs found")
        return 1
    bad = 0
    for pack_dir in targets:
        problems = check_pack(pack_dir)
        label = str(pack_dir.relative_to(PACKS_DIR.parent)) \
            if pack_dir.is_relative_to(PACKS_DIR.parent) \
            else str(pack_dir)
        if problems:
            bad += 1
            print(f"{label}: {len(problems)} problem(s)")
            for p in problems:
                print(f"  - {p}")
        else:
            print(f"{label}: OK")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
