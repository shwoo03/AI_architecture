from tests.test_support import *


class OwnershipInitializeTests(unittest.TestCase):
    SCRIPT = SCRIPTS / "ownership-initialize.py"

    def test_empty_target_emits_empty_draft(self) -> None:
        tmp = _make_external_tmpdir_or_skip(self, "ownership-init-empty")
        try:
            target = tmp / "proj"
            target.mkdir(parents=True)
            result = _run([str(self.SCRIPT), "--target", str(target), "--format", "json"], cwd=REPO_ROOT)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "draft")
            self.assertEqual(payload["analyzed_paths"], 0)
            self.assertEqual(payload["candidate_paths"], 0)
            self.assertEqual(payload["draft_yaml"], "project_overrides:\n  rules: []\n")
            self.assertFalse((target / "config" / "ownership.yaml").exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_target_specific_paths_are_grouped_by_directory_depth(self) -> None:
        tmp = _make_external_tmpdir_or_skip(self, "ownership-init-groups")
        try:
            target = tmp / "proj"
            (target / "apps" / "web" / "src").mkdir(parents=True)
            (target / "infra").mkdir(parents=True)
            (target / "apps" / "web" / "src" / "page.ts").write_text("export default 1\n", encoding="utf-8")
            (target / "apps" / "web" / "package.json").write_text("{}\n", encoding="utf-8")
            (target / "infra" / "main.tf").write_text("terraform {}\n", encoding="utf-8")
            result = _run([str(self.SCRIPT), "--target", str(target), "--format", "json"], cwd=REPO_ROOT)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            patterns = {item["pattern"] for item in payload["groups"]}
            self.assertIn("apps/web/**", patterns)
            self.assertIn("infra/**", patterns)
            self.assertIn("    - pattern: apps/web/**", payload["draft_yaml"])
            self.assertIn("      owner: project_owned", payload["draft_yaml"])
            self.assertFalse((target / "config" / "ownership.yaml").exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_existing_config_without_lock_emits_lock_next_step_only(self) -> None:
        tmp = _make_external_tmpdir_or_skip(self, "ownership-init-lock-missing")
        try:
            target = tmp / "proj"
            (target / "config").mkdir(parents=True)
            (target / "config" / "ownership.yaml").write_text("schema_version: ai-architecture.ownership.v1\n", encoding="utf-8")
            result = _run([str(self.SCRIPT), "--target", str(target), "--format", "json"], cwd=REPO_ROOT)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "lock_missing")
            self.assertEqual(payload["draft_yaml"], "")
            self.assertIn("ownership-lock.py", payload["next_command"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_already_initialized_target_is_refused(self) -> None:
        tmp = _make_external_tmpdir_or_skip(self, "ownership-init-existing")
        try:
            target = tmp / "proj"
            (target / "config").mkdir(parents=True)
            (target / "runtime").mkdir(parents=True)
            (target / "config" / "ownership.yaml").write_text("schema_version: ai-architecture.ownership.v1\n", encoding="utf-8")
            (target / "runtime" / "ownership-classification.lock.json").write_text("{}\n", encoding="utf-8")
            result = _run([str(self.SCRIPT), "--target", str(target), "--format", "json"], cwd=REPO_ROOT)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "already_initialized")
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["draft_yaml"], "")
            self.assertIn("ownership-lock.py", payload["next_command"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
