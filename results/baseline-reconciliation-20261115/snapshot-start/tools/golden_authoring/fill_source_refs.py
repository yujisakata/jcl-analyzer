"""Authoring aid: insert/refresh `source_reference` blocks in Golden cases from specs/rules.yaml.

source_reference is a required, self-contained attribute of every case (Step 3 instruction 1.1),
but it must never drift from the rule registry. The loader rejects any mismatch; this script
writes the registry values after each `rule_ids:` line. It edits the text in place (keeping
anchors and comments) and does not touch expected values. Run it before sealing.

usage: uv run python tools/golden_authoring/fill_source_refs.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from jclprof.harness.registry import load_rules

ROOT = Path(__file__).resolve().parents[2]
RULE_LINE = re.compile(r"^(?P<indent>\s*)rule_ids: \[(?P<ids>[^\]]*)\]\s*$")
BLOCK_RULE_LINE = re.compile(r"^(?P<indent>\s*)rule_ids:\s*$")
BLOCK_ITEM = re.compile(r"^\s*- (?P<id>[A-Z0-9-]+)\s*$")


def main() -> None:
    registry = load_rules(ROOT / "specs" / "rules.yaml")
    for f in sorted((ROOT / "tests" / "golden" / "cases").glob("*.yaml")):
        lines = f.read_text(encoding="utf-8").split("\n")
        out: list[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            out.append(line)
            m = RULE_LINE.match(line)
            i += 1
            if not m:
                bm = BLOCK_RULE_LINE.match(line)
                if not bm:
                    continue
                # block-style list ("rule_ids:" followed by "- ID" lines): rewrite as flow style
                ids_block: list[str] = []
                while i < len(lines) and BLOCK_ITEM.match(lines[i]):
                    ids_block.append(BLOCK_ITEM.match(lines[i])["id"])  # type: ignore[index]
                    i += 1
                out[-1] = f"{bm['indent']}rule_ids: [{', '.join(ids_block)}]"
                m = RULE_LINE.match(out[-1])
                assert m
            # drop an existing block
            if i < len(lines) and lines[i].strip() == "source_reference:":
                i += 1
                while i < len(lines) and lines[i].startswith(m["indent"] + "  - {rule_id:"):
                    i += 1
            ids = [x.strip() for x in m["ids"].split(",") if x.strip()]
            out.append(f"{m['indent']}source_reference:")
            for ref in registry.source_references(ids):
                body = ", ".join(f"{k}: {json.dumps(v, ensure_ascii=False)}"
                                 for k, v in ref.items())
                out.append(f"{m['indent']}  - {{{body}}}")
        f.write_text("\n".join(out), encoding="utf-8", newline="\n")
        print(f"updated {f.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
