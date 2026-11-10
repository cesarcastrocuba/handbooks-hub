"""Portal Pages workflow: catalog push trigger and deploy gate."""

from __future__ import annotations

from pathlib import Path
import re
import sys
import unittest

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402

WORKFLOW = support.REPO_ROOT / ".github/workflows/portal-pages.yml"
DEPLOY_CONDITION = (
    "github.ref == 'refs/heads/main' && "
    "(github.event_name == 'push' || inputs.deploy)"
)


def deploy_allowed(ref: str, event: str, deploy: bool) -> bool:
    """Mirror the workflow expression asserted below, for the truth-table test."""

    return ref == "refs/heads/main" and (event == "push" or deploy)


class PortalPagesWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        # PyYAML reads an unquoted ``on`` key as boolean True.
        self.triggers = self.workflow.get("on") or self.workflow.get(True)

    def steps(self):
        for job in self.workflow["jobs"].values():
            yield from job["steps"]

    def test_catalog_push_on_main_triggers_the_workflow(self) -> None:
        push = self.triggers["push"]
        self.assertEqual(push["branches"], ["main"])
        self.assertEqual(push["paths"], ["catalog/**"])

    def test_manual_dispatch_keeps_its_deploy_input(self) -> None:
        deploy = self.triggers["workflow_dispatch"]["inputs"]["deploy"]
        self.assertEqual(deploy["type"], "boolean")
        self.assertFalse(deploy["default"])
        self.assertEqual(deploy["description"], "Deploy the generated catalog to Pages (main only)")

    def test_configure_pages_and_deploy_share_the_deploy_gate(self) -> None:
        configure = next(
            step
            for step in self.steps()
            if step.get("uses", "").startswith("actions/configure-pages@")
        )
        self.assertEqual(configure["if"], DEPLOY_CONDITION)
        deploy = self.workflow["jobs"]["deploy"]
        self.assertEqual(deploy["if"], DEPLOY_CONDITION)
        self.assertEqual(deploy["needs"], "build")

    def test_deploy_gate_truth_table(self) -> None:
        cases = (
            ("refs/heads/main", "push", False, True),
            ("refs/heads/main", "workflow_dispatch", True, True),
            ("refs/heads/main", "workflow_dispatch", False, False),
            ("refs/heads/feature", "workflow_dispatch", True, False),
            ("refs/heads/feature", "workflow_dispatch", False, False),
        )
        for ref, event, deploy, expected in cases:
            with self.subTest(ref=ref, event=event, deploy=deploy):
                self.assertEqual(deploy_allowed(ref, event, deploy), expected)

    def test_permissions_and_concurrency_are_unchanged(self) -> None:
        self.assertEqual(self.workflow["permissions"], {"contents": "read"})
        self.assertEqual(self.workflow["concurrency"], {"group": "portal-pages", "cancel-in-progress": False})
        self.assertEqual(
            self.workflow["jobs"]["build"]["permissions"],
            {"contents": "read", "pages": "read"},
        )
        self.assertEqual(
            self.workflow["jobs"]["deploy"]["permissions"],
            {"pages": "write", "id-token": "write"},
        )

    def test_actions_are_pinned_and_no_new_action_is_added(self) -> None:
        names = set()
        for step in self.steps():
            if "uses" not in step:
                continue
            self.assertRegex(step["uses"], re.compile(r"^[\w./-]+@[0-9a-f]{40}$"))
            names.add(step["uses"].split("@", 1)[0])
        self.assertEqual(
            names,
            {
                "actions/checkout",
                "actions/setup-python",
                "actions/configure-pages",
                "actions/upload-pages-artifact",
                "actions/deploy-pages",
            },
        )


if __name__ == "__main__":
    unittest.main()
