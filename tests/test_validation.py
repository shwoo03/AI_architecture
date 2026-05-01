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
        "skeleton-doctor.py",
        "security-scan.py",
        "reference-copy-ledger.py",
        "agent-autonomy-check.py",
        "completion-evidence.py",
        "resume-readiness.py",
        "skill-surface-check.py",
        "task-closeout.py",
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
        names = {item["name"] for item in payload["checks"]}
        self.assertIn("verify-skeleton", names)
        self.assertIn("resume-readiness", names)
        self.assertIn("skill-surface", names)
        self.assertIn("python-syntax", names)

    def test_quality_gate_bad_root_exits_two(self) -> None:
        result = _run(
            [str(self.SCRIPT), "--root", str(REPO_ROOT / "does-not-exist")],
            cwd=REPO_ROOT,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("root not a directory", result.stderr)


class SkillSurfaceTests(unittest.TestCase):
    """`skill-surface-check.py` keeps .codex canonical and .claude shimmed."""

    SCRIPT = SCRIPTS / "skill-surface-check.py"

    def test_current_skill_surface_is_canonicalized(self) -> None:
        result = _run([str(self.SCRIPT), "--root", str(REPO_ROOT), "--strict", "--format", "json"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["duplicate_files"], 0)
        self.assertGreaterEqual(payload["shimmed_claude_skills"], 1)

    def test_duplicate_payload_is_rejected(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"skill-surface-{uuid.uuid4().hex}"
        try:
            codex = tmp / ".codex" / "skills" / "demo"
            claude = tmp / ".claude" / "skills" / "demo"
            codex.mkdir(parents=True)
            claude.mkdir(parents=True)
            (codex / "SKILL.md").write_text("---\nname: demo\ndescription: demo\n---\n", encoding="utf-8")
            (claude / "SKILL.md").write_text("---\nname: demo\ndescription: demo\n---\n", encoding="utf-8")
            (claude / "helper.md").write_text("payload\n", encoding="utf-8")
            result = _run([str(self.SCRIPT), "--root", str(tmp), "--strict", "--format", "json"])
            self.assertEqual(result.returncode, 1)
            rules = {finding["check"] for finding in json.loads(result.stdout)["findings"]}
            self.assertIn("claude_duplicate_payload", rules)
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
