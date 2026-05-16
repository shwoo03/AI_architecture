from tests.test_support import *


class OwnershipClassifierTests(unittest.TestCase):
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

    def _config(self) -> dict:
        return {
            "schema_version": "ai-architecture.ownership.v1",
            "system_defaults": {
                "skip_patterns": ["dist/**", "__pycache__/**"],
                "protected": ["runtime/activity-log.jsonl"],
                "system_locked": ["scripts/agent-flow.py", "schemas/**", "AGENTS.md"],
                "rules": [
                    {"pattern": "scripts/**", "owner": "manual_merge"},
                    {"pattern": "scripts/agent-flow.py", "owner": "system_owned"},
                    {"pattern": "docs/**", "owner": "manual_merge"},
                    {"pattern": "docs/OPERATING_LOOP.md", "owner": "system_owned"},
                    {"pattern": "AGENTS.md", "owner": "manual_merge"},
                ],
            },
            "project_overrides": {
                "rules": [
                    {"pattern": "**", "owner": "project_owned"},
                    {"pattern": "docs/PROJECT.md", "owner": "manual_merge"},
                ]
            },
            "unknown_policy": {
                "source_new_file": "manual_approval",
                "target_only_file": "preserve_project",
                "both_exist_differ": "manual_merge",
                "generated_or_cache": "skip_generated",
            },
        }

    def test_protected_short_circuits_project_override(self) -> None:
        ownership = self._module()
        result = ownership.classify_path(
            "runtime/activity-log.jsonl",
            self._config(),
            source_exists=True,
            target_exists=True,
        )
        self.assertEqual(result.owner, "protected")
        self.assertEqual(result.action, "protected_preserve")
        self.assertEqual(result.matched_pattern, "runtime/activity-log.jsonl")

    def test_system_locked_blocks_broad_project_override(self) -> None:
        ownership = self._module()
        result = ownership.classify_path(
            "scripts/agent-flow.py",
            self._config(),
            source_exists=True,
            target_exists=True,
        )
        self.assertEqual(result.owner, "system_owned")
        self.assertEqual(result.action, "update_system")
        self.assertTrue(result.system_locked)

    def test_system_locked_can_still_use_system_default_manual_merge(self) -> None:
        ownership = self._module()
        result = ownership.classify_path(
            "AGENTS.md",
            self._config(),
            source_exists=True,
            target_exists=True,
        )
        self.assertEqual(result.owner, "manual_merge")
        self.assertEqual(result.action, "manual_merge")
        self.assertTrue(result.system_locked)

    def test_normal_rules_are_order_based_last_match_wins(self) -> None:
        ownership = self._module()
        result = ownership.classify_path(
            "docs/OPERATING_LOOP.md",
            self._config(),
            source_exists=True,
            target_exists=False,
        )
        self.assertEqual(result.owner, "project_owned")
        self.assertEqual(result.action, "preserve_project")
        self.assertEqual(result.reason, "project_overrides.rules")

    def test_project_override_can_make_unlocked_path_manual_merge(self) -> None:
        ownership = self._module()
        result = ownership.classify_path(
            "docs/PROJECT.md",
            self._config(),
            source_exists=True,
            target_exists=True,
        )
        self.assertEqual(result.owner, "manual_merge")
        self.assertEqual(result.action, "manual_merge")
        self.assertEqual(result.reason, "project_overrides.rules")

    def test_skip_patterns_define_generated_paths(self) -> None:
        ownership = self._module()
        result = ownership.classify_path(
            "dist/app.js",
            self._config(),
            source_exists=True,
            target_exists=False,
        )
        self.assertEqual(result.owner, "skip_generated")
        self.assertEqual(result.action, "skip_generated")

    def test_recursive_skip_patterns_match_nested_generated_paths(self) -> None:
        ownership = self._module()
        config = self._config()
        config["system_defaults"]["skip_patterns"].append("**/__pycache__/**")
        result = ownership.classify_path(
            "scripts/__pycache__/lib_ownership.cpython-314.pyc",
            config,
            source_exists=True,
            target_exists=True,
        )
        self.assertEqual(result.owner, "skip_generated")
        self.assertEqual(result.action, "skip_generated")

    def test_unknown_policy_distinguishes_source_and_target(self) -> None:
        ownership = self._module()
        config = self._config()
        config["project_overrides"]["rules"] = []
        source_only = ownership.classify_path("new-tool.txt", config, source_exists=True, target_exists=False)
        target_only = ownership.classify_path("local-note.txt", config, source_exists=False, target_exists=True)
        both = ownership.classify_path("shared-note.txt", config, source_exists=True, target_exists=True)
        self.assertEqual(source_only.action, "manual_approval")
        self.assertEqual(target_only.action, "preserve_project")
        self.assertEqual(both.action, "manual_merge")

    def test_content_identical_short_circuits_after_skip_before_owner_action(self) -> None:
        ownership = self._module()
        result = ownership.classify_path(
            "runtime/activity-log.jsonl",
            self._config(),
            source_exists=True,
            target_exists=True,
            content_equal=True,
        )
        self.assertEqual(result.owner, "unchanged")
        self.assertEqual(result.action, "unchanged")

    def test_lock_compare_only_halts_on_existing_owner_or_action_drift(self) -> None:
        ownership = self._module()
        current = {
            "added.md": ownership.Classification("added.md", "system_owned", "add_system", "test"),
            "changed.md": ownership.Classification("changed.md", "project_owned", "preserve_project", "test"),
        }
        locked = {
            "removed.md": {"owner": "manual_merge", "action": "manual_merge"},
            "changed.md": {"owner": "system_owned", "action": "update_system"},
        }
        changes = ownership.compare_lock(current, locked)
        kinds = {change.path: change.kind for change in changes}
        self.assertEqual(kinds["added.md"], "lock_addition")
        self.assertEqual(kinds["removed.md"], "lock_removal")
        self.assertEqual(kinds["changed.md"], "classification_drift")

    def test_current_ownership_yaml_parses_and_classifies_new_library(self) -> None:
        ownership = self._module()
        config = ownership.load_ownership_config(REPO_ROOT / "config" / "ownership.yaml")
        result = ownership.classify_path(
            "scripts/lib_ownership.py",
            config,
            source_exists=True,
            target_exists=False,
        )
        self.assertEqual(result.owner, "system_owned")
        self.assertEqual(result.action, "add_system")
        self.assertTrue(result.system_locked)

    def test_collect_repo_paths_preserves_non_ascii_git_paths(self) -> None:
        ownership = self._module()
        tmp = Path(tempfile.mkdtemp(prefix="ownership-nonascii-"))
        try:
            (tmp / "주제").write_text("topic\n", encoding="utf-8")
            for command in (
                ["git", "init"],
                ["git", "config", "user.email", "test@example.invalid"],
                ["git", "config", "user.name", "Test User"],
                ["git", "add", "."],
                ["git", "commit", "-m", "initial"],
            ):
                result = subprocess.run(command, cwd=str(tmp), capture_output=True, text=True, encoding="utf-8", timeout=30)
                if result.returncode != 0:
                    self.skipTest(f"git unavailable for non-ascii ownership test: {result.stderr or result.stdout}")
            paths = ownership.collect_repo_paths(tmp)
            self.assertIn("주제", paths)
            self.assertNotIn('"\\354\\243\\274\\354\\240\\234"', paths)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
