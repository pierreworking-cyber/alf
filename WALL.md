# WALL

Working architectural notes for ALF.

This document records current design direction, architectural boundaries,
important decisions and areas still under consideration.

It is intentionally temporary.

When an idea becomes an established and durable part of ALF's design, it
should move into ALF's persistent memory and be removed from this document.

The repository and current implementation remain the authoritative source for
what ALF actually does. This document describes the design that should guide
development.

---

## Core philosophy

ALF is Peter's long-term local computing companion.

ALF is not intended to become another chatbot.

The fundamental architectural principle is:

**ALF owns the application. The LLM is a replaceable component.**

The LLM may interpret evidence and provide natural-language responses, but it
must not quietly acquire responsibilities that belong to ALF's deterministic
application layer.

ALF should remain:

* local;
* persistent;
* inspectable;
* evidence-aware;
* deterministic where appropriate;
* LLM-assisted rather than LLM-controlled;
* useful rather than theatrical.

The design should make it possible to replace the LLM without replacing ALF.

---

# Architecture

ALF is composed of small, focused subsystems.

Each subsystem should own its own knowledge and, where appropriate, describe
its capabilities rather than requiring other parts of ALF to maintain
duplicated knowledge.

Interfaces should consume those capabilities rather than maintaining
independent registration lists.

Prefer simple modules over clever abstractions.

Keep modules focused on a single responsibility.

Current major responsibilities include:

* `identity.py` — ALF identity;
* `memory.py` — persistent memory;
* `presentation.py` — user-facing output;
* `status.py` — runtime/status information;
* `system.py` — controlled operating-system information;
* `git.py` — repository awareness;
* `commands.py` — command registration, dispatch and command metadata;
* `command_catalogue.py` — structured command metadata;
* `research.py` — external research and evidence retrieval;
* `llm.py` — local LLM interaction;
* routing/interpretation modules — determining how questions are handled and
  interpreting supplied evidence.

Capability discovery currently identifies reporting subsystems.

Future introspection may distinguish between capability-reporting modules and
internal helper modules.

---

# Evidence and the LLM

ALF follows the principle:

**Capabilities produce evidence → the LLM interprets evidence → presentation
renders the answer.**

The LLM is not ALF's source of truth.

ALF may obtain evidence from:

* persistent memory;
* current system information;
* repository information;
* external research;
* other explicitly permitted capabilities.

The LLM may then interpret and synthesise that evidence into a useful
natural-language response.

Where appropriate, ALF may also allow the LLM's existing general knowledge
to contribute to an answer. This does not make that knowledge authoritative.

ALF must be able to distinguish between information it has obtained and an
interpretation supplied by the LLM.

The routing mechanism should determine what evidence or capability is required
before asking the LLM to formulate the final response.

---

## LLM knowledge-provider qualification

The local LLM must not be assumed to be a reliable independent source of
factual knowledge merely because it produces fluent answers.

The configured Qwen 3:4b model was tested against a fixed 20-question factual
knowledge corpus.

The qualification standard was deliberately strict: one substantive factual
failure is sufficient to reject a model as an independent knowledge provider.

The initial qualification produced:

* 20 questions tested;
* 19 acceptable answers;
* 1 substantive failure;
* result: **rejected as a knowledge provider**.

The failed question concerned Python's `venv` module. The model described
`venv` only as providing isolated environments for dependency management,
rather than adequately identifying Python virtual environments.

The conclusion is that the local LLM must remain an interpreter of supplied
evidence rather than an authoritative knowledge provider.

The qualification corpus and test are retained as an explicit model-
qualification benchmark.

They are not part of normal ALF operation and are excluded from the ordinary
pytest run.

If the configured LLM changes, the benchmark may be rerun to determine
whether the new model qualifies. The qualification standard should not be
weakened to accommodate a model.

### LLM evaluation experiment

Two local LLMs were also tested as independent evaluators of candidate factual
answers against the deterministic knowledge corpus.

