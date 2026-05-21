# Git Hygiene

- force push 절대 금지 (사용자 컨펌 받아도 신중)
- 기본은 PR을 통한 반영이지만, 사용자가 private mirror 또는 main 직접 push를 명시하면 그 범위 안에서 직접 push 가능
- 커밋 메시지: <type>: <description> (feat/fix/refactor/docs/test/chore)
- private near-original mirror에서는 `.codex/`, `.claude/`, `.mcp.json`, `CLAUDE.md` 같은 generated surface도 커밋 가능
  - 단, 직접 편집하지 말고 canonical source(`skills/`, `agents/`, `rules/`, `mcp/servers.yaml`)를 수정한 뒤 `scripts/convert.py`로 재생성
- `.env`, `.claude/settings.local.json`, `.codex/config.toml` 같은 로컬/시크릿성 파일은 사용자가 private repo 범위와 포함을 명시 승인한 경우에만 커밋
  - 커밋은 가능해도 로그, 리뷰, 응답에는 평문 시크릿 값을 출력하지 않음
- 항상 제외: `__pycache__/`, `*.py[cod]`, `node_modules/`, `.venv/`, `venv/`, `env/`, 빌드 산출물, 재생성 가능한 로컬 캐시
- Python bytecode가 이미 git에 추적되면 cleanup으로 해결하지 말고 `git rm --cached`로 추적을 끊은 뒤 ignore 규칙을 유지한다. `scripts/verify-skeleton.py`는 tracked `.pyc/.pyo/.pyd`와 `__pycache__` 내부 추적 파일을 오류로 보고한다.
