---
date: 2026-07-27
purpose: how to author a skill for this marketplace, and how every frontmatter field changes its behavior
status: live
spec_checked: 2026-07-27 against https://code.claude.com/docs/en/skills (page dated 2026-07-24)
---

# Authoring skills

Skills are the capability this marketplace publishes today. You write one folder under `src/skills/`; CI packages it, publishes it, and generates its install instructions. This page is the contract for that folder — what goes in it, what each part changes, and what we check before it ships.

New here? Read sections 1 to 3 and you can ship something. The rest is reference.

## Table of contents

- [1. What a skill is, and what happens when you add one](#1-what-a-skill-is-and-what-happens-when-you-add-one)
- [2. Your first skill](#2-your-first-skill)
- [3. The two layouts](#3-the-two-layouts)
- [4. Frontmatter: who defines it, and why you can use fields this page doesn't list](#4-frontmatter-who-defines-it-and-why-you-can-use-fields-this-page-doesnt-list)
- [5. Field reference](#5-field-reference)
- [6. Shipping patterns](#6-shipping-patterns)
- [7. Shipping files alongside your skill](#7-shipping-files-alongside-your-skill)
- [8. What we check before publishing](#8-what-we-check-before-publishing)
  - [The full list is generated, not written](#the-full-list-is-generated-not-written)
- [9. How a skill surfaces after install](#9-how-a-skill-surfaces-after-install)
- [10. Scope: skills only](#10-scope-skills-only)
- [11. When something here doesn't work](#11-when-something-here-doesnt-work)

## 1. What a skill is, and what happens when you add one

[↑ Table of contents](#table-of-contents)

A **skill** is a folder containing a markdown file called `SKILL.md`. The markdown is the instructions; the frontmatter at the top of it controls **when** those instructions load and **what the agent may do** while they are loaded.

Once installed, a skill can be triggered two ways: a **user** types `/name`, or the **agent** loads it on its own because the task matches its description. Which of those is possible is something you decide, in frontmatter — see [section 5.3](#53-invocation).

Two words are used precisely throughout this page. The **agent** is the model doing the work. The **harness** is the program hosting it — the thing that discovers skills, decides what loads, and grants or withholds tools. Skills are consumed by more than one harness, so the page names a specific product only when quoting its specification.

What happens after you commit a skill folder:

```
you add src/skills/my-skill/SKILL.md
 └▶ CI validates the folder                    ← section 8, the rules we enforce
     └▶ the generator packages it              ← you write no packaging files yourself
         └▶ it is published to the marketplace ← appears in the generated catalog
             └▶ a user installs and invokes it ← section 9, how it surfaces
```

You write the skill. The generator produces whatever packaging the target platform needs, and CI commits that output — you never write or edit it. What that packaging looks like today is described in [ARCHITECTURE](../ARCHITECTURE.md); it is deliberately not your concern here, because it changes when platforms change and your skill folder should not.

## 2. Your first skill

[↑ Table of contents](#table-of-contents)

Create `src/skills/summarize-diff/SKILL.md`:

```markdown
---
description: Summarize uncommitted changes and flag anything risky. Use when asked what changed.
---

Summarize the uncommitted changes in this repository.

List the files touched, state the intent of the change in two sentences,
and flag anything that looks unintentional.
```

That is a complete, publishable skill. Commit and push; CI does the rest.

Only `description` is required by us, and it does double duty: it is how the agent decides whether the skill is relevant, and it is the one-line summary shown in the marketplace catalog. Write it as *what this does and when to use it*, not as a title.

## 3. The two layouts

[↑ Table of contents](#table-of-contents)

A folder under `src/skills/<plugin>/` is one of exactly two shapes. Which one you want depends on whether you are shipping a single skill or a related set that should install together.

```
solo — one skill                    multi — several skills, one install
src/skills/<plugin>/                src/skills/<plugin>/
├── SKILL.md                        ├── .metadata-SKILL.toml
└── (supporting files)              └── skills/
                                        ├── <skill-a>/SKILL.md
                                        └── <skill-b>/SKILL.md
```

- **Solo** — the folder names the *plugin*; the skill takes its name from the `SKILL.md` frontmatter `name`, falling back to the folder when none is set. Its `description` is also the catalog line. (The shipped example uses this: folder `example-single`, skill `hello`.)
- **Multi** — several skills install as one unit. There is no single `SKILL.md` to take a catalog line from, so `.metadata-SKILL.toml` supplies it:

  ```toml
  description = "One line describing the set, for the marketplace catalog."
  ```

  `description` is the only key read from that file.

Having both a root `SKILL.md` and a `skills/` subdirectory is an error — the generator cannot tell which shape you meant, and will say so.

**Both shapes publish the same package.** Solo is an authoring convenience, not a packaging shape: the generator lifts a root `SKILL.md` into `skills/<name>/SKILL.md` so every published plugin has one layout. A published plugin never declares its skills at its own root — see [hygiene/no-self-referential-skills-path](../../_generated/LINTING_RULES.md#hygieneno-self-referential-skills-path) for what that would break.

## 4. Frontmatter: who defines it, and why you can use fields this page doesn't list

[↑ Table of contents](#table-of-contents)

**Anthropic defines the skill format.** The [skills specification](https://code.claude.com/docs/en/skills) published for Claude Code is what the whole ecosystem writes against — it is the de facto standard for the format, and every skill here follows it. This page does not compete with it. Where the two disagree, **the specification is right and this page is stale** — please open an issue so we can fix it.

What this marketplace does with your frontmatter is narrow, and worth knowing precisely:

> **We copy your `SKILL.md` into the published package byte-for-byte. We read frontmatter only to find `description`.**

The consequence matters more than the mechanism:

> **Any frontmatter field the specification supports works here, whether or not this page lists it.**

If a new field is specified next month, you can use it next month. Nothing in this repository needs to change first, and you do not need to wait for this page to be updated. Section 5 is a convenience — a snapshot of the specification as of the date in this file's header — not a gate on what you are allowed to write.

## 5. Field reference

[↑ Table of contents](#table-of-contents)

> **Nothing in this section is ours.** These fields are the specification's, and we pass every one of them through untouched. This marketplace does enforce its own rules — but they are about **folder and name shape**, never about frontmatter values, and they are listed separately in [section 8](#8-what-we-check-before-publishing).

A snapshot of the specification, reorganized so you can find a field by *what you are trying to change* rather than alphabetically. Every quote is verbatim from [the frontmatter reference](https://code.claude.com/docs/en/skills#frontmatter-reference), retrieved on the date in this file's header. **All fields are optional.**

Each field sits on exactly one **axis**, and each axis answers one question:

| Axis | Question it answers |
|---|---|
| [Identity](#51-identity) | What is it called? |
| [Discovery](#52-discovery) | When is it offered? |
| [Invocation](#53-invocation) | Who may trigger it, and with what? |
| [Execution](#54-execution) | Where and how does it run? |
| [Authority](#55-authority) | What may it do while active? |

Effects are described in three registers, always in this order:

- **Outcome** — what the person using the skill sees change.
- **Harness** — what the hosting program does differently: discovery, loading, menus, permissions.
- **Agent** — what the model itself can and cannot do.

This page states effects in those terms rather than naming a product, because a skill outlives the harness it was first written for. Where a behavior is genuinely specific to one implementation, it is quoted from that implementation's specification and marked with the version that introduced it.

### 5.1 Identity

[↑ Table of contents](#table-of-contents)

| Field | Specification says |
|---|---|
| `name` | "Display name shown in skill listings. Defaults to the directory name. See [How a skill gets its command name](https://code.claude.com/docs/en/skills#how-a-skill-gets-its-command-name) for how the field interacts with the name you type to invoke the skill." |

**Effect**

- **Outcome** — in a published plugin, `name` sets the last segment of what a user types: `skills/review/SKILL.md` with `name: fancy` is invoked as `/<plugin>:fancy`.
- **Harness** — the plugin prefix always remains; the bare `/fancy` form resolves only while that name is unambiguous.
- **Agent** — changes what the skill is called, not whether the agent may use it.

In the multi layout we require `name` to match its folder name, so one skill can never end up with two user-visible names ([hygiene/folder-matches-name](../../_generated/LINTING_RULES.md#hygienefolder-matches-name)). The solo layout is exempt because it cannot diverge: the folder there names the plugin, and the generator names the published skill folder *from* the frontmatter `name`.

### 5.2 Discovery

[↑ Table of contents](#table-of-contents)

| Field | Specification says |
|---|---|
| `description` | "What the skill does and when to use it. Claude uses this to decide when to apply the skill. If omitted, uses the first paragraph of markdown content. Put the key use case first: the combined `description` and `when_to_use` text is truncated at **1,536 characters** in the skill listing to reduce context usage." |
| `when_to_use` | "Additional context for when Claude should invoke the skill, such as trigger phrases or example requests. Appended to `description` in the skill listing and counts toward the 1,536-character cap." |
| `paths` | "Glob patterns that limit when this skill is activated. Accepts a comma-separated string or a YAML list. When set, Claude loads the skill automatically only when working with files matching the patterns." |

**Effect**

- **Outcome** — a skill that never fires when you expected it to is almost always a `description` problem, not a content problem.
- **Harness** — `description` and `when_to_use` share one 1,536-character budget in the session listing; text past the cap is dropped silently.
- **Agent** — this text is the *only* part of your skill the agent sees before deciding to load it. The body is invisible until invocation.

### 5.3 Invocation

[↑ Table of contents](#table-of-contents)

| Field | Specification says |
|---|---|
| `disable-model-invocation` | "Set to `true` to prevent Claude from automatically loading this skill. Use for workflows you want to trigger manually with `/name`. Also prevents the skill from being preloaded into subagents. **As of v2.1.196**, also prevents the skill from running when a scheduled task fires with the skill as its prompt. Default: `false`." |
| `user-invocable` | "Set to `false` to hide from the `/` menu. Use for background knowledge users shouldn't invoke directly. Default: `true`." |
| `argument-hint` | "Hint shown during autocomplete to indicate expected arguments. Example: `[issue-number]` or `[filename] [format]`." |
| `arguments` | "Named positional arguments for `$name` substitution in the skill content. Accepts a space-separated string or a YAML list. Names map to argument positions in order." |

**Effect**

The two booleans are mirror images, and between them they define the whole invocation surface:

| Frontmatter | Agent may invoke | User may invoke |
|---|---|---|
| *(neither set)* | yes | yes |
| `disable-model-invocation: true` | **no** | yes |
| `user-invocable: false` | yes | **no** |

- **Outcome** — `disable-model-invocation: true` gives you a skill that runs only when a user types it. Use it for anything with side effects: deploys, commits, sending messages.
- **Harness** — it removes the skill from the agent's listing entirely, and also blocks subagent preloading and scheduled-task firing.
- **Agent** — the agent cannot reach the skill at all. It is not discouraged from invoking it; it is unable to.

Arguments are substituted into the body before the agent reads it. `$ARGUMENTS` is the full trailing text as typed; `$ARGUMENTS[N]` and the shorthand `$N` are positional and use shell-style quoting. Declaring `arguments` lets you write `$environment` instead of `$1`.

### 5.4 Execution

[↑ Table of contents](#table-of-contents)

| Field | Specification says |
|---|---|
| `context` | "Set to `fork` to run in a forked subagent context." |
| `agent` | "Which subagent type to use when `context: fork` is set." |
| `background` | "Only applies with `context: fork`. Set to `false` to wait for the forked subagent's result in the turn that invoked the skill, instead of running it in the background. Default: `true`. **Requires Claude Code v2.1.218 or later.**" |
| `model` | "Model to use when this skill is active. The override applies for the rest of the current turn and is not saved to settings; the session model resumes on your next prompt. Accepts the same values as `/model`, or `inherit` to keep the active model." |
| `effort` | "Effort level when this skill is active. Overrides the session effort level. Default: inherits from session. Options: `low`, `medium`, `high`, `xhigh`, `max`; available levels depend on the model." |
| `shell` | "Shell to use for `` !`command` `` and ` ```! ` blocks in this skill. Accepts `bash` (default) or `powershell`." |

**Effect**

- **Outcome** — `context: fork` changes the shape of the interaction: the work happens elsewhere and a result comes back, instead of the skill's instructions joining your conversation.
- **Harness** — a forked skill gets its own context window and, by default, runs in the background while you keep working. `model` and `effort` overrides last only for the current turn and are never written to settings.
- **Agent** — a forked run has **no access to your conversation history**. The skill body becomes the subagent's entire prompt, so it must be self-contained.

`shell: powershell` matters for cross-platform skills — inline `` !`command` `` blocks then run through PowerShell rather than bash.

### 5.5 Authority

[↑ Table of contents](#table-of-contents)

| Field | Specification says |
|---|---|
| `allowed-tools` | "Tools Claude can use without asking permission during the turn that invokes this skill. The grant clears when you send your next message. Accepts a space- or comma-separated string, or a YAML list." |
| `disallowed-tools` | "Tools removed from Claude's available pool while this skill is active. Use for autonomous skills that should never call certain tools, such as `AskUserQuestion` for a background loop. The restriction clears when you send your next message." |
| `hooks` | "Hooks scoped to this skill's lifecycle." |

**Effect**

- **Outcome** — `allowed-tools` removes permission prompts for the listed tools. Without it, a script your skill tells the agent to run still prompts.
- **Harness** — the grant is **turn-scoped**: it applies to the turn that invoked the skill and clears on the next message, even though the skill's instructions stay loaded. Invoking again re-applies it.
- **Agent** — `allowed-tools` does not restrict anything; every other tool stays callable under normal permission settings. `disallowed-tools` is the field that removes capability.

## 6. Shipping patterns

[↑ Table of contents](#table-of-contents)

Three shapes that cover most of what people write.

**Background knowledge — the agent loads it, nobody types it**

```markdown
---
description: How the legacy billing system models proration. Use when touching billing code.
paths: "src/billing/**"
user-invocable: false
---
```

**A workflow you trigger — you type it, the agent never starts it**

```markdown
---
name: deploy
description: Deploy the current branch to an environment and report the result.
disable-model-invocation: true
argument-hint: "[environment]"
allowed-tools: Bash
---

Current branch: !`git branch --show-current`

Deploy this branch to the `$1` environment (default `staging`).
Report the deployed SHA and any failing health check.
```

This is the pattern for anything with side effects. `disable-model-invocation: true` is what makes it human-only.

**An isolated investigation — runs elsewhere, reports back**

```markdown
---
description: Audit the repository for unused dependencies and report findings.
context: fork
background: false
effort: high
---
```

Remember that a forked skill cannot see your conversation, so say everything it needs in the body.

## 7. Shipping files alongside your skill

[↑ Table of contents](#table-of-contents)

Your skill folder can hold more than `SKILL.md`. Scripts, reference documents, templates and examples all travel with it and are copied into the published package unchanged. This is what a folder buys you over a lone file: `SKILL.md` stays short, and the bulky material loads only when it is actually needed.

```
src/skills/render-chart/
├── SKILL.md
├── scripts/plot.py
└── references/chart-types.md
```

**The problem this creates:** when a user installs your skill, it lands somewhere you cannot predict — a cache path that includes a version and changes on every update. A hardcoded path in your instructions would break immediately.

**The fix:** refer to bundled files through `${CLAUDE_PLUGIN_ROOT}`, which the harness replaces at runtime with wherever your skill actually ended up.

```markdown
Run: uv run ${CLAUDE_PLUGIN_ROOT}/scripts/plot.py
```

Mention each supporting file in `SKILL.md` and say what it contains, so the agent knows when to open it. There is no other substitution mechanism — nothing rewrites paths for you at install time, so a path that does not start with `${CLAUDE_PLUGIN_ROOT}` will be taken literally.

## 8. What we check before publishing

[↑ Table of contents](#table-of-contents)

[Section 5](#5-field-reference) is the specification's territory — we pass all of it through untouched. This section is ours, and it is deliberately narrow: rules about the **shape of your folder and the names in it**, so that what a user ends up typing is predictable. We enforce nothing about frontmatter values.

They run on every commit. An `error` blocks publishing; a `warning` does not.

| Applies to | We check that it |
|---|---|
| Your skill folder name | is kebab-case, at most 32 characters |
| Your skill name | is kebab-case, 1-32 characters, unique within the plugin |
| Your skill name | does not shadow a built-in command name *(warning)* |
| Any markdown with frontmatter | declares a non-empty `description` |
| Multi-layout skill folders | the folder name matches the frontmatter `name` |
| The folder generally | contains no generated-packaging directory |
| Marketplace identity | is well-formed — a forker's concern, not a contributor's |

### The full list is generated, not written

[↑ Table of contents](#table-of-contents)

The authoritative list lives at [`_generated/LINTING_RULES.md`](../../_generated/LINTING_RULES.md). Every rule there carries its id, what it applies to, the requirement, why it exists, its severity, and a real captured example of the failure.

It is **generated from `scripts/lint_rules/`** on every run and drift-checked in CI, exactly like the catalog. The registry is not a description of the checks — each rule *is* the check, so the list cannot describe a rule that does not run, or omit one that does.

Every rule also ships input that provokes it. That input is executed at generation time, and the failure message quoted under each rule is the one the validator actually produced — not one somebody typed. A rule that stops firing fails the build rather than quietly becoming fiction.

Every failure message quotes its rule id, and the id itself says what went wrong:

```
src/skills/My_Skill: folder name is not kebab-case (naming/folder-kebab-case)
                                                    ^^^^^^^^^^^^^^^^^^^^^^^^
```

Run them yourself before pushing:

```bash
uv run scripts/lint.py                   # just these rules, fast
uv run scripts/tasks.py verify           # the full gate CI runs
```

Note that `description` is **required by us** but only *recommended* by the specification. We require it because it is also the marketplace catalog line, and an entry with no line is unusable in a listing.

## 9. How a skill surfaces after install

[↑ Table of contents](#table-of-contents)

- Namespaced: `/<brand>-skill-<plugin>:<name>` — always resolves.
- Bare: `/<name>` — resolves only while that name is unambiguous across everything the user has installed.
- The agent may also invoke it on its own from `description` — **unless** `disable-model-invocation: true` is set.

The full chain from folder name to what a user types is in [ARCHITECTURE](../ARCHITECTURE.md), "The name chain".

## 10. Scope: skills only

[↑ Table of contents](#table-of-contents)

**Skills are the only shape this marketplace accepts.** We do not emit or accept a `commands/` directory, and flat command files are not a source layout here.

Claude Code merged slash commands into skills in [v2.1.3](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) — *"Merged slash commands and skills, simplifying the mental model with no change in behavior"* — so a flat file and a skill folder produce the same result. Accepting both would give this repository two spellings for one thing and two ways for a name to resolve. Everything a flat file could do, `SKILL.md` does; the workflow pattern in [section 6](#6-shipping-patterns) is how.

## 11. When something here doesn't work

[↑ Table of contents](#table-of-contents)

If a frontmatter field appears to do nothing, check your Claude Code version before assuming the field is wrong. Some behaviors described above landed in specific releases:

| Behavior | Needs |
|---|---|
| `background` | v2.1.218 or later |
| Booleans written as `yes` / `no` / `on` / `off` / `1` / `0` | v2.1.218 or later (before that, only `true` / `false`) |
| `disable-model-invocation` also blocking scheduled tasks | v2.1.196 or later |
| Skills and slash commands being the same thing | v2.1.3 or later |

Run `claude --version` to check. `claude --debug` shows why a skill was skipped at load time.

If the problem is not a version gap, this page may simply be out of date. The header of this file records when it was last checked against the specification; the specification itself is authoritative:

- [Extend Claude with skills](https://code.claude.com/docs/en/skills) — frontmatter, invocation, arguments, lifecycle.
- [Plugins reference](https://code.claude.com/docs/en/plugins-reference) — how plugins package and load skills.

For symptoms specific to this marketplace, see [troubleshooting](../troubleshooting/).

