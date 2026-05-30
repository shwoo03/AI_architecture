# Skill writing recipe

Official links: see `templates/links.md`.

A skill is a small reusable workflow contract. Do not create skills for one-off
tasks.

## When to use

- A workflow repeats across projects or sessions.
- Inputs, outputs, permissions, and verification can be described.
- The skill reduces real duplication or operational risk.

## When not to use

- The task is a one-off prompt.
- The workflow has unclear activation conditions.
- The skill would silently perform broad side effects.

## Template

```text
# <skill-name>

## Purpose

## Activation

## Input contract

## Output contract

## Required tools / permissions

## Failure modes

## Verification

## Examples

## Anti-patterns
```

## Checklist

- Purpose is one sentence.
- Activation condition is specific.
- Inputs and outputs are named.
- Tool permissions are explicit.
- Failure modes say whether retry is safe.
- Verification has at least one acceptance check.
- Examples include one good and one bad use.

## Reuse-first skills

Use a skill when you repeatedly paste the same checklist or multi-step procedure.

Recommended optional skill:

- `open-source-adoption`
- Purpose: force agents to evaluate official SDKs/open-source projects before custom infrastructure.

A skill should be concise. Supporting files can hold candidate cards and decision matrices. Skills are optional and should not be enabled by default in every generated project.

## Common mistakes

- Using natural-language-only inputs for structured tasks.
- Leaving side effects after failure.
- Replacing official SDK behavior with a skill.
- Creating a skill that cannot be validated.
