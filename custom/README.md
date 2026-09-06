# `custom/` — your marketplace's own automation

This directory is **yours**. It is the home for scripts, helpers, tests, and data that *your* fork
runs — a self-updating vendoring job, a custom check, a report generator, anything. Everything here
survives every template sync (see [`docs/UPDATING.md`](../docs/UPDATING.md)); the template treats it
as fork-owned territory it does not manage.

The files shipped here (`hello_custom.py`, `tests/test_hello_custom.py`) are a **working hello-world
example** — copy or delete them exactly like the example skills under `src/skills/`.

## The two reserved zones

| You own | For |
|---|---|
| `custom/**` | scripts, helpers, lock files, data, and tests |
| `.github/workflows/custom-*.yml` | your own GitHub Actions workflows |

Both are protected by `merge=ours` in `.gitattributes`: if a future template update ever shipped a
file of the same name, your version wins whole-file.

## Rules of the road

- Python is PEP 723 + `uv run`, never `pip` — same as the rest of the repo.
- Put tests in `custom/tests/`; `uv run scripts/tasks.py test` discovers and runs them alongside the
  template's own suites, so your CI checks your code with no edits to any template-owned file.
- Push your `custom-*.yml` workflows with your own credentials. The default CI token cannot push
  `.github/workflows/`, but that restriction only affects the template's sync bot, never you.
- Your published capabilities still live in `src/`. `custom/` holds the machinery that *produces* or
  *checks* them, not the capabilities themselves.

## Copy me, don't edit me in place

To own a workflow outright, give it your **own** `custom-*.yml` name rather than editing the shipped
`custom-hello.yml`. Fork-only files — names the template does not ship — are preserved by every sync
path. A file whose name the template *does* ship is kept by the normal daily merge, but the manual
"finish a held-back workflow update" step restores the template's copy. So treat the shipped example
as a starting point you copy, the same way you copy `src/skills/example-single/`.
