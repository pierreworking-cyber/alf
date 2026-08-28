# ALF — Project Overview

A concise briefing on ALF as it stands today. Part 1 is a human-readable
overview; Part 2 is a technical appendix intended as ChatGPT context for a
future development session.

---

# Part 1 — Human-readable overview

## ALF at a glance

ALF ("Peter's local computing companion") is a long-lived, persistent personal
system whose knowledge, memories and capabilities evolve over time. It is
deliberately not a chatbot: it owns its identity, tools, memory, workflow and
architecture, and treats the local LLM as a bounded, replaceable component.

The governing philosophy is **"the LLM is replaceable. ALF is not."** ALF
should be useful rather than impressive, correct rather than fluent, local and
inspectable, evidence-aware, and deterministic where appropriate. Core
principles: *correctness over speed*, *tools over guesses*, *records over
assumed memories*, *simplicity over unnecessary complexity*.

ALF owns its application core and its persistent SQLite memory. The LLM's role
is limited to interpreting supplied information, classifying questions,
evaluating evidence and composing answers — it is never the owner of
application state or an authoritative source of facts. The three interfaces
(CLI, TUI, web) are all views over the same ALF application layer, not separate
implementations.

## Current capabilities

* System awareness through explicitly permitted, controlled interfaces
  (no unrestricted shell access, no autonomous privilege escalation).
* Git repository awareness (status, recent history).
* Persistent memory in SQLite with permanent memory IDs.
* Memory categories (`note`, `fact`, `decision`, `preference`), memory search,
  and relationships between memories.
* Memory history through a `previous_memory_id` chain; archiving/restore; and
  permanent deletion.
* Question answering and research: evidence gathered from Wikipedia and web
  search, interpreted by the LLM, presented with explicit failure when no
  reliable evidence is found.
* Calculator (`calc`) via sympy.
* Mind maps through the web interface, with connected nodes organised into
  categories (category management, drag-and-drop, save/load).
* Health/self-description (`health`, `about`, `version`), capability and
  command discovery.
* Three interfaces: CLI (primary), an experimental Textual TUI, and a local
  web interface.

Command dispatch is deterministic — unambiguous command prefixes work, but ALF
does not guess commands from natural language.

## How the project is organised

The architecture is a small set of layers over one codebase:

* **Application core** — owns the identity, capability and workflow of ALF,
  plus the deterministic command system.
* **Persistent data layer** — SQLite stores memories and mind maps; the one
  source of truth for state.
* **Command system** — deterministic discovery, resolution and dispatch of
  commands; interfaces consume this same layer.
* **Question/LLM/research pipeline** — a bounded component: route the question,
  interpret it, gather evidence, evaluate evidence, compose an answer.
* **Interfaces** — thin views: CLI, TUI, web.

The important principle: **the interfaces are views over ALF, not separate
implementations of ALF.** Future interfaces should consume ALF's existing
command and capability metadata rather than maintaining their own description
of what ALF does. The LLM is deliberately kept out of the critical deterministic
paths (command dispatch, memory, persistence).

## Current state

* Commit `386ea0b` ("Update project review and documentation"), branch `main`,
  version 0.2.0.
* 315 tests, all passing; clean working tree.
* The architecture is in good shape: coherent, small, testable, and faithful
  to its stated philosophy in `README.md` and `WALL.md`.
* No major refactoring is currently needed. Memory-related code is a candidate
  for gentle decomposition as it grows, but this is not pressing.
* The project is in a good state for continued feature development.

## Current known concerns

These are worth keeping in mind, but none is alarming.

* **WUI exposure** — the web interface has no authentication and binds
  `0.0.0.0:5000`. Acceptable on a trusted local network; an access-control
  mechanism becomes important before it is ever exposed beyond that.
* **LLM-dependent routing/evaluation** — question routing and evidence
  evaluation depend on LLM calls, the least deterministic part of the system.
  The question engine weakens this by returning an explicit failure rather
  than letting the model guess. Worth watching/moving toward more
  deterministic scoring.
