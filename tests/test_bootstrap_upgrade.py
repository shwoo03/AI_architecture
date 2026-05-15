from tests.test_support import *


class BootstrapIntegrationTests(unittest.TestCase):
    """End-to-end: bootstrap a new project into a tmpdir and verify it.

    This is the single most valuable test in the file: it exercises copy
    semantics, profile seeding, knowledge seeding, and then runs the full
    verifier against the produced tree. A regression in any of those steps
    fails this one test.
    """

    def test_new_project_then_verify(self) -> None:
        tmp = _make_external_tmpdir_or_skip(self, "skeleton-smoke")
        fake_clone = (
            REPO_ROOT
            / "runtime"
            / "external-repos"
            / "test.invalid"
            / "example__service"
        )
        try:
            fake_clone.mkdir(parents=True, exist_ok=True)
            (fake_clone / "README.md").write_text(
                "# fake external repo\n", encoding="utf-8"
            )
            target = tmp / "proj"
            # bootstrap
            result = _run(
                [
                    str(SCRIPTS / "bootstrap" / "new-project.py"),
                    "--name",
                    "smoke",
                    "--target",
                    str(target),
                    "--domain",
                    "test",
                    "--stack",
                    "python",
                    "--owner",
                    "tester",
                    "--profile",
                    "cli",
                ]
            )
            self.assertEqual(
                result.returncode,
                0,
                f"new-project failed:\nstdout={result.stdout}\nstderr={result.stderr}",
            )
            self.assertTrue((target / "CLAUDE.md").exists())
            self.assertTrue((target / "docs" / "PROJECT_PROFILE.md").exists())
            self.assertTrue((target / "docs" / "REFERENCE_REVIEW.template.md").exists())
            self.assertTrue((target / "docs" / "RUNTIME_STARTUP.template.md").exists())
            self.assertTrue((target / ".codex" / "skills").is_dir())
            self.assertTrue((target / ".claude" / "skills").is_dir())
            self.assertTrue((target / "runtime" / "install-state.jsonl").exists())
            self.assertTrue((target / "runtime" / "skill-usage.jsonl").exists())
            self.assertTrue((target / "runtime" / "skill-lifecycle.jsonl").exists())
            self.assertTrue((target / "runtime" / "session-snapshot.json").exists())
            self.assertTrue((target / "runtime" / "external-repos" / "README.md").exists())
            self.assertFalse(
                (target / "runtime" / "external-repos" / "test.invalid").exists(),
                "bootstrap must not copy external repo clones into new projects",
            )

            # verify the produced project
            verify = _run(
                [
                    str(SCRIPTS / "verify-skeleton.py"),
                    "--root",
                    str(target),
                    "--skip-wiki-lint",
                ]
            )
            self.assertEqual(
                verify.returncode,
                0,
                f"verify-skeleton on bootstrapped project failed:\n"
                f"stdout={verify.stdout}\nstderr={verify.stderr}",
            )
            parity = _run([str(SCRIPTS / "verify-parity.py"), "--root", str(target)])
            self.assertEqual(parity.returncode, 0, parity.stdout + parity.stderr)
            install_state = (target / "runtime" / "install-state.jsonl").read_text(encoding="utf-8").strip().splitlines()
            self.assertGreaterEqual(len(install_state), 2)
            bootstrap_record = json.loads(install_state[0])
            self.assertEqual(bootstrap_record["requested_profile"], "cli")
            self.assertIn("cli", bootstrap_record["selected_components"])
        finally:
            shutil.rmtree(fake_clone.parent, ignore_errors=True)
            shutil.rmtree(tmp, ignore_errors=True)

