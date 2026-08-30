# ALF — Project Overview

A concise briefing on ALF as it stands today. Part 1 is a human-readable
overview; Part 2 is a technical appendix intended as ChatGPT context for a
future development session.

---

# Part 1 — Human-readable overview

## 1. ALF at a glance

ALF ("Peter's local computing companion") is a long-lived, persistent personal
system whose knowledge, memories and capabilities evolve over time. It is
deliberately not a chatbot: it owns its identity, tools, memory, workflow and
architecture, and treats the local LLM as a bounded, replaceable component. The
LLM only classifies questions, interprets supplied information, evaluates
evidence and composes answers — it is never the owner of application state or
an authoritative source of facts. The three interfaces (CLI, TUI, web) are all
views over the same ALF application layer, not separate implementations.

The governing philosophy is **"the LLM is replaceable. ALF is not."** ALF
should be useful rather than impressive, correct rather than fluent, local and
inspectable, evidence-aware, and deterministic where appropriate. Core
principles: *correctness over speed*, *tools over guesses*, *records over
assumed memories*, *simplicity over unnecessary complexity*.

The governing architecture is recorded in `WALL.md` ("the WALL"), a living
architectural document, not a user manual.

## 2. What ALF currently does

* System awareness through explicitly permitted, controlled interfaces (no
  unrestricted shell access, no autonomous privilege escalation, no `sudo`).
* Git repository awareness (status, recent history).
* Persistent memory in SQLite with permanent memory IDs.
* Memory categories (`note`, `fact`, `decision`, `preference`), memory search,
  relationships between memories, history through a `previous_memory_id` chain,
  archiving/restore, and permanent deletion with confirmation.
* Question answering and research: routed questions are answered from general
  knowledge, system facts, or memory, or researched via Wikipedia and SearXNG
  and interpreted by the LLM — with an explicit failure rather than a guess
  when no reliable evidence is found.
* Calculator (`calc`) via sympy.
* Mind maps through the web interface, with connected nodes organised into
  categories (category management, drag-and-drop, save/load).
* Health/self-description (`health`, `about`, `version`), plus capability and
  command discovery.
* Three interfaces: CLI (primary), Textual TUI, and a local web interface.

Command dispatch is deterministic — unambiguous command prefixes work, but ALF
does not guess commands from natural language.

## 3. How the project is organised

The architecture is a small set of layers over one codebase:

* **Application core** — owns identity, capability, workflow and the
  deterministic command system.
* **Persistent data layer** — SQLite stores memories and mind maps; the single
  source of truth for state.
* **Command system** — deterministic discovery, resolution and dispatch;
  interfaces consume this same layer.
* **Question/LLM/research pipeline** — a bounded component: route the question,
  interpret it, gather evidence, evaluate evidence, compose an answer.
* **Interfaces** — thin views: CLI, TUI, web.

The important principle: **the interfaces are views over ALF, not separate
implementations of ALF.** The LLM is kept out of the critical deterministic
paths (command dispatch, memory, persistence).

## 4. Current interfaces

* **CLI** — `alf [command]`; the primary, deterministic, reference interface.
* **Textual TUI** — `alf tui`; Question, Remember, Memories and Calc
  workspaces.
* **Web** — `alf web`; Question, Remember, Memories, Calc and Mind Maps
  workspaces.

The interfaces call the same application layer rather than implementing their
own application logic.

## 5. Current project state

* Commit `5aece93` ("Prevent concurrent TUI questions"), branch `main`,
  version 0.2.0 (no tag at HEAD).
* **330 tests, all passing**; clean working tree.
* The architecture remains coherent (ALF owns the application; interfaces are
  views; the LLM stays out of dispatch/memory/calc).
* The TUI feature-completion programme is finished (see below).
* The next development priority is gentle decomposition of `memory.py`.

## 6. TUI status — feature-complete

The Textual TUI is now considered **feature-complete within its defined
scope** — not perfect, but complete, with **18 behavioural tests** covering
navigation and all four workspaces. It supports its workspaces end to end:

* **Question** — full asynchronous pipeline with success/failure presentation
  via a real worker thread (no UI blocking).
* **Remember** — category + content + related-memory candidates, with empty
  input rejected.
