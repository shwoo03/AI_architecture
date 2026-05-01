from tests.test_support import *


class RotateActivityLogDryRunTests(unittest.TestCase):
    """`rotate-activity-log.py` without --apply must be a safe no-op that
    prints a plan and exits 0. This is our guard against the planner
    crashing on a real project's logs."""

    def test_dry_run_exits_zero(self) -> None:
        result = _run(
            [str(SCRIPTS / "rotate-activity-log.py")],
            cwd=REPO_ROOT,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"rotate dry-run failed:\nstdout={result.stdout}\nstderr={result.stderr}",
        )
        self.assertIn("dry-run", result.stdout)

class PostToolUseLogTests(unittest.TestCase):
    """`scripts/hooks/post-tool-use-log.py` is invoked by the Claude Code harness
    with JSON on stdin. Two failure modes have burned us before and are cheap to
    pin down here:

    1. A UTF-8 BOM leading the stdin payload used to make json.loads raise.
    2. A `--log` path outside the project root would silently write to an
       attacker-controlled location. Must be refused with a non-zero exit.
    """

    HOOK = SCRIPTS / "hooks" / "post-tool-use-log.py"

    def test_bom_prefixed_stdin_is_accepted(self) -> None:
        # The --log containment check rejects paths outside the repo root
        # (see test_log_outside_root_is_refused), so the scratch dir for this
        # test must live inside REPO_ROOT. Use runtime/ (the skeleton's own
        # throwaway area) and clean up the file in a try/finally so a failure
        # mid-test does not leave junk behind.
        scratch_dir = REPO_ROOT / "runtime"
        scratch_dir.mkdir(exist_ok=True)
        with tempfile.NamedTemporaryFile(
            prefix="skeleton-bom-", suffix=".jsonl", dir=str(scratch_dir), delete=False
        ) as tmpfile:
            log_path = Path(tmpfile.name)
        try:
            # Start from an empty file so we assert exactly 1 appended line.
            log_path.write_bytes(b"")
            # BOM + minimal well-formed event payload.
            payload = b"\xef\xbb\xbf" + b'{"tool":"Bash","status":"completed"}'
            result = _run_bytes(
                [str(self.HOOK), "--log", str(log_path), "--project", "bom-smoke"],
                stdin_bytes=payload,
            )
            self.assertEqual(
                result.returncode,
                0,
                f"BOM-prefixed stdin rejected:\n"
                f"stdout={result.stdout!r}\nstderr={result.stderr!r}",
            )
            self.assertTrue(log_path.exists(), "log file was not written")
            written = log_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(written), 1, f"expected 1 line, got {written!r}")
        finally:
            lock_path = log_path.parent / f".{log_path.stem}.rotation.lock"
            try:
                log_path.unlink()
            except FileNotFoundError:
                pass
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass

    def test_log_outside_root_is_refused(self) -> None:
        # Absolute path outside the repo root must be rejected; the script
        # should never open a write handle to an arbitrary filesystem location.
        outside = Path.home() / f".skeleton-escape-{uuid.uuid4().hex}" / "escape.jsonl"
        result = _run_bytes(
            [str(self.HOOK), "--log", str(outside), "--project", "escape-smoke"],
            stdin_bytes=b'{"tool":"Bash"}',
        )
        self.assertNotEqual(
            result.returncode,
            0,
            f"--log outside root was accepted (should have been refused):\n"
            f"stdout={result.stdout!r}\nstderr={result.stderr!r}",
        )
        self.assertFalse(
            outside.exists(),
            f"script wrote to forbidden path {outside}",
        )

