# Lightweight Reference Recipe

Use this recipe to keep provenance without turning the project into a research
ledger.

## Default

Use `docs/REFERENCES.md` with one short entry per important source.

Track:

- Source URL.
- Checked date.
- Why it matters.
- Adoption mode.
- Risk or license notes.

## Escalate To Research-Heavy Only When

- You copy code.
- You adopt architecture from an external repository.
- The project has compliance or audit requirements.
- Multiple references conflict and a decision record is needed.

## Adoption Modes

- `link`: reference only.
- `concept`: idea translated into local design.
- `dependency`: installed package or service.
- `wrapper`: thin adapter around external tool or API.
- `partial_copy`: copied code or structure with license and revision recorded.

## Avoid

- Collecting long link lists with no reason.
- Treating stars or popularity as adoption evidence.
- Copying code without license and source revision.