* **Memories** — select, view, edit, archive, restore, and *permanent delete
  behind an explicit confirmation dialog*.
* **Calc** — calculator backed by the same `alf.calc` application layer.

Notable engineering:

* Question handling is genuinely asynchronous (thread worker, progress
  messages, re-armed button after completion);
* a guard prevents **concurrent/double Question submissions** through any entry
  path (including Enter while a question is in flight);
* permanent memory deletion requires an explicit confirmation dialog;
* the TUI delegates to the application layer rather than re-implementing it.

Deferred minor-polish items are **accepted / non-blocking**, not active work:
stale related-memory repopulation after clearing input (S2), stale detail pane
after archive/delete (S3), and long-memory content overflow in the detail pane
(S4). The calculator's `CalculationError` handling (S5) and the absence of
keyboard bindings beyond standard widget input (S6) are acceptable as-is.

## 7. Known concerns / accepted limitations

These are genuine but understood; none blocks the current direction.

* **Web interface exposure** — no authentication, bound to `0.0.0.0:5000`.
  Acceptable on a trusted local network only; must be addressed before any
  wider exposure. This is the closest thing to a real outstanding risk.
* **LLM-dependence in question routing and research evaluation** — the least
  deterministic parts of the system, mitigated by explicit failure rather than
  guessing. Note: `WALL.md`'s Routing Doctrine states routing is deterministic
  and owned by ALF, while the question router currently uses LLM
  classification; this implementation/doctrine tension is acknowledged and
  deliberately left unchanged for now.
* **Mind-map schema leftovers** — an effectively-constant `status` column,
  legacy nullable `position`, and a retained older migration path. Accepted.
* **One cosmetic lint finding** — un-sorted imports in `web/__init__.py`
  (ruff I001), deliberately accepted.
* **No JavaScript test harness** — front-end JS is validated with
  `node --check`.
* **README still calls the TUI "experimental"** — accurate for its age, not a
  functional gap; the label can be reviewed later.

## 8. Next development priority

**Decompose `src/alf/memory.py`**. At 1833 lines it is more than twice the
size of the next-largest module and contains two distinct domains (the memory
system and the web-only mind-map store) held together only by the shared
SQLite connection. The goal is better structure, not a rewrite: extract
domain modules while preserving the existing public API and behaviour, keeping
all 330 tests green.

## 9. Recommended direction for memory.py decomposition

Extract the **mind-map domain** into `src/alf/mind_maps.py`:

* it owns category management and mind-map/document persistence (~660 lines,
  roughly 36% of `memory.py`);
* it is used **exclusively** by the web interface (verified — no CLI, TUI,
  question, or status code touches a mind-map function);
* it has **zero** function-level dependency on the memory domain — it shares
  only the SQLite connection;
* it has its own tables and row shapes (mindmap_categories, mindmaps,
  mindmap_documents) and its own migrations.

The memory domain (memories, FTS, relationships, history, lifecycle, search)
stays in `memory.py`. Detailed boundaries, per-function ownership, dependency
notes, and the ordering constraints (one shared `PRAGMA user_version` ladder)
are in Part 2. A follow-up decomposition of memory relationships/history is a
possible later step, but is not needed for this phase.

---

# Part 2 — Technical appendix for ChatGPT

## Repository

* Path: `/var/home/peter/Projects/alf` (git, branch `main`).
* HEAD: `5aece93` — "Prevent concurrent TUI questions".
* Version: package `0.2.0`; `git describe` = `v0.2.0-137-g5aece93` (137 commits
  since tag v0.2.0; HEAD is not itself tagged). Requires Python `>=3.11`
  (venv interpreter is Python 3.14; ruff targets py311).
* Entry point: `alf = "alf.main:main"`.
* Runtime dependencies (`pyproject.toml`): `rich`, `sympy`, `flask`, `textual`,
  `waitress`.
* Tests: pytest via `.venv/bin/python -m pytest`. **330 tests, all passing.**
* Lint: ruff (`E, F, I, UP`, line-length 88). One finding: I001 (un-sorted
  imports, `src/alf/web/__init__.py`) — cosmetic, deliberately accepted.
