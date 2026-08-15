# ALF Development Handover

## Session status

ALF is currently on `main` with a clean working tree.

Latest commit:

`0da9126 commands: add conventional query option aliases`

Recent commits:

* `0da9126 commands: add conventional query option aliases`
* `95b5dad main: support conventional help flags`
* `bfa65c0 commands: support conventional option syntax`
* `382e028 presentation: add command structure error`
* `af36956 commands: add deterministic vocabulary resolution`

Full test suite currently passes:

`123 passed`

Ruff passes cleanly and `git diff --check` is clean.

---

## What was completed

### 1. Deterministic command vocabulary

ALF now resolves command names using deterministic vocabulary resolution.

Examples such as:

```text
alf rem ...
alf reme ...
```

can resolve to the canonical `remember` command when the prefix is unambiguous.

Natural-language guessing is deliberately not used for command dispatch.

The design principle is:

> Where an explicit vocabulary can provide an unambiguous answer, ALF should resolve deterministically rather than ask an LLM to infer intent.

---

## 2. Deterministic category vocabulary

Memory categories use the same principle.

Examples:

```text
note
notes
pref
preference
```

can resolve to canonical categories where the resolution is unambiguous.

This behaviour is shared between positional arguments and option values.

For example:

```text
alf rem pref "Just a short test"
alf rem -c pref "Just a short test"
alf rem --category pref "Just a short test"
```

all resolve `pref` to:

```text
preference
```

---

## 3. Conventional command-line option syntax

ALF now follows normal command-line conventions.

Short options use:

```text
-a
-c
-g
-r
```

Long options use:

```text
--all
--category
--group
--relate
```

The short and long forms represent the same semantic option.

Examples:

```text
alf rem -c note "Dave is fictional"
alf rem --category note "Dave is fictional"

alf rem -c note "Dave is fictional" -r 41
alf rem note "Dave is fictional" --relate 41
```

Both positional and option-based category specification are deliberately supported where useful.

---

## 4. Query options

Memory queries now support conventional short aliases.

### Memories

```text
alf memories -a
alf memories --all

alf memories -c pref
alf memories --category preference

alf memories -g category
alf memories --group category
```

### Search

```text
alf search Peter -c pref
alf search Peter --category preference

alf search Peter --all
```

Category option values are resolved through the same deterministic category vocabulary used elsewhere.

Invalid categories are rejected at the command boundary rather than being passed deeper into the memory layer.

---

## 5. Command structure errors

ALF now handles malformed command structures gracefully.

Instead of allowing an incomplete or malformed command to fall through into an interactive `>` prompt, ALF presents:

```text
✗ Improper command structure.

See: alf help remember

Press Return to continue...
```

The user can therefore immediately discover the correct syntax.

This behaviour is deliberately presentation-level: command handlers determine that the structure is invalid, while `presentation.py` controls how that failure is communicated.

---

## 6. Help is part of command discoverability

The command catalogue is the authoritative source for command help.

The help system exposes:

* command description
* usage
* options
* notes
* examples

The conventional forms are therefore discoverable rather than being hidden implementation details.

For example:

```text
alf help remember
```

documents:

```text
-c, --category <name>
-r, --relate <ids>
```

and provides examples for both positional and option-based forms.

---

## 7. Conventional top-level help flags

`main.py` now handles:

```text
alf --help
alf -h
```

as presentation conveniences.

They are deliberately handled **outside normal command processing**.

They produce the same help presentation as:

```text
alf help
```

This distinction is intentional:

> `--help` and `-h` are conventional command-line presentation affordances, not ALF vocabulary commands.

---

## 8. Design constraint established

A significant architectural/design constraint has now been established:

> **ALF command syntax should conform to normal command-line design conventions wherever practical.**

This includes:

* positional arguments where natural
* short options using a single dash
* long options using a double dash
* options accepting values where required
* consistent short/long aliases
* options being allowed before or after positional content where the command permits it
* malformed option structures failing clearly
* controlled vocabulary being resolved deterministically
* syntax being discoverable through `alf help ...`

We should resist inventing ALF-specific command syntax merely because ALF could technically support it.

---

## Current command examples

The following are now legitimate forms:

```text
alf --help
alf -h
alf help
alf help remember
alf help search

alf rem pref "..."
alf rem -c pref "..."
alf rem --category preference "..."

alf rem note "..." -r 41
alf rem -c note "..." -r 41
alf rem note "..." --relate 41

alf memories
alf memories -a
alf memories --all
alf memories -c pref
alf memories --category preference
alf memories -g category
alf memories --group category

alf search Peter
alf search Peter -c pref
alf search Peter --category preference
alf search Peter --all
```

---

## Important architectural locations

### `src/alf/main.py`

Top-level process entry point.

Responsible for:

* interpreting the invocation
* conventional `-h` / `--help`
* passing ordinary commands to command dispatch
* handling unknown commands

It should remain thin.

### `src/alf/commands.py`

Command dispatch and command-specific argument processing.

Contains:

* command resolution
* command handlers
* remember syntax processing
* query option parsing
* command structure validation

This is where command syntax belongs.

### `src/alf/command_resolution.py`

Deterministic vocabulary resolution.

Responsible for resolving:

* command names
* memory categories

It should remain deliberately small and should **not become an intent-classification engine**.

### `src/alf/command_catalogue.py`

Authoritative command metadata.

Contains:

* command IDs
* descriptions
* usage
* options
* notes
* examples

Help should continue to derive from this catalogue rather than duplicating command syntax elsewhere.

### `src/alf/presentation.py`

Responsible for how ALF communicates results.

Important helpers now include:

```text
render_command_structure_error()
render_command_help()
render_commands()
render_invalid_memory_category()
```

Presentation should not decide what a command means.

---

## Testing state

The full test suite currently reports:

```text
123 passed
```

The command dispatch tests specifically cover:

* command prefix resolution
* category prefix resolution
* positional categories
* `-c` / `--category`
* `-a` / `--all`
* `-g` / `--group`
* `-r` / `--relate`
* malformed options
* missing option values
* duplicate category specification
* invalid categories
* command structure errors

Do not discard these tests: they encode the command-interface contract we have deliberately established.

---

## Current philosophy

ALF is increasingly being designed around a useful separation:

### Deterministic layer

Use explicit rules when the answer can be known reliably.

Examples:

* command resolution
* category resolution
* option parsing
* command structure
* safety boundaries
* capability routing

### LLM layer

Use the LLM where interpretation genuinely benefits from language understanding.

The LLM should not be allowed to replace straightforward deterministic mechanisms.

This is an important ALF architectural principle.

---

## Immediate next-session context

The command-interface milestone is complete.

Before starting new implementation, inspect:

```bash
git status
git log --oneline -10
pytest -q
```

Expected state:

* branch: `main`
* working tree: clean
* latest commit: `0da9126`
* tests: 123 passing

Then continue from the next agreed ALF development task rather than reopening the command-option work unless a genuine defect is discovered.

---

## Session boundary

This document represents the state at the end of the command-interface milestone.

The next session should treat the above command conventions as an established ALF design constraint, not merely as an implementation detail.

In particular:

> **ALF's command language should look and behave like a well-designed conventional command-line application.**

That principle should guide future commands, options, help output, parsing and error handling.