class UpgradeFromSkeletonTests(unittest.TestCase):
    """Existing projects must receive safe missing skeleton files without
    clobbering project-owned or locally edited files."""

    SCRIPT = SCRIPTS / "upgrade-from-skeleton.py"

    def test_dry_run_reports_missing_safe_files_and_risky_updates(self) -> None:
        tmp = _make_external_tmpdir_or_skip(self, "skeleton-upgrade-dry-run")
        try:
            target = tmp / "proj"
            (target / "docs").mkdir(parents=True)
            (target / "AGENTS.md").write_text("# project custom agent rules\n", encoding="utf-8")

            result = _run(
                [str(self.SCRIPT), "--target", str(target), "--json"],
                cwd=REPO_ROOT,
            )
            self.assertEqual(
                result.returncode,
                0,
                f"upgrade dry-run failed:\nstdout={result.stdout}\nstderr={result.stderr}",
            )
            payload = json.loads(result.stdout)
            by_path = {item["path"]: item for item in payload["actions"]}
            self.assertEqual(by_path["docs/REFERENCE_REVIEW.template.md"]["action"], "add")
            self.assertEqual(by_path["docs/REFERENCE_REVIEW.template.md"]["safety"], "safe")
            self.assertEqual(by_path["AGENTS.md"]["action"], "review")
            self.assertEqual(by_path["AGENTS.md"]["safety"], "manual")
            self.assertEqual(by_path["AGENTS.md"]["owner"], "manual_merge")
            self.assertEqual(by_path["AGENTS.md"]["ownership_action"], "manual_merge")
            self.assertFalse(
                (target / "docs" / "REFERENCE_REVIEW.template.md").exists(),
                "dry-run must not copy files",
            )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_brief_json_is_dry_run_ai_summary(self) -> None:
        tmp = _make_external_tmpdir_or_skip(self, "skeleton-upgrade-brief")
        try:
            target = tmp / "proj"
            target.mkdir(parents=True)
            (target / "AGENTS.md").write_text("# project custom agent rules\n", encoding="utf-8")
            before = sorted(path.relative_to(target).as_posix() for path in target.rglob("*"))
            result = _run(
                [str(self.SCRIPT), "--target", str(target), "--brief", "--format", "json"],
                cwd=REPO_ROOT,
            )
            after = sorted(path.relative_to(target).as_posix() for path in target.rglob("*"))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(before, after)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["dry_run"])
            brief = payload["brief"]
            self.assertEqual(brief["profile"], "stable")
            self.assertIn("docs/REFERENCE_REVIEW.template.md", {item["path"] for item in brief["safe_additions"]})
            self.assertIn("AGENTS.md", {item["path"] for item in brief["manual_reviews"]})
            safe_item = next(item for item in brief["safe_additions"] if item["path"] == "docs/REFERENCE_REVIEW.template.md")
            self.assertEqual(safe_item["feature_id"], "upgrade-brief")
            self.assertEqual(safe_item["tier"], "stable")
            self.assertTrue(safe_item["overlay_default"])
            self.assertFalse(safe_item["approval_required"])
            self.assertTrue(brief["approval_required"])
            self.assertIn("not approval", brief["approval_note"])
            self.assertIn("python3 scripts/quality-gate.py --format json", brief["validation_commands"])
            self.assertIn("AGENTS.md", brief["manual_merge_order"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_ownership_aware_upgrade_classifies_system_owned_and_config_seed(self) -> None:
        tmp = _make_external_tmpdir_or_skip(self, "skeleton-upgrade-ownership")
        try:
            target = tmp / "proj"
            (target / "scripts").mkdir(parents=True)
            (target / "scripts" / "agent-flow.py").write_text("print('local')\n", encoding="utf-8")

            result = _run(
                [str(self.SCRIPT), "--target", str(target), "--format", "json"],
                cwd=REPO_ROOT,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            by_path = {item["path"]: item for item in json.loads(result.stdout)["actions"]}
            self.assertEqual(by_path["scripts/agent-flow.py"]["owner"], "system_owned")
            self.assertEqual(by_path["scripts/agent-flow.py"]["ownership_action"], "update_system")
            self.assertEqual(by_path["scripts/agent-flow.py"]["action"], "update_available")
            self.assertEqual(by_path["scripts/agent-flow.py"]["safety"], "risky")
            self.assertTrue(by_path["scripts/agent-flow.py"]["system_locked"])
            self.assertEqual(by_path["config/ownership.yaml"]["action"], "add")
            self.assertEqual(by_path["config/ownership.yaml"]["safety"], "safe")
            self.assertEqual(by_path["runtime/ownership-classification.lock.json"]["action"], "add")
            self.assertEqual(by_path["runtime/ownership-classification.lock.json"]["safety"], "safe")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_brief_profiles_expose_incubating_and_experimental_with_warnings(self) -> None:
        tmp = _make_external_tmpdir_or_skip(self, "skeleton-upgrade-brief-profile")
        try:
            target = tmp / "proj"
            target.mkdir(parents=True)
            stable = _run(
                [str(self.SCRIPT), "--target", str(target), "--brief", "--profile", "stable", "--format", "json"],
                cwd=REPO_ROOT,
            )
            incubating = _run(
                [str(self.SCRIPT), "--target", str(target), "--brief", "--profile", "incubating", "--format", "json"],
                cwd=REPO_ROOT,
            )
            all_profile = _run(
                [str(self.SCRIPT), "--target", str(target), "--brief", "--profile", "all", "--format", "json"],
                cwd=REPO_ROOT,
            )
            self.assertEqual(stable.returncode, 0, stable.stdout + stable.stderr)
            self.assertEqual(incubating.returncode, 0, incubating.stdout + incubating.stderr)
            self.assertEqual(all_profile.returncode, 0, all_profile.stdout + all_profile.stderr)
            stable_brief = json.loads(stable.stdout)["brief"]
            incubating_brief = json.loads(incubating.stdout)["brief"]
            all_brief = json.loads(all_profile.stdout)["brief"]
            stable_tiers = {item["tier"] for bucket in ("safe_additions", "manual_reviews", "risky_reviews", "protected_skips") for item in stable_brief[bucket]}
            incubating_items = [item for bucket in ("safe_additions", "manual_reviews", "risky_reviews", "protected_skips") for item in incubating_brief[bucket] if item["tier"] == "incubating"]
            experimental_items = [item for bucket in ("safe_additions", "manual_reviews", "risky_reviews", "protected_skips") for item in all_brief[bucket] if item["tier"] == "experimental"]
            self.assertEqual(stable_tiers, {"stable"})
            self.assertTrue(incubating_items)
            self.assertTrue(any(item["tier_warning"] for item in incubating_items))
            self.assertTrue(experimental_items)
            self.assertTrue(all(item["approval_required"] for item in experimental_items))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_stable_profile_excludes_incubating_overlay_actions(self) -> None:
        tmp = _make_external_tmpdir_or_skip(self, "skeleton-upgrade-stable-profile")
        try:
            target = tmp / "proj"
            target.mkdir(parents=True)
            result = _run(
                [str(self.SCRIPT), "--target", str(target), "--brief", "--profile", "stable", "--format", "json"],
                cwd=REPO_ROOT,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            brief_paths = {
                item["path"]
                for bucket in ("safe_additions", "manual_reviews", "risky_reviews", "protected_skips")
                for item in payload["brief"][bucket]
            }
            self.assertNotIn("scripts/incubating/agent-run.py", brief_paths)
            self.assertNotIn("scripts/incubating/agent-flow-delegate.py", brief_paths)
            by_path = {item["path"]: item for item in payload["actions"]}
            self.assertEqual(by_path["scripts/incubating/agent-run.py"]["action"], "skip")
            self.assertEqual(by_path["scripts/incubating/agent-run.py"]["safety"], "profile")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agents_layer_is_opt_in(self) -> None:
        tmp = _make_external_tmpdir_or_skip(self, "skeleton-upgrade-agents-opt-in")
        try:
            target = tmp / "proj"
            target.mkdir(parents=True)
            default = _run(
                [str(self.SCRIPT), "--target", str(target), "--format", "json"],
                cwd=REPO_ROOT,
            )
            opt_in = _run(
                [str(self.SCRIPT), "--target", str(target), "--include-personal-skills", "--format", "json"],
                cwd=REPO_ROOT,
            )
            self.assertEqual(default.returncode, 0, default.stdout + default.stderr)
            self.assertEqual(opt_in.returncode, 0, opt_in.stdout + opt_in.stderr)
            default_paths = {item["path"] for item in json.loads(default.stdout)["actions"]}
            opt_in_paths = {item["path"] for item in json.loads(opt_in.stdout)["actions"]}
            self.assertFalse(any(path.startswith(".agents/") for path in default_paths))
            self.assertTrue(any(path.startswith(".agents/") for path in opt_in_paths))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_safe_only_apply_copies_stable_operating_bundle(self) -> None:
        tmp = _make_external_tmpdir_or_skip(self, "skeleton-upgrade-stable-bundle")
        try:
            target = tmp / "proj"
            target.mkdir(parents=True)
            result = _run(
                [str(self.SCRIPT), "--target", str(target), "--apply", "--safe-only", "--profile", "stable", "--format", "json"],
                cwd=REPO_ROOT,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((target / "scripts" / "agent-flow.py").exists())
            self.assertTrue((target / "scripts" / "quality-gate.py").exists())
            self.assertTrue((target / "docs" / "OPERATING_LOOP.md").exists())
            self.assertTrue((target / "rules" / "common" / "README.md").exists())
            self.assertTrue((target / "schemas" / "runtime-event.schema.json").exists())
            self.assertTrue((target / "skills" / "active" / "search-first" / "SKILL.md").exists())
            self.assertFalse((target / "scripts" / "incubating" / "agent-run.py").exists())
            applied_paths = {item["path"] for item in json.loads(result.stdout)["actions"] if item.get("applied")}
            self.assertIn("scripts/agent-flow.py", applied_paths)
            self.assertNotIn("scripts/incubating/agent-run.py", applied_paths)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_reference_candidates_are_not_overlaid(self) -> None:
        tmp = _make_external_tmpdir_or_skip(self, "skeleton-upgrade-reference-collision")
        try:
            target = tmp / "proj"
            candidate = target / "research" / "reference-candidates" / "project.md"
            candidate.parent.mkdir(parents=True)
            candidate.write_text("# Project candidate\n", encoding="utf-8")
            result = _run(
                [str(self.SCRIPT), "--target", str(target), "--format", "json"],
                cwd=REPO_ROOT,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            paths = {item["path"] for item in json.loads(result.stdout)["actions"]}
            self.assertFalse(any(path.startswith("research/reference-candidates/") for path in paths))
            self.assertEqual(candidate.read_text(encoding="utf-8"), "# Project candidate\n")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_brief_rejects_apply(self) -> None:
        tmp = _make_external_tmpdir_or_skip(self, "skeleton-upgrade-brief-apply")
        try:
            target = tmp / "proj"
            target.mkdir(parents=True)
            result = _run(
                [str(self.SCRIPT), "--target", str(target), "--brief", "--apply", "--format", "json"],
                cwd=REPO_ROOT,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("dry-run only", result.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_safe_only_apply_copies_missing_templates_without_overwrite(self) -> None:
        tmp = _make_external_tmpdir_or_skip(self, "skeleton-upgrade-safe-apply")
        try:
            target = tmp / "proj"
            target.mkdir(parents=True)
            custom_agents = "# project custom agent rules\n"
            (target / "AGENTS.md").write_text(custom_agents, encoding="utf-8")

            result = _run(
                [
                    str(self.SCRIPT),
                    "--target",
                    str(target),
                    "--apply",
                    "--safe-only",
                    "--json",
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(
                result.returncode,
                0,
                f"upgrade safe apply failed:\nstdout={result.stdout}\nstderr={result.stderr}",
            )
            self.assertEqual((target / "AGENTS.md").read_text(encoding="utf-8"), custom_agents)
            self.assertTrue((target / "docs" / "REFERENCE_REVIEW.template.md").exists())
            self.assertTrue((target / "docs" / "RUNTIME_STARTUP.template.md").exists())
            self.assertTrue((target / "runtime" / "activity-log.jsonl").exists())
            payload = json.loads(result.stdout)
            applied = {
                item["path"]
                for item in payload["actions"]
                if item["applied"]
            }
            self.assertIn("docs/REFERENCE_REVIEW.template.md", applied)
            self.assertNotIn("AGENTS.md", applied)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

class SkeletonDoctorTests(unittest.TestCase):
    """`skeleton-doctor.py` is the operator-facing readiness diagnostic.

    It must stay read-only, emit parseable JSON for automation, and fail fast
    on invalid roots.
    """

    SCRIPT = SCRIPTS / "skeleton-doctor.py"

    def test_current_skeleton_doctor_passes(self) -> None:
        result = _run([str(self.SCRIPT), "--root", str(REPO_ROOT)], cwd=REPO_ROOT)
        self.assertEqual(
            result.returncode,
            0,
            f"doctor failed:\nstdout={result.stdout}\nstderr={result.stderr}",
        )
        self.assertIn("Skeleton Doctor", result.stdout)
        self.assertIn("verify-skeleton", result.stdout)

    def test_json_output_is_parseable(self) -> None:
        result = _run(
            [str(self.SCRIPT), "--root", str(REPO_ROOT), "--format", "json"],
            cwd=REPO_ROOT,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"doctor json failed:\nstdout={result.stdout}\nstderr={result.stderr}",
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["root"], str(REPO_ROOT.resolve()))
        self.assertTrue(payload["checks"])

    def test_bad_root_exits_two(self) -> None:
        result = _run(
            [str(self.SCRIPT), "--root", str(REPO_ROOT / "does-not-exist")],
            cwd=REPO_ROOT,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("root not a directory", result.stderr)