* Front-end check: `node --check src/alf/web/static/mindmaps.js` (OK).
* Standard validation: `.venv/bin/python -m pytest -q`, `ruff check .`,
  `node --check src/alf/web/static/mindmaps.js`, `git diff --check`.

## Architecture and module boundaries

Key modules in `src/alf/`:

* `main.py` — CLI entry point.
* `commands.py` — deterministic application commands (the layer interfaces
  consume; includes `tui_command()`, `web_command()`).
* `command_catalogue.py`, `command_resolution.py` — command registry,
  metadata, help, discovery, and deterministic unambiguous resolution (no
  natural-language guessing).
* `memory.py` — SQLite persistence and memory operations; owner of memory
  schema, FTS, relationships, history, lifecycle, and the mind-map tables.
  **The next decomposition target.**
* `question.py` — end-to-end question pipeline coordinator: route → (LLM /
  system / memory / decline) or research (interpret → Wikipedia → evaluate →
  web/SearXNG → evaluate) with explicit failure on weak evidence.
* `router.py` / `routes.py` / `classifier.py` — `router.route()` wraps
  `classifier.classify()`, an **LLM-based** classification into the `Route`
  enum (`classifier.py` calls `llm.generate`). Question dispatch downstream in
  `question.py` is deterministic once classified. (WALL Routing Doctrine
  tension — see Part 1 §7.)
* `interpretation.py` — LLM extraction of a research question from the user's
  question.
* `research.py` — evidence retrieval: Wikipedia API first, then SearXNG web
  search (`http://127.0.0.1:8080/search`), 10s timeout, Wikipedia UA from
  identity.
* `answer.py` — LLM answer composition from evidence and relevant memories.
* `llm.py` — Ollama boundary.
* `system.py`, `git.py`, `status.py`, `time.py`, `capabilities.py`,
  `healthcheck.py` — deterministic environment/capability facts.
* `calc.py` — sympy-powered calculator; normalises bad input to
  `CalculationError`, so the TUI/web only need that single catch.
* `presentation.py` — rich-based CLI output formatting.
* `paths.py` — data directory resolution.
* `identity.toml` — packaged identity metadata.
* `tui.py` — Textual TUI (Question, Remember, Memories, Calc).
* `web/__init__.py` — Flask app served by waitress (Question, Remember,
  Memories, Calc, Mind Maps) + templates/static (incl. vendored jsmind).

## Data / schema

* SQLite database: `~/.local/share/alf/alf.db` (`paths.get_data_directory() /
  "alf.db"`); never in version control.
* Schema version: `PRAGMA user_version = 6` (`memory.SCHEMA_VERSION`).
* Tables:
  * `memories(id, created, category, content, status='active',
    previous_memory_id, related_memory_ids)`
  * `memory_fts` — FTS5 external-content index over `memories.content`
    (`content='memories'`, `content_rowid='id'`), rewritten explicitly by
    remember/update/delete.
  * `mindmap_categories(id, name UNIQUE, status='active', created, modified,
    position)` — `position` may be legacy `NULL`; `status` effectively
    constant. Reserved `Uncategorised` category always at position 0.
  * `mindmaps(id, category_id FK→mindmap_categories ON DELETE CASCADE, name,
    status='active', created, modified)` — `status` is effectively a filter
    (`get_mindmaps` returns status='active'); update accepts a status value.
  * `mindmap_documents(mindmap_id PK, content)` — jsMind JSON content; the
    name predates its current single-document shape.
* Memory model: permanent IDs; history via `previous_memory_id` chain; edit in
  place (no revision); relationships via `related_memory_ids`
  (comma-separated, one level, directional, additive); archiving/restore flip
  `status`; deletion is permanent row removal and references are not rewritten
  (lookups ignore missing rows). `PRAGMA foreign_keys = ON` is always enabled.
* See `README.md` ("Memory", "Current limitations") and `WALL.md` for the full
  doctrine.

## memory.py — responsibilities and decomposition

### Why decomposition is warranted (evidence, not opinion)

At **1833 lines** `memory.py` is the largest module (next: `tui.py` 1259,
`presentation.py` 746, `commands.py` 734). It contains two domains that share
only the SQLite connection:

* the **memory system** — the actual `memories` domain, used by CLI, TUI, web,
  status and the question pipeline;
