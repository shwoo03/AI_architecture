import hashlib

from tests.test_support import *


class ScriptsCompileTests(unittest.TestCase):
    """Every script must byte-compile. Catches typos at PR time, not runtime."""

    def test_all_scripts_compile(self) -> None:
        import tokenize

        failures: list[str] = []
        for path in sorted(SCRIPTS.rglob("*.py")):
            try:
                with tokenize.open(path) as handle:
                    source = handle.read()
                compile(source, str(path), "exec")
            except (OSError, SyntaxError, UnicodeDecodeError) as exc:
                failures.append(f"{path.relative_to(REPO_ROOT).as_posix()}: {exc}")
        self.assertEqual(failures, [], "scripts failed to compile:\n" + "\n".join(failures))

class ScriptHelpTests(unittest.TestCase):
    """Each primary script must produce `--help` output without errors.

    Guards against argparse misconfiguration (e.g. a `required=True` arg that
    breaks `--help` flow, or a malformed format string in a help= kwarg).
    """

    MAIN_SCRIPTS = (
        "agent-flow.py",
        "verify-skeleton.py",
        "rotate-activity-log.py",
        "wiki-lint.py",
        "bootstrap/new-project.py",
        "search-activity-log.py",
        "list-open-questions.py",
        "validate-reference-candidates.py",
        "validate-reference-proposals.py",
        "create-reference-proposal.py",
        "quality-gate.py",
        "review-queue.py",
        "upgrade-from-skeleton.py",
        "ownership-lock.py",
        "ownership-initialize.py",
        "skeleton-doctor.py",
        "security-scan.py",
        "reference-copy-ledger.py",
        "generate-codemaps.py",
        "agent-autonomy-check.py",
        "completion-evidence.py",
        "lsp-diagnostics.py",
        "cleanup-ephemeral.py",
        "resume-readiness.py",
        "skill-surface-check.py",
        "task-closeout.py",
        "convert.py",
        "verify-parity.py",
        "eval.py",
        "eval-all.py",
        "install-state.py",
        "skill-lifecycle.py",
        "cost-log.py",
        "session-snapshot.py",
        "refresh-references.py",
        "reference-inventory.py",
        "reference-intake.py",
        "verify.py",
        "portability-scan.py",
        "knowledge-search.py",
        "agent-brief.py",
        "checkpoint.py",
        "change-drift-check.py",
        "redact.py",
        "subdir-hints.py",
        "feature-status.py",
        "operational-readiness.py",
        "safe-write.py",
        "diff-quality-gate.py",
        "validate-plans.py",
        "reference-wiki.py",
        "source-recovery.py",
    )

    def test_each_main_script_prints_help(self) -> None:
        for rel in self.MAIN_SCRIPTS:
            with self.subTest(script=rel):
                result = _run([str(SCRIPTS / rel), "--help"])
                self.assertEqual(
                    result.returncode,
                    0,
                    f"--help failed for {rel}\nstdout={result.stdout}\nstderr={result.stderr}",
                )
                self.assertIn("usage:", result.stdout.lower())

class VerifySkeletonTests(unittest.TestCase):
    """`verify-skeleton.py --skip-wiki-lint` against the skeleton itself must
    exit 0. If this breaks, the structural invariants have drifted."""

    def test_skeleton_is_healthy(self) -> None:
        result = _run(
            [str(SCRIPTS / "verify-skeleton.py"), "--skip-wiki-lint"],
            cwd=REPO_ROOT,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"verify-skeleton failed:\nstdout={result.stdout}\nstderr={result.stderr}",
        )


