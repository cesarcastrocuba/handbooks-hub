"""Adapter drift check: thin projections of AGENTS.md, never a second policy."""

from __future__ import annotations

from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402

ROOT = support.REPO_ROOT
AGENTS = ROOT / "AGENTS.md"
CONTRACT = ROOT / "docs/adapter-contract.md"

# Real adapters registered for this repository. Add new paths here when adding an adapter.
ADAPTERS = (
    Path("CLAUDE.md"),
    Path(".github/copilot-instructions.md"),
)

MAX_LINES = 12

MAKE_TARGET = re.compile(r"\bmake\s+([a-z][a-z0-9-]*)", re.IGNORECASE)
POLICY = re.compile(
    r"\b(?:must|shall|never|always|required|prohibited|forbidden)\b|\bdo not\b",
    re.IGNORECASE,
)
STATUS = re.compile(
    r"\b(?:status|phase|release|owner|implementer|reviewer|decision)\b",
    re.IGNORECASE,
)
CHECKLIST = re.compile(r"^\s*[-*]\s*\[[ xX]\]")


def adapter_path(relative: Path) -> Path:
    return ROOT / relative


def missing_adapters(relative_paths: tuple[Path, ...] | list[Path]) -> list[str]:
    return [str(path) for path in relative_paths if not adapter_path(path).is_file()]


def make_targets(text: str) -> set[str]:
    return {match.group(1).lower() for match in MAKE_TARGET.finditer(text)}


def references_agents(text: str) -> bool:
    return re.search(r"\bAGENTS\.md\b", text) is not None


def policy_violations(text: str) -> list[str]:
    violations = []
    for number, line in enumerate(text.splitlines(), start=1):
        if POLICY.search(line) or STATUS.search(line) or CHECKLIST.match(line):
            violations.append(f"line {number}: {line.strip()}")
    return violations


def adapter_issues(name: str, text: str, agents_text: str) -> list[str]:
    issues = []
    lines = text.splitlines()
    if len(lines) > MAX_LINES:
        issues.append(f"{name}: {len(lines)} lines exceeds the {MAX_LINES}-line limit")
    if not references_agents(text):
        issues.append(f"{name}: does not reference AGENTS.md")
    allowed = make_targets(agents_text)
    for target in sorted(make_targets(text) - allowed):
        issues.append(f"{name}: names make target {target!r} not listed in AGENTS.md")
    issues.extend(f"{name}: normative or status content at {item}" for item in policy_violations(text))
    return issues


class AdapterTests(unittest.TestCase):
    def test_registered_adapters_exist(self) -> None:
        self.assertEqual(missing_adapters(ADAPTERS), [])

    def test_registered_adapters_are_projections_of_agents(self) -> None:
        agents_text = AGENTS.read_text(encoding="utf-8")
        for relative in ADAPTERS:
            with self.subTest(adapter=str(relative)):
                text = adapter_path(relative).read_text(encoding="utf-8")
                self.assertEqual(adapter_issues(str(relative), text, agents_text), [])

    def test_adapters_are_not_required_by_the_build(self) -> None:
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        names = [relative.name for relative in ADAPTERS]
        for name in names:
            self.assertNotIn(name, makefile)
        for source in (ROOT / "tools/src").rglob("*.py"):
            text = source.read_text(encoding="utf-8")
            for name in names:
                self.assertNotIn(name, text, f"{source} depends on adapter {name}")

    def test_contract_document_covers_the_adapter_rules(self) -> None:
        text = CONTRACT.read_text(encoding="utf-8")
        self.assertIn("AGENTS.md", text)
        for heading in (
            "What an adapter may contain",
            "What an adapter may not contain",
            "Which tools need an adapter",
            "Add an adapter",
        ):
            self.assertIn(heading, text)
        for target in (
            "../AGENTS.md",
            "../STATUS.md",
            "../tools/tests/test_adapters.py",
            "decisions.md",
            "implementation-plan.md",
        ):
            self.assertTrue((CONTRACT.parent / target).resolve().is_file(), target)
        for path in ("CLAUDE.md", ".github/copilot-instructions.md"):
            self.assertIn(path, text)

    def test_missing_adapter_is_rejected(self) -> None:
        missing = missing_adapters([Path("CLAUDE.md"), Path("does-not-exist.md")])
        self.assertEqual(len(missing), 1)
        self.assertIn("does-not-exist.md", missing[0])

    def test_adapter_without_agents_reference_is_rejected(self) -> None:
        issues = adapter_issues("fixture.md", "Run make check.\n", AGENTS.read_text())
        self.assertTrue(any("AGENTS.md" in issue for issue in issues), issues)

    def test_adapter_with_unknown_make_target_is_rejected(self) -> None:
        issues = adapter_issues("fixture.md", "@AGENTS.md\n\nRun make deploy.\n", AGENTS.read_text())
        self.assertTrue(any("'deploy'" in issue for issue in issues), issues)

    def test_overlong_adapter_is_rejected(self) -> None:
        text = "@AGENTS.md\n" + "tool note\n" * (MAX_LINES + 1)
        issues = adapter_issues("fixture.md", text, AGENTS.read_text())
        self.assertTrue(any("exceeds" in issue for issue in issues), issues)

    def test_normative_policy_is_rejected(self) -> None:
        issues = adapter_issues(
            "fixture.md", "@AGENTS.md\n\nYou must run make check.\n", AGENTS.read_text()
        )
        self.assertTrue(any("normative or status" in issue for issue in issues), issues)

    def test_status_content_is_rejected(self) -> None:
        issues = adapter_issues("fixture.md", "@AGENTS.md\n\nStatus: Approved.\n", AGENTS.read_text())
        self.assertTrue(any("normative or status" in issue for issue in issues), issues)

    def test_checklist_is_rejected(self) -> None:
        issues = adapter_issues("fixture.md", "@AGENTS.md\n\n- [x] reviewed\n", AGENTS.read_text())
        self.assertTrue(any("normative or status" in issue for issue in issues), issues)


if __name__ == "__main__":
    unittest.main()