* the **mind-map store** — categories + maps + documents, used **only** by the
  web interface, with no function-level dependency on any memory function.

The test suite already reflects the seam: `tests/test_memory.py` (127 tests)
contains ~40 mind-map tests and ~85 memory tests, so the extraction is
mechanical and behaviour-preserving.

### Proposed extraction A — `alf/mind_maps.py` (this phase)

* **Responsibility:** persistence and category management for web mind maps
  (jsMind document store + ordered categories).
* **Functions (agents of `memory.py`):** `_create_uncategorised`,
  `create_mindmap_category`, `get_mindmap_categories`, `move_mindmap_category`,
  `update_mindmap_category`, `delete_mindmap_category`, `create_mindmap`,
  `get_mindmap`, `get_mindmaps`, `update_mindmap`, `move_mindmap`,
  `delete_mindmap` (~660 lines, ~36% of `memory.py`).
* **Schema/migrations owned here:** table creation for
  `mindmap_categories` / `mindmaps` / `mindmap_documents`, plus the version-4
  rebuild and version-5 `position` migration logic.
* **Callers:** only `src/alf/web/__init__.py` (11 imports). No CLI/TUI/question/
  status usage (verified by grep).
* **Dependencies:** `get_connection` (+ `DATABASE`), `sqlite3`, `datetime`.
  Zero dependency on memory functions; `_create_uncategorised` stays with the
  mind-map group it serves.
* **API preservation:** yes — `memory.py` re-exports the migrated names
  (`from .mind_maps import ...`), so existing `from alf.memory import
  create_mindmap` sites (web and tests) keep working unchanged. Web may switch
  to direct imports later.
* **Risks / ordering constraints:**
  * **One `PRAGMA user_version` ladder.** `initialise_database` is the single
    authoritative runner (versions <2, 4, 5). The mind-map module must expose a
    schema/migration step that `memory.initialise_database` calls at the
    correct rungs; it must NOT write `user_version` itself. The memory module
    keeps driving the combined version number.
  * Migration behaviour is anchored by `test_database_migrates_mindmaps_from_
    version_four` (and the version-one memory migration test) — keep those
    green.
  * Preserve precise semantics, including: `Uncategorised` stay-at-position-0
    rules, lazy category creation inside `create_mindmap`, delete-into-
    `Uncategorised` behaviour, `get_mindmaps` status filtering, and the
    `"duplicate"`/`False` return values.
  * Optional cleaner variant: introduce `alf/store.py` owning `DATABASE`,
    `get_connection`, and the schema runner, consumed by both `memory.py` and
    `mind_maps.py`. Slightly larger but fixes the dependency direction. Either
    variant is acceptable; the minimal re-export variant is lowest risk.

### What remains in memory.py after extraction A

Connection/schema runners, `VALID_MEMORY_CATEGORIES`, `get_memory_categories`,
`get_memory_query_options`, `validate_related_memory_ids`, `relate_memory`,
`remember`, `update_memory`, `get_memories`, `search_memories`,
`find_related_memory_candidates`, `find_relevant_memories`, `get_memory`,
`get_related_memories`, `get_memory_history`, `archive_memory(s)`,
`restore_memory(s)`, `delete_memory(s)`, `get_memory_information`,
`get_capability` (~1150 lines — a single-domain, defensible size).

### Deferred / other notes

* **Proposed extraction B — memory relationships/history** (later phase if
  `memory.py` keeps growing): `validate_related_memory_ids`, `relate_memory`,
  `get_related_memories`, `get_memory_history` into e.g.
  `memory_relationships.py`, importing `get_memory` from `memory.py`
  (one-directional; keep `memory.py` from importing back at import time).
* **Internal tidy-up (not a split):** the memory-row→dict mapping is
  duplicated in ~7 places; a private `_memory_to_dict` helper is a safe small
  refactor.
* **Search semantics differ by design:** `search_memories` uses `LIKE`
  substring (CLI whole-content search); `find_related_memory_candidates` /
  `find_relevant_memories` use FTS5 term matching (interactive recall and the
  question memory route). Do not unify casually.
* No LLM involvement anywhere in `memory.py` — all recall is deterministic
  term matching. Keep it that way.

## Interfaces

