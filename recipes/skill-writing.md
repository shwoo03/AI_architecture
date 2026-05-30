# Skill Writing Recipe

Use skills for repeated workflows. Do not create skills for one-off prompts.

## Recommended Structure

```text
skills/
  <skill-name>/
    skill.md
    accept.md       # optional
    deps.md         # optional
    examples/       # optional
```

## Required Sections

`skill.md` should include:

- Purpose and scope.
- Activation condition.
- Input contract.
- Output contract.
- Required tools and permissions.
- Failure modes.
- Verification.
- Examples.
- Anti-patterns.

## Input Contract Example

```text
Input:
- target_path: required path under repository root
- mode: review | edit | generate
- constraints: optional list of project constraints
```

## Output Contract Example

```text
Output:
- summary
- changed_files
- validation
- blockers
```

## Failure Modes

Classify failures as:

- `needs_user_input`
- `blocked_by_permission`
- `dependency_missing`
- `validation_failed`
- `unsafe_to_continue`

## Anti-Patterns

- Skills that silently edit broad parts of the repo.
- Skills that require undocumented secrets.
- Skills that duplicate official SDK behavior.
- Skills with vague activation conditions.
- Skills that cannot be validated.

