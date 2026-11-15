"""Specification Registry (CTX-05): rules.yaml and the diagnostic catalog."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from jclprof.diagnostics import CODES as INVENTORY_CODES

RULE_STATUSES = ("VERIFIED", "CROSS-CHECKED", "PENDING", "PROJECT-POLICY")


class RegistryError(ValueError):
    pass


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    edition: str
    url: str
    retrieved: str
    sha256: str | None


@dataclass(frozen=True)
class Rule:
    id: str
    applies_to: str
    summary: str
    conditions: str
    doc: str
    chapter: str
    section: str
    pages: str
    status: str

    @property
    def is_policy(self) -> bool:
        return self.status == "PROJECT-POLICY"


@dataclass(frozen=True)
class RuleRegistry:
    documents: dict[str, Document]
    rules: dict[str, Rule]

    def source_reference(self, rule_id: str) -> dict[str, str]:
        r = self.rules[rule_id]
        d = self.documents[r.doc]
        return {"rule_id": r.id, "url": d.url, "edition": d.edition,
                "section": f"{r.chapter} > {r.section}", "pages": r.pages}

    def source_references(self, rule_ids: list[str]) -> list[dict[str, str]]:
        return [self.source_reference(r) for r in rule_ids]


def load_rules(path: Path) -> RuleRegistry:
    data: Any = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise RegistryError(f"{path}: expected schema_version 1")
    docs = {
        k: Document(k, v["title"], v["edition"], v["url"], v["retrieved"], v.get("sha256"))
        for k, v in data["documents"].items()
    }
    rules: dict[str, Rule] = {}
    for r in data["rules"]:
        s = r["source"]
        rule = Rule(r["id"], r["applies_to"], r["summary"], r["conditions"], s["doc"],
                    s["chapter"], s["section"], s["pages"], r["status"])
        if rule.id in rules:
            raise RegistryError(f"duplicate rule id {rule.id}")
        if rule.status not in RULE_STATUSES:
            raise RegistryError(f"{rule.id}: invalid status {rule.status}")
        if rule.doc not in docs:
            raise RegistryError(f"{rule.id}: unknown document {rule.doc}")
        rules[rule.id] = rule
    return RuleRegistry(docs, rules)


def load_catalog(path: Path) -> dict[str, Any]:
    """Analyzer diagnostic catalog merged with the inventory (INV) registry."""
    data: Any = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise RegistryError(f"{path}: expected schema_version 1")
    codes: dict[str, Any] = dict(data["codes"])
    for code, c in INVENTORY_CODES.items():
        codes[code] = {"severity": c.severity, "stage": "inventory",
                       "rules": [c.rule_id] if c.rule_id else [], "title": c.title}
    return codes