* **CLI** — `alf [command]`; primary, deterministic; `alf question` prompts
  interactively; `alf tui` / `alf web` launch the other interfaces.
* **TUI** — `alf tui`; feature-complete for its scope (Question, Remember,
  Memories, Calc). 18 behavioural tests: navigation (2), Remember (2),
  Memories select/edit/archive/restore (5), Question (3, success, failure,
  double-submit guard — exercising the real thread worker), calc (3), delete
  confirmation (3). Internal note: the Question worker sets `#ask` disabled
  while running; the double-submit guard early-returns in `ask_question()` when
  that button is disabled.
* **Web** — `alf web`; Flask + waitress, `0.0.0.0:5000`, threads=4, **no
  authentication**. Question, Remember (with `/remember/related` candidates),
  Memories (list/archive/restore/delete/edit), Calc, Mind Maps (full category
  + map CRUD, move, drag-and-drop via jsmind, saved-notification).
* All three call the same application layer.

## LLM/research boundary

* Ollama at `http://127.0.0.1:11434` (`/api/generate`, `/api/tags`); model
  `qwen3:8b`; generate timeout 60s, availability check 2s, research fetches 10s.
* Research: Wikipedia API first; SearXNG web search fallback (`127.0.0.1:8080`,
  3 results max); results are candidates the LLM evaluates
  (`llm.evaluate_research`).
* The LLM is responsible for: question interpretation, route classification,
  evidence evaluation/scoring, and answer composition. It is **not**
  responsible for application state, memory truth, command dispatch, or being a
  factual authority.

## Testing structure

330 tests, all passing. Counts by file (largest first): `test_memory.py` 127,
`test_command_dispatch.py` 46, `test_web.py` 29, `test_tui.py` 18,
`test_commands.py` 18, `test_calc.py` 17, `test_presentation.py` 13,
`test_llm.py` 11, `test_command_resolution.py` 9, `test_question.py` 8,
`test_classifier.py` 6, `test_research.py` 6, `test_router.py` 5,
`test_healthcheck.py` 4, `test_interpretation.py` 4,
`test_question_cli_errors.py` 4, `test_answer.py` 3, `test_identity.py` 2.

Notes for safety when refactoring `memory.py`: `tests/test_memory.py` uses a
`database` fixture (temporary DB) and covers migrations, all mind-map
functions, FTS sync (remember/update/delete), relationships, history, search
and lifecycle — treat its 127 tests as the behavioural contract. TUI tests use
patching of the `alf.tui.*` application boundary plus `alf.tui.asyncio.sleep`
no-op; Question worker tests sync via `worker.wait()` after grabbing the worker
by name from `app.workers`.

## Packaging / runtime

* setuptools build backend; package data includes `identity.toml`,
  `web/templates/*`, `web/static/*`, `web/static/jsmind/*`.
* No managed dependency pins; uses system Python packages via the venv.
* `identity.toml`: name ALF, owner Peter, version 0.2.0.

## Accepted design decisions (regarding as non-regressions)

* Deterministic command resolution: unambiguous prefixes only.
* Deterministic, inspectable persistent state: SQLite is the single source of
  truth; memory operations are explicit and permanent.
* LLM is replaceable and bounded; ALF owns all state and behaviour.
* Interfaces are views over the same ALF; no per-interface application logic.
* Explicit failure over guessing (question engine, research).
* No unnecessary abstraction; small, understandable, thoroughly tested modules.
* Safety doctrine: only explicitly permitted system interfaces; never
  autonomous privilege escalation; never imply actions that did not happen.

## Outstanding technical debt

* WUI unauthenticated/broad-bound (real risk only off a trusted network).
* LLM dependence in question routing + research evaluation; WALL Routing
  Doctrine wording vs. `classifier.py` implementation tension (accepted).
* Mind-map schema leftovers (`status`, legacy `NULL` position, v4 migration
  path, `mindmap_documents` name).
* Cosmetic ruff I001 in `web/__init__.py`.
* No JS test harness (use `node --check`).
* TUI deferred polish S2 (stale related-memory repopulation), S3 (stale detail
  pane after archive/delete), S4 (long-memory detail overflow) — accepted,
  non-blocking, not active work.
* `memory.py` size — the next development phase (see Part 1 §8/§9).