The experiment demonstrated that agreement between LLM evaluators does not
establish factual correctness.

Both Qwen3:4B and Qwen3:8B accepted some objectively rejected answers,
including approximate or semantically incorrect answers.

The experiment also exposed limitations in deterministic answer matching:
exact string matching can reject semantically correct answers and can accept
answers containing correct phrases while making an incorrect assertion.

Therefore:

**LLM agreement is not evidence of factual correctness.**

This experiment reinforces the architectural boundary between evidence and
interpretation.

---

# Question and knowledge routing

ALF is responsible for deciding how a question should be answered.

Knowledge-source selection should be deterministic and implemented by ALF
rather than delegated to the LLM.

The routing mechanism should remain:

* small;
* explicit;
* deterministic;
* testable.

Do not introduce confidence scoring, secondary LLM judges, semantic
classification or similar machinery unless simpler routing proves inadequate.

Potential knowledge sources include:

* persistent memory;
* current system information;
* repository information;
* fresh external research;
* the local LLM's general knowledge.

Memory should be considered before external research where appropriate.

The LLM should receive the evidence selected by ALF and interpret it rather
than deciding what information ALF should obtain.

### Research

ALF's local search service is the general web-search interface.

Do not introduce a separate Wikipedia search layer unless a concrete
requirement demonstrates that the general search service cannot satisfy the
need.

The user's original question should be preserved faithfully.

In particular, the local LLM has demonstrated that it can produce useful
search queries but can be unreliable when interpreting punctuation.

Therefore:

* do not allow the LLM to casually rewrite away meaningful punctuation;
* preserve the original question;
* allow the research stage to determine what evidence is retrieved;
* allow the evidence-evaluation stage to determine whether the evidence
  actually answers the question.

### Known limitation

Questions classified as `Route.LLM` are currently answered by the local model
without external evidence.

Consequently, the model may confidently answer incorrectly when it lacks
knowledge of a named application, library, command or other specific subject.

This is currently considered a knowledge-provider limitation, not
necessarily a routing failure.

ALF may honestly decline to answer when no suitable capability or reliable
source is available.

An honest limitation is a valid outcome, not a failure.

---

# Memory

ALF's memory is persistent structured data stored in SQLite.

The current development database is:

`~/.local/share/alf/alf.db`

The longer-term design is to keep runtime and personal data outside the source
tree and version control.

Memory is intended to preserve not only facts but also decisions, preferences,
reasoning and the evolution of ideas over time.

Current memory capabilities include:

* persistent memory;
* permanent memory IDs;
* categories;
* active/archived state;
* memory search;
* memory history;
* relationships between memories;
* `previous_memory_id`;
* permanent deletion;
* in-place editing.

Memory relationships remain deliberately simple until a concrete use case
requires richer relationship types.

## Memory history

Memory history is based on the `previous_memory_id` chain.

Creating a new memory or revision does not modify an existing memory.

This preserves the evolution of knowledge rather than overwriting historical
records.

Newer memories may supersede older memories while the older records remain
available.

## Deletion

The previous `forget` concept has been removed.

ALF now supports permanent deletion through:

* `delete_memory(memory_id)`;
* `delete_memories(memory_ids)`.

Deletion uses SQL `DELETE` and genuinely removes the selected records from the
`memories` table.

Deletion does not rewrite references held by surviving memories.

Consequently:

* `previous_memory_id` may refer to a deleted memory;
* `related_memory_ids` may contain IDs that no longer exist;
* history and relationship lookup naturally ignore missing records.

This behaviour deliberately preserves surviving historical/reference
information rather than silently rewriting it after deletion.

## Editing

`update_memory(memory_id, content)` edits an existing memory in place.

It does not create a new memory.

This distinction is intentional:

* creating a new memory/revision participates in the memory-history model;
* explicit editing is an in-place operation.

The distinction should not be changed casually.

## Future memory work

Potential future work includes:

* database migration support when the schema first requires it;
* duplicate detection;
* richer memory metadata;
* timestamps and additional metadata;
* further relationship facilities;
* additional memory maintenance tools.

Migration machinery should not be introduced until an actual schema change
requires it.

---

# Presentation

Presentation is responsible only for displaying information.

Rules:

* business logic belongs outside renderers;
* renderers receive structured data rather than formatted strings;
* avoid capability-specific logic inside presentation;
* never expose Python implementation details to the user;
* use established presentation helpers rather than ad-hoc output in command
  logic.

User-facing ALF output should not expose internal Python namespaces such as
`alf.some_module` unless explicitly requested.

Rendering responsibilities should remain separate from application logic.

---

# Commands

Command dispatch is deliberately deterministic.

Unambiguous command prefixes are permitted.

For example:

`alf rem`

may resolve to:

`alf remember`

Natural-language guessing is not used for command dispatch.

The command vocabulary currently includes commands such as:

* `help`;
* `calc`;
* `remember`;
* `relate`;
* `memories`;
* `categories`;
* `memory`;
* `history`;
* `health`;
* `about`;
* `archive`;
* `delete`;
* `version`;
* `search`;
* `question`.

The command catalogue is the central source of command metadata.

Future interfaces should consume command metadata rather than duplicating
command descriptions.

---

# System awareness

ALF's system capability is defined by the **interfaces it is permitted to
inspect**, rather than by a hard-coded inventory of system components.

`system.py` should therefore provide controlled access to explicitly permitted
system interfaces.

The distinction is:

* **Interfaces** — what ALF is permitted to inspect;
* **System information** — what ALF has obtained from those interfaces;
* **Presentation** — how that information is displayed;
* **LLM** — how available information is interpreted and explained.

The system capability should advertise its permitted interfaces rather than
presenting a fixed machine snapshot as the definition of the capability.

ALF must never be given unrestricted shell execution through the system
capability.

Interfaces must be explicit and controlled.

The LLM should remain replaceable. System-interface descriptions and prompts
should therefore use general, model-independent language and should not depend
on behaviour specific to the current local model.

---

# Privilege boundary and user-directed actions

ALF must not autonomously invoke `sudo`, elevate privileges, or execute
commands requiring elevated privileges.

When privileged information is required, ALF may explain that the information
requires a privileged operation.

ALF must not turn a privileged operation into an instruction for the user to
carry out.

If a privileged command needs to be mentioned for explanatory purposes, it
should be described as an example of the operation that would be required,
rather than presented as a requested or recommended action.

ALF must never imply that an action has occurred when it has not.

A harmless part of a question must not legitimise a dangerous part.

---

# Health and self-inspection

ALF should be able to inspect its own internal health.

The health system should consume subsystem self-description rather than
maintaining duplicated knowledge about individual subsystems.

Initial health responsibilities include:

* auditing capability providers;
* reporting self-describing subsystems;
* reporting non-reporting modules separately;
* detecting malformed capability metadata;
* detecting module import failures.

Health reports should record complete subsystem state.

User-facing health output should prioritise actionable problems over normal
operation.

Potential future health checks include:

* database integrity;
* configuration validation;
* dependency checks;
* migration status.

---

# TUI

A Textual TUI exists as an experimental interface in:

`src/alf/tui.py`

It currently provides workspaces for:

* Question;
* Remember;
* Memories;
* Calc.

The Memories workspace supports:

* selecting a memory;
* editing a memory;
* saving an edit;
* cancelling an edit;
* archiving a memory;
* permanently deleting a memory.

The TUI should consume ALF's existing command and subsystem knowledge rather
than becoming an independent implementation of ALF's architecture.

The Question workspace remains partly a playground and does not yet represent
the completed question machinery.

The TUI is therefore an experimental interface, not a completed architectural
commitment.

---

# Data and project boundaries

User and runtime data should belong in the user data directory.

Examples include:

