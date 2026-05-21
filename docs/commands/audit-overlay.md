---
name: audit-overlay
intent: Read-only audit for a skeleton overlay installed in an existing project.
public: true
maps_to: python3 scripts/agent-flow.py audit-overlay --target <path> --format json
write_policy: read_only
requires_confirmation: false
---

# /audit-overlay

Read-only overlay audit. The agent should run:

`python3 scripts/agent-flow.py audit-overlay --target <path> --format json`

Use it after installing the skeleton into an existing project to separate skeleton health, project-owned behavior, environment availability, and security findings without rewriting generated surfaces or project files.