* **Accepted mind-map leftovers** — a `status` column that is effectively
  constant, legacy `NULL` category positions, and a removed archive feature
  remain in the schema/model. Deliberately accepted.
* **Watch items** — the TUI remains experimental; there is no JavaScript test
  harness; one cosmetic ruff import-sort finding exists in `web/__init__.py`.

Distinguish: **actual current risks** (only the unauthenticated, broadly-bound
WUI rises to that level, and only off a trusted network); **accepted
limitations** (mind-map schema leftovers, LLM in classification paths,
experimental TUI); **things worth watching** (routing determinism, JS test
coverage, memory module size).

## Current direction / next work

No specific next feature is currently decided. The sensible place to continue
from is the area already flagged as "to watch":

* Access control for the web interface (or documenting/hardening that it is
  localhost-only).
* Reducing the routing/evidence-evaluation dependence on the LLM toward
  deterministic, measurable scoring.
* A JavaScript test harness for the web front-ends; modestly better TUI/web
  parity.
* Gentle decomposition of the large memory module as functionality grows.

These are sensible directions grounded in the current repository, not a
committed roadmap.

---

# Part 2 — Technical appendix — ChatGPT context

## Repository

* Path: `/var/home/peter/Projects/alf` (git, branch `main`).
* HEAD: `386ea0b` — "Update project review and documentation"; tag `v0.2.0`.
* Package `alf` version `0.2.0`; requires Python `>=3.11` (venv interpreter is
  Python 3.14; ruff targets py311). Entry point: `alf = "alf.main:main"`.
* Runtime dependencies (`pyproject.toml`): `rich`, `sympy`, `flask`, `textual`,
  `waitress`.
* Tests: pytest, run via `.venv/bin/python -m pytest`. 315 tests, all passing.
* Lint: ruff (`E, F, I, UP`, line-length 88) — available system-wide as
  `/usr/bin/ruff`, not installed in the venv. The only current finding is a
  cosmetic, deliberately accepted `I001` in `src/alf/web/__init__.py`.
* No package-manager/extras beyond the above.

## Architecture

Key modules in `src/alf/` and their responsibilities:

* `main.py` — CLI entry point.
* `commands.py` — deterministic application commands (the layer interfaces
  consume).
* `command_catalogue.py` — command registry/metadata/help/discovery.
* `command_resolution.py` — deterministic, unambiguous command resolution; no
  natural-language guessing.
* `memory.py` — SQLite persistence and memory operations; owns the schema
  (memories, FTS, mind-map tables). The largest module; a decomposition
  candidate, not urgent.
* `question.py` — end-to-end question pipeline coordinator: route → interpret
  → research → evaluate → answer, with explicit failure on weak evidence.
* `router.py` / `routes.py` / `classifier.py` — `router` is a thin boundary
  over `classify` (LLM-based route decision); `Route` enum in `routes.py`.
* `interpretation.py` — LLM extraction of research terms/intent from a
  question.
* `research.py` — evidence retrieval: Wikipedia API first, then web search.
* `answer.py` — LLM answer composition from evidence and relevant memories.
* `llm.py` — the Ollama boundary (see LLM/research below).
* `system.py`, `git.py`, `status.py`, `time.py`, `capabilities.py`,
  `healthcheck.py` — deterministic environment/capability facts.
* `calc.py` — sympy-powered calculator.
* `presentation.py` — `rich`-based CLI output formatting.
* `paths.py` — data directory resolution.
* `identity.toml` — packaged identity metadata.
* `tui.py` — Textual TUI (Question, Remember, Memories, Calc workspaces).
* `web/__init__.py` — Flask application and serve entry (waitress); workspaces
  Question, Remember, Memories, Calc, Mind Maps.
* Mind-map web assets — `web/static/mindmaps.js`, `mindmaps.css`, and bundled
  `jsmind/` (vendored jsMind library).

## Data

* SQLite database: `~/.local/share/alf/alf.db` (from `paths.get_data_directory`);
  never stored in version control.