* SQLite databases;
* identity data;
* configuration;
* future runtime state.

The project directory should contain source code and project assets rather than
personal runtime data.


Configuration should eventually be clearly separated from identity.

---

# Development principles

When uncertain:

* choose the simpler design;
* prefer explicit code over abstraction;
* preserve backwards compatibility where practical;
* keep changes small and testable;
* refactor only after duplication becomes obvious.

If something is difficult to explain, it is probably too complicated.

ALF's architecture should evolve through experience.

Earlier assumptions are not sacred. If experience demonstrates that a feature
or abstraction is unnecessary, ALF should become simpler rather than retaining
it merely because it was previously planned.

---

# Development workflow

Development should proceed deliberately.

Before changing code:

1. Understand the requested change fully.
2. Consider the complete approach before proposing code.
3. Inspect the relevant existing code.
4. Use focused inspection such as `sed` output where appropriate.
5. Identify an exact insertion point or provide a complete replacement
   function.
6. Make one coherent change at a time.
7. Allow the result to be tested before proposing cascading changes.

After a coherent change:

1. Run the relevant focused tests.
2. Run Ruff.
3. Inspect `git diff`.
4. Run `git diff --check`.
5. Check `git status`.
6. Run the full test suite before a clean checkpoint.
7. Commit meaningful, coherent changes.

Do not knowingly commit failing tests or Ruff errors.

When Peter supplies command output, it should be treated as authoritative
evidence of the current repository state.

A clean committed checkpoint should be treated as a stable base. Avoid
unnecessary changes to stable code merely for the sake of activity.

Peter uses Neovim.

Code changes should identify the exact file and function or provide a
complete replacement. Instructions such as "find where this is registered"
should be avoided.

Code snippets should preserve the surrounding indentation so they can be
pasted directly.

Do not produce a large cascade of changes while an earlier change is still
being applied or tested.

---

# Interfaces and future direction

As ALF grows, possible future interfaces include:

* improved terminal interaction;
* interactive shell mode;
* Textual TUI;
* natural-language command interpretation;
* grouped commands for discoverability.

These are possibilities, not commitments.

The CLI should remain a stable foundation.

Future interfaces should consume ALF's existing command and capability
metadata rather than creating parallel descriptions of the system.

Natural-language command interpretation, if introduced, must not undermine the
deterministic command-dispatch model without a deliberate architectural
decision.

---

# Current future considerations

These are ideas that have been discussed but are not current implementation
requirements:

* symbolic mathematics in help examples;
* routing `alf status` to `alf health detail`;
* examining command routing for questions such as:
  "How do I close a terminal window in Ghostty?";
* keeping ALF awake while an SSH connection is established;
* further development of `alf relate`;
* further TUI development;
* deciding whether ALF should run manually or as a user service;
* separating configuration from identity;
* application logging;
* reviewing module responsibilities;
* memory duplicate detection;
* richer memory metadata;
* configurable greeting/personality behaviour.

The roadmap is not a sequence of mandatory tasks.

A simpler or more useful direction may supersede an earlier idea.

---

# ALF personality

The local LLM is intended to act as ALF's mouthpiece.

The intended personality is:

* serious;
* thoughtful;
* friendly;
* useful;
* a study companion;
* an ideas repository;
* with a small sense of soul.

ALF may occasionally offer a related exploration.

For example:

> "On a related subject, shall we look at…?"

Such suggestions must have a clear user-controlled yes/no mechanism.

Personality must remain subordinate to usefulness.

It must never become intrusive, frivolous or distracting.

---

# Long-term vision

ALF is intended to become a long-lived personal computing companion whose
knowledge accumulates over years.

Its memory should preserve not only facts, but decisions, preferences,
reasoning and the evolution of ideas that produced them.

The intelligence layer may change.

The underlying companion should not.

The goal is not to accumulate features for their own sake.

The goal is to develop a coherent, maintainable system whose architecture
remains understandable as its capabilities grow.
