from tests.test_support import *


class SkeletonSelfClassificationTests(unittest.TestCase):
    def _module(self):
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location("lib_ownership", SCRIPTS / "lib_ownership.py")
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def test_skeleton_paths_have_no_unknown_ownership(self) -> None:
        ownership = self._module()
        config = ownership.load_ownership_config(REPO_ROOT / "config" / "ownership.yaml")
        report = ownership.classify_self(REPO_ROOT, config)
        self.assertEqual(report.unknown, [])
        self.assertGreater(report.total, 100)

    def test_core_paths_classify_to_expected_owners(self) -> None:
        ownership = self._module()
        config = ownership.load_ownership_config(REPO_ROOT / "config" / "ownership.yaml")
        report = ownership.classify_self(
            REPO_ROOT,
            config,
            paths=[
                "scripts/agent-flow.py",
                "scripts/ownership-lock.py",
                "runtime/activity-log.jsonl",
                "docs/OWNERSHIP_MODEL.md",
                "docs/VERSION_ROADMAP.md",
                "docs/PROJECT_PROFILE.template.md",
                "CLAUDE.md",
                "runtime/ownership-classification.lock.json",
            ],
        )
        self.assertEqual(report.classifications["scripts/agent-flow.py"].owner, "system_owned")
        self.assertTrue(report.classifications["scripts/agent-flow.py"].system_locked)
        self.assertEqual(report.classifications["scripts/ownership-lock.py"].owner, "system_owned")
        self.assertTrue(report.classifications["scripts/ownership-lock.py"].system_locked)
        self.assertEqual(report.classifications["runtime/activity-log.jsonl"].action, "protected_preserve")
        self.assertEqual(report.classifications["docs/OWNERSHIP_MODEL.md"].owner, "system_owned")
        self.assertTrue(report.classifications["docs/OWNERSHIP_MODEL.md"].system_locked)
        self.assertEqual(report.classifications["docs/VERSION_ROADMAP.md"].owner, "system_owned")
        self.assertTrue(report.classifications["docs/VERSION_ROADMAP.md"].system_locked)
        self.assertEqual(report.classifications["docs/PROJECT_PROFILE.template.md"].owner, "system_owned")
        self.assertEqual(report.classifications["CLAUDE.md"].owner, "manual_merge")
        self.assertTrue(report.classifications["CLAUDE.md"].system_locked)
        self.assertEqual(report.classifications["runtime/ownership-classification.lock.json"].owner, "project_owned")

    def test_source_equals_target_idempotence_short_circuits_to_unchanged(self) -> None:
        ownership = self._module()
        config = ownership.load_ownership_config(REPO_ROOT / "config" / "ownership.yaml")
        for rel in ["scripts/agent-flow.py", "docs/OPERATING_LOOP.md", "CLAUDE.md"]:
            with self.subTest(path=rel):
                result = ownership.classify_path(rel, config, source_exists=True, target_exists=True, content_equal=True)
                self.assertEqual(result.action, "unchanged")

    def test_ownership_lock_matches_current_skeleton_classification(self) -> None:
        ownership = self._module()
        config = ownership.load_ownership_config(REPO_ROOT / "config" / "ownership.yaml")
        changes = ownership.lock_changes_for_root(
            REPO_ROOT,
            config,
            REPO_ROOT / "runtime" / "ownership-classification.lock.json",
        )
        self.assertEqual([change for change in changes if change.kind == "classification_drift"], [])
