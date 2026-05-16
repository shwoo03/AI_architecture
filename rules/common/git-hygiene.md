# Git Hygiene

- force push 절대 금지 (사용자 컨펌 받아도 신중)
- main 브랜치 직접 push 금지 (PR 통해)
- 커밋 메시지: <type>: <description> (feat/fix/refactor/docs/test/chore)
- `.codex/`, `.claude/`, `.mcp.json`, `CLAUDE.md` 변경분은 커밋 X
  (canonical source에서 재생성되는 runtime artifact, `.gitignore`)
- `.claude/settings.local.json`과 `.codex/config.toml`은 개인/런타임 설정으로 커밋 X