class ResumeReadinessTests(unittest.TestCase):
    """`resume-readiness.py` verifies handoff and ledgers line up for the next agent."""

    SCRIPT = SCRIPTS / "resume-readiness.py"

    def _make_root(
        self,
        *,
        handoff_ts: str = "2026-04-30T09:00:00Z",
        activity_ts: str = "2026-04-30T08:59:00Z",
        handoff_event_ts: str = "2026-04-30T09:00:00Z",
        evidence_ts: str = "2026-04-30T08:58:00Z",
        include_resume_prompt: bool = True,
    ) -> Path:
        tmp = REPO_ROOT / "runtime" / f"resume-readiness-{uuid.uuid4().hex}"
        (tmp / "runtime" / "state").mkdir(parents=True)
        sections = [
            "# Session Handoff",
            "",
            "## Last Updated",
            "",
            handoff_ts,
            "",
            "## Current Task",
            "",
            "Resume smoke.",
            "",
            "## Last Completed",
            "",
            "- Prior task.",
            "",
            "## Validation",
            "",
            "- Checked.",
            "",
            "## Recommended Next Step",
            "",
            "Run the next agent step.",
            "",
            "## Open Questions / Blockers",
            "",
            "- None.",
            "",
        ]
        if include_resume_prompt:
            sections.extend(["## Resume Prompt", "", "Continue from this smoke state.", ""])
        (tmp / "runtime" / "state" / "session-handoff.md").write_text("\n".join(sections), encoding="utf-8")
        activity = [
            {"ts": handoff_event_ts, "phase": "session", "action": "handoff_saved", "project": "smoke", "data": {}},
            {"ts": activity_ts, "phase": "implementation", "action": "some_work", "project": "smoke", "data": {}},
        ]
        (tmp / "runtime" / "activity-log.jsonl").write_text(
            "".join(json.dumps(item, separators=(",", ":")) + "\n" for item in activity),
            encoding="utf-8",
        )
        evidence = {
            "ts": evidence_ts,
            "goal": "smoke",
            "changed_paths": ["docs/example.md"],
            "validations": [{"name": "verify", "status": "OK"}],
            "outcome": "genuine_success",
        }
        (tmp / "runtime" / "completion-evidence.jsonl").write_text(
            json.dumps(evidence, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        return tmp

    def test_ready_root_passes_strict_json(self) -> None:
        tmp = self._make_root()
        try:
            result = _run([str(self.SCRIPT), "--root", str(tmp), "--strict", "--format", "json"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["summary"]["ERROR"], 0)
            self.assertEqual(payload["summary"]["WARN"], 0)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_activity_newer_than_handoff_fails_strict(self) -> None:
        tmp = self._make_root(activity_ts="2026-04-30T09:01:00Z")
        try:
            result = _run([str(self.SCRIPT), "--root", str(tmp), "--strict", "--format", "json"])
            self.assertEqual(result.returncode, 1)
            rules = {finding["check"] for finding in json.loads(result.stdout)["findings"]}
            self.assertIn("activity_log_newer_than_handoff", rules)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_completion_evidence_newer_than_handoff_fails_strict(self) -> None:
        tmp = self._make_root(evidence_ts="2026-04-30T09:01:00Z")
        try:
            result = _run([str(self.SCRIPT), "--root", str(tmp), "--strict", "--format", "json"])
            self.assertEqual(result.returncode, 1)
            rules = {finding["check"] for finding in json.loads(result.stdout)["findings"]}
            self.assertIn("completion_evidence_newer_than_handoff", rules)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_missing_handoff_section_fails(self) -> None:
        tmp = self._make_root(include_resume_prompt=False)
        try:
            result = _run([str(self.SCRIPT), "--root", str(tmp), "--strict", "--format", "json"])
            self.assertEqual(result.returncode, 1)
            rules = {finding["check"] for finding in json.loads(result.stdout)["findings"]}
            self.assertIn("handoff_section_missing", rules)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

class AgentAutonomyTests(unittest.TestCase):
    """`agent-autonomy-check.py` keeps routine execution assigned to agents."""

    SCRIPT = SCRIPTS / "agent-autonomy-check.py"

    def test_current_docs_pass_strict(self) -> None:
        result = _run([str(self.SCRIPT), "--root", str(REPO_ROOT), "--strict", "--format", "json"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["findings"], [])

    def test_user_run_instruction_is_flagged(self) -> None:
        scratch = REPO_ROOT / "docs" / "_tmp_agent_autonomy_smoke.md"
        scratch.write_text(
            "# bad\n\n사용자가 직접 python scripts/example.py 명령을 실행합니다.\n",
            encoding="utf-8",
        )
        try:
            result = _run([str(self.SCRIPT), "--root", str(REPO_ROOT), "--strict"])
            self.assertEqual(result.returncode, 1)
            self.assertIn("user_runs_command", result.stdout)
        finally:
            scratch.unlink(missing_ok=True)

class CompletionEvidenceTests(unittest.TestCase):
    """Completion evidence is append-only and agent-owned."""

    SCRIPT = SCRIPTS / "completion-evidence.py"

    def test_add_list_check_round_trip(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"completion-evidence-{uuid.uuid4().hex}"
        try:
            tmp.mkdir(parents=True)
            add = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "add",
                    "--goal",
                    "smoke closeout",
                    "--changed-path",
                    "docs/example.md",
                    "--validation",
                    '{"name":"verify","status":"OK"}',
                    "--json",
                ]
            )
            self.assertEqual(add.returncode, 0, add.stderr)
            record = json.loads(add.stdout)
            self.assertEqual(record["goal"], "smoke closeout")

            listing = _run([str(self.SCRIPT), "--root", str(tmp), "list", "--json"])
            self.assertEqual(listing.returncode, 0, listing.stderr)
            self.assertEqual(len(json.loads(listing.stdout)), 1)

            check = _run([str(self.SCRIPT), "--root", str(tmp), "check"])
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

class TaskCloseoutTests(unittest.TestCase):
    """`task-closeout.py` selects checks and can record completion evidence."""

    SCRIPT = SCRIPTS / "task-closeout.py"

    def test_docs_profile_runs_read_only_checks(self) -> None:
        result = _run(
            [
                str(self.SCRIPT),
                "--root",
                str(REPO_ROOT),
                "--profile",
                "docs",
                "--goal",
                "docs smoke",
                "--changed-path",
                "docs/OPERATING_LOOP.md",
                "--no-record",
                "--format",
                "json",
            ]
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        names = {check["name"] for check in payload["checks"]}
        self.assertIn("verify-skeleton", names)
        self.assertIn("agent-autonomy-check", names)
        self.assertFalse(payload["recorded"])

    def test_record_writes_completion_evidence_in_target_root(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"task-closeout-{uuid.uuid4().hex}"
        try:
            (tmp / "scripts").mkdir(parents=True)
            (tmp / "docs").mkdir()
            (tmp / "scripts" / "verify-skeleton.py").write_text(
                "import sys\nprint('ok')\nraise SystemExit(0)\n",
                encoding="utf-8",
            )
            (tmp / "scripts" / "agent-autonomy-check.py").write_text(
                "import sys\nprint('ok')\nraise SystemExit(0)\n",
                encoding="utf-8",
            )
            shutil.copyfile(SCRIPTS / "completion-evidence.py", tmp / "scripts" / "completion-evidence.py")

            result = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "--profile",
                    "docs",
                    "--goal",
                    "record smoke",
                    "--changed-path",
                    "docs/example.md",
                    "--record",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["recorded"])
            self.assertTrue((tmp / "runtime" / "completion-evidence.jsonl").exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

class ReviewQueueTests(unittest.TestCase):
    """Human review queue stores unresolved decisions as JSONL events."""

    SCRIPT = SCRIPTS / "review-queue.py"

    def test_add_list_resolve_flow(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"review-queue-smoke-{uuid.uuid4().hex}"
        try:
            (tmp / "runtime").mkdir(parents=True)
            add = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "add",
                    "--type",
                    "duplicate",
                    "--title",
                    "Notion page duplicate",
                    "--description",
                    "Choose update or supersede.",
                    "--affected-path",
                    "docs/NOTION.md",
                    "--option",
                    "update_existing",
                    "--json",
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(add.returncode, 0, add.stderr)
            item_id = json.loads(add.stdout)["id"]

            listing = _run([str(self.SCRIPT), "--root", str(tmp), "list", "--json"])
            self.assertEqual(listing.returncode, 0, listing.stderr)
            items = json.loads(listing.stdout)
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["id"], item_id)

            resolved = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "resolve",
                    item_id,
                    "--decision",
                    "update_existing",
                ]
            )
            self.assertEqual(resolved.returncode, 0, resolved.stderr)

            count = _run([str(self.SCRIPT), "--root", str(tmp), "count"])
            self.assertEqual(count.stdout.strip(), "0")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_duplicate_open_items_are_merged(self) -> None:
        tmp = REPO_ROOT / "runtime" / f"review-queue-dedupe-{uuid.uuid4().hex}"
        try:
            (tmp / "runtime").mkdir(parents=True)
            base = [
                str(self.SCRIPT),
                "--root",
                str(tmp),
                "add",
                "--type",
                "risky-update",
                "--title",
                "AGENTS.md risky update",
                "--description",
                "Review before applying.",
                "--affected-path",
                "AGENTS.md",
                "--json",
            ]
            first = _run(base)
            second = _run(base)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(json.loads(second.stdout)["status"], "merged")

            listing = _run([str(self.SCRIPT), "--root", str(tmp), "list", "--json"])
            self.assertEqual(len(json.loads(listing.stdout)), 1)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
