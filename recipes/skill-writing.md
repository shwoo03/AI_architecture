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

## Common mistakes

- Using natural-language-only inputs for structured tasks.
- Leaving side effects after failure.
- Replacing official SDK behavior with a skill.
- Creating a skill that cannot be validated.

