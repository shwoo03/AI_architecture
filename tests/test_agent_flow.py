from tests.test_support import *
import re


class AgentFlowTests(unittest.TestCase):
    SCRIPT = SCRIPTS / "agent-flow.py"

    def _tmp_root(self, name: str) -> Path:
        tmp = REPO_ROOT / "runtime" / f"agent-flow-{name}-{uuid.uuid4().hex}"
        tmp.mkdir(parents=True)
        return tmp

    def _copy_scripts(self, root: Path, names: list[str]) -> None:
        (root / "scripts").mkdir(parents=True, exist_ok=True)
        for name in names:
            shutil.copyfile(SCRIPTS / name, root / "scripts" / name)

    def _init_clean_git_target(self, target: Path) -> None:
        target.mkdir(parents=True, exist_ok=True)
        (target / "README.md").write_text("# Legacy Target\n", encoding="utf-8")
        (target / "LICENSE").write_text("MIT License\n", encoding="utf-8")
        (target / "docs").mkdir()
        (target / "docs" / "PROJECT_PROFILE.md").write_text(
            "primary_goal: keep legacy project running\n"
            "success_criteria: tests pass\n"
            "failure_definition: data loss\n",
            encoding="utf-8",
        )
        for command in (
            ["git", "init"],
            ["git", "config", "user.email", "test@example.invalid"],
            ["git", "config", "user.name", "Test User"],
            ["git", "add", "."],
            ["git", "commit", "-m", "initial"],
        ):
            result = subprocess.run(command, cwd=str(target), capture_output=True, text=True, encoding="utf-8", timeout=30)
            if result.returncode != 0:
                self.skipTest(f"git unavailable for adopt tests: {result.stderr or result.stdout}")

    def _fake_adopt_tools(self, root: Path, *, candidate_paths: int = 0, safe_additions: int = 1) -> None:
        scripts = root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        (scripts / "upgrade-from-skeleton.py").write_text(
            "import json\n"
            f"safe = [{{'path': f'file-{{i}}.md'}} for i in range({safe_additions})]\n"
            "print(json.dumps({'dry_run': True, 'summary': {'add:safe': len(safe)}, 'brief': {'safe_additions': safe, 'manual_reviews': [], 'risky_reviews': []}}))\n",
            encoding="utf-8",
        )
        (scripts / "ownership-initialize.py").write_text(
            "import json\n"
            f"print(json.dumps({{'ok': True, 'status': 'draft', 'analyzed_paths': 3, 'candidate_paths': {candidate_paths}}}))\n",
            encoding="utf-8",
        )

    def _fake_reference_root(self, root: Path) -> Path:
        repo = root / "runtime" / "external-repos" / "local" / "fake"
        (repo / "scripts").mkdir(parents=True)
        (repo / "tests").mkdir()
        (repo / "README.md").write_text("# Fake\n\nReusable helper patterns.\n", encoding="utf-8")
        (repo / "LICENSE").write_text("MIT License\n", encoding="utf-8")
        (repo / "pyproject.toml").write_text("[project]\nname='fake'\n", encoding="utf-8")
        (repo / "scripts" / "helper.py").write_text("print('ok')\n", encoding="utf-8")
        (repo / "tests" / "test_helper.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
        return repo

    def _fake_reference_named(self, root: Path, name: str, markers: tuple[str, ...]) -> Path:
        repo = root / "runtime" / "external-repos" / "local" / name
        repo.mkdir(parents=True)
        if "README.md" in markers:
            (repo / "README.md").write_text(f"# {name}\n", encoding="utf-8")
        if "LICENSE" in markers:
            (repo / "LICENSE").write_text("MIT License\n", encoding="utf-8")
        if "pyproject.toml" in markers:
            (repo / "pyproject.toml").write_text(f"[project]\nname='{name}'\n", encoding="utf-8")
        if "scripts" in markers:
            (repo / "scripts").mkdir()
            (repo / "scripts" / "helper.py").write_text("print('ok')\n", encoding="utf-8")
        if "tests" in markers:
            (repo / "tests").mkdir()
            (repo / "tests" / "test_helper.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
        return repo

    def _prepare_research_root(self) -> Path:
        tmp = self._tmp_root("research")
        self._copy_scripts(
            tmp,
            [
                "reference-intake.py",
                "validate-reference-candidates.py",
                "create-reference-proposal.py",
                "validate-reference-proposals.py",
                "review-queue.py",
                "reference-task-queue.py",
            ],
        )
        self._fake_reference_root(tmp)
        return tmp

    def test_help_exits_zero(self) -> None:
        result = _run([str(self.SCRIPT), "--help"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("usage:", result.stdout.lower())

    def test_start_json_reports_project_status(self) -> None:
        tmp = self._tmp_root("start")
        try:
            self._copy_scripts(tmp, ["review-queue.py"])
            (tmp / "runtime" / "state").mkdir(parents=True)
            (tmp / "runtime" / "state" / "session-handoff.md").write_text("# Handoff\n\nReady.\n", encoding="utf-8")
            result = _run([str(self.SCRIPT), "--root", str(tmp), "start", "--format", "json"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["root"], str(tmp.resolve()))
            self.assertEqual(payload["review_queue_count"], 0)
            self.assertIn(payload["recommended_next_action"], {"research", "decide", "closeout"})
            self.assertIn(payload["mode"], {"research", "decide", "build", "maintain", "closeout"})
            self.assertEqual(payload["recommended_next_action"], payload["mode"])
            self.assertIn("next_command", payload)
            self.assertIn("signals", payload)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_start_build_goal_keeps_recommended_action_aligned(self) -> None:
        tmp = self._tmp_root("start-build-aligned")
        try:
            self._copy_scripts(tmp, ["review-queue.py"])
            result = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "start",
                    "--goal",
                    "이 기능 구현해줘",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["mode"], "build")
            self.assertEqual(payload["recommended_next_action"], "build")
            self.assertEqual(payload["next_action_type"], "manual_work_required")
            self.assertIn("manual:", payload["next_command"])
            self.assertTrue(payload["build_intake"]["plan_required"])
            self.assertIn("plans/active", payload["build_intake"]["plan_location"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_start_goal_routes_research_request(self) -> None:
        tmp = self._tmp_root("start-goal")
        try:
            self._copy_scripts(tmp, ["review-queue.py"])
            result = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "start",
                    "--goal",
                    "쇼핑몰 웹앱 만들고 있어. 오픈소스 먼저 보고 해줘",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["mode"], "research")
            self.assertIn("research --auto", payload["next_command"])
            self.assertIn("--goal", payload["next_command"])
            self.assertNotIn("--write-card", payload["next_command"])
            self.assertFalse(payload["requires_confirmation"])
            self.assertEqual(payload["next_action_type"], "agent_flow_command")
            self.assertIn(payload["catalog_status"]["source"], {"scripts/catalog.yaml", "defaults"})
            self.assertIn(payload["confidence"], {"high", "medium"})
            self.assertEqual(payload["write_policy"], "read_only")
            self.assertIn("reference_tasks", payload)
            self.assertIn("goal_mentions_reference", payload["signals"])
            questions = "\n".join(payload["suggested_questions"])
            self.assertIn("프로젝트 타입", questions)
            self.assertIn("레퍼런스", questions)
            self.assertIn("MVP", questions)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_start_goal_routes_closeout_request(self) -> None:
        tmp = self._tmp_root("start-closeout")
        try:
            self._copy_scripts(tmp, ["review-queue.py"])
            result = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "start",
                    "--goal",
                    "검증하고 마무리해줘",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["mode"], "closeout")
            self.assertIn("goal_mentions_closeout", payload["signals"])
            self.assertTrue(payload["requires_confirmation"])
            self.assertEqual(payload["next_action_type"], "confirmation_required")
            self.assertEqual(payload["write_policy"], "write_with_confirmation")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_start_goal_routes_maintain_request(self) -> None:
        tmp = self._tmp_root("start-maintain")
        try:
            self._copy_scripts(tmp, ["review-queue.py"])
            result = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "start",
                    "--goal",
                    "우리 시스템 구조 개선해줘",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["mode"], "maintain")
            self.assertEqual(payload["next_action_type"], "manual_work_required")
            self.assertEqual(payload["write_policy"], "manual_work_required")
            self.assertTrue(payload["next_command"].startswith("manual:"))
            self.assertIn("goal_mentions_maintain", payload["signals"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_start_reference_maintain_request_prefers_reference_review(self) -> None:
        tmp = self._tmp_root("start-maintain-reference")
        try:
            self._copy_scripts(tmp, ["review-queue.py"])
            result = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "start",
                    "--goal",
                    "ECC opencode 같은 성숙한 레퍼런스 참고해서 우리 뼈대 개선해줘",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["mode"], "maintain")
            self.assertEqual(payload["next_action_type"], "reference_review_required")
            self.assertIn("research --auto", payload["next_command"])
            self.assertIn("--goal", payload["next_command"])
            self.assertIn("goal_mentions_reference", payload["signals"])
            self.assertIn("reference_review_required", payload["signals"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_start_without_goal_does_not_closeout_from_old_reference_files(self) -> None:
        tmp = self._tmp_root("start-no-goal-old-reference")
        try:
            self._copy_scripts(tmp, ["review-queue.py"])
            (tmp / "research" / "reference-candidates").mkdir(parents=True)
            (tmp / "runtime" / "proposals" / "reference-adoption").mkdir(parents=True)
            (tmp / "research" / "reference-candidates" / "old.md").write_text("# Old\n", encoding="utf-8")
            (tmp / "runtime" / "proposals" / "reference-adoption" / "old.md").write_text("# Old\n", encoding="utf-8")
            result = _run([str(self.SCRIPT), "--root", str(tmp), "start", "--format", "json"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["mode"], "build")
            self.assertEqual(payload["next_action_type"], "manual_work_required")
            self.assertIn("no_goal_provided", payload["signals"])
            self.assertNotEqual(payload["recommended_next_action"], "closeout")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_start_goal_routes_plain_build_request_to_build(self) -> None:
        tmp = self._tmp_root("start-build")
        try:
            self._copy_scripts(tmp, ["review-queue.py"])
            result = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "start",
                    "--goal",
                    "이 기능 구현해줘",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["mode"], "build")
            self.assertEqual(payload["next_action_type"], "manual_work_required")
            self.assertTrue(payload["next_command"].startswith("manual:"))
            self.assertIn("goal_mentions_build", payload["signals"])
            self.assertTrue(payload["build_intake"]["plan_required"])
            self.assertEqual(payload["build_intake"]["goal"], "이 기능 구현해줘")
            questions = "\n".join(payload["suggested_questions"])
            self.assertIn("구현할 정확한 범위", questions)
            self.assertIn("수용 기준", questions)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_start_open_review_queue_overrides_goal(self) -> None:
        tmp = self._tmp_root("start-decision")
        try:
            self._copy_scripts(tmp, ["review-queue.py"])
            add = _run(
                [
                    str(tmp / "scripts" / "review-queue.py"),
                    "--root",
                    str(tmp),
                    "add",
                    "--type",
                    "reference-adoption",
                    "--title",
                    "Approve proposal",
                    "--description",
                    "Needs user decision.",
                    "--source-path",
                    "runtime/proposals/reference-adoption/example.md",
                    "--option",
                    "accept",
                ]
            )
            self.assertEqual(add.returncode, 0, add.stdout + add.stderr)
            result = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "start",
                    "--goal",
                    "새 프로젝트라 오픈소스 먼저 보고 해줘",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["mode"], "decide")
            self.assertTrue(payload["requires_confirmation"])
            self.assertEqual(payload["next_action_type"], "user_decision_required")
            self.assertEqual(payload["write_policy"], "read_only")
            self.assertIn("runtime/proposals/reference-adoption/example.md", payload["next_command"])
            self.assertIn("open_review_queue", payload["signals"])
            self.assertIn("accepted, rejected, deferred", "\n".join(payload["suggested_questions"]))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_research_preview_does_not_write_candidate_card(self) -> None:
        tmp = self._prepare_research_root()
        try:
            result = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "research",
                    "--local-path",
                    "runtime/external-repos/local/fake",
                    "--url",
                    "https://example.com/fake.git",
                ]
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("# suggested_output:", result.stdout)
            self.assertFalse((tmp / "research" / "reference-candidates").exists())
            self.assertTrue((tmp / "runtime" / "external-repos" / "local" / "fake" / "README.md").exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_research_auto_preview_selects_fake_reference_without_writes(self) -> None:
        tmp = self._prepare_research_root()
        try:
            result = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "research",
                    "--auto",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["auto"])
            self.assertEqual(payload["selected_reference"], "runtime/external-repos/local/fake")
            self.assertEqual(len(payload["reference_candidates"]), 1)
            self.assertEqual(payload["reference_candidates"][0]["path"], payload["selected_reference"])
            self.assertIn("not_yet_candidate_carded", payload["selection_signals"])
            self.assertIn("matched_goal_terms", payload)
            self.assertIn("excluded_references", payload)
            self.assertIn("reference_memory", payload)
            self.assertFalse(payload["reuse_existing_card_suggested"])
            self.assertTrue(any(item.startswith("repo_markers:") for item in payload["selection_signals"]))
            self.assertFalse((tmp / "research" / "reference-candidates").exists())
            self.assertTrue((tmp / "runtime" / "external-repos" / "local" / "fake" / "README.md").exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_research_auto_write_card_and_proposal(self) -> None:
        tmp = self._prepare_research_root()
        try:
            result = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "research",
                    "--auto",
                    "--write-card",
                    "--proposal",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["selected_reference"], "runtime/external-repos/local/fake")
            self.assertEqual(payload["reference_candidates"][0]["path"], payload["selected_reference"])
            self.assertIn("not_yet_candidate_carded", payload["selection_signals"])
            self.assertTrue((tmp / payload["candidate_path"]).is_file())
            self.assertTrue((tmp / payload["proposal_path"]).is_file())
            self.assertTrue(payload["reference_task_id"].startswith("ref-task-"))
            self.assertIn("reference-adoption", (tmp / "runtime" / "review-queue.jsonl").read_text(encoding="utf-8"))
            tasks = (tmp / "runtime" / "reference-tasks.jsonl").read_text(encoding="utf-8")
            self.assertIn(payload["reference_task_id"], tasks)
            self.assertIn('"action":"complete"', tasks)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_research_write_card_and_proposal_creates_review_item(self) -> None:
        tmp = self._prepare_research_root()
        try:
            result = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "research",
                    "--local-path",
                    "runtime/external-repos/local/fake",
                    "--url",
                    "https://example.com/fake.git",
                    "--write-card",
                    "--proposal",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["selection_reason"], "explicit local path")
            self.assertIn("explicit_local_path", payload["selection_signals"])
            self.assertEqual(len(payload["reference_candidates"]), 1)
            self.assertEqual(payload["reference_candidates"][0]["path"], "runtime/external-repos/local/fake")
            candidate = tmp / payload["candidate_path"]
            proposal = tmp / payload["proposal_path"]
            self.assertTrue(candidate.is_file())
            self.assertTrue(proposal.is_file())
            self.assertIn("- `sources`:", candidate.read_text(encoding="utf-8"))
            self.assertIn("Source-backed evidence:", proposal.read_text(encoding="utf-8"))
            queue_text = (tmp / "runtime" / "review-queue.jsonl").read_text(encoding="utf-8")
            self.assertIn("reference-adoption", queue_text)
            self.assertTrue(all(item["ok"] for item in payload["commands"]))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_research_auto_reports_top_three_candidates_sorted_by_score(self) -> None:
        tmp = self._tmp_root("research-top")
        try:
            self._copy_scripts(
                tmp,
                [
                    "reference-intake.py",
                    "validate-reference-candidates.py",
                    "create-reference-proposal.py",
                    "validate-reference-proposals.py",
                    "review-queue.py",
                ],
            )
            self._fake_reference_named(tmp, "gamma", ("README.md", "scripts"))
            self._fake_reference_named(tmp, "beta", ("README.md", "LICENSE", "scripts"))
            self._fake_reference_named(tmp, "alpha", ("README.md", "LICENSE", "pyproject.toml", "scripts", "tests"))
            result = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "research",
                    "--auto",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            candidates = payload["reference_candidates"]
            self.assertEqual(len(candidates), 3)
            self.assertEqual(payload["selected_reference"], candidates[0]["path"])
            self.assertEqual(candidates[0]["path"], "runtime/external-repos/local/alpha")
            scores = [item["score"] for item in candidates]
            self.assertEqual(scores, sorted(scores, reverse=True))
            self.assertTrue(all("selection_reason" in item for item in candidates))
            self.assertTrue(all("selection_signals" in item for item in candidates))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_research_auto_goal_prioritizes_named_reference_over_uncarded_repo(self) -> None:
        tmp = self._tmp_root("research-goal-aware")
        try:
            self._copy_scripts(
                tmp,
                [
                    "reference-intake.py",
                    "validate-reference-candidates.py",
                    "create-reference-proposal.py",
                    "validate-reference-proposals.py",
                    "review-queue.py",
                ],
            )
            self._fake_reference_named(tmp, "paperclip", ("README.md", "LICENSE", "scripts", "tests"))
            self._fake_reference_named(tmp, "opencode", ("README.md", "LICENSE", "pyproject.toml", "scripts", "tests"))
            self._fake_reference_named(tmp, "everything-claude-code", ("README.md", "LICENSE", "pyproject.toml", "scripts", "tests"))
            cards = tmp / "research" / "reference-candidates"
            cards.mkdir(parents=True)
            (cards / "2026-05-02-opencode.md").write_text(
                "# opencode\n\n- `name`: opencode\n- `url`: runtime/external-repos/local/opencode\n- `reviewed_at`: 2026-05-02\n",
                encoding="utf-8",
            )
            result = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "research",
                    "--auto",
                    "--goal",
                    "ECC opencode 참고해서 개선해줘",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertIn(payload["selected_reference"], {"runtime/external-repos/local/opencode", "runtime/external-repos/local/everything-claude-code"})
            self.assertNotEqual(payload["selected_reference"], "runtime/external-repos/local/paperclip")
            self.assertIn("opencode", payload["matched_goal_terms"])
            self.assertIn("goal_reference_match", payload["selection_signals"])
            if payload["selected_reference"].endswith("opencode"):
                self.assertTrue(payload["reuse_existing_card_suggested"])
                self.assertEqual(payload["reference_memory"]["recommended_action"], "reuse_existing_card")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_research_auto_prefer_and_exclude_control_candidates(self) -> None:
        tmp = self._tmp_root("research-prefer-exclude")
        try:
            self._copy_scripts(tmp, ["reference-intake.py"])
            self._fake_reference_named(tmp, "paperclip", ("README.md", "LICENSE", "scripts", "tests"))
            self._fake_reference_named(tmp, "opencode", ("README.md", "LICENSE", "scripts", "tests"))
            result = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "research",
                    "--auto",
                    "--prefer",
                    "opencode",
                    "--exclude",
                    "paperclip",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["selected_reference"], "runtime/external-repos/local/opencode")
            self.assertTrue(any(item.endswith("paperclip") for item in payload["excluded_references"]))
            self.assertNotIn("paperclip", "\n".join(item["path"] for item in payload["reference_candidates"]))
            self.assertIn("prefer_match", payload["selection_signals"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_decide_updates_proposal_review_queue_and_activity_log(self) -> None:
        tmp = self._prepare_research_root()
        try:
            research = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "research",
                    "--local-path",
                    "runtime/external-repos/local/fake",
                    "--url",
                    "https://example.com/fake.git",
                    "--write-card",
                    "--proposal",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(research.returncode, 0, research.stdout + research.stderr)
            proposal_path = json.loads(research.stdout)["proposal_path"]
            decide = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "decide",
                    "--proposal",
                    proposal_path,
                    "--decision",
                    "accepted",
                    "--by",
                    "test",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(decide.returncode, 0, decide.stdout + decide.stderr)
            proposal_text = (tmp / proposal_path).read_text(encoding="utf-8")
            self.assertIn("- `decision`: accepted", proposal_text)
            self.assertIn("- `decided_by`: test", proposal_text)
            queue = _run([str(tmp / "scripts" / "review-queue.py"), "--root", str(tmp), "list", "--all", "--json"])
            self.assertEqual(queue.returncode, 0, queue.stdout + queue.stderr)
            items = json.loads(queue.stdout)
            self.assertEqual(items[0]["status"], "resolved")
            self.assertEqual(items[0]["decision"], "accepted")
            activity = (tmp / "runtime" / "activity-log.jsonl").read_text(encoding="utf-8")
            self.assertIn("reference_decision", activity)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_decide_defer_alias_marks_review_item_deferred(self) -> None:
        tmp = self._prepare_research_root()
        try:
            research = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "research",
                    "--local-path",
                    "runtime/external-repos/local/fake",
                    "--write-card",
                    "--proposal",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(research.returncode, 0, research.stdout + research.stderr)
            proposal_path = json.loads(research.stdout)["proposal_path"]
            decide = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "decide",
                    "--proposal",
                    proposal_path,
                    "--decision",
                    "defer",
                    "--by",
                    "test",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(decide.returncode, 0, decide.stdout + decide.stderr)
            payload = json.loads(decide.stdout)
            self.assertEqual(payload["decision"], "deferred")
            self.assertEqual(payload["review_queue_action"], "deferred")
            queue = _run([str(tmp / "scripts" / "review-queue.py"), "--root", str(tmp), "list", "--all", "--json"])
            self.assertEqual(json.loads(queue.stdout)[0]["status"], "deferred")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def _prepare_specialist_root(self) -> Path:
        tmp = self._tmp_root("specialist")
        self._copy_scripts(tmp, ["agent-brief.py"])
        (tmp / "scripts" / "incubating").mkdir(parents=True)
        shutil.copyfile(SCRIPTS / "incubating" / "agent-flow-delegate.py", tmp / "scripts" / "incubating" / "agent-flow-delegate.py")
        (tmp / "config").mkdir(parents=True)
        (tmp / "runtime").mkdir(parents=True)
        (tmp / "docs").mkdir()
        (tmp / "config" / "agent-team.yaml").write_text(
            "specialists:\n"
            "  docs-sync-auditor:\n"
            "    mission: \"Check docs drift.\"\n"
            "    write_policy: read_only\n"
            "    default_scope: [\"docs\"]\n"
            "    recommended_checks: [\"python3 scripts/verify-skeleton.py\"]\n",
            encoding="utf-8",
        )
        (tmp / "docs" / "README.md").write_text("# Docs\n", encoding="utf-8")
        return tmp

    def _specialist_usage_records(self, root: Path) -> list[dict]:
        path = root / "runtime" / "specialist-usage.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_specialist_propose_requires_on_demand_trigger(self) -> None:
        tmp = self._prepare_specialist_root()
        try:
            result = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "specialist",
                    "propose",
                    "--role",
                    "tiny-helper",
                    "--mission",
                    "Help with tiny things.",
                    "--write-policy",
                    "read_only",
                    "--scope",
                    "docs",
                    "--reason",
                    "quick targeted fix",
                    "--format",
                    "json",
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("at least one on-demand trigger", result.stderr)
            self.assertFalse((tmp / "runtime" / "proposals" / "specialists").exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_specialist_propose_and_approve_apply_overlay(self) -> None:
        tmp = self._prepare_specialist_root()
        try:
            propose = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "specialist",
                    "propose",
                    "--role",
                    "docs-migration-specialist",
                    "--mission",
                    "Review docs migration edge cases.",
                    "--write-policy",
                    "read_only",
                    "--scope",
                    "docs",
                    "--recommended-check",
                    "python3 scripts/verify-skeleton.py",
                    "--reason",
                    "context isolation for repeated docs migration review",
                    "--created-by",
                    "test",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(propose.returncode, 0, propose.stdout + propose.stderr)
            proposal_path = json.loads(propose.stdout)["proposal_path"]
            approve = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "specialist",
                    "approve",
                    "--proposal",
                    proposal_path,
                    "--by",
                    "test",
                    "--apply-overlay",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(approve.returncode, 0, approve.stdout + approve.stderr)
            payload = json.loads(approve.stdout)
            self.assertTrue(payload["overlay_applied"])
            overlay = (tmp / "config" / "agent-team-overrides.yaml").read_text(encoding="utf-8")
            self.assertIn("docs-migration-specialist:", overlay)
            brief = _run(
                [
                    str(tmp / "scripts" / "agent-brief.py"),
                    "--root",
                    str(tmp),
                    "--role",
                    "docs-migration-specialist",
                    "--goal",
                    "review docs",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(brief.returncode, 0, brief.stdout + brief.stderr)
            self.assertEqual(json.loads(brief.stdout)["role_source"], "project")
            records = self._specialist_usage_records(tmp)
            self.assertEqual(records[-1]["schema_version"], "ai-architecture.specialist-usage.v1")
            self.assertEqual(records[-1]["event_type"], "proposal_approved")
            self.assertEqual(records[-1]["proposal_id"], payload["proposal"]["proposal_id"])
            self.assertEqual(records[-1]["user_decision"], "approved")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_specialist_reject_records_usage_evidence(self) -> None:
        tmp = self._prepare_specialist_root()
        try:
            propose = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "specialist",
                    "propose",
                    "--role",
                    "docs-review-specialist",
                    "--mission",
                    "Review docs edge cases.",
                    "--write-policy",
                    "read_only",
                    "--scope",
                    "docs",
                    "--reason",
                    "context isolation for repeated docs review",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(propose.returncode, 0, propose.stdout + propose.stderr)
            proposal_path = json.loads(propose.stdout)["proposal_path"]
            reject = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "specialist",
                    "reject",
                    "--proposal",
                    proposal_path,
                    "--by",
                    "test",
                    "--note",
                    "token=supersecretvalue1234567890",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(reject.returncode, 0, reject.stdout + reject.stderr)
            records = self._specialist_usage_records(tmp)
            self.assertEqual(records[-1]["event_type"], "proposal_rejected")
            self.assertEqual(records[-1]["user_decision"], "rejected")
            self.assertIn("[REDACTED:generic_secret]", json.dumps(records[-1], ensure_ascii=False))
            self.assertNotIn("supersecretvalue1234567890", json.dumps(records[-1], ensure_ascii=False))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_specialist_preview_can_select_zero_specialists(self) -> None:
        tmp = self._prepare_specialist_root()
        try:
            result = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "specialist",
                    "preview",
                    "--goal",
                    "quick typo fix",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["delegation_plan"]["selected_roles"], [])
            self.assertFalse(payload["delegation_plan"]["requires_confirmation"])
            self.assertTrue((tmp / payload["plan_path"]).is_file())
            records = self._specialist_usage_records(tmp)
            self.assertEqual(records[-1]["event_type"], "preview_created")
            self.assertIn("docs-sync-auditor", records[-1]["candidate_roles"])
            self.assertEqual(records[-1]["selected_roles"], [])
            self.assertIn("docs-sync-auditor", records[-1]["rejected_roles"])
            self.assertIn("docs-sync-auditor", records[-1]["score_reasons"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_specialist_preview_and_execute_approved_plan_uses_existing_delegate(self) -> None:
        tmp = self._prepare_specialist_root()
        try:
            preview = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "specialist",
                    "preview",
                    "--goal",
                    "context isolation docs migration review",
                    "--approve",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
            preview_payload = json.loads(preview.stdout)
            self.assertEqual(preview_payload["delegation_plan"]["status"], "approved")
            self.assertIn("docs-sync-auditor", preview_payload["delegation_plan"]["selected_roles"])

            blocked = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "specialist",
                    "execute",
                    "--plan",
                    preview_payload["plan_path"],
                    "--format",
                    "json",
                ]
            )
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("--confirm", blocked.stderr)
            blocked_records = self._specialist_usage_records(tmp)
            self.assertEqual(blocked_records[-1]["event_type"], "delegation_execute_blocked")
            self.assertEqual(blocked_records[-1]["outcome"], "blocked")
            self.assertFalse(blocked_records[-1]["confirmed"])

            executed = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "specialist",
                    "execute",
                    "--plan",
                    preview_payload["plan_path"],
                    "--confirm",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(executed.returncode, 0, executed.stdout + executed.stderr)
            payload = json.loads(executed.stdout)
            self.assertEqual(payload["status"], "prepared")
            self.assertEqual(payload["handoffs"][0]["role"], "docs-sync-auditor")
            self.assertTrue((tmp / payload["handoffs"][0]["brief_path"]).is_file())
            records = self._specialist_usage_records(tmp)
            self.assertEqual(records[0]["event_type"], "preview_created")
            self.assertEqual(records[-1]["event_type"], "delegation_execute_prepared")
            self.assertEqual(records[-1]["outcome"], "prepared")
            self.assertTrue(records[-1]["confirmed"])
            self.assertEqual(records[-1]["handoff_paths"], [item["brief_path"] for item in payload["handoffs"]])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_specialist_packet_writes_harness_agnostic_spawn_packet(self) -> None:
        tmp = self._prepare_specialist_root()
        try:
            preview = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "specialist",
                    "preview",
                    "--goal",
                    "context isolation docs migration review",
                    "--approve",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
            preview_payload = json.loads(preview.stdout)
            result = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "specialist",
                    "packet",
                    "--plan",
                    preview_payload["plan_path"],
                    "--confirm",
                    "--by",
                    "test",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            packet_path = tmp / payload["packet_path"]
            self.assertTrue(packet_path.is_file())
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
            self.assertEqual(packet["schema_version"], "ai-architecture.spawn-ready-packet.v1")
            self.assertEqual(packet["status"], "ready")
            self.assertFalse(packet["auto_spawn"])
            self.assertFalse(packet["auto_chain"])
            self.assertFalse(packet["recursive_delegation_allowed"])
            self.assertEqual(packet["confirmed_by"], "test")
            self.assertIn("docs-sync-auditor", packet["selected_roles"])
            self.assertGreaterEqual(len(packet["units"]), 1)
            unit = packet["units"][0]
            self.assertEqual(unit["role"], "docs-sync-auditor")
            self.assertTrue((tmp / unit["brief_path"]).is_file())
            self.assertIn("completion_command", unit)
            self.assertEqual(unit["expected_result_schema"]["ledger"], "runtime/agent-runs.jsonl")
            self.assertTrue(unit["requires_individual_confirmation"])
            self.assertFalse(unit["recursive_delegation_allowed"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_specialist_packet_requires_approved_plan_and_confirmation(self) -> None:
        tmp = self._prepare_specialist_root()
        try:
            draft = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "specialist",
                    "preview",
                    "--goal",
                    "context isolation docs migration review",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(draft.returncode, 0, draft.stdout + draft.stderr)
            draft_payload = json.loads(draft.stdout)
            from_draft = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "specialist",
                    "packet",
                    "--plan",
                    draft_payload["plan_path"],
                    "--confirm",
                    "--format",
                    "json",
                ]
            )
            self.assertNotEqual(from_draft.returncode, 0)
            self.assertIn("approved", from_draft.stderr)

            approved = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "specialist",
                    "plan-approve",
                    "--plan",
                    draft_payload["plan_path"],
                    "--by",
                    "test",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(approved.returncode, 0, approved.stdout + approved.stderr)
            without_confirm = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "specialist",
                    "packet",
                    "--plan",
                    draft_payload["plan_path"],
                    "--format",
                    "json",
                ]
            )
            self.assertNotEqual(without_confirm.returncode, 0)
            self.assertIn("--confirm", without_confirm.stderr)
            self.assertFalse((tmp / "runtime" / "spawn-packets").exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_specialist_plan_approve_records_usage_evidence(self) -> None:
        tmp = self._prepare_specialist_root()
        try:
            preview = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "specialist",
                    "preview",
                    "--goal",
                    "context isolation docs migration review",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
            preview_payload = json.loads(preview.stdout)
            approve = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "specialist",
                    "plan-approve",
                    "--plan",
                    preview_payload["plan_path"],
                    "--by",
                    "test",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(approve.returncode, 0, approve.stdout + approve.stderr)
            records = self._specialist_usage_records(tmp)
            self.assertEqual(records[-1]["event_type"], "delegation_plan_approved")
            self.assertEqual(records[-1]["plan_id"], preview_payload["delegation_plan"]["plan_id"])
            self.assertEqual(records[-1]["user_decision"], "approved")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_closeout_failure_does_not_record_completion_evidence(self) -> None:
        tmp = self._tmp_root("closeout")
        try:
            scripts = tmp / "scripts"
            scripts.mkdir()
            (scripts / "verify.py").write_text(
                "import sys\nprint('forced failure')\nsys.exit(1)\n",
                encoding="utf-8",
            )
            (scripts / "quality-gate.py").write_text(
                "import sys\nprint('{\"checks\": []}')\nsys.exit(0 if '--strict' in sys.argv else 2)\n",
                encoding="utf-8",
            )
            (scripts / "task-closeout.py").write_text(
                "from pathlib import Path\nPath('called-task-closeout').write_text('called', encoding='utf-8')\n",
                encoding="utf-8",
            )
            result = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "closeout",
                    "--goal",
                    "forced failure",
                    "--changed-path",
                    "docs/example.md",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["recorded"])
            self.assertEqual(payload["skipped_record_reason"], "verify_or_quality_gate_failed")
            self.assertIn("source-recovery.py", payload["source_recovery_command"])
            self.assertIn("--failure verify", payload["source_recovery_command"])
            self.assertIn("--changed-path docs/example.md", payload["source_recovery_command"])
            self.assertIn("recovery_packet", payload)
            self.assertFalse(payload["recovery_packet"]["mutates_files"])
            self.assertEqual(payload["recovery_packet"]["failed_command"]["name"], "verify")
            self.assertIn("failure_classification", payload["recovery_packet"])
            timing_path = tmp / payload["timing_log"]
            self.assertTrue(timing_path.is_file())
            timing_records = [json.loads(line) for line in timing_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([record["phase"] for record in timing_records], ["verify"])
            self.assertEqual(timing_records[0]["profile"], "auto")
            self.assertEqual(timing_records[0]["exit_status"], 1)
            self.assertIsInstance(timing_records[0]["duration_ms"], int)
            self.assertFalse((tmp / "called-task-closeout").exists())
            self.assertFalse((tmp / "runtime" / "completion-evidence.jsonl").exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_start_routes_read_only_recommendations_to_research(self) -> None:
        result = _run([
            str(self.SCRIPT),
            "--root",
            str(REPO_ROOT),
            "start",
            "--goal",
            "다른 기능들 살펴봐줘 추천해줘",
            "--format",
            "json",
        ])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["mode"], "research")
        self.assertEqual(payload["write_policy"], "read_only")

    def test_start_keeps_direct_implementation_as_build(self) -> None:
        result = _run([
            str(self.SCRIPT),
            "--root",
            str(REPO_ROOT),
            "start",
            "--goal",
            "바로 통합할 것 5개 구현",
            "--format",
            "json",
        ])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["mode"], "build")
        self.assertEqual(payload["write_policy"], "manual_work_required")

    def test_closeout_invokes_quality_gate_strict(self) -> None:
        tmp = self._tmp_root("closeout-strict")
        try:
            scripts = tmp / "scripts"
            scripts.mkdir()
            (scripts / "verify.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
            (scripts / "quality-gate.py").write_text(
                "from pathlib import Path\nimport sys\nPath('strict-seen').write_text(str('--strict' in sys.argv), encoding='utf-8')\nPath('explain-seen').write_text(str('--explain' in sys.argv), encoding='utf-8')\nprint('{\"checks\": []}')\nsys.exit(0)\n",
                encoding="utf-8",
            )
            (scripts / "task-closeout.py").write_text("import sys\nprint('{\"recorded\": true}')\nsys.exit(0)\n", encoding="utf-8")
            result = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "closeout",
                    "--goal",
                    "strict closeout",
                    "--changed-path",
                    "docs/example.md",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual((tmp / "strict-seen").read_text(encoding="utf-8"), "True")
            self.assertEqual((tmp / "explain-seen").read_text(encoding="utf-8"), "True")
            timing_path = tmp / payload["timing_log"]
            timing_records = [json.loads(line) for line in timing_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([record["phase"] for record in timing_records], ["verify", "quality-gate", "task-closeout"])
            self.assertTrue(all(record["schema_version"] == "ai-architecture.closeout-timing.v1" for record in timing_records))
            self.assertTrue(all(isinstance(record["duration_ms"], int) for record in timing_records))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_closeout_quality_gate_failure_includes_explanations(self) -> None:
        tmp = self._tmp_root("closeout-explain")
        try:
            scripts = tmp / "scripts"
            scripts.mkdir()
            (scripts / "verify.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
            (scripts / "quality-gate.py").write_text(
                "import json, sys\n"
                "print(json.dumps({'checks': [], 'explanations': [{'name': 'codemap-freshness', 'classification': 'stale_docs', 'mutates_files': True, 'requires_confirmation': True, 'write_policy': 'write_with_confirmation', 'read_only_alternative': 'python3 scripts/generate-codemaps.py'}]}))\n"
                "sys.exit(1)\n",
                encoding="utf-8",
            )
            (scripts / "task-closeout.py").write_text("from pathlib import Path\nPath('called-task-closeout').write_text('called', encoding='utf-8')\n", encoding="utf-8")
            result = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "closeout",
                    "--goal",
                    "quality gate failure",
                    "--changed-path",
                    "docs/example.md",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["recorded"])
            self.assertEqual(payload["quality_gate_explanations"][0]["classification"], "stale_docs")
            self.assertTrue(payload["quality_gate_explanations"][0]["mutates_files"])
            self.assertFalse((tmp / "called-task-closeout").exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_start_build_intake_includes_plan_command(self) -> None:
        tmp = self._tmp_root("plan-intake")
        try:
            result = _run([str(self.SCRIPT), "--root", str(tmp), "start", "--goal", "새 기능 구현", "--format", "json"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertIn("agent-flow.py plan", payload["build_intake"]["plan_command"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_plan_command_creates_structured_active_plan(self) -> None:
        tmp = self._tmp_root("plan-create")
        try:
            result = _run([str(self.SCRIPT), "--root", str(tmp), "plan", "--goal", "새 기능 구현", "--format", "json"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            plan = tmp / payload["path"]
            text = plan.read_text(encoding="utf-8")
            self.assertIn("## Definition of Done", text)
            self.assertIn("python3 scripts/agent-flow.py closeout", text)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_recall_wrapper_passes_through_session_recall_json(self) -> None:
        tmp = self._tmp_root("recall")
        try:
            self._copy_scripts(tmp, ["session-recall.py", "redact.py"])
            (tmp / "runtime").mkdir(parents=True)
            (tmp / "state").mkdir()
            (tmp / "runtime" / "activity-log.jsonl").write_text('{"action":"recallneedle"}\n', encoding="utf-8")
            (tmp / "runtime" / "completion-evidence.jsonl").write_text("", encoding="utf-8")
            (tmp / "runtime" / "skill-usage.jsonl").write_text("", encoding="utf-8")
            (tmp / "state" / "decisions.md").write_text("## first\n", encoding="utf-8")
            result = _run([str(self.SCRIPT), "--root", str(tmp), "recall", "recallneedle", "--format", "json"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload)
            self.assertEqual(payload[0]["source_type"], "activity")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_recall_wrapper_rejects_empty_query(self) -> None:
        tmp = self._tmp_root("recall-empty")
        try:
            result = _run([str(self.SCRIPT), "--root", str(tmp), "recall", "   ", "--format", "json"])
            self.assertEqual(result.returncode, 2)
            self.assertIn("query is required", result.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_adopt_status_reports_target_without_running_full_tools(self) -> None:
        tmp = self._tmp_root("adopt-status")
        try:
            target = tmp / "target"
            self._init_clean_git_target(target)
            scripts = tmp / "scripts"
            scripts.mkdir()
            marker = tmp / "runtime" / "adopt-full-tool-ran"
            (scripts / "upgrade-from-skeleton.py").write_text(
                f"from pathlib import Path\nPath({str(marker)!r}).write_text('ran', encoding='utf-8')\n",
                encoding="utf-8",
            )
            (scripts / "ownership-initialize.py").write_text(
                f"from pathlib import Path\nPath({str(marker)!r}).write_text('ran', encoding='utf-8')\n",
                encoding="utf-8",
            )
            result = _run([str(self.SCRIPT), "--root", str(tmp), "adopt", "--target", str(target), "--status", "--format", "json"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["mode"], "status")
            self.assertTrue(payload["target_exists"])
            self.assertTrue(payload["target_git_clean"])
            self.assertFalse(marker.exists())
            self.assertEqual(payload["upgrade_brief"], {"safe_missing": 0, "manual_merge": 0, "risky_changed": 0})
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_adopt_profile_ready_allows_wiki_links_and_tbd_guidance(self) -> None:
        tmp = self._tmp_root("adopt-profile-ready")
        try:
            target = tmp / "target"
            self._init_clean_git_target(target)
            (target / "docs" / "PROJECT_PROFILE.md").write_text(
                "primary_goal: preserve [[wiki/link]] content\n"
                "success_criteria: tests pass and data remains intact\n"
                "failure_definition: operational data loss\n"
                "notes: unknown fields may be marked as TBD in future edits\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "docs/PROJECT_PROFILE.md"], cwd=str(target), check=True, capture_output=True, text=True)
            subprocess.run(["git", "commit", "-m", "profile"], cwd=str(target), check=True, capture_output=True, text=True)
            result = _run([str(self.SCRIPT), "--root", str(tmp), "adopt", "--target", str(target), "--status", "--format", "json"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["project_profile_state"], "ready")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_adopt_dry_run_synthesizes_upgrade_and_ownership(self) -> None:
        tmp = self._tmp_root("adopt-dry-run")
        try:
            target = tmp / "target"
            self._init_clean_git_target(target)
            self._fake_adopt_tools(tmp, candidate_paths=0, safe_additions=2)
            result = _run([str(self.SCRIPT), "--root", str(tmp), "adopt", "--target", str(target), "--format", "json"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["mode"], "dry_run")
            self.assertEqual(payload["upgrade_brief"]["safe_missing"], 2)
            self.assertEqual(payload["ownership"]["candidate_paths"], 0)
            self.assertEqual(payload["recommendation"], "apply_safe_ready")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_adopt_stops_when_candidate_threshold_exceeded(self) -> None:
        tmp = self._tmp_root("adopt-candidates")
        try:
            target = tmp / "target"
            self._init_clean_git_target(target)
            self._fake_adopt_tools(tmp, candidate_paths=21, safe_additions=2)
            result = _run([str(self.SCRIPT), "--root", str(tmp), "adopt", "--target", str(target), "--format", "json"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["recommendation"], "stop")
            self.assertTrue(payload["ownership"]["exceeds_threshold"])
            self.assertTrue(any("candidate_paths" in reason for reason in payload["stop_reasons"]))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_adopt_stops_when_target_git_dirty(self) -> None:
        tmp = self._tmp_root("adopt-dirty")
        try:
            target = tmp / "target"
            self._init_clean_git_target(target)
            (target / "dirty.txt").write_text("dirty\n", encoding="utf-8")
            self._fake_adopt_tools(tmp, candidate_paths=0, safe_additions=2)
            result = _run([str(self.SCRIPT), "--root", str(tmp), "adopt", "--target", str(target), "--format", "json"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["target_git_clean"])
            self.assertEqual(payload["recommendation"], "stop")
            self.assertTrue(any("dirty" in reason for reason in payload["stop_reasons"]))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_adopt_warns_on_gpl_license(self) -> None:
        tmp = self._tmp_root("adopt-license")
        try:
            target = tmp / "target"
            self._init_clean_git_target(target)
            (target / "LICENSE").write_text("GNU General Public License version 3\n", encoding="utf-8")
            subprocess.run(["git", "add", "LICENSE"], cwd=str(target), check=True, capture_output=True, text=True)
            subprocess.run(["git", "commit", "-m", "license"], cwd=str(target), check=True, capture_output=True, text=True)
            self._fake_adopt_tools(tmp, candidate_paths=0, safe_additions=2)
            result = _run([str(self.SCRIPT), "--root", str(tmp), "adopt", "--target", str(target), "--format", "json"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["license_signal"], "warning")
            self.assertEqual(payload["recommendation"], "stop")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_adopt_does_not_expose_write_or_risky_modes(self) -> None:
        tmp = self._tmp_root("adopt-flags")
        try:
            target = tmp / "target"
            target.mkdir()
            for forbidden in ("--apply-safe", "--verify", "--rollback", "--include-risky"):
                result = _run([str(self.SCRIPT), "--root", str(tmp), "adopt", "--target", str(target), forbidden, "--format", "json"])
                self.assertEqual(result.returncode, 2, forbidden)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_doctor_runs_common_diagnostics_without_tests_by_default(self) -> None:
        tmp = self._tmp_root("doctor")
        try:
            scripts = tmp / "scripts"
            scripts.mkdir()
            (scripts / "skeleton-doctor.py").write_text(
                "import json\nprint(json.dumps({'summary': {'OK': 2, 'WARN': 0, 'FAIL': 0}}))\n",
                encoding="utf-8",
            )
            (scripts / "verify-skeleton.py").write_text("print('skeleton OK: all checks passed')\n", encoding="utf-8")
            (scripts / "ownership-lock.py").write_text(
                "import json, sys\n"
                "print(json.dumps({'ok': True, 'argv': sys.argv}))\n",
                encoding="utf-8",
            )
            (scripts / "resume-readiness.py").write_text(
                "import json\nprint(json.dumps({'summary': {'ERROR': 0, 'WARN': 0, 'INFO': 0}}))\n",
                encoding="utf-8",
            )
            (scripts / "quality-gate.py").write_text(
                "import json, sys\nprint(json.dumps({'summary': {'OK': 5, 'SKIP': 1}, 'argv': sys.argv}))\n",
                encoding="utf-8",
            )
            result = _run([str(self.SCRIPT), "--root", str(tmp), "doctor", "--format", "json"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "OK")
            self.assertEqual(payload["summary"]["OK"], 5)
            self.assertEqual(payload["summary"]["FAIL"], 0)
            names = [item["name"] for item in payload["commands"]]
            self.assertEqual(
                names,
                ["skeleton-doctor", "verify-skeleton", "ownership-lock", "resume-readiness", "quality-gate"],
            )
            quality = next(item for item in payload["commands"] if item["name"] == "quality-gate")
            self.assertIn("--skip-tests", quality["json"]["argv"])
            self.assertIn("--tier", quality["json"]["argv"])
            self.assertIn("stable", quality["json"]["argv"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_doctor_reports_failure_but_keeps_full_report(self) -> None:
        tmp = self._tmp_root("doctor-failure")
        try:
            scripts = tmp / "scripts"
            scripts.mkdir()
            (scripts / "skeleton-doctor.py").write_text("print('{\"summary\": {\"OK\": 1}}')\n", encoding="utf-8")
            (scripts / "verify-skeleton.py").write_text("print('ok')\n", encoding="utf-8")
            (scripts / "ownership-lock.py").write_text(
                "import sys\nprint('classification drift')\nsys.exit(1)\n",
                encoding="utf-8",
            )
            (scripts / "resume-readiness.py").write_text("print('{\"summary\": {\"ERROR\": 0}}')\n", encoding="utf-8")
            (scripts / "quality-gate.py").write_text("print('{\"summary\": {\"OK\": 1}}')\n", encoding="utf-8")
            result = _run([str(self.SCRIPT), "--root", str(tmp), "doctor", "--format", "json"])
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "FAIL")
            self.assertEqual(payload["summary"]["FAIL"], 1)
            names = [item["name"] for item in payload["commands"]]
            self.assertIn("quality-gate", names)
            failed = next(item for item in payload["commands"] if item["name"] == "ownership-lock")
            self.assertFalse(failed["ok"])
            self.assertIn("inspect ownership-lock", payload["next_action"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_doctor_with_tests_omits_quality_gate_skip_tests(self) -> None:
        tmp = self._tmp_root("doctor-with-tests")
        try:
            scripts = tmp / "scripts"
            scripts.mkdir()
            for name in ("skeleton-doctor.py", "resume-readiness.py"):
                (scripts / name).write_text("print('{\"summary\": {}}')\n", encoding="utf-8")
            (scripts / "verify-skeleton.py").write_text("print('ok')\n", encoding="utf-8")
            (scripts / "ownership-lock.py").write_text("print('{\"ok\": true}')\n", encoding="utf-8")
            (scripts / "quality-gate.py").write_text(
                "import json, sys\nprint(json.dumps({'summary': {}, 'argv': sys.argv}))\n",
                encoding="utf-8",
            )
            result = _run(
                [str(self.SCRIPT), "--root", str(tmp), "doctor", "--tier", "all", "--with-tests", "--format", "json"]
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            quality = next(item for item in payload["commands"] if item["name"] == "quality-gate")
            self.assertNotIn("--skip-tests", quality["json"]["argv"])
            self.assertIn("all", quality["json"]["argv"])
            self.assertTrue(payload["with_tests"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_closeout_can_compare_quality_gate_baseline(self) -> None:
        tmp = self._tmp_root("closeout-diff")
        try:
            scripts = tmp / "scripts"
            scripts.mkdir()
            (tmp / "runtime").mkdir()
            baseline = tmp / "runtime" / "baseline.json"
            baseline.write_text('{"checks": []}', encoding="utf-8")
            (scripts / "verify.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
            (scripts / "quality-gate.py").write_text("import sys\nprint('{\"checks\": []}')\nsys.exit(0)\n", encoding="utf-8")
            (scripts / "diff-quality-gate.py").write_text("import sys\nprint('{\"introduced\": []}')\nsys.exit(0)\n", encoding="utf-8")
            (scripts / "task-closeout.py").write_text("import sys\nprint('{\"recorded\": true}')\nsys.exit(0)\n", encoding="utf-8")
            result = _run([
                str(self.SCRIPT),
                "--root",
                str(tmp),
                "closeout",
                "--goal",
                "diff closeout",
                "--changed-path",
                "docs/example.md",
                "--quality-baseline",
                str(baseline),
                "--format",
                "json",
            ])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            names = [item["name"] for item in json.loads(result.stdout)["commands"]]
            self.assertIn("diff-quality-gate", names)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_script_catalog_marks_agent_flow_as_only_public_command(self) -> None:
        catalog = REPO_ROOT / "scripts" / "catalog.yaml"
        self.assertTrue(catalog.is_file())
        text = catalog.read_text(encoding="utf-8")
        public_block = text.split("internal:", 1)[0]
        self.assertIn("path: scripts/agent-flow.py", public_block)
        self.assertNotIn("path: scripts/quality-gate.py", public_block)
        paths = re.findall(r"path:\s+(scripts/[A-Za-z0-9_./-]+)", text)
        missing = [path for path in paths if not (REPO_ROOT / path).exists()]
        self.assertEqual(missing, [])

    def test_start_marks_catalog_write_command_as_confirmation_required(self) -> None:
        tmp = self._tmp_root("catalog-write")
        try:
            self._copy_scripts(tmp, ["review-queue.py"])
            (tmp / "scripts" / "catalog.yaml").write_text(
                "version: 1\n"
                "public:\n"
                "  - path: scripts/agent-flow.py\n"
                "routing:\n"
                "  modes:\n"
                "    research:\n"
                "      goal_pattern: (오픈소스|reference)\n"
                "      reason: writes for test\n"
                "      confidence: high\n"
                "      requires_confirmation: false\n"
                "      signal: goal_mentions_reference\n"
                "      next_command: python scripts/agent-flow.py research --auto --write-card --proposal --format json\n"
                "      suggested_questions:\n"
                "        - q\n",
                encoding="utf-8",
            )
            result = _run(
                [
                    str(self.SCRIPT),
                    "--root",
                    str(tmp),
                    "start",
                    "--goal",
                    "오픈소스 먼저 봐줘",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["requires_confirmation"])
            self.assertEqual(payload["next_action_type"], "confirmation_required")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