class FeatureStatusTests(unittest.TestCase):
    SCRIPT = SCRIPTS / "feature-status.py"

    def test_manifest_is_valid_for_all_tiers(self) -> None:
        result = _run([str(self.SCRIPT), "--root", str(REPO_ROOT), "--format", "json", "check", "--tier", "all"], cwd=REPO_ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertGreater(payload["features_by_tier"]["stable"], 0)
        self.assertGreater(payload["features_by_tier"]["incubating"], 0)
        self.assertGreater(payload["features_by_tier"]["experimental"], 0)

    def test_stable_tier_does_not_validate_incubating_doc_paths(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"feature-status-{uuid.uuid4().hex}"
        try:
            (tmp / "docs").mkdir(parents=True)
            (tmp / "docs" / "stable.md").write_text("# stable\n", encoding="utf-8")
            (tmp / "docs" / "feature-status.yaml").write_text(
                "version: 1\n"
                "tiers: [stable, incubating, experimental, deprecated]\n"
                "features:\n"
                "  - id: stable.feature\n"
                "    tier: stable\n"
                "    overlay_default: true\n"
                "    docs: [docs/stable.md]\n"
                "  - id: incubating.feature\n"
                "    tier: incubating\n"
                "    overlay_default: false\n"
                "    docs: [docs/missing.md]\n",
                encoding="utf-8",
            )
            stable = _run([str(self.SCRIPT), "--root", str(tmp), "--format", "json", "check", "--tier", "stable"], cwd=REPO_ROOT)
            self.assertEqual(stable.returncode, 0, stable.stdout + stable.stderr)
            stable_payload = json.loads(stable.stdout)
            self.assertIn("incubating.feature", stable_payload["skipped_by_tier"])
            all_tiers = _run([str(self.SCRIPT), "--root", str(tmp), "--format", "json", "check", "--tier", "all"], cwd=REPO_ROOT)
            self.assertNotEqual(all_tiers.returncode, 0)
            all_payload = json.loads(all_tiers.stdout)
            self.assertEqual(all_payload["findings"][0]["check"], "doc_exists")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class ScriptCatalogValidationTests(unittest.TestCase):
    def _load_verify_module(self):
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location("verify_skeleton_module", SCRIPTS / "verify-skeleton.py")
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def _catalog_root(self, catalog_text: str, extra_scripts=None) -> Path:
        tmp = REPO_ROOT / "runtime" / f"script-catalog-{uuid.uuid4().hex}"
        scripts = tmp / "scripts"
        scripts.mkdir(parents=True)
        for rel in ["agent-flow.py", *(extra_scripts or [])]:
            path = scripts / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
        (scripts / "catalog.yaml").write_text(catalog_text, encoding="utf-8")
        return tmp

    def test_script_catalog_current_root_is_valid(self) -> None:
        result = _run([str(SCRIPTS / "verify-skeleton.py"), "--skip-wiki-lint"], cwd=REPO_ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_current_root_ownership_check_has_no_errors(self) -> None:
        module = self._load_verify_module()
        findings: list[object] = []
        module.check_ownership_classification(REPO_ROOT, findings)
        self.assertEqual([finding.detail for finding in findings if finding.level == "error"], [])

    def test_ownership_check_reports_classification_drift(self) -> None:
        module = self._load_verify_module()
        tmp = REPO_ROOT / "runtime" / f"ownership-drift-{uuid.uuid4().hex}"
        try:
            (tmp / "config").mkdir(parents=True)
            (tmp / "runtime").mkdir(parents=True)
            (tmp / "known.txt").write_text("known\n", encoding="utf-8")
            (tmp / "config" / "ownership.yaml").write_text(
                "schema_version: ai-architecture.ownership.v1\n"
                "system_defaults:\n"
                "  skip_patterns: []\n"
                "  protected: []\n"
                "  system_locked: []\n"
                "  rules:\n"
                "    - pattern: known.txt\n"
                "      owner: system_owned\n"
                "project_overrides:\n"
                "  rules: []\n"
                "unknown_policy:\n"
                "  source_new_file: manual_approval\n"
                "  target_only_file: preserve_project\n"
                "  both_exist_differ: manual_merge\n"
                "  generated_or_cache: skip_generated\n",
                encoding="utf-8",
            )
            (tmp / "runtime" / "ownership-classification.lock.json").write_text(
                json.dumps(
                    {
                        "schema_version": "ai-architecture.ownership.v1",
                        "classifications": {
                            "known.txt": {
                                "owner": "project_owned",
                                "action": "preserve_project",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            findings: list[object] = []
            module.check_ownership_classification(tmp, findings)
            self.assertIn("ownership_classification_drift", {finding.check for finding in findings})
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_script_catalog_rejects_extra_public_command(self) -> None:
        module = self._load_verify_module()
        tmp = self._catalog_root(
            "version: 1\n"
            "public:\n"
            "  - path: scripts/agent-flow.py\n"
            "  - path: scripts/quality-gate.py\n"
            "internal:\n",
            ["quality-gate.py"],
        )
        try:
            findings: list[object] = []
            module.check_script_catalog(tmp, findings)
            self.assertIn("script_catalog_invalid", {finding.check for finding in findings})
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_script_catalog_rejects_missing_internal_path(self) -> None:
        module = self._load_verify_module()
        tmp = self._catalog_root(
            "version: 1\n"
            "public:\n"
            "  - path: scripts/agent-flow.py\n"
            "internal:\n"
            "  validation:\n"
            "    - path: scripts/missing-tool.py\n",
        )
        try:
            findings: list[object] = []
            module.check_script_catalog(tmp, findings)
            details = "\n".join(finding.detail for finding in findings)
            self.assertIn("script_catalog_invalid", {finding.check for finding in findings})
            self.assertIn("scripts/missing-tool.py", details)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_command_docs_metadata_mismatch_is_reported(self) -> None:
        module = self._load_verify_module()
        tmp = self._catalog_root(
            "version: 1\n"
            "public:\n"
            "  - path: scripts/agent-flow.py\n"
            "routing:\n"
            "  modes:\n"
            "    research:\n"
            "      goal_pattern: (reference)\n"
            "      reason: ok\n"
            "      confidence: high\n"
            "      requires_confirmation: false\n"
            "      write_policy: read_only\n"
            "      signal: goal_mentions_reference\n"
            "      next_command: python3 scripts/agent-flow.py research --auto --goal \"{goal}\" --format json\n"
            "      suggested_questions:\n"
            "        - q\n"
            "    decide:\n"
            "      reason: ok\n"
            "      confidence: high\n"
            "      requires_confirmation: true\n"
            "      write_policy: read_only\n"
            "      signal: open_review_queue\n"
            "      next_command: python3 scripts/agent-flow.py decide --proposal <proposal-path> --decision accepted|rejected|deferred --by <name> --format json\n"
            "      suggested_questions:\n"
            "        - q\n"
            "    closeout:\n"
            "      goal_pattern: (verify)\n"
            "      reason: ok\n"
            "      confidence: high\n"
            "      requires_confirmation: true\n"
            "      write_policy: write_with_confirmation\n"
            "      signal: goal_mentions_closeout\n"
            "      next_command: python3 scripts/agent-flow.py closeout --goal \"{goal}\" --changed-path . --format json\n"
            "      suggested_questions:\n"
            "        - q\n"
            "    maintain:\n"
            "      goal_pattern: (system)\n"
            "      reason: ok\n"
            "      confidence: medium\n"
            "      requires_confirmation: false\n"
            "      write_policy: manual_work_required\n"
            "      signal: goal_mentions_maintain\n"
            "      next_command: manual: clarify\n"
            "      suggested_questions:\n"
            "        - q\n"
            "    build:\n"
            "      reason: ok\n"
            "      confidence: medium\n"
            "      requires_confirmation: false\n"
            "      write_policy: manual_work_required\n"
            "      signal: goal_mentions_build\n"
            "      next_command: manual: clarify\n"
            "      suggested_questions:\n"
            "        - q\n",
        )
        try:
            (tmp / "docs" / "commands").mkdir(parents=True)
            (tmp / "docs" / "commands" / "research.md").write_text(
                "---\n"
                "name: research\n"
                "intent: test\n"
                "public: true\n"
                "maps_to: python3 scripts/agent-flow.py research --auto --format json\n"
                "write_policy: write_with_confirmation\n"
                "requires_confirmation: false\n"
                "---\n"
                "# /research\n",
                encoding="utf-8",
            )
            findings: list[object] = []
            module.check_script_catalog(tmp, findings)
            self.assertIn("command_metadata_invalid", {finding.check for finding in findings})
            self.assertIn("write_policy differs", "\n".join(finding.detail for finding in findings))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class PermissionPolicyValidationTests(unittest.TestCase):
    def _load_verify_module(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("verify_skeleton_module_permissions", SCRIPTS / "verify-skeleton.py")
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def test_permission_policy_rejects_wildcard_shell_allow(self) -> None:
        module = self._load_verify_module()
        tmp = REPO_ROOT / "runtime" / f"permission-policy-{uuid.uuid4().hex}"
        try:
            (tmp / "config").mkdir(parents=True)
            (tmp / "config" / "policy.yaml").write_text(
                "permissions:\n"
                "  default_action: ask\n"
                "  timeout_action: deny\n"
                "  decision_values: [allow_once, allow_session, deny]\n"
                "  rules:\n"
                "    - id: unsafe\n"
                "      match: shell:*\n"
                "      action: allow\n",
                encoding="utf-8",
            )
            findings: list[object] = []
            module.check_permission_policy(tmp, findings)
            details = "\n".join(finding.detail for finding in findings)
            self.assertIn("permission_policy_invalid", {finding.check for finding in findings})
            self.assertIn("wildcard shell", details)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

class QualityGateTests(unittest.TestCase):
    """`quality-gate.py` runs the detected local validation surface."""

    SCRIPT = SCRIPTS / "quality-gate.py"

    def test_quality_gate_json_is_parseable_without_recursive_tests(self) -> None:
        result = _run(
            [str(self.SCRIPT), "--root", str(REPO_ROOT), "--skip-tests", "--format", "json"],
            cwd=REPO_ROOT,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"quality gate failed:\nstdout={result.stdout}\nstderr={result.stderr}",
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["root"], str(REPO_ROOT.resolve()))
        self.assertEqual(payload["tier"], "stable")
        self.assertIn("feature_manifest", payload)
        self.assertIn("skipped_by_tier", payload)
        names = {item["name"] for item in payload["checks"]}
        self.assertIn("feature-status", names)
        self.assertIn("verify-skeleton", names)
        self.assertIn("resume-readiness", names)
        self.assertIn("skill-surface", names)
        self.assertIn("codemap-freshness", names)
        self.assertIn("operational-readiness", names)
        self.assertIn("validate-plans", names)
        self.assertIn("reference-wiki", names)
        self.assertIn("reference-inventory", names)
        self.assertIn("lsp-diagnostics", names)
        self.assertIn("python-syntax", names)
        self.assertNotIn("python-unittest", names)

    def test_quality_gate_stable_skips_incubating_manifest_failure(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"quality-tier-{uuid.uuid4().hex}"
        try:
            (tmp / "docs").mkdir(parents=True)
            (tmp / "scripts").mkdir(parents=True)
            (tmp / "runtime").mkdir(parents=True)
            (tmp / "docs" / "stable.md").write_text("# stable\n", encoding="utf-8")
            (tmp / "runtime" / "agent-runs.jsonl").write_text(
                json.dumps(
                    {
                        "schema_version": "ai-architecture.agent-run.v1",
                        "ts": "2026-05-14T00:00:00Z",
                        "agent_run_id": "run-temp",
                        "brief_id": "2026-05-14-adhoc-human-operator-01",
                        "tier": "incubating",
                        "agent": "human_operator",
                        "workflow": "manual_smoke",
                        "status": "completed",
                        "goal_lineage": [{"type": "brief", "ref": "runtime/agent-briefs/tmp.json", "summary": "temp"}],
                        "artifacts": [],
                        "result_summary": "temp",
                        "changed_paths": [],
                        "validation": [],
                        "created_by": "manual",
                        "ext": {},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (tmp / "docs" / "feature-status.yaml").write_text(
                "version: 1\n"
                "tiers: [stable, incubating, experimental, deprecated]\n"
                "features:\n"
                "  - id: stable.feature\n"
                "    tier: stable\n"
                "    overlay_default: true\n"
                "    docs: [docs/stable.md]\n"
                "  - id: incubating.feature\n"
                "    tier: incubating\n"
                "    overlay_default: false\n"
                "    docs: [docs/missing.md]\n",
                encoding="utf-8",
            )
            for rel in ["quality-gate.py", "feature-status.py", "lib_feature_status.py", "failure-classify.py"]:
                shutil.copy2(SCRIPTS / rel, tmp / "scripts" / rel)
            stable = _run(
                [
                    str(tmp / "scripts" / "quality-gate.py"),
                    "--root",
                    str(tmp),
                    "--skip-tests",
                    "--skip-node",
                    "--skip-skeleton",
                    "--format",
                    "json",
                ],
                cwd=tmp,
            )
            self.assertEqual(stable.returncode, 0, stable.stdout + stable.stderr)
            stable_payload = json.loads(stable.stdout)
            self.assertEqual(stable_payload["tier"], "stable")
            self.assertIn("incubating.feature", stable_payload["skipped_by_tier"])
            all_tiers = _run(
                [
                    str(tmp / "scripts" / "quality-gate.py"),
                    "--root",
                    str(tmp),
                    "--tier",
                    "all",
                    "--skip-tests",
                    "--skip-node",
                    "--skip-skeleton",
                    "--format",
                    "json",
                ],
                cwd=tmp,
            )
            self.assertNotEqual(all_tiers.returncode, 0, all_tiers.stdout + all_tiers.stderr)
            all_payload = json.loads(all_tiers.stdout)
            self.assertEqual(all_payload["tier"], "all")
            self.assertEqual(all_payload["feature_manifest"]["ok"], False)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_quality_gate_all_blocks_broken_agent_run_ledger_but_stable_skips(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"quality-agent-run-{uuid.uuid4().hex}"
        try:
            (tmp / "docs").mkdir(parents=True)
            (tmp / "scripts" / "incubating").mkdir(parents=True)
            (tmp / "runtime").mkdir(parents=True)
            (tmp / "docs" / "stable.md").write_text("# stable\n", encoding="utf-8")
            (tmp / "docs" / "agent-run.md").write_text("# agent run\n", encoding="utf-8")
            (tmp / "docs" / "feature-status.yaml").write_text(
                "version: 1\n"
                "tiers: [stable, incubating, experimental, deprecated]\n"
                "features:\n"
                "  - id: stable.feature\n"
                "    tier: stable\n"
                "    overlay_default: true\n"
                "    docs: [docs/stable.md]\n"
                "  - id: agent-run-ledger\n"
                "    tier: incubating\n"
                "    overlay_default: false\n"
                "    docs: [docs/agent-run.md]\n",
                encoding="utf-8",
            )
            (tmp / "runtime" / "agent-runs.jsonl").write_text(
                json.dumps(
                    {
                        "schema_version": "ai-architecture.agent-run.v1",
                        "ts": "2026-05-13T00:00:00Z",
                        "agent_run_id": "run-bad-01",
                        "brief_id": "bad",
                        "tier": "incubating",
                        "agent": "human_operator",
                        "workflow": "manual_smoke",
                        "status": "completed",
                        "goal_lineage": [],
                        "artifacts": [],
                        "result_summary": "bad",
                        "changed_paths": [],
                        "validation": [],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            for rel in ["quality-gate.py", "feature-status.py", "lib_feature_status.py", "failure-classify.py", "lib_runtime_lock.py"]:
                shutil.copy2(SCRIPTS / rel, tmp / "scripts" / rel)
            shutil.copy2(SCRIPTS / "incubating" / "agent-run.py", tmp / "scripts" / "incubating" / "agent-run.py")
            stable = _run(
                [
                    str(tmp / "scripts" / "quality-gate.py"),
                    "--root",
                    str(tmp),
                    "--tier",
                    "stable",
                    "--skip-tests",
                    "--skip-node",
                    "--skip-skeleton",
                    "--format",
                    "json",
                ],
                cwd=tmp,
            )
            self.assertEqual(stable.returncode, 0, stable.stdout + stable.stderr)
            self.assertIn("agent-run-ledger", json.loads(stable.stdout)["skipped_by_tier"])
            all_tier = _run(
                [
                    str(tmp / "scripts" / "quality-gate.py"),
                    "--root",
                    str(tmp),
                    "--tier",
                    "all",
                    "--skip-tests",
                    "--skip-node",
                    "--skip-skeleton",
                    "--format",
                    "json",
                ],
                cwd=tmp,
            )
            self.assertEqual(all_tier.returncode, 1)
            checks = {item["name"]: item for item in json.loads(all_tier.stdout)["checks"]}
            self.assertEqual(checks["agent-run-ledger"]["status"], "FAIL")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_quality_gate_all_warns_but_does_not_fail_agent_run_missing_changed_path(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"quality-agent-run-warn-{uuid.uuid4().hex}"
        try:
            (tmp / "docs").mkdir(parents=True)
            (tmp / "scripts" / "incubating").mkdir(parents=True)
            (tmp / "runtime").mkdir(parents=True)
            (tmp / "docs" / "stable.md").write_text("# stable\n", encoding="utf-8")
            (tmp / "docs" / "agent-run.md").write_text("# agent run\n", encoding="utf-8")
            (tmp / "docs" / "feature-status.yaml").write_text(
                "version: 1\n"
                "tiers: [stable, incubating, experimental, deprecated]\n"
                "features:\n"
                "  - id: stable.feature\n"
                "    tier: stable\n"
                "    overlay_default: true\n"
                "    docs: [docs/stable.md]\n"
                "  - id: agent-run-ledger\n"
                "    tier: incubating\n"
                "    overlay_default: false\n"
                "    docs: [docs/agent-run.md]\n",
                encoding="utf-8",
            )
            agent_run_id = "run-warn-01"
            (tmp / "runtime" / "agent-runs.jsonl").write_text(
                json.dumps(
                    {
                        "schema_version": "ai-architecture.agent-run.v1",
                        "ts": "2026-05-13T00:00:00Z",
                        "agent_run_id": agent_run_id,
                        "brief_id": "warn",
                        "tier": "incubating",
                        "agent": "human_operator",
                        "workflow": "manual_smoke",
                        "status": "completed",
                        "goal_lineage": [{"type": "agent_run", "ref": f"runtime/agent-runs.jsonl#{agent_run_id}", "summary": "warn"}],
                        "artifacts": [],
                        "result_summary": "warn",
                        "changed_paths": ["docs/deleted.md"],
                        "validation": [],
                        "created_by": "manual",
                        "ext": {},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            for rel in ["quality-gate.py", "feature-status.py", "lib_feature_status.py", "failure-classify.py", "lib_runtime_lock.py"]:
                shutil.copy2(SCRIPTS / rel, tmp / "scripts" / rel)
            shutil.copy2(SCRIPTS / "incubating" / "agent-run.py", tmp / "scripts" / "incubating" / "agent-run.py")
            result = _run(
                [
                    str(tmp / "scripts" / "quality-gate.py"),
                    "--root",
                    str(tmp),
                    "--tier",
                    "all",
                    "--skip-tests",
                    "--skip-node",
                    "--skip-skeleton",
                    "--format",
                    "json",
                ],
                cwd=tmp,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            checks = {item["name"]: item for item in json.loads(result.stdout)["checks"]}
            self.assertEqual(checks["agent-run-ledger"]["status"], "WARN")
            self.assertIn("changed_paths_missing", checks["agent-run-ledger"]["detail"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_quality_gate_uses_separate_unittest_timeout(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location("quality_gate_under_test", self.SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        seen = {}

        def fake_run_command(root, command, timeout):
            seen["timeout"] = timeout
            return module.GateCheck("python-unittest", "OK", "mocked", command, 0.0)

        original = module.run_command
        try:
            module.run_command = fake_run_command
            check = module.check_unittest(REPO_ROOT, 240)
        finally:
            module.run_command = original
        self.assertEqual(check.status, "OK")
        self.assertEqual(seen["timeout"], 240)

    def test_quality_gate_includes_first_json_finding_detail(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location("quality_gate_under_test_detail", self.SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / "runtime") as tmp_name:
            tmp = Path(tmp_name)
            scripts = tmp / "scripts"
            scripts.mkdir()
            (scripts / "fake-findings.py").write_text(
                "import json\nprint(json.dumps({'findings': [{'check': 'bad_check', 'detail': 'broken detail'}]}))\n",
                encoding="utf-8",
            )
            check = module.check_json_findings_tool(tmp, "fake-findings.py", [], 10, strict=False, name="fake")
        self.assertEqual(check.status, "WARN")
        self.assertIn("bad_check", check.detail)
        self.assertIn("broken detail", check.detail)

    def test_quality_gate_lsp_includes_first_finding_detail(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location("quality_gate_under_test_lsp", self.SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / "runtime") as tmp_name:
            tmp = Path(tmp_name)
            scripts = tmp / "scripts"
            scripts.mkdir()
            (scripts / "lsp-diagnostics.py").write_text(
                "import json\nprint(json.dumps({'status': 'FAIL', 'findings': [{'tool': 'pyright', 'message': 'type problem'}]}))\nraise SystemExit(1)\n",
                encoding="utf-8",
            )
            check = module.check_lsp_diagnostics(tmp, 10, strict=False)
        self.assertEqual(check.status, "WARN")
        self.assertIn("pyright", check.detail)
        self.assertIn("type problem", check.detail)

    def test_quality_gate_explain_classifies_common_warnings(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location("quality_gate_under_test_explain", self.SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        checks = [
            module.GateCheck("operational-readiness", "WARN", "Harnesses parity failure", [], 0.0),
            module.GateCheck("codemap-freshness", "WARN", "codemaps may be stale", [], 0.0),
            module.GateCheck("reference-inventory", "WARN", "missing reference card", [], 0.0),
            module.GateCheck("unknown-check", "WARN", "mystery", [], 0.0),
        ]
        explanations = module.explain_checks(checks)
        by_name = {item["name"]: item for item in explanations}
        self.assertEqual(by_name["operational-readiness"]["classification"], "stale_generated")
        self.assertIn("verify-parity.py", by_name["operational-readiness"]["next_command"])
        self.assertFalse(by_name["operational-readiness"]["mutates_files"])
        self.assertEqual(by_name["operational-readiness"]["write_policy"], "read_only")
        self.assertEqual(by_name["codemap-freshness"]["classification"], "stale_docs")
        self.assertTrue(by_name["codemap-freshness"]["mutates_files"])
        self.assertTrue(by_name["codemap-freshness"]["requires_confirmation"])
        self.assertEqual(by_name["codemap-freshness"]["write_policy"], "write_with_confirmation")
        self.assertIn("generate-codemaps.py", by_name["codemap-freshness"]["read_only_alternative"])
        self.assertEqual(by_name["reference-inventory"]["classification"], "needs_review")
        self.assertEqual(by_name["unknown-check"]["classification"], "investigate")

    def test_quality_gate_reference_proposal_lifecycle_warns_and_strict_fails(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location("quality_gate_under_test_lifecycle", self.SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / "runtime") as tmp_name:
            tmp = Path(tmp_name)
            scripts = tmp / "scripts"
            scripts.mkdir()
            (scripts / "validate-reference-proposals.py").write_text(
                "import json, sys\n"
                "print(json.dumps({'summary': {'checked': 1}, 'findings': [{'severity': 'WARN', 'path': 'proposal.md', 'message': 'missing lifecycle'}]}))\n"
                "raise SystemExit(1 if '--strict-lifecycle' in sys.argv else 0)\n",
                encoding="utf-8",
            )
            relaxed = module.check_reference_proposal_lifecycle(tmp, 10, strict=False)
            strict = module.check_reference_proposal_lifecycle(tmp, 10, strict=True)
        self.assertEqual(relaxed.status, "WARN")
        self.assertEqual(strict.status, "FAIL")
        self.assertIn("missing lifecycle", relaxed.detail)

    def test_quality_gate_bad_root_exits_two(self) -> None:
        result = _run(
            [str(self.SCRIPT), "--root", str(REPO_ROOT / "does-not-exist")],
            cwd=REPO_ROOT,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("root not a directory", result.stderr)

    def test_quality_gate_treats_eval_all_fail_payload_as_failure(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"quality-gate-eval-fail-{uuid.uuid4().hex}"
        try:
            scripts = tmp / "scripts"
            scripts.mkdir(parents=True)
            shutil.copyfile(SCRIPTS / "quality-gate.py", scripts / "quality-gate.py")
            shutil.copyfile(SCRIPTS / "lib_feature_status.py", scripts / "lib_feature_status.py")
            shutil.copyfile(SCRIPTS / "failure-classify.py", scripts / "failure-classify.py")
            (tmp / "docs").mkdir(parents=True)
            (tmp / "docs" / "feature-status.yaml").write_text(
                "version: 1\n"
                "features:\n"
                "  - id: stable.feature\n"
                "    tier: stable\n"
                "    overlay_default: true\n"
                "    docs: [docs/feature-status.yaml]\n",
                encoding="utf-8",
            )
            (scripts / "eval-all.py").write_text(
                "import json\nprint(json.dumps({'results': [{'status': 'FAIL'}]}))\n",
                encoding="utf-8",
            )
            result = _run([
                str(scripts / "quality-gate.py"),
                "--root",
                str(tmp),
                "--skip-skeleton",
                "--skip-tests",
                "--skip-node",
                "--format",
                "json",
            ])
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            checks = {item["name"]: item for item in json.loads(result.stdout)["checks"]}
            self.assertEqual(checks["eval-all"]["status"], "FAIL")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class NewInternalToolTests(unittest.TestCase):
    def test_lsp_diagnostics_skips_when_no_tools_available(self) -> None:
        import os
        import subprocess

        with tempfile.TemporaryDirectory(dir=REPO_ROOT / "runtime") as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("print('ok')\n", encoding="utf-8")
            env = os.environ.copy()
            env["PATH"] = ""
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "lsp-diagnostics.py"), "--root", str(root), "--format", "json"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["status"], "SKIP")
        self.assertEqual(payload["findings"], [])

    def test_lsp_diagnostics_parses_fake_pyright_and_tsc_findings(self) -> None:
        import os
        import subprocess

        with tempfile.TemporaryDirectory(dir=REPO_ROOT / "runtime") as tmp:
            root = Path(tmp)
            fakebin = root / "fakebin"
            fakebin.mkdir()
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("x: int = 'bad'\n", encoding="utf-8")
            (root / "tsconfig.json").write_text("{}\n", encoding="utf-8")
            pyright = fakebin / "pyright"
            pyright.write_text(
                "#!/bin/sh\n"
                "cat <<'JSON'\n"
                "{\"generalDiagnostics\":[{\"file\":\"src/app.py\",\"range\":{\"start\":{\"line\":0,\"character\":1}},\"severity\":\"error\",\"message\":\"bad type\"}]}\n"
                "JSON\n"
                "exit 1\n",
                encoding="utf-8",
            )
            tsc = fakebin / "tsc"
            tsc.write_text("#!/bin/sh\nprintf '%s\n' \"src/app.ts(1,2): error TS2322: bad assignment\"\nexit 2\n", encoding="utf-8")
            pyright.chmod(0o755)
            tsc.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = str(fakebin)
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "lsp-diagnostics.py"), "--root", str(root), "--format", "json"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                check=False,
            )
        self.assertEqual(result.returncode, 1, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["status"], "FAIL")
        self.assertIn("pyright", {tool["name"] for tool in payload["tools"]})
        self.assertIn("tsc", {tool["name"] for tool in payload["tools"]})
        self.assertIn("pyright", {item["tool"] for item in payload["findings"]})
        self.assertIn("tsc", {item["tool"] for item in payload["findings"]})

    def test_source_recovery_scripts_scope_plan(self) -> None:
        result = _run(
            [
                str(SCRIPTS / "source-recovery.py"),
                "--root",
                str(REPO_ROOT),
                "--changed-path",
                "scripts/example.py",
                "--failure",
                "quality-gate",
                "--format",
                "json",
            ]
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["mutates_files"])
        self.assertEqual(payload["scopes"][0]["scope"], "scripts")
        commands = "\n".join(payload["scopes"][0]["recommended_commands"])
        self.assertIn("quality-gate", commands)
        self.assertIn("unittest", commands)
        self.assertIn("git reset --hard", payload["scopes"][0]["do_not_run"])

    def test_source_recovery_runtime_scope_plan(self) -> None:
        result = _run(
            [
                str(SCRIPTS / "source-recovery.py"),
                "--root",
                str(REPO_ROOT),
                "--changed-path",
                "runtime/state/session-handoff.md",
                "--failure",
                "resume-readiness",
                "--format",
                "json",
            ]
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["scopes"][0]["scope"], "runtime")
        commands = "\n".join(payload["scopes"][0]["recommended_commands"])
        self.assertIn("session-snapshot", commands)
        self.assertIn("resume-readiness", commands)

    def test_source_recovery_rejects_empty_and_outside_paths(self) -> None:
        empty = _run(
            [
                str(SCRIPTS / "source-recovery.py"),
                "--root",
                str(REPO_ROOT),
                "--changed-path",
                "",
                "--failure",
                "quality-gate",
                "--format",
                "json",
            ]
        )
        outside = _run(
            [
                str(SCRIPTS / "source-recovery.py"),
                "--root",
                str(REPO_ROOT),
                "--changed-path",
                "../outside",
                "--failure",
                "quality-gate",
                "--format",
                "json",
            ]
        )
        self.assertEqual(empty.returncode, 2)
        self.assertEqual(outside.returncode, 2)

    def test_source_recovery_does_not_modify_files(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / "runtime") as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            (root / "scripts" / "app.py").write_text("print('ok')\n", encoding="utf-8")
            before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
            result = _run(
                [
                    str(SCRIPTS / "source-recovery.py"),
                    "--root",
                    str(root),
                    "--changed-path",
                    "scripts/app.py",
                    "--failure",
                    "quality-gate",
                    "--format",
                    "json",
                ]
            )
            after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, after)

    def test_portability_scan_reports_machine_path(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"portability-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            (tmp / "README.md").write_text("local path: /Users/shwoo/example/project\n", encoding="utf-8")
            result = _run([str(SCRIPTS / "portability-scan.py"), "--root", str(tmp), "--format", "json", "--strict"])
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["count"], 1)
            self.assertEqual(payload["findings"][0]["check"], "home_path")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_knowledge_search_finds_index_hit(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"knowledge-search-{uuid.uuid4().hex}"
        try:
            (tmp / "knowledge").mkdir(parents=True)
            (tmp / "knowledge" / "index.md").write_text("# Index\n\ncheckout reference workflow\n", encoding="utf-8")
            result = _run([str(SCRIPTS / "knowledge-search.py"), "--root", str(tmp), "search", "checkout", "--format", "json"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertGreaterEqual(len(payload["hits"]), 1)
            self.assertIn("rrf_score", payload["hits"][0])
            self.assertIn("rank_sources", payload["hits"][0])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_knowledge_search_rank_fusion_prefers_multi_signal_hit(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"knowledge-search-fusion-{uuid.uuid4().hex}"
        try:
            (tmp / "knowledge").mkdir(parents=True)
            (tmp / "docs" / "wiki-ops").mkdir(parents=True)
            (tmp / "knowledge" / "checkout.md").write_text("# Checkout\n\ncheckout appears in title and body\n", encoding="utf-8")
            (tmp / "docs" / "wiki-ops" / "other.md").write_text("# Other\n\ncheckout appears in body only\n", encoding="utf-8")
            result = _run([str(SCRIPTS / "knowledge-search.py"), "--root", str(tmp), "search", "checkout", "--format", "json"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            hits = json.loads(result.stdout)["hits"]
            self.assertEqual(hits[0]["path"], "knowledge/checkout.md")
            self.assertGreaterEqual(len(hits[0]["rank_sources"]), 2)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_knowledge_gap_check_reports_covered_missing_weak_and_blocked(self) -> None:
        covered_root = REPO_ROOT / "runtime" / f"knowledge-gap-covered-{uuid.uuid4().hex}"
        missing_root = REPO_ROOT / "runtime" / f"knowledge-gap-missing-{uuid.uuid4().hex}"
        weak_root = REPO_ROOT / "runtime" / f"knowledge-gap-weak-{uuid.uuid4().hex}"
        blocked_root = REPO_ROOT / "runtime" / f"knowledge-gap-blocked-{uuid.uuid4().hex}"
        try:
            (covered_root / "knowledge").mkdir(parents=True)
            (covered_root / "knowledge" / "index.md").write_text(
                "| id | topic | status | pointer |\n"
                "| --- | --- | --- | --- |\n"
                "| K001 | checkout | active | `checkout.md:1` |\n",
                encoding="utf-8",
            )
            (covered_root / "knowledge" / "checkout.md").write_text("# Checkout\n\ncheckout flow uses checkout validation\n", encoding="utf-8")
            covered = _run([str(SCRIPTS / "knowledge-search.py"), "--root", str(covered_root), "gap-check", "checkout", "--format", "json"])
            self.assertEqual(covered.returncode, 0, covered.stdout + covered.stderr)
            self.assertEqual(json.loads(covered.stdout)["status"], "covered")

            missing_root.mkdir(parents=True)
            missing = _run([str(SCRIPTS / "knowledge-search.py"), "--root", str(missing_root), "gap-check", "absent-topic", "--format", "json"])
            self.assertEqual(missing.returncode, 0, missing.stdout + missing.stderr)
            missing_payload = json.loads(missing.stdout)
            self.assertEqual(missing_payload["status"], "missing")
            self.assertIn("no_hits", {finding["category"] for finding in missing_payload["findings"]})

            (weak_root / "knowledge").mkdir(parents=True)
            (weak_root / "knowledge" / "note.md").write_text("only checkout appears here\n", encoding="utf-8")
            weak = _run([str(SCRIPTS / "knowledge-search.py"), "--root", str(weak_root), "gap-check", "checkout", "--format", "json"])
            self.assertEqual(weak.returncode, 0, weak.stdout + weak.stderr)
            self.assertEqual(json.loads(weak.stdout)["status"], "weak")

            (blocked_root / "docs").mkdir(parents=True)
            (blocked_root / "docs" / "question.md").write_text("[NEEDS CLARIFICATION: Which target?]\n", encoding="utf-8")
            blocked = _run([str(SCRIPTS / "knowledge-search.py"), "--root", str(blocked_root), "gap-check", "checkout", "--format", "json"])
            self.assertEqual(blocked.returncode, 0, blocked.stdout + blocked.stderr)
            blocked_payload = json.loads(blocked.stdout)
            self.assertEqual(blocked_payload["status"], "blocked_by_question")
            self.assertIn("open_question", {finding["category"] for finding in blocked_payload["findings"]})
        finally:
            for root in (covered_root, missing_root, weak_root, blocked_root):
                shutil.rmtree(root, ignore_errors=True)

    def test_knowledge_gap_check_surfaces_wiki_lint_and_does_not_mutate(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"knowledge-gap-lint-{uuid.uuid4().hex}"
        try:
            knowledge = tmp / "knowledge"
            knowledge.mkdir(parents=True)
            (knowledge / "index.md").write_text("| id | topic |\n| --- | --- |\n| bad | broken |\n", encoding="utf-8")
            before = sorted(path.relative_to(tmp).as_posix() for path in tmp.rglob("*"))
            result = _run([str(SCRIPTS / "knowledge-search.py"), "--root", str(tmp), "gap-check", "broken", "--format", "json"])
            after = sorted(path.relative_to(tmp).as_posix() for path in tmp.rglob("*"))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertIn("knowledge_lint", {finding["category"] for finding in payload["findings"]})
            self.assertEqual(before, after)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def _agent_brief_overlay_root(self, name: str) -> Path:
        tmp = REPO_ROOT / "runtime" / f"agent-brief-overlay-{name}-{uuid.uuid4().hex}"
        (tmp / "scripts").mkdir(parents=True)
        (tmp / "config").mkdir()
        shutil.copyfile(SCRIPTS / "agent-brief.py", tmp / "scripts" / "agent-brief.py")
        return tmp

    def _write_agent_team(self, root: Path, body: str) -> None:
        (root / "config" / "agent-team.yaml").write_text(body, encoding="utf-8")

    def _write_agent_team_overlay(self, root: Path, body: str) -> None:
        (root / "config" / "agent-team-overrides.yaml").write_text(body, encoding="utf-8")

    def test_agent_brief_reports_scope_and_policy(self) -> None:
        result = _run([
            str(SCRIPTS / "agent-brief.py"),
            "--root",
            str(REPO_ROOT),
            "--role",
            "security-reviewer",
            "--goal",
            "review copied code",
            "--scope",
            "scripts",
            "--write-policy",
            "read_only",
            "--format",
            "json",
        ])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["role"], "security-reviewer")
        self.assertEqual(payload["role_source"], "base")
        self.assertEqual(payload["read_scope"], ["scripts"])
        self.assertIn("Do not modify files", "\n".join(payload["forbidden_actions"]))
        self.assertNotIn("allowed_files", payload)

    def test_agent_brief_accepts_overlay_only_specialist(self) -> None:
        tmp = self._agent_brief_overlay_root("project-only")
        try:
            self._write_agent_team(tmp, "specialists:\n")
            self._write_agent_team_overlay(
                tmp,
                "specialists:\n"
                "  docs-migration-specialist:\n"
                "    mission: migrate docs\n"
                "    write_policy: read_only\n"
                "    default_scope: [\"docs/\"]\n"
                "    recommended_checks: [\"python scripts/verify-skeleton.py\"]\n",
            )
            (tmp / "docs").mkdir()
            result = _run([
                str(tmp / "scripts" / "agent-brief.py"),
                "--root",
                str(tmp),
                "--role",
                "docs-migration-specialist",
                "--goal",
                "review docs migration",
                "--format",
                "json",
            ])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["role"], "docs-migration-specialist")
            self.assertEqual(payload["role_source"], "project")
            self.assertEqual(payload["read_scope"], ["docs"])
            self.assertEqual(payload["write_scope"], [])
            self.assertIn("python3 scripts/verify-skeleton.py", payload["validation_hints"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_brief_allows_overlay_narrowing(self) -> None:
        tmp = self._agent_brief_overlay_root("narrow")
        try:
            self._write_agent_team(
                tmp,
                "specialists:\n"
                "  build-error-resolver:\n"
                "    mission: fix builds\n"
                "    write_policy: manual_work_required\n"
                "    default_scope: [\"scripts/\", \"tests/\"]\n",
            )
            self._write_agent_team_overlay(
                tmp,
                "specialists:\n"
                "  build-error-resolver:\n"
                "    write_policy: read_only\n"
                "    default_scope: [\"tests/\"]\n",
            )
            (tmp / "scripts").mkdir(exist_ok=True)
            (tmp / "tests").mkdir()
            result = _run([
                str(tmp / "scripts" / "agent-brief.py"),
                "--root",
                str(tmp),
                "--role",
                "build-error-resolver",
                "--goal",
                "inspect test failure",
                "--format",
                "json",
            ])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["role_source"], "base")
            self.assertEqual(payload["write_policy"], "read_only")
            self.assertEqual(payload["read_scope"], ["tests"])
            self.assertEqual(payload["write_scope"], [])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_brief_rejects_overlay_policy_broadening(self) -> None:
        tmp = self._agent_brief_overlay_root("policy-broaden")
        try:
            self._write_agent_team(
                tmp,
                "specialists:\n"
                "  security-reviewer:\n"
                "    mission: audit\n"
                "    write_policy: read_only\n"
                "    default_scope: [\"config/\"]\n",
            )
            self._write_agent_team_overlay(
                tmp,
                "specialists:\n"
                "  security-reviewer:\n"
                "    write_policy: manual_work_required\n",
            )
            result = _run([
                str(tmp / "scripts" / "agent-brief.py"),
                "--root",
                str(tmp),
                "--role",
                "security-reviewer",
                "--goal",
                "audit",
                "--format",
                "json",
            ])
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("broadens base specialist write_policy", result.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_brief_rejects_overlay_scope_broadening(self) -> None:
        tmp = self._agent_brief_overlay_root("scope-broaden")
        try:
            self._write_agent_team(
                tmp,
                "specialists:\n"
                "  docs-sync-auditor:\n"
                "    mission: audit docs\n"
                "    write_policy: read_only\n"
                "    default_scope: [\"docs/\"]\n",
            )
            self._write_agent_team_overlay(
                tmp,
                "specialists:\n"
                "  docs-sync-auditor:\n"
                "    default_scope: [\".\"]\n",
            )
            result = _run([
                str(tmp / "scripts" / "agent-brief.py"),
                "--root",
                str(tmp),
                "--role",
                "docs-sync-auditor",
                "--goal",
                "audit docs",
                "--format",
                "json",
            ])
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("broadens base specialist default_scope", result.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_brief_rejects_policy_broadening(self) -> None:
        result = _run([
            str(SCRIPTS / "agent-brief.py"),
            "--root",
            str(REPO_ROOT),
            "--role",
            "security-reviewer",
            "--goal",
            "review copied code",
            "--write-policy",
            "manual_work_required",
            "--format",
            "json",
        ])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("broadens specialist policy", result.stderr)

    def test_agent_brief_intersects_parent_scope(self) -> None:
        result = _run([
            str(SCRIPTS / "agent-brief.py"),
            "--root",
            str(REPO_ROOT),
            "--role",
            "reference-reviewer",
            "--goal",
            "review references",
            "--scope",
            "runtime/proposals/reference-adoption",
            "--parent-role",
            "strategy-planner",
            "--parent-write-policy",
            "manual_work_required",
            "--parent-scope",
            "runtime",
            "--format",
            "json",
        ])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        inheritance = payload["policy_inheritance"]
        self.assertEqual(inheritance["effective_scope"], ["runtime/proposals/reference-adoption"])
        self.assertEqual(inheritance["inherited_write_policy"], "manual_work_required")

    def test_agent_brief_write_creates_manual_smoke_artifact_and_increments_seq(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-brief-write-{uuid.uuid4().hex}"
        try:
            (tmp / "scripts").mkdir(parents=True)
            shutil.copyfile(SCRIPTS / "agent-brief.py", tmp / "scripts" / "agent-brief.py")
            common = [
                str(tmp / "scripts" / "agent-brief.py"),
                "--root",
                str(tmp),
                "--role",
                "security-reviewer",
                "--goal",
                "manual smoke",
                "--parent-plan",
                "plans/active/0007-v2-runtime.md",
                "--parent-goal",
                "v2 runtime",
                "--user-goal",
                "prepare v2 runtime slice",
                "--write",
                "--format",
                "json",
            ]
            first = _run(common)
            second = _run(common)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            first_payload = json.loads(first.stdout)
            second_payload = json.loads(second.stdout)
            first_brief = first_payload["brief"]
            second_brief = second_payload["brief"]
            self.assertRegex(first_brief["brief_id"], r"^\d{4}-\d{2}-\d{2}-0007-v2-runtime-security-reviewer-01$")
            self.assertRegex(second_brief["brief_id"], r"^\d{4}-\d{2}-\d{2}-0007-v2-runtime-security-reviewer-02$")
            self.assertTrue((tmp / first_payload["brief_path"]).exists())
            self.assertEqual(first_brief["schema_version"], "ai-architecture.agent-brief.v1")
            self.assertEqual(first_brief["tier"], "incubating")
            self.assertEqual(first_brief["execution_mode"], "manual_human")
            self.assertEqual(first_brief["ext"], {})
            self.assertIsInstance(first_brief["goal_lineage"], list)
            self.assertEqual(first_brief["goal_lineage"][0]["type"], "user_goal")
            self.assertEqual(first_brief["goal_lineage"][-1]["type"], "brief")
            self.assertTrue(all(item.startswith("python3 ") for item in first_brief["validation_hints"]))
            for key in ("goal", "mission", "scope", "allowed_files", "handoff_expectation", "recommended_checks"):
                self.assertNotIn(key, first_brief)
            for key in ("parent_role", "inherited_write_policy", "effective_write_policy", "effective_scope"):
                self.assertNotIn(key, first_brief)
            self.assertEqual(
                first_brief["policy_inheritance"],
                {
                    "parent_role": "",
                    "inherited_write_policy": "read_only",
                    "effective_write_policy": "read_only",
                    "effective_scope": ["."],
                },
            )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_brief_rejects_parent_plan_outside_root(self) -> None:
        result = _run([
            str(SCRIPTS / "agent-brief.py"),
            "--root",
            str(REPO_ROOT),
            "--role",
            "security-reviewer",
            "--goal",
            "review copied code",
            "--parent-plan",
            "/tmp/outside-plan.md",
            "--format",
            "json",
        ])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside root", result.stderr)

    def test_agent_flow_does_not_expose_delegate_command(self) -> None:
        result = _run([str(SCRIPTS / "agent-flow.py"), "--help"], cwd=REPO_ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("delegate", result.stdout.lower())
        self.assertNotIn("agent-run", result.stdout.lower())

    def _sha256(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_agent_flow_delegate_creates_brief_handoff_json(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-flow-delegate-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            result = _run([
                str(SCRIPTS / "incubating" / "agent-flow-delegate.py"),
                "--root",
                str(tmp),
                "--role",
                "docs-sync-auditor",
                "--goal",
                "delegate smoke test",
                "--format",
                "json",
            ])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            required = {
                "brief_path",
                "brief_id",
                "role",
                "objective",
                "read_scope",
                "write_scope",
                "write_policy",
                "validation_hints",
                "goal_lineage",
                "next_prompt",
                "completion_command",
                "workflow",
                "tier",
                "role_source",
            }
            self.assertEqual(set(payload), required)
            self.assertEqual(payload["role"], "docs-sync-auditor")
            self.assertEqual(payload["role_source"], "base")
            self.assertEqual(payload["objective"], "delegate smoke test")
            self.assertEqual(payload["tier"], "incubating")
            self.assertEqual(payload["workflow"], "manual_smoke")
            self.assertTrue((tmp / payload["brief_path"]).exists())
            self.assertEqual(json.loads((tmp / payload["brief_path"]).read_text(encoding="utf-8"))["brief_id"], payload["brief_id"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_flow_delegate_completion_command_uses_agent_run_flags(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-flow-delegate-command-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            result = _run([
                str(SCRIPTS / "incubating" / "agent-flow-delegate.py"),
                "--root",
                str(tmp),
                "--role",
                "docs-sync-auditor",
                "--goal",
                "delegate smoke test",
                "--format",
                "json",
            ])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            command = json.loads(result.stdout)["completion_command"]
            for flag in ("--brief", "--status", "--result-summary", "--validation", "--workflow", "--agent", "--created-by"):
                self.assertIn(flag, command)
            self.assertNotIn("--changed-path", command)
            self.assertIn("scripts/incubating/agent-run.py add", command)
            self.assertIn(json.loads(result.stdout)["brief_path"], command)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_flow_delegate_default_manual_smoke_omits_changed_path(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-flow-delegate-default-workflow-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            result = _run([
                str(SCRIPTS / "incubating" / "agent-flow-delegate.py"),
                "--root",
                str(tmp),
                "--role",
                "docs-sync-auditor",
                "--goal",
                "delegate default workflow test",
                "--format",
                "json",
            ])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["workflow"], "manual_smoke")
            self.assertIn("--workflow manual_smoke", payload["completion_command"])
            self.assertNotIn("--changed-path", payload["completion_command"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_flow_delegate_dry_run_omits_changed_path(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-flow-delegate-dry-run-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            result = _run([
                str(SCRIPTS / "incubating" / "agent-flow-delegate.py"),
                "--root",
                str(tmp),
                "--role",
                "docs-sync-auditor",
                "--goal",
                "delegate dry run workflow test",
                "--workflow",
                "dry_run",
                "--format",
                "json",
            ])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["workflow"], "dry_run")
            self.assertIn("--workflow dry_run", payload["completion_command"])
            self.assertNotIn("--changed-path", payload["completion_command"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_flow_delegate_write_workflow_keeps_changed_path_placeholder(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-flow-delegate-write-workflow-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            result = _run([
                str(SCRIPTS / "incubating" / "agent-flow-delegate.py"),
                "--root",
                str(tmp),
                "--role",
                "build-error-resolver",
                "--goal",
                "delegate write workflow test",
                "--workflow",
                "completed_run",
                "--format",
                "json",
            ])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["workflow"], "completed_run")
            self.assertIn("--workflow completed_run", payload["completion_command"])
            self.assertIn('--changed-path "<repo-relative-path>"', payload["completion_command"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_flow_delegate_read_only_prompt_mentions_changed_path_omission(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-flow-delegate-readonly-prompt-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            result = _run([
                str(SCRIPTS / "incubating" / "agent-flow-delegate.py"),
                "--root",
                str(tmp),
                "--role",
                "docs-sync-auditor",
                "--goal",
                "delegate prompt test",
                "--format",
                "json",
            ])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertIn("--changed-path is omitted", payload["next_prompt"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_flow_delegate_completion_command_omits_retry_of_by_default(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-flow-delegate-no-retry-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            result = _run([
                str(SCRIPTS / "incubating" / "agent-flow-delegate.py"),
                "--root",
                str(tmp),
                "--role",
                "docs-sync-auditor",
                "--goal",
                "delegate retry test",
                "--format",
                "json",
            ])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("--retry-of", json.loads(result.stdout)["completion_command"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_flow_delegate_accepts_freeform_write_workflow(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-flow-delegate-freeform-workflow-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            result = _run([
                str(SCRIPTS / "incubating" / "agent-flow-delegate.py"),
                "--root",
                str(tmp),
                "--role",
                "build-error-resolver",
                "--goal",
                "delegate freeform workflow test",
                "--workflow",
                "custom_write_flow",
                "--format",
                "json",
            ])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["workflow"], "custom_write_flow")
            self.assertIn("--workflow custom_write_flow", payload["completion_command"])
            self.assertIn("--changed-path", payload["completion_command"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_flow_delegate_requires_role_and_goal(self) -> None:
        missing_role = _run([
            str(SCRIPTS / "incubating" / "agent-flow-delegate.py"),
            "--goal",
            "delegate smoke test",
            "--format",
            "json",
        ])
        missing_goal = _run([
            str(SCRIPTS / "incubating" / "agent-flow-delegate.py"),
            "--role",
            "docs-sync-auditor",
            "--format",
            "json",
        ])
        self.assertNotEqual(missing_role.returncode, 0)
        self.assertNotEqual(missing_goal.returncode, 0)

    def test_agent_flow_delegate_forwards_scope_to_brief_writer(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-flow-delegate-scope-{uuid.uuid4().hex}"
        try:
            (tmp / "config").mkdir(parents=True)
            (tmp / "config" / "agent-team.yaml").write_text(
                "version: 1\n"
                "specialists:\n"
                "  build-error-resolver:\n"
                "    write_policy: manual_work_required\n"
                "    default_scope: [\".\"]\n",
                encoding="utf-8",
            )
            result = _run([
                str(SCRIPTS / "incubating" / "agent-flow-delegate.py"),
                "--root",
                str(tmp),
                "--role",
                "build-error-resolver",
                "--goal",
                "delegate scope test",
                "--scope",
                "docs",
                "--write-policy",
                "manual_work_required",
                "--format",
                "json",
            ])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["read_scope"], ["docs"])
            self.assertEqual(payload["write_scope"], ["docs"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_flow_delegate_does_not_touch_ledgers(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-flow-delegate-ledger-{uuid.uuid4().hex}"
        try:
            (tmp / "runtime").mkdir(parents=True)
            live = tmp / "runtime" / "agent-runs.jsonl"
            legacy = tmp / "runtime" / "agent-runs.legacy.jsonl"
            live.write_text('{"live": true}\n', encoding="utf-8")
            legacy.write_text('{"legacy": true}\n', encoding="utf-8")
            before = (self._sha256(live), self._sha256(legacy))
            result = _run([
                str(SCRIPTS / "incubating" / "agent-flow-delegate.py"),
                "--root",
                str(tmp),
                "--role",
                "docs-sync-auditor",
                "--goal",
                "delegate smoke test",
                "--format",
                "json",
            ])
            after = (self._sha256(live), self._sha256(legacy))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(before, after)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_flow_delegate_keeps_public_surface_unmodified(self) -> None:
        result = _run([str(SCRIPTS / "agent-flow.py"), "--help"], cwd=REPO_ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("delegate", result.stdout.lower())
        self.assertNotIn("agent-run", result.stdout.lower())

    def test_agent_flow_delegate_works_in_temp_root(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / "runtime") as tmp_name:
            tmp = Path(tmp_name)
            result = _run([
                str(SCRIPTS / "incubating" / "agent-flow-delegate.py"),
                "--root",
                str(tmp),
                "--role",
                "docs-sync-auditor",
                "--goal",
                "delegate temp root test",
                "--format",
                "json",
            ])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue((tmp / payload["brief_path"]).exists())

    def _write_agent_run_brief(self, root: Path, role: str = "docs-sync-auditor") -> str:
        result = _run([
            str(SCRIPTS / "agent-brief.py"),
            "--root",
            str(root),
            "--role",
            role,
            "--goal",
            "manual smoke",
            "--parent-plan",
            "plans/active/0008-agent-run.md",
            "--parent-goal",
            "agent run writer",
            "--user-goal",
            "write one manual smoke run",
            "--write",
            "--format",
            "json",
        ])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return str(root / json.loads(result.stdout)["brief_path"])

    def _agent_run_record(
        self,
        root: Path,
        *,
        changed_paths: list[str],
        workflow: str = "manual_smoke",
        agent_run_id: str = "run-test-01",
        brief_id: str = "test",
        status: str = "completed",
        retry_of: str | None = None,
    ) -> dict[str, object]:
        record: dict[str, object] = {
            "schema_version": "ai-architecture.agent-run.v1",
            "ts": "2026-05-13T00:00:00Z",
            "agent_run_id": agent_run_id,
            "brief_id": brief_id,
            "tier": "incubating",
            "agent": "human_operator",
            "workflow": workflow,
            "status": status,
            "goal_lineage": [{"type": "agent_run", "ref": f"runtime/agent-runs.jsonl#{agent_run_id}", "summary": "test"}],
            "artifacts": [],
            "result_summary": "test",
            "changed_paths": changed_paths,
            "validation": [],
            "created_by": "manual",
            "ext": {},
        }
        if retry_of is not None:
            record["retry_of"] = retry_of
        return record

    def _brief_id_from_path(self, path: str) -> str:
        return str(json.loads(Path(path).read_text(encoding="utf-8"))["brief_id"])

    def test_agent_run_add_and_dump_manual_smoke_record(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            brief_path = self._write_agent_run_brief(tmp)
            add_result = _run([
                str(SCRIPTS / "incubating" / "agent-run.py"),
                "--root",
                str(tmp),
                "add",
                "--brief",
                brief_path,
                "--result-summary",
                "manual smoke passed",
                "--validation",
                "manual_read=passed",
                "--format",
                "json",
            ])
            self.assertEqual(add_result.returncode, 0, add_result.stdout + add_result.stderr)
            record = json.loads(add_result.stdout)
            required = {
                "schema_version",
                "ts",
                "agent_run_id",
                "brief_id",
                "tier",
                "agent",
                "workflow",
                "status",
                "goal_lineage",
                "artifacts",
                "result_summary",
                "changed_paths",
                "validation",
                "created_by",
                "ext",
            }
            self.assertEqual(set(record), required)
            self.assertEqual(record["agent_run_id"], f"run-{record['brief_id']}-01")
            self.assertRegex(record["ts"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
            self.assertEqual(record["tier"], "incubating")
            self.assertEqual(record["agent"], "human_operator")
            self.assertEqual(record["validation"], [{"command": "manual_read", "status": "passed"}])
            self.assertEqual(record["goal_lineage"][-1]["type"], "agent_run")
            self.assertEqual(record["goal_lineage"][-1]["ref"], f"runtime/agent-runs.jsonl#{record['agent_run_id']}")
            dump_result = _run([
                str(SCRIPTS / "incubating" / "agent-run.py"),
                "--root",
                str(tmp),
                "dump",
                "--tail",
                "5",
                "--format",
                "json",
            ])
            self.assertEqual(dump_result.returncode, 0, dump_result.stdout + dump_result.stderr)
            self.assertEqual(json.loads(dump_result.stdout)[-1]["agent_run_id"], record["agent_run_id"])
            list_result = _run([str(SCRIPTS / "incubating" / "agent-run.py"), "--root", str(tmp), "list", "--format", "json"])
            self.assertEqual(list_result.returncode, 0, list_result.stdout + list_result.stderr)
            self.assertEqual(json.loads(list_result.stdout)[0]["agent_run_id"], record["agent_run_id"])
            check_result = _run([str(SCRIPTS / "incubating" / "agent-run.py"), "--root", str(tmp), "check", "--format", "json"])
            self.assertEqual(check_result.returncode, 0, check_result.stdout + check_result.stderr)
            self.assertTrue(json.loads(check_result.stdout)["ok"])
            summary_result = _run([str(SCRIPTS / "incubating" / "agent-run.py"), "--root", str(tmp), "summary", "--format", "json"])
            self.assertEqual(summary_result.returncode, 0, summary_result.stdout + summary_result.stderr)
            summary = json.loads(summary_result.stdout)
            self.assertEqual(summary["total"], 1)
            self.assertEqual(summary["by_status"], {"completed": 1})
            self.assertEqual(summary["findings_count"], 0)
            self.assertEqual(summary["retried_count"], 0)
            self.assertEqual(summary["retry_chain_heads"], 1)
            self.assertEqual(summary["unresolved_failures"], 0)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_validate_appends_closeout_validator_verdict_record(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-validator-pass-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            target_brief = self._write_agent_run_brief(tmp)
            add_result = _run([
                str(SCRIPTS / "incubating" / "agent-run.py"),
                "--root",
                str(tmp),
                "add",
                "--brief",
                target_brief,
                "--result-summary",
                "specialist work completed",
                "--validation",
                "manual_read=passed",
                "--format",
                "json",
            ])
            self.assertEqual(add_result.returncode, 0, add_result.stdout + add_result.stderr)
            target = json.loads(add_result.stdout)
            validator_brief = self._write_agent_run_brief(tmp, role="closeout-validator")
            validate_result = _run([
                str(SCRIPTS / "incubating" / "agent-run.py"),
                "--root",
                str(tmp),
                "validate",
                "--brief",
                validator_brief,
                "--target-run-id",
                target["agent_run_id"],
                "--verdict",
                "pass",
                "--reason",
                "verify and quality gate evidence passed",
                "--validation",
                "verify=passed",
                "--format",
                "json",
            ])
            self.assertEqual(validate_result.returncode, 0, validate_result.stdout + validate_result.stderr)
            record = json.loads(validate_result.stdout)
            self.assertEqual(record["agent"], "closeout-validator")
            self.assertEqual(record["workflow"], "validator_loop")
            self.assertEqual(record["status"], "completed")
            self.assertEqual(record["ext"]["validator"]["target_run_id"], target["agent_run_id"])
            self.assertEqual(record["ext"]["validator"]["verdict"], "pass")
            self.assertEqual(record["ext"]["validator"]["next_status"], "completed")
            self.assertEqual(record["goal_lineage"][-2]["ref"], f"runtime/agent-runs.jsonl#{target['agent_run_id']}")
            self.assertEqual(record["goal_lineage"][-1]["ref"], f"runtime/agent-runs.jsonl#{record['agent_run_id']}")
            check = _run([str(SCRIPTS / "incubating" / "agent-run.py"), "--root", str(tmp), "check", "--format", "json"])
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            self.assertTrue(json.loads(check.stdout)["ok"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_validate_needs_human_maps_to_paused_status(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-validator-paused-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            target_brief = self._write_agent_run_brief(tmp)
            target_result = _run([
                str(SCRIPTS / "incubating" / "agent-run.py"),
                "--root",
                str(tmp),
                "add",
                "--brief",
                target_brief,
                "--result-summary",
                "specialist needs independent review",
                "--validation",
                "manual_read=passed",
                "--format",
                "json",
            ])
            self.assertEqual(target_result.returncode, 0, target_result.stdout + target_result.stderr)
            target = json.loads(target_result.stdout)
            validator_brief = self._write_agent_run_brief(tmp, role="closeout-validator")
            validate_result = _run([
                str(SCRIPTS / "incubating" / "agent-run.py"),
                "--root",
                str(tmp),
                "validate",
                "--brief",
                validator_brief,
                "--target-run-id",
                target["agent_run_id"],
                "--verdict",
                "needs_human",
                "--reason",
                "requires human decision before continuing",
                "--format",
                "json",
            ])
            self.assertEqual(validate_result.returncode, 0, validate_result.stdout + validate_result.stderr)
            record = json.loads(validate_result.stdout)
            self.assertEqual(record["status"], "paused")
            self.assertTrue(record["ext"]["validator"]["needs_human"])
            summary = _run([str(SCRIPTS / "incubating" / "agent-run.py"), "--root", str(tmp), "summary", "--format", "json"])
            self.assertEqual(summary.returncode, 0, summary.stdout + summary.stderr)
            payload = json.loads(summary.stdout)
            self.assertEqual(payload["by_status"]["paused"], 1)
            self.assertEqual(payload["unresolved_failures"], 1)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_validate_requires_closeout_validator_brief(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-validator-role-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            target_brief = self._write_agent_run_brief(tmp)
            target_result = _run([
                str(SCRIPTS / "incubating" / "agent-run.py"),
                "--root",
                str(tmp),
                "add",
                "--brief",
                target_brief,
                "--result-summary",
                "target completed",
                "--format",
                "json",
            ])
            self.assertEqual(target_result.returncode, 0, target_result.stdout + target_result.stderr)
            target = json.loads(target_result.stdout)
            wrong_brief = self._write_agent_run_brief(tmp, role="docs-sync-auditor")
            validate_result = _run([
                str(SCRIPTS / "incubating" / "agent-run.py"),
                "--root",
                str(tmp),
                "validate",
                "--brief",
                wrong_brief,
                "--target-run-id",
                target["agent_run_id"],
                "--verdict",
                "pass",
                "--reason",
                "should reject",
            ])
            self.assertEqual(validate_result.returncode, 1)
            self.assertIn("closeout-validator brief", validate_result.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_add_rejects_changed_path_outside_root(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-path-outside-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            brief_path = self._write_agent_run_brief(tmp)
            result = _run([
                str(SCRIPTS / "incubating" / "agent-run.py"),
                "--root",
                str(tmp),
                "add",
                "--brief",
                brief_path,
                "--result-summary",
                "should reject",
                "--changed-path",
                str(REPO_ROOT / "AGENTS.md"),
                "--format",
                "json",
            ])
            self.assertEqual(result.returncode, 1)
            self.assertIn("outside root", result.stderr)
            self.assertFalse((tmp / "runtime" / "agent-runs.jsonl").exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_add_rejects_missing_changed_path(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-path-missing-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            brief_path = self._write_agent_run_brief(tmp)
            result = _run([
                str(SCRIPTS / "incubating" / "agent-run.py"),
                "--root",
                str(tmp),
                "add",
                "--brief",
                brief_path,
                "--result-summary",
                "should reject",
                "--changed-path",
                "docs/missing.md",
                "--format",
                "json",
            ])
            self.assertEqual(result.returncode, 1)
            self.assertIn("does not exist", result.stderr)
            self.assertFalse((tmp / "runtime" / "agent-runs.jsonl").exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_add_rejects_symlink_escape_changed_path(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-path-symlink-{uuid.uuid4().hex}"
        outside = REPO_ROOT / "runtime" / f"agent-run-path-target-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            outside.mkdir(parents=True)
            (outside / "target.md").write_text("outside\n", encoding="utf-8")
            os.symlink(outside, tmp / "escape")
            brief_path = self._write_agent_run_brief(tmp)
            result = _run([
                str(SCRIPTS / "incubating" / "agent-run.py"),
                "--root",
                str(tmp),
                "add",
                "--brief",
                brief_path,
                "--result-summary",
                "should reject",
                "--changed-path",
                "escape/target.md",
                "--format",
                "json",
            ])
            self.assertEqual(result.returncode, 1)
            self.assertIn("symlink escapes root", result.stderr)
            self.assertFalse((tmp / "runtime" / "agent-runs.jsonl").exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            shutil.rmtree(outside, ignore_errors=True)

    def test_agent_run_add_allows_empty_changed_paths_for_manual_smoke(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-path-empty-smoke-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            brief_path = self._write_agent_run_brief(tmp)
            result = _run([
                str(SCRIPTS / "incubating" / "agent-run.py"),
                "--root",
                str(tmp),
                "add",
                "--brief",
                brief_path,
                "--result-summary",
                "manual smoke passed",
                "--workflow",
                "manual_smoke",
                "--format",
                "json",
            ])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["changed_paths"], [])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_add_requires_changed_paths_for_non_read_only_workflow(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-path-empty-write-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            brief_path = self._write_agent_run_brief(tmp)
            result = _run([
                str(SCRIPTS / "incubating" / "agent-run.py"),
                "--root",
                str(tmp),
                "add",
                "--brief",
                brief_path,
                "--result-summary",
                "should reject",
                "--workflow",
                "completed_run",
                "--format",
                "json",
            ])
            self.assertEqual(result.returncode, 1)
            self.assertIn("changed_paths required", result.stderr)
            self.assertFalse((tmp / "runtime" / "agent-runs.jsonl").exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_check_accepts_existing_changed_path(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-path-check-ok-{uuid.uuid4().hex}"
        try:
            (tmp / "runtime").mkdir(parents=True)
            (tmp / "docs").mkdir()
            (tmp / "docs" / "changed.md").write_text("changed\n", encoding="utf-8")
            (tmp / "runtime" / "agent-runs.jsonl").write_text(
                json.dumps(self._agent_run_record(tmp, changed_paths=["docs/changed.md"], workflow="completed_run")) + "\n",
                encoding="utf-8",
            )
            result = _run([str(SCRIPTS / "incubating" / "agent-run.py"), "--root", str(tmp), "check", "--format", "json"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["findings"], [])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_check_warns_for_historical_missing_changed_path(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-path-check-warn-{uuid.uuid4().hex}"
        try:
            (tmp / "runtime").mkdir(parents=True)
            (tmp / "runtime" / "agent-runs.jsonl").write_text(
                json.dumps(self._agent_run_record(tmp, changed_paths=["docs/deleted.md"], workflow="completed_run")) + "\n",
                encoding="utf-8",
            )
            result = _run([str(SCRIPTS / "incubating" / "agent-run.py"), "--root", str(tmp), "check", "--format", "json"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["findings"][0]["severity"], "WARN")
            self.assertEqual(payload["findings"][0]["check"], "changed_paths_missing")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_add_without_retry_of_preserves_existing_append_behavior(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-retry-none-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            brief_path = self._write_agent_run_brief(tmp)
            result = _run([
                str(SCRIPTS / "incubating" / "agent-run.py"),
                "--root",
                str(tmp),
                "add",
                "--brief",
                brief_path,
                "--result-summary",
                "no retry",
                "--format",
                "json",
            ])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("retry_of", json.loads(result.stdout))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_add_rejects_missing_retry_target(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-retry-missing-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            brief_path = self._write_agent_run_brief(tmp)
            result = _run([
                str(SCRIPTS / "incubating" / "agent-run.py"),
                "--root",
                str(tmp),
                "add",
                "--brief",
                brief_path,
                "--result-summary",
                "missing retry",
                "--retry-of",
                "run-missing-01",
            ])
            self.assertEqual(result.returncode, 1)
            self.assertIn("retry_of target not found in live ledger", result.stderr)
            self.assertFalse((tmp / "runtime" / "agent-runs.jsonl").exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_add_rejects_retry_self_reference(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-retry-self-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            brief_path = self._write_agent_run_brief(tmp)
            brief_id = self._brief_id_from_path(brief_path)
            result = _run([
                str(SCRIPTS / "incubating" / "agent-run.py"),
                "--root",
                str(tmp),
                "add",
                "--brief",
                brief_path,
                "--result-summary",
                "self retry",
                "--retry-of",
                f"run-{brief_id}-01",
            ])
            self.assertEqual(result.returncode, 1)
            self.assertIn("retry_of cannot reference self", result.stderr)
            self.assertFalse((tmp / "runtime" / "agent-runs.jsonl").exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_add_rejects_retry_target_brief_mismatch(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-retry-brief-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            brief_path = self._write_agent_run_brief(tmp)
            (tmp / "runtime").mkdir(exist_ok=True)
            target_id = "run-other-brief-01"
            (tmp / "runtime" / "agent-runs.jsonl").write_text(
                json.dumps(self._agent_run_record(tmp, changed_paths=[], agent_run_id=target_id, brief_id="other-brief", status="failed")) + "\n",
                encoding="utf-8",
            )
            result = _run([
                str(SCRIPTS / "incubating" / "agent-run.py"),
                "--root",
                str(tmp),
                "add",
                "--brief",
                brief_path,
                "--result-summary",
                "mismatch retry",
                "--retry-of",
                target_id,
            ])
            self.assertEqual(result.returncode, 1)
            self.assertIn("retry_of target brief mismatch", result.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_add_rejects_retry_target_completed_status(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-retry-completed-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            brief_path = self._write_agent_run_brief(tmp)
            brief_id = self._brief_id_from_path(brief_path)
            target_id = f"run-{brief_id}-01"
            (tmp / "runtime").mkdir(exist_ok=True)
            (tmp / "runtime" / "agent-runs.jsonl").write_text(
                json.dumps(self._agent_run_record(tmp, changed_paths=[], agent_run_id=target_id, brief_id=brief_id, status="completed")) + "\n",
                encoding="utf-8",
            )
            result = _run([
                str(SCRIPTS / "incubating" / "agent-run.py"),
                "--root",
                str(tmp),
                "add",
                "--brief",
                brief_path,
                "--result-summary",
                "completed retry",
                "--retry-of",
                target_id,
            ])
            self.assertEqual(result.returncode, 1)
            self.assertIn("retry_of target status must be failed or blocked", result.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_add_accepts_failed_and_blocked_retry_targets(self) -> None:
        for status in ("failed", "blocked"):
            with self.subTest(status=status):
                tmp = REPO_ROOT / "runtime" / f"agent-run-retry-{status}-{uuid.uuid4().hex}"
                try:
                    tmp.mkdir(parents=True)
                    brief_path = self._write_agent_run_brief(tmp)
                    brief_id = self._brief_id_from_path(brief_path)
                    target_id = f"run-{brief_id}-01"
                    (tmp / "runtime").mkdir(exist_ok=True)
                    (tmp / "runtime" / "agent-runs.jsonl").write_text(
                        json.dumps(self._agent_run_record(tmp, changed_paths=[], agent_run_id=target_id, brief_id=brief_id, status=status)) + "\n",
                        encoding="utf-8",
                    )
                    result = _run([
                        str(SCRIPTS / "incubating" / "agent-run.py"),
                        "--root",
                        str(tmp),
                        "add",
                        "--brief",
                        brief_path,
                        "--result-summary",
                        f"{status} retry",
                        "--retry-of",
                        target_id,
                        "--format",
                        "json",
                    ])
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    payload = json.loads(result.stdout)
                    self.assertEqual(payload["retry_of"], target_id)
                    self.assertEqual(payload["agent_run_id"], f"run-{brief_id}-02")
                finally:
                    shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_add_allows_read_only_workflow_retry(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-retry-readonly-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            brief_path = self._write_agent_run_brief(tmp)
            brief_id = self._brief_id_from_path(brief_path)
            target_id = f"run-{brief_id}-legacy-01"
            (tmp / "runtime").mkdir(exist_ok=True)
            (tmp / "runtime" / "agent-runs.jsonl").write_text(
                json.dumps(self._agent_run_record(tmp, changed_paths=[], agent_run_id=target_id, brief_id=brief_id, status="blocked")) + "\n",
                encoding="utf-8",
            )
            result = _run([
                str(SCRIPTS / "incubating" / "agent-run.py"),
                "--root",
                str(tmp),
                "add",
                "--brief",
                brief_path,
                "--workflow",
                "manual_smoke",
                "--result-summary",
                "read-only retry",
                "--retry-of",
                target_id,
                "--format",
                "json",
            ])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["retry_of"], target_id)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_add_excludes_legacy_ledger_from_retry_lookup(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-retry-legacy-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            brief_path = self._write_agent_run_brief(tmp)
            brief_id = self._brief_id_from_path(brief_path)
            target_id = f"run-{brief_id}-legacy-01"
            (tmp / "runtime").mkdir(exist_ok=True)
            (tmp / "runtime" / "agent-runs.legacy.jsonl").write_text(
                json.dumps(self._agent_run_record(tmp, changed_paths=[], agent_run_id=target_id, brief_id=brief_id, status="failed")) + "\n",
                encoding="utf-8",
            )
            result = _run([
                str(SCRIPTS / "incubating" / "agent-run.py"),
                "--root",
                str(tmp),
                "add",
                "--brief",
                brief_path,
                "--result-summary",
                "legacy retry",
                "--retry-of",
                target_id,
            ])
            self.assertEqual(result.returncode, 1)
            self.assertIn("retry_of target not found in live ledger", result.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_check_accepts_valid_retry_chain(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-retry-check-ok-{uuid.uuid4().hex}"
        try:
            (tmp / "runtime").mkdir(parents=True)
            first = self._agent_run_record(tmp, changed_paths=[], agent_run_id="run-test-01", brief_id="test", status="failed")
            second = self._agent_run_record(tmp, changed_paths=[], agent_run_id="run-test-02", brief_id="test", status="completed", retry_of="run-test-01")
            (tmp / "runtime" / "agent-runs.jsonl").write_text(json.dumps(first) + "\n" + json.dumps(second) + "\n", encoding="utf-8")
            result = _run([str(SCRIPTS / "incubating" / "agent-run.py"), "--root", str(tmp), "check", "--format", "json"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(json.loads(result.stdout)["ok"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_summary_counts_retry_chains_and_unresolved_failures(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-summary-retry-{uuid.uuid4().hex}"
        try:
            (tmp / "runtime").mkdir(parents=True)
            records = [
                self._agent_run_record(tmp, changed_paths=[], agent_run_id="run-a-01", brief_id="a", status="failed"),
                self._agent_run_record(tmp, changed_paths=[], agent_run_id="run-a-02", brief_id="a", status="completed", retry_of="run-a-01"),
                self._agent_run_record(tmp, changed_paths=[], agent_run_id="run-b-01", brief_id="b", status="blocked"),
                self._agent_run_record(tmp, changed_paths=[], agent_run_id="run-c-01", brief_id="c", status="failed"),
                self._agent_run_record(tmp, changed_paths=[], agent_run_id="run-c-02", brief_id="c", status="blocked", retry_of="run-c-01"),
            ]
            (tmp / "runtime" / "agent-runs.jsonl").write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")
            result = _run([str(SCRIPTS / "incubating" / "agent-run.py"), "--root", str(tmp), "summary", "--format", "json"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["retried_count"], 2)
            self.assertEqual(payload["retry_chain_heads"], 3)
            self.assertEqual(payload["unresolved_failures"], 2)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_summary_missing_retry_target_warns_and_counts_live_heads(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-summary-missing-{uuid.uuid4().hex}"
        try:
            (tmp / "runtime").mkdir(parents=True)
            record = self._agent_run_record(tmp, changed_paths=[], agent_run_id="run-test-02", brief_id="test", status="completed", retry_of="run-missing-01")
            (tmp / "runtime" / "agent-runs.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
            summary = _run([str(SCRIPTS / "incubating" / "agent-run.py"), "--root", str(tmp), "summary", "--format", "json"])
            self.assertEqual(summary.returncode, 0, summary.stdout + summary.stderr)
            payload = json.loads(summary.stdout)
            self.assertEqual(payload["findings_count"], 1)
            self.assertEqual(payload["retried_count"], 1)
            self.assertEqual(payload["retry_chain_heads"], 1)
            self.assertEqual(payload["unresolved_failures"], 0)
            check = _run([str(SCRIPTS / "incubating" / "agent-run.py"), "--root", str(tmp), "check", "--format", "json"])
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            self.assertEqual(json.loads(check.stdout)["findings"][0]["check"], "retry_target_missing")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_summary_ignores_legacy_ledger(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-summary-legacy-{uuid.uuid4().hex}"
        try:
            (tmp / "runtime").mkdir(parents=True)
            legacy = self._agent_run_record(tmp, changed_paths=[], agent_run_id="run-legacy-01", brief_id="legacy", status="failed")
            (tmp / "runtime" / "agent-runs.legacy.jsonl").write_text(json.dumps(legacy) + "\n", encoding="utf-8")
            result = _run([str(SCRIPTS / "incubating" / "agent-run.py"), "--root", str(tmp), "summary", "--format", "json"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["total"], 0)
            self.assertEqual(payload["retried_count"], 0)
            self.assertEqual(payload["retry_chain_heads"], 0)
            self.assertEqual(payload["unresolved_failures"], 0)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_check_warns_for_missing_retry_target(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-retry-check-missing-{uuid.uuid4().hex}"
        try:
            (tmp / "runtime").mkdir(parents=True)
            record = self._agent_run_record(tmp, changed_paths=[], agent_run_id="run-test-02", brief_id="test", status="completed", retry_of="run-missing-01")
            (tmp / "runtime" / "agent-runs.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
            result = _run([str(SCRIPTS / "incubating" / "agent-run.py"), "--root", str(tmp), "check", "--format", "json"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["findings"][0]["check"], "retry_target_missing")
            self.assertEqual(payload["findings"][0]["severity"], "WARN")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_check_rejects_retry_self_reference(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-retry-check-self-{uuid.uuid4().hex}"
        try:
            (tmp / "runtime").mkdir(parents=True)
            record = self._agent_run_record(tmp, changed_paths=[], agent_run_id="run-test-01", brief_id="test", status="failed", retry_of="run-test-01")
            (tmp / "runtime" / "agent-runs.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
            result = _run([str(SCRIPTS / "incubating" / "agent-run.py"), "--root", str(tmp), "check", "--format", "json"])
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)["findings"][0]["check"], "retry_self_reference")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_check_rejects_retry_brief_mismatch_duplicate_ordering_and_status(self) -> None:
        cases = {
            "retry_brief_mismatch": [
                self._agent_run_record(REPO_ROOT, changed_paths=[], agent_run_id="run-a-01", brief_id="a", status="failed"),
                self._agent_run_record(REPO_ROOT, changed_paths=[], agent_run_id="run-b-01", brief_id="b", status="completed", retry_of="run-a-01"),
            ],
            "agent_run_id_duplicate": [
                self._agent_run_record(REPO_ROOT, changed_paths=[], agent_run_id="run-a-01", brief_id="a", status="failed"),
                self._agent_run_record(REPO_ROOT, changed_paths=[], agent_run_id="run-a-01", brief_id="a", status="blocked"),
            ],
            "retry_ordering": [
                self._agent_run_record(REPO_ROOT, changed_paths=[], agent_run_id="run-a-02", brief_id="a", status="completed", retry_of="run-a-01"),
                self._agent_run_record(REPO_ROOT, changed_paths=[], agent_run_id="run-a-01", brief_id="a", status="failed"),
            ],
            "retry_target_status": [
                self._agent_run_record(REPO_ROOT, changed_paths=[], agent_run_id="run-a-01", brief_id="a", status="completed"),
                self._agent_run_record(REPO_ROOT, changed_paths=[], agent_run_id="run-a-02", brief_id="a", status="completed", retry_of="run-a-01"),
            ],
        }
        for expected_check, records in cases.items():
            with self.subTest(check=expected_check):
                tmp = REPO_ROOT / "runtime" / f"agent-run-{expected_check}-{uuid.uuid4().hex}"
                try:
                    (tmp / "runtime").mkdir(parents=True)
                    (tmp / "runtime" / "agent-runs.jsonl").write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")
                    result = _run([str(SCRIPTS / "incubating" / "agent-run.py"), "--root", str(tmp), "check", "--format", "json"])
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    checks = {finding["check"] for finding in json.loads(result.stdout)["findings"]}
                    self.assertIn(expected_check, checks)
                finally:
                    shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_check_reports_schema_findings(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-check-{uuid.uuid4().hex}"
        try:
            (tmp / "runtime").mkdir(parents=True)
            (tmp / "runtime" / "agent-runs.jsonl").write_text(
                json.dumps(
                    {
                        "schema_version": "ai-architecture.agent-run.v1",
                        "ts": "2026-05-13T00:00:00Z",
                        "agent_run_id": "run-bad-01",
                        "brief_id": "bad",
                        "tier": "incubating",
                        "agent": "human_operator",
                        "workflow": "manual_smoke",
                        "status": "completed",
                        "goal_lineage": [],
                        "artifacts": [],
                        "result_summary": "bad",
                        "changed_paths": [],
                        "validation": [],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            result = _run([str(SCRIPTS / "incubating" / "agent-run.py"), "--root", str(tmp), "check", "--format", "json"])
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])
            self.assertIn("ext", "\n".join(item["detail"] for item in payload["findings"]))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_agent_run_dump_empty_and_malformed_ledgers(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-empty-{uuid.uuid4().hex}"
        bad = REPO_ROOT / "runtime" / f"agent-run-bad-{uuid.uuid4().hex}"
        try:
            empty = _run([str(SCRIPTS / "incubating" / "agent-run.py"), "--root", str(tmp), "dump", "--tail", "5", "--format", "json"])
            self.assertEqual(empty.returncode, 0, empty.stdout + empty.stderr)
            self.assertEqual(json.loads(empty.stdout), [])
            (bad / "runtime").mkdir(parents=True)
            (bad / "runtime" / "agent-runs.jsonl").write_text("{bad\n", encoding="utf-8")
            malformed = _run([str(SCRIPTS / "incubating" / "agent-run.py"), "--root", str(bad), "dump", "--tail", "5", "--format", "json"])
            self.assertEqual(malformed.returncode, 2)
            self.assertIn("agent-runs.jsonl:1", malformed.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            shutil.rmtree(bad, ignore_errors=True)

    def test_agent_run_rejects_brief_outside_root_without_append(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"agent-run-outside-{uuid.uuid4().hex}"
        try:
            result = _run([
                str(SCRIPTS / "incubating" / "agent-run.py"),
                "--root",
                str(tmp),
                "add",
                "--brief",
                "/tmp/outside-brief.json",
                "--result-summary",
                "should not append",
            ])
            self.assertEqual(result.returncode, 1)
            self.assertIn("outside root", result.stderr)
            self.assertFalse((tmp / "runtime" / "agent-runs.jsonl").exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_path_safety_denies_generated_files(self) -> None:
        for rel in (".mcp.json", "CLAUDE.md"):
            with self.subTest(path=rel):
                result = _run([
                    str(SCRIPTS / "path-safety.py"),
                    "--root",
                    str(REPO_ROOT),
                    "--format",
                    "json",
                    "check",
                    "--path",
                    rel,
                    "--operation",
                    "write",
                ])
                self.assertEqual(result.returncode, 1)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["decision"], "deny")

    def test_operational_readiness_reports_harnesses(self) -> None:
        result = _run([str(SCRIPTS / "operational-readiness.py"), "--root", str(REPO_ROOT), "--format", "json"])
        self.assertIn(result.returncode, {0, 1}, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        names = {item["name"] for item in payload["harnesses"]}
        self.assertIn("codex", names)
        self.assertIn("claude", names)
        self.assertIn("observability", payload)

    def test_safe_write_rejects_generated_artifact(self) -> None:
        result = _run([
            str(SCRIPTS / "safe-write.py"),
            "--root",
            str(REPO_ROOT),
            "--format",
            "json",
            "check",
            "--path",
            "CLAUDE.md",
        ])
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)["ok"])

    def test_safe_write_applies_inside_runtime(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"safe-write-{uuid.uuid4().hex}"
        try:
            result = _run([
                str(SCRIPTS / "safe-write.py"),
                "--root",
                str(REPO_ROOT),
                "--format",
                "json",
                "write",
                "--path",
                str(tmp.relative_to(REPO_ROOT) / "note.txt"),
                "--text",
                "safe\n",
                "--apply",
            ])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual((tmp / "note.txt").read_text(encoding="utf-8"), "safe\n")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_diff_quality_gate_reports_new_failure(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"diff-quality-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            baseline = tmp / "baseline.json"
            current = tmp / "current.json"
            baseline.write_text(json.dumps({"checks": [{"name": "unit", "status": "OK"}]}), encoding="utf-8")
            current.write_text(json.dumps({"checks": [{"name": "unit", "status": "FAIL", "detail": "boom"}]}), encoding="utf-8")
            result = _run([
                str(SCRIPTS / "diff-quality-gate.py"),
                "--baseline",
                str(baseline),
                "--current",
                str(current),
                "--format",
                "json",
            ])
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["introduced"][0]["name"], "unit")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_validate_plans_rejects_unstructured_plan(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"plan-contract-{uuid.uuid4().hex}"
        try:
            (tmp / "plans" / "active").mkdir(parents=True)
            (tmp / "plans" / "active" / "0001-bad.md").write_text("# Bad\n", encoding="utf-8")
            result = _run([str(SCRIPTS / "validate-plans.py"), "--root", str(tmp), "--format", "json"])
            self.assertEqual(result.returncode, 1)
            self.assertIn("missing heading", "\n".join(json.loads(result.stdout)["findings"]))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_reference_wiki_current_contract_passes(self) -> None:
        result = _run([str(SCRIPTS / "reference-wiki.py"), "--root", str(REPO_ROOT), "--format", "json"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(json.loads(result.stdout)["ok"])

    def test_reference_wiki_sync_indexes_raw_sources(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"reference-wiki-{uuid.uuid4().hex}"
        try:
            (tmp / "docs" / "reference-wiki" / "raw").mkdir(parents=True)
            (tmp / "docs" / "reference-wiki" / "wiki").mkdir(parents=True)
            (tmp / "docs" / "reference-wiki" / "README.md").write_text("# Wiki\n", encoding="utf-8")
            (tmp / "docs" / "reference-wiki" / "raw" / "sample.md").write_text("# Sample\n", encoding="utf-8")
            result = _run([str(SCRIPTS / "reference-wiki.py"), "--root", str(tmp), "--format", "json", "--sync"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("docs/reference-wiki/raw/sample.md", (tmp / "docs" / "reference-wiki" / "wiki" / "index.md").read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class CodemapTests(unittest.TestCase):
    SCRIPT = SCRIPTS / "generate-codemaps.py"

    def test_generate_codemaps_preview_reports_areas(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"codemap-{uuid.uuid4().hex}"
        try:
            (tmp / "scripts").mkdir(parents=True)
            (tmp / "skills" / "active" / "demo").mkdir(parents=True)
            (tmp / "tests").mkdir()
            (tmp / "scripts" / "tool.py").write_text("print('ok')\n", encoding="utf-8")
            (tmp / "skills" / "active" / "demo" / "SKILL.md").write_text("---\nname: demo\n---\n", encoding="utf-8")
            (tmp / "tests" / "test_demo.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
            result = _run([str(self.SCRIPT), "--root", str(tmp), "--format", "json"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertIn("scripts", payload["areas"])
            self.assertIn("skills", payload["areas"])
            self.assertEqual(payload["written"], [])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class WikiGraphReportTests(unittest.TestCase):
    SCRIPT = SCRIPTS / "wiki-lint.py"

    def test_graph_gap_is_reported_for_related_entries(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"wiki-graph-{uuid.uuid4().hex}"
        try:
            knowledge = tmp / "knowledge"
            knowledge.mkdir(parents=True)
            (knowledge / "index.md").write_text(
                "| id | topic | status | pointer |\n"
                "| --- | --- | --- | --- |\n"
                "| K001 | checkout flow | active | `a.md:1` |\n"
                "| K002 | checkout validation | active | `b.md:1` |\n"
                "| K003 | payment shared | active | `c.md:1` |\n",
                encoding="utf-8",
            )
            (knowledge / "a.md").write_text("# A\n[[K003]]\n", encoding="utf-8")
            (knowledge / "b.md").write_text("# B\n[[K003]]\n", encoding="utf-8")
            (knowledge / "c.md").write_text("# C\n", encoding="utf-8")
            result = _run([str(self.SCRIPT), "--root", str(tmp), "--format", "json", "--stale-days", "99999"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            graph_gap = json.loads(result.stdout)["findings"]["graph_gap"]
            self.assertTrue(any("K001 <-> K002" in item for item in graph_gap))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_knowledge_frontmatter_source_contract_warns(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"wiki-source-contract-{uuid.uuid4().hex}"
        try:
            knowledge = tmp / "knowledge"
            knowledge.mkdir(parents=True)
            (knowledge / "index.md").write_text(
                "| id | topic | status | pointer |\n"
                "| --- | --- | --- | --- |\n"
                "| K001 | source contract | active | `entry.md:1` |\n",
                encoding="utf-8",
            )
            (knowledge / "entry.md").write_text(
                "---\n"
                "id: K001\n"
                "status: active\n"
                "updated_at: 2026-05-02\n"
                "sources:\n"
                "  - missing.md:1\n"
                "---\n"
                "# Entry\n",
                encoding="utf-8",
            )
            result = _run([str(self.SCRIPT), "--root", str(tmp), "--format", "json", "--stale-days", "99999"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            findings = json.loads(result.stdout)["findings"]["source_contract"]
            self.assertTrue(any("source reference not found" in item for item in findings))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_generate_codemaps_write_creates_index(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"codemap-write-{uuid.uuid4().hex}"
        try:
            (tmp / "scripts").mkdir(parents=True)
            (tmp / "scripts" / "tool.py").write_text("print('ok')\n", encoding="utf-8")
            result = _run([str(SCRIPTS / "generate-codemaps.py"), "--root", str(tmp), "--write", "--format", "json"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((tmp / "docs" / "CODEMAPS" / "INDEX.md").exists())
            self.assertIn("docs/CODEMAPS/INDEX.md", json.loads(result.stdout)["written"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class CleanupEphemeralTests(unittest.TestCase):
    SCRIPT = SCRIPTS / "cleanup-ephemeral.py"

    def test_preview_does_not_delete_and_apply_removes_pycache(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"cleanup-ephemeral-{uuid.uuid4().hex}"
        try:
            cache = tmp / "scripts" / "__pycache__"
            cache.mkdir(parents=True)
            (cache / "x.pyc").write_bytes(b"cache")
            preview = _run([str(self.SCRIPT), "--root", str(tmp), "--format", "json"])
            self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
            self.assertTrue(cache.exists())
            self.assertEqual(json.loads(preview.stdout)["matches"], ["scripts/__pycache__"])

            apply = _run([str(self.SCRIPT), "--root", str(tmp), "--apply", "--format", "json"])
            self.assertEqual(apply.returncode, 0, apply.stdout + apply.stderr)
            self.assertFalse(cache.exists())
            self.assertEqual(json.loads(apply.stdout)["removed"], ["scripts/__pycache__"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_rejects_targets_outside_root(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"cleanup-ephemeral-outside-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            result = _run([str(self.SCRIPT), "--root", str(tmp), "--target", "../outside", "--format", "json"])
            self.assertEqual(result.returncode, 2)
            self.assertIn("inside project root", result.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class SkillSurfaceTests(unittest.TestCase):
    """`skill-surface-check.py` keeps skills/active canonical and artifacts synced."""

    SCRIPT = SCRIPTS / "skill-surface-check.py"

    def test_current_skill_surface_is_canonicalized(self) -> None:
        result = _run([str(self.SCRIPT), "--root", str(REPO_ROOT), "--strict", "--format", "json"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertGreaterEqual(payload["active_skills"], 1)
        self.assertTrue(payload["parity_ok"])

    def test_generated_parity_mismatch_is_rejected(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"skill-surface-{uuid.uuid4().hex}"
        try:
            active = tmp / "skills" / "active" / "demo"
            codex = tmp / ".codex" / "skills"
            claude = tmp / ".claude" / "skills" / "demo"
            active.mkdir(parents=True)
            codex.mkdir(parents=True)
            claude.mkdir(parents=True)
            (active / "SKILL.md").write_text("---\nname: demo\ndescription: demo\nstatus: active\n---\n", encoding="utf-8")
            (claude / "SKILL.md").write_text("---\nname: demo\ndescription: demo\nstatus: active\n---\n", encoding="utf-8")
            result = _run([str(self.SCRIPT), "--root", str(tmp), "--strict", "--format", "json"])
            self.assertEqual(result.returncode, 1)
            rules = {finding["check"] for finding in json.loads(result.stdout)["findings"]}
            self.assertIn("codex_skill_parity", rules)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_missing_generated_skill_dirs_are_errors(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"skill-surface-missing-{uuid.uuid4().hex}"
        try:
            active = tmp / "skills" / "active" / "demo"
            active.mkdir(parents=True)
            (active / "SKILL.md").write_text("---\nname: demo\ndescription: demo\nstatus: active\n---\n", encoding="utf-8")
            result = _run([str(self.SCRIPT), "--root", str(tmp), "--strict", "--format", "json"])
            self.assertEqual(result.returncode, 1)
            rules = {finding["check"] for finding in json.loads(result.stdout)["findings"]}
            self.assertIn("codex_skill_surface_missing", rules)
            self.assertIn("claude_skill_surface_missing", rules)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_duplicate_skill_name_is_rejected(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"skill-surface-duplicate-{uuid.uuid4().hex}"
        try:
            for base in ("skills/active/a", "skills/_meta/b"):
                path = tmp / base
                path.mkdir(parents=True)
                (path / "SKILL.md").write_text("---\nname: same\ndescription: demo\nstatus: active\n---\n", encoding="utf-8")
            (tmp / ".codex" / "skills").mkdir(parents=True)
            (tmp / ".claude" / "skills").mkdir(parents=True)
            result = _run([str(self.SCRIPT), "--root", str(tmp), "--strict", "--format", "json"])
            self.assertEqual(result.returncode, 1)
            rules = {finding["check"] for finding in json.loads(result.stdout)["findings"]}
            self.assertIn("skill_name_duplicate", rules)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class ConvertSafetyTests(unittest.TestCase):
    SCRIPT = SCRIPTS / "convert.py"

    def _minimal_root(self) -> Path:
        tmp = REPO_ROOT / "runtime" / f"convert-safety-{uuid.uuid4().hex}"
        for rel in ("skills/active/demo", "agents", "rules", "mcp", ".codex/skills"):
            (tmp / rel).mkdir(parents=True)
        (tmp / "skills" / "active" / "demo" / "SKILL.md").write_text("---\nname: demo\ndescription: demo\n---\n", encoding="utf-8")
        (tmp / "mcp" / "servers.yaml").write_text("servers:\n", encoding="utf-8")
        (tmp / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        (tmp / ".codex" / "skills" / "keep.txt").write_text("keep\n", encoding="utf-8")
        return tmp

    def test_unsafe_manifest_target_does_not_delete_existing_files(self) -> None:
        tmp = self._minimal_root()
        try:
            (tmp / "manifest.yaml").write_text(
                "mappings:\n"
                "  skills:\n"
                "    source: skills/active/\n"
                "    targets:\n"
                "      codex: .\n",
                encoding="utf-8",
            )
            result = _run([str(self.SCRIPT), "--root", str(tmp), "--format", "json"])
            self.assertEqual(result.returncode, 1)
            self.assertTrue((tmp / ".codex" / "skills" / "keep.txt").exists())
            self.assertIn("target not allowlisted", result.stdout)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_missing_source_does_not_wipe_target(self) -> None:
        tmp = self._minimal_root()
        try:
            shutil.rmtree(tmp / "skills" / "active")
            result = _run([str(self.SCRIPT), "--root", str(tmp), "--format", "json"])
            self.assertEqual(result.returncode, 1)
            self.assertTrue((tmp / ".codex" / "skills" / "keep.txt").exists())
            self.assertIn("source missing", result.stdout)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class VerifyParityTests(unittest.TestCase):
    CONVERT = SCRIPTS / "convert.py"
    SCRIPT = SCRIPTS / "verify-parity.py"

    def _root(self) -> Path:
        tmp = REPO_ROOT / "runtime" / f"verify-parity-{uuid.uuid4().hex}"
        for rel in ("skills/active/demo/nested", "agents", "rules", "mcp"):
            (tmp / rel).mkdir(parents=True)
        (tmp / "skills" / "active" / "demo" / "SKILL.md").write_text("---\nname: demo\ndescription: demo\n---\n", encoding="utf-8")
        (tmp / "skills" / "active" / "demo" / "nested" / "note.txt").write_text("canonical\n", encoding="utf-8")
        (tmp / "mcp" / "servers.yaml").write_text("servers:\n", encoding="utf-8")
        (tmp / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        return tmp

    def test_recursive_content_drift_is_rejected(self) -> None:
        tmp = self._root()
        try:
            convert = _run([str(self.CONVERT), "--root", str(tmp)])
            self.assertEqual(convert.returncode, 0, convert.stdout + convert.stderr)
            (tmp / ".codex" / "skills" / "demo" / "SKILL.md").write_text("changed\n", encoding="utf-8")
            result = _run([str(self.SCRIPT), "--root", str(tmp)])
            self.assertEqual(result.returncode, 1)
            self.assertIn("changed_files", result.stdout)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_nested_content_drift_is_rejected(self) -> None:
        tmp = self._root()
        try:
            convert = _run([str(self.CONVERT), "--root", str(tmp)])
            self.assertEqual(convert.returncode, 0, convert.stdout + convert.stderr)
            (tmp / ".claude" / "skills" / "demo" / "nested" / "note.txt").write_text("drift\n", encoding="utf-8")
            result = _run([str(self.SCRIPT), "--root", str(tmp)])
            self.assertEqual(result.returncode, 1)
            self.assertIn("nested/note.txt", result.stdout)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_brief_json_explains_parity_drift(self) -> None:
        tmp = self._root()
        try:
            convert = _run([str(self.CONVERT), "--root", str(tmp)])
            self.assertEqual(convert.returncode, 0, convert.stdout + convert.stderr)
            (tmp / ".codex" / "skills" / "demo" / "SKILL.md").write_text("changed\n", encoding="utf-8")
            result = _run([str(self.SCRIPT), "--root", str(tmp), "--brief", "--format", "json"])
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertIn("brief", payload)
            finding = payload["findings"][0]
            self.assertEqual(finding["canonical_source"], "skills/active")
            self.assertEqual(finding["generated_target"], ".codex/skills")
            self.assertFalse(finding["direct_edit_allowed"])
            self.assertIn("scripts/convert.py", finding["recommended_command"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_brief_json_is_clean_when_parity_matches(self) -> None:
        tmp = self._root()
        try:
            convert = _run([str(self.CONVERT), "--root", str(tmp)])
            self.assertEqual(convert.returncode, 0, convert.stdout + convert.stderr)
            result = _run([str(self.SCRIPT), "--root", str(tmp), "--brief", "--format", "json"])
            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["findings"], [])
            self.assertTrue(payload["brief"]["ok"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

class ListOpenQuestionsTests(unittest.TestCase):
    """`scripts/list-open-questions.py` must exit 0 on a clean skeleton and
    must detect a real [NEEDS CLARIFICATION: ...] marker when one is injected
    outside any code fence. Guards the marker aggregator behavior documented
    in rules/common/README.md."""

    SCRIPT = SCRIPTS / "list-open-questions.py"

    def test_clean_skeleton_reports_zero(self) -> None:
        result = _run([str(self.SCRIPT), "--count"], cwd=REPO_ROOT)
        self.assertEqual(
            result.returncode, 0, f"failed:\nstdout={result.stdout}\nstderr={result.stderr}"
        )
        self.assertEqual(result.stdout.strip(), "0")

    def test_real_marker_is_detected_and_strict_exits_nonzero(self) -> None:
        # Create a temp doc inside docs/ (not runtime/tmp-, which is skipped
        # by SKIP_DIR_PREFIXES). Always clean up.
        scratch = REPO_ROOT / "docs" / "_tmp_open_q_smoke.md"
        scratch.write_text(
            "# tmp\n- [NEEDS CLARIFICATION: smoke-test real question?]\n",
            encoding="utf-8",
        )
        try:
            result = _run([str(self.SCRIPT), "--strict"], cwd=REPO_ROOT)
            self.assertNotEqual(result.returncode, 0, "strict mode did not flag a real marker")
            self.assertIn("smoke-test real question?", result.stdout)
        finally:
            scratch.unlink(missing_ok=True)

class RotateActivityLogArgParseTests(unittest.TestCase):
    """Surface-level argparse contract for rotate-activity-log: unknown flags
    must fail fast with a non-zero exit. Guards against a future refactor that
    silently drops an unknown option on the floor."""

    def test_unknown_flag_is_rejected(self) -> None:
        result = _run(
            [str(SCRIPTS / "rotate-activity-log.py"), "--definitely-not-a-flag"],
            cwd=REPO_ROOT,
        )
        self.assertNotEqual(
            result.returncode,
            0,
            f"unknown flag was accepted:\nstdout={result.stdout}\nstderr={result.stderr}",
        )