* Schema version: `PRAGMA user_version = 6` (`memory.SCHEMA_VERSION`).
* Tables:
  * `memories(id, created, category, content, status='active',
    previous_memory_id, related_memory_ids)`
  * `memory_fts` — FTS5 full-text index over `memories.content`.
  * `mindmap_categories(id, name UNIQUE, status='active', created, modified,
    position)` — `position` may be `NULL` (legacy); `status` is effectively
    constant.
  * `mindmaps(id, category_id FK→CATEGORIES ON DELETE CASCADE, name, status,
    created, modified)`
  * `mindmap_documents(mindmap_id PK, content)` — jsMind JSON document content;
    no separate documents/relations table despite the name.
* Memory model: permanent IDs; history via `previous_memory_id`; relationships
  via `related_memory_ids` (comma-separated). Archiving changes status; editing
  in place is allowed and does not create a revision — creating a new memory
  with a `previous_memory_id` reference is the evolution mechanism. Deletion is
  permanent row removal; existing references are not rewritten and lookups
  ignore missing records. `foreign_keys=ON` is always enabled.

## Interfaces

* **CLI** — `alf [command]`; primary and reference interface.
* **TUI** — `alf tui`; experimental Textual interface with Question, Remember,
  Memories and Calc workspaces.
* **WUI** — `alf web`; Flask served by waitress on `0.0.0.0:5000` (threads=4);
  no authentication.
* All three call the same application/command layer — no interface implements
  its own application logic.

## LLM/research

* Ollama at `http://127.0.0.1:11434`; endpoints `/api/generate` and
  `/api/tags`.
* Configured model: `qwen3:8b` (`llm.OLLAMA_MODEL`).
* Timeouts: generate 60s; availability check 2s; research fetches 10s.
* Research: Wikipedia API first; web search as fallback; results are candidates
  the LLM evaluates.
* The LLM is responsible for: question interpretation, route classification,
  evaluation/scoring of evidence candidates, and answer composition. It is not
  responsible for: application state, memory truth, command dispatch, or acting
  as a factual authority.

## Testing

* 315 passing tests. Areas covered: memory/persistence, command dispatch and
  resolution, question engine and CLI error paths, router/classifier (mocked),
  interpretation, answer, llm/research, calc, presentation, healthcheck,
  identity, TUI, and web routes.
* No JavaScript test harness. Validate front-end JS with
  `node --check src/alf/web/static/mindmaps.js`.
* Standard validation: `.venv/bin/python -m pytest -q`, `ruff check .`,
  `node --check src/alf/web/static/mindmaps.js`, `git diff --check`.

## Important design decisions

Violating any of these would be a regression:

* **Correctness over speed; tools over guesses; records over assumed
  memories; simplicity.**
* **Deterministic command resolution** — unambiguous prefixes, no
  natural-language guessing in dispatch.
* **Deterministic, inspectable persistent state** — SQLite is the single
  source of truth; memory operations are explicit and permanent.
* **LLM is replaceable and bounded** — it interprets/classifies/evaluates/
  composes only; ALF owns all state and behaviour.
* **Interfaces are views over the same ALF** — no separate application logic
  per interface; future interfaces reuse command/capability metadata.
* **No unnecessary abstraction** — small, understandable, thoroughly tested
  modules.
* **Safety doctrine** — only explicitly permitted system interfaces; never
  autonomous privilege escalation (no `sudo`), no implying actions that did not
  happen.

## Known accepted leftovers

* WUI: unauthenticated, bound `0.0.0.0:5000` — acceptable on trusted local
  networks only.
* LLM dependence in question routing and evidence evaluation; mitigated by
  explicit failure rather than guessing.
* Mind-map schema/model: constant `status` column, legacy `NULL` positions,
  retained older migration path, removed archive feature.
* Cosmetic ruff `I001` in `web/__init__.py`.
* TUI experimental; no JS test harness; `memory.py` is large (decomposition
  candidate).