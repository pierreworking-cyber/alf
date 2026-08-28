# ALF Position Audit — 29 Aug 2026

This is a fresh, independent audit of the ALF project at commit `b3d0efa`
("Improve mind map categories and web error handling"), replacing all earlier
review documents. The repository, not this document or any prior review, is the
source of truth. Claims below were verified against the working tree, the tests,
and git history at the time of writing.

**Status of this audit:** documentation only. No application code was changed
as part of producing it. Historical review content has been superseded; it is
not carried forward as authority.

---

## Post-audit amendments

The audit above records the position of the repository as it stood at commit
`b3d0efa`. Since the audit was completed, two of its documentation/cleanup
findings have since been deliberately addressed. The historical statements in
§§1–16 remain an accurate snapshot of the repository **at audit time** and
should be read as such rather than as a claim about the current working tree.

The post-audit changes were documentation/cleanup only and did not alter
application behaviour:

* `README.md` and `WALL.md` now recognise Mind Maps as an implemented ALF
  capability provided through the web interface (previously absent from the
  README and implied to be hypothetical in the WALL).
* The obsolete `.mindmap-archive` CSS rule was removed from
  `src/alf/web/static/mindmaps.css`.

---

## 1. Executive position

ALF is a small, coherent, genuinely architectural system: a deterministic
application core owned by ALF itself, with the local LLM confined to
interpretation, classification and answer composition, and three interfaces
(CLI, Textual TUI, web) drafted as specialised views over the same application
layer. This matches the stated philosophy in `README.md` and `WALL.md` closely.

The repository is clean at `b3d0efa`, the last several commits were focused
improvements to the mind-map workspace and its web API, and the full test suite
is 315 tests, all passing. There are no TODO/FIXME markers. The architecture is
coherent enough that new features can be added without a redesign; the main
risks are procedural rather than structural: a WUI that binds to all
interfaces with no authentication, mind-map state that carries a few accepted
formatting/status leftovers, and drifting documentation (mind maps are absent
from `README.md` while present in the web interface).

**Most important risks, in order:**
1. The web interface binds `0.0.0.0:5000` with no authentication and exposes
   read/write/delete operations over memory and mind maps.
2. Both question routing (`classifier.py`) and research evaluation depend on an
   external local LLM service for correctness; behaviour when the model is
   unavailable or misbehaves is still only partially covered by tests.
3. Mind-map data carries several deliberate, accepted schema leftovers
   (constant `status`, unconstrained `position`) that could confuse a future
   maintainer without continuing documentation.
4. Documentation drift: the README does not mention mind maps, and the web
   homepage advertises "Mind Maps" as a capability while the capability
   registry (`discover_capabilities()`) does not.

**Does major refactoring need to happen before new features? No.** The
`memory.py` module is large (1833 lines) but internally consistent; splitting
it is optional hygiene, not a prerequisite.

---

## 2. Current repository state

**Facts (verified):**
- Working tree is clean.
- HEAD: `b3d0efa "Improve mind map categories and web error handling"`.
- Previous meaningful commit: `27b9dd6 "Fix packaging, mindmap handling, and
  review findings"`.
- Branch: `main`. Also present: `routing-torture` (experimental routing
  exploration). Tag: `v0.2.0`.
- Package `alf` 0.2.0, `requires-python >= 3.11` in `pyproject.toml`.
- Dependencies: `rich`, `sympy`, `flask`, `textual`, `waitress`.
- Entry point: `alf = "alf.main:main"`.
- Ruff selects E, F, I, UP; line length 88.
- Data directory: `~/.local/share/alf/` (SQLite `alf.db`, user-owned
  `identity.toml`).
- `pytest --collect-only`: 315 tests; full suite passes.

**git history sequence (mind-map workspace evolution):**
persistent saving → save notification → separation of CSS/JS → canvas
improvements → drag-to-delete → category management → library controls →
removal of debug logging → packaging fixes → category/API hardening.

---

## 3. Architecture

**Layered boundary (facts):**
- `src/alf/memory.py` is the persistent data layer (SQLite) covering both
  memories and mind maps, with FTS5 for memory search.
- Application modules sit above it: `commands.py` (dispatch), `command_catalogue.py`
  (declarative metadata), `command_resolution.py` (deterministic resolution),
  `status.py`, `identity.py`, `system.py`, `git.py`, `calc.py` (SymPy sandbox),
  `healthcheck.py`.
- Question pipeline: `question.py` → `router.py` → `classifier.py`; evidence
  stages in `research.py`, `interpretation.py`, `answer.py`, `llm.py`.
- Interfaces: CLI (`main.py`/`commands.py`), TUI (`tui.py`), web
  (`web/__init__.py` + templates + JS). Each delegates application logic to the
  shared modules rather than duplicating it.

**Deterministic dispatch (facts):**
- `resolve_command` accepts exact names and unambiguous leading prefixes,
  case-insensitive; ambiguous or unknown values are rejected, never guessed.
- Options and memory categories resolve the same way (`resolve_option`,
  `resolve_category`, including singular forms).
- `main.py` reports ambiguous prefixes explicitly; a bare `alf` invocation shows
  greeting + status.

**Routing (facts + assessment):**
- `Route` enum: system, memory, research, llm, decline.
- `classifier.py` asks the local LLM to pick exactly one of the five fixed
  categories, using examples; the result is converted to `Route`, and an
  unrecognised answer raises `ValueError`.
- `question.py` answers LLM/SYSTEM/MEMORY/DECLINE directly and routes RESEARCH
  through Wikipedia → web → explicit failure ("I don't want to guess").
- **Assessment:** this is LLM-*assisted* routing over a fixed, closed category
  set owned by ALF, with deterministic conversion afterwards. `WALL.md` §11
  explicitly permits LLM classification "as a component of ALF". The reserved
  concern from earlier review (LLM could manufacture a category) is mitigated:
  the output space is fixed and unknown output raises rather than guessing. The
  `routing-torture` branch exists to exercise this area; routing remains a
  legitimate ongoing attention item, not a finding.

**Recommendation (near-term):** when the model is down, `alf question` and the
web question page surface a failure; that is acceptable. No change required
now. Keep watching routing because it is the only place the LLM influences which
capability runs.

---

## 4. Core application (CLI, commands)

**Facts:**
- 17 commands in the catalogue; each has `id`, `help`, `usage`; handlers are
  verified against the catalogue by `healthcheck.check_command_integrity`.
- Handlers: help, calc, remember, memories, categories, memory, relate,
  history, health, about, archive, delete, version, search, question, tui, web.
- `health_command` supports `--details`; `about_command` supports `--details`.
- `calc` re-implements option parsing (symbolic/places/degrees/radians) with
  explicit structure errors; SymPy parser is constrained to an explicit
  vocabulary (`LOCAL_DICT`, `_validate_functions`) — a deliberate sandbox.
- Memory selection (`archive`/`delete`) supports `id`, commas, and inclusive
  ranges via `interpret_memory_selection`.

**Assessment:** solid, small, deterministic. `calc`'s manual flag parsing is a
little verbose but matches the "no guessing" constraint. The CLI remains the
reference implementation as required by `WALL.md` §5.

---

## 5. Memory data layer

**Facts:**
- `memories` table + FTS5 external-content index; `SCHEMA_VERSION = 6`.
- Lifecycle: create (`remember`), in-place edit (`update_memory`, rebuilding
  FTS), archive/restore, permanent delete (repairing FTS, leaving
  `previous_memory_id`/relationship references to silently resolve to
  nothing — documented and deliberate).
- Relationships are directional, one-level, additive, deduplicated; validated
  against existence.
- History is a `previous_memory_id` chain walked by `get_memory_history`.
- Relevance search (`find_relevant_memories`) is term-overlap scoring against
  active memories with a stop-word list; candidate surfacing for the TUI uses
  the similar `find_related_memory_candidates`.
- `get_memory_information()` feeds `alf status`.

**Assessment:** matches README/WALL claims precisely. The FTS-per-term loop is
fine at this scale. Archive/restore is intact for *memories* (TUI and web both
use it); the earlier removal of the lifecycle from *mind maps* was intentional
and is now documented in the memory-layer docstrings and tests.

---

## 6. Mind maps

**Facts:**
- Tables `mindmap_categories` (name UNIQUE, status, created, modified,
  position), `mindmaps` (FK → category, ON DELETE CASCADE), `mindmap_documents`
  (1:1 content JSON). FTS is not used for mind maps.
- Reserved `Uncategorised` category is always placed at position 0
  (`_create_uncategorised` shifts existing categories up).
- `create_mindmap_category` returns `"duplicate"` on name collision (web → 409);
  allows lazy creation of `Uncategorised`.
- `update_mindmap_category` now guards the reserved row itself (returns
  `False`), returns `"duplicate"` when renaming *to* the reserved name or an
  existing name, otherwise renames.
- `delete_mindmap_category` moves its maps to `Uncategorised` (creating it if
  needed), refuses to delete the reserved row, and **renumbers remaining
  positions sequentially 0..n-1** (position-hole fix; verified by tests).
- `move_mindmap_category` moves a block; returns `True` early for the
  `Uncategorised` row and for no-change (see Open issues).
- Save route now distinguishes `404 Mind map not found` (bad id) from
  `404 Mind map category not found` (bad category on update); create path
  lazily creates the category.
- Web PATCH and DELETE routes first guard `_is_uncategorised_category` →
  `400 {"error": "Uncategorised cannot be modified"}` — the API's observable
  behaviour. (An earlier review expected 404 here; the actual guard is the 400,
  and the tests were corrected to match production behaviour.)

**Assessment:** the category lifecycle is now coherent and well-tested:
duplicates 409, reserved category immutable, missing rows 404, delete compacts
positions, delete moves maps to `Uncategorised`. The reserved "Uncategorised"
move no-op returning 200 is the only soft spot (see Open issues).

---

## 7. Web / WUI

**Facts:**
- Flask app in `web/__init__.py`; served by waitress on `0.0.0.0:5000`,
  threads=4, **no authentication** (accepted residual).
- Workspaces: question, remember, memories (view/edit/archive/restore/delete),
  calc, mind maps. Homepage links all five.
- Mind-map workspace is HTML + `mindmaps.js` + `mindmaps.css` + vendored
  `jsmind` assets; drag-and-drop for category reordering and map moves, canvas
  pan (incl. touch), per-category collapse persisted via `localStorage`,
  in-page menu (rename/delete) for categories, prompt-based rename, drag-to-bin
  delete, and node editing via the jsmind widget.
- All 8 `fetch()` calls now have uniform error handling:
  - save, move-map, move-category already reported errors;
  - b3d0efa added error handling for the previously silent create-category,
    delete-map, rename-category, delete-category and open-map calls
    (`try/catch` → notification, `!response.ok` → `readErrorMessage` →
    notification). `node --check` passes.
- `showNotification` auto-dismisses success messages and persists error
  messages with an `.error` style.

**Assessment:** the WUI is the most active interface and is in good shape.
Residual issues are documented in section 14. The lack of auth is the single
largest real-world risk and is a known, accepted choice (local companion on the
owner's machine), but it should stay on the watch list.

---

## 8. TUI

**Facts:**
- Textual `ALFTUI` with Question, Calc, Remember, Memories workspaces; nav
  driven by `command_catalogue` TUI metadata.
- Question runs via a threaded worker with progress callbacks and a source
  line. Calc mirrors CLI semantics. Remember surfaces related-memory candidates
  (debounced). Memories supports list, detail, edit in place, archive/restore,
  delete, and an "Show archived" toggle.
- Test coverage is light (3 tests in `test_tui.py`) consistent with its
  "experimental" status.

**Assessment:** consistent with the "interfaces are specialised views" rule; it
consumes the shared application layer and catalogue rather than duplicating
logic. Fine to leave experimental.

---

## 9. LLM / Question / Research

**Facts:**
- `llm.py` is the only boundary to Ollama (`http://127.0.0.1:11434`,
  model `qwen3:8b`). Timeout is 60s for generation (increased from 10s in this
  workstream), 2s for the health/tags check.
- Personality is defined in `personality.py` and injected into answer prompts;
  evidence-usage instructions tell the model not to guess and not to claim the
  evidence contains what it does not.
- `interpretation.py` refines questions for research without adding facts.
- `research.py` wraps Wikipedia and SearXNG (`127.0.0.1:8080`), trimming text
  to ~1500 chars.
- Evidence evaluation is LLM-judged (`evaluate_research`); only candidates judged
  relevant are handed to answer composition, and ALF returns an explicit
  "couldn't find reliable research" failure rather than guessing.

**Assessment:** the "evidence-aware, LLM-as-interpreter" doctrine is well
executed. The LLM decides relevance of research and picks a routing category,
which is allowed by WALL but is the correct place to remain alert (see §3). The
60s timeout change is now in committed tests.

---

## 10. Testing

**Facts:**
- 19 test modules, ~5,950 lines.
- Largest: `test_memory.py` (2013), `test_command_dispatch.py` (1082),
  `test_question.py` (481), `test_web.py` (466), `test_commands.py`/`test_llm.py`
  (370 each).
- Mind maps: 28 mind-map test functions in `test_memory.py` plus the full
  black-box web API suite in `test_web.py` (create/duplicate/rename/delete/move/
  save/get, reserved-category guards, category-created-by-delete, position
  compaction, 404/400/409 status semantics).
- CLI dispatch is heavily tested (`test_command_dispatch.py`); resolution
  (`test_command_resolution.py`, 44 lines) and router (`test_router.py`, 22
  lines) are proven by small focused suites.
- Model-dependent behaviour is stubbed via monkeypatch (`test_llm.py`,
  `test_question.py`, `test_interpretation.py`, `test_classifier.py`);
  `test_research.py` exercises the parsing logic offline.
- No JavaScript test harness. Verification is `node --check` only (accepted
  residual).
- The full suite runs quickly (`--collect-only` in ~0.4s; execution is fast).

**Assessment:** strong for the size of the project. The black-box WUI API
coverage is the notable improvement this workstream. Prior steps — a removed
stale test (`status` no longer exposed via API) and a corrected test — kept the
suite aligned with actual behaviour.

---

## 11. Runtime / configuration / deployment

**Facts:**
- Installable Python package (setuptools) with `package-data` including
  `identity.toml`, web templates/static, and jsmind assets.
- First run copies the packaged `identity.toml` into the data directory; the
  user-owned copy is never overwritten.
- `.gitignore` excludes `.venv/`, databases, runtime data, `docs/`, local
  SearXNG config, benchmarks.
- `health` reviews module import integrity, command integrity, and Ollama
  availability; `about --details` lists capabilities.

**Assessment:** packaging was fixed in `27b9dd6` and is now consistent with the
runtime layout. The `docs/` ignore entry is a holdover from a previous
convention and could be reconsidered (see Open issues), but nothing currently
depends on it.

---

## 12. Documentation

**Facts:**
- `README.md`: philosophy, capabilities, commands, memory semantics, evidence
  doctrine, data storage, safety, interfaces, limitations, status. It is
  accurate for everything it covers — with one exception:
  **mind maps are not mentioned** (no capability line, no command, no interface
  note), even though the web interface ships them and the homepage links them.
- `WALL.md` (556 lines): architectural principles record, including the
  mind-map/spatial-interaction section (§7) and routing doctrine (§12/§11).
- Docstrings are consistently maintained (memory-layer docs describe category
  lifecycle, reserved category, and position compaction).

**Recommendation (near-term):** add a brief mind-map entry to the README
(interface list and/or a short capability description) so the living doc
matches the shipped interface.

---

## 13. Technical debt / accepted leftovers

The following are **known, deliberate, or otherwise accepted**. They are not
being re-opened unless a concrete reason appears; they are recorded so a future
maintainer can judge them quickly.

1. `mindmap_categories.status` is always `"active"`; categories have no
   lifecycle (F2 decision). No schema migration; the column remains for
   historical compatibility. Documented in `update_mindmap_category`.
2. Legacy rows from before version 5 could carry `NULL` positions; the v5
   migration backfills all existing rows, and every current write path assigns a
   position, but the column has no `NOT NULL`/`UNIQUE` constraint. Compaction
   renumbers on delete only.
3. Mind-map `status`/`archive` functionality was removed; moves are retained.
   Memories' archive/restore is untouched and intact in TUI + web.
4. Moving the reserved `Uncategorised` category returns HTTP 200
   ("moved": True) — a silent no-op at the API boundary (the move itself is
   refused internally). This is the softest remaining edge.
5. `.mindmap-archive` orphan CSS rule at `mindmaps.css:230` (dead selector).
6. No JS test harness; `node --check` only.
7. WUI binds `0.0.0.0`, no auth.
8. `ruff check` reports a pre-existing `I001` (import ordering) in
   `web/__init__.py`.
9. `memory.py` is large (1833 lines) and mixes memory + mind-map persistence;
   coherent, so splitting is optional hygiene.
10. `docs/` in `.gitignore` is a stale entry; harmless unless documentation
    directories are planned under that name.

---

## 14. Open issues (assessment as of this audit)

| Area | Position |
| --- | --- |
| Uncategorised move → 200 no-op | Accepted; note for possible future "no-op/204" refinement. |
| README lacks mind maps | Actionable, near-term doc fix. |
| Homepage advertises "Mind Maps" capability but capability registry doesn't | Cosmetic; consistent with "interfaces are views", but the two self-descriptions disagree. |
| WUI auth | Accepted residual; revisit only if usage assumptions change. |
| LLM-dependent routing | Monitored; fixed category set + deterministic conversion; covered by stubbed tests. |
| `.mindmap-archive` dead CSS | Trivial clean-up, low priority. |
| `memory.py` size | No action now. |
| `price`/`position` invariants not enforced by schema | No action; covered by code paths + tests. |

---

## 15. Recommended priorities

**Immediate (next work):**
- README mind-map mention (one paragraph).
- Optionally remove the dead `.mindmap-archive` CSS rule while touching the
  stylesheet.

**Near-term:**
- Decide explicitly whether the WUI stays unauthenticated and record that
  decision somewhere durable (README or WALL) so it is not re-litigated per
  review.
- Add a short note to `WALL.md` (or the schema/_migration docstrings) recording
  the accepted mind-map status/quantity leftovers, so they remain decisions
  rather than secrets.
- Consider aligning homepage capability cards with `discover_capabilities()`
  or explicitly labelling Mind Maps as an experimental web-only workspace.

**Later:**
- Reconsider routing/relevance evaluation once real usage data exists
  (`routing-torture` branch is the natural home).
- If the web interface stays unauthenticated, at minimum confirm it is
  firewalled to localhost or the LAN is trusted.

**Deliberately leave alone for now:**
- Memory archive/restore semantics, FTS approach, `calc` sandbox, TUI
  experimental status, `memory.py` single-module layout, `status`/historical
  columns in the mind-map schema.

---

## 16. Overall assessment

- **Architecture coherent?** Yes. The "ALF owns the application" model is
  consistently applied: one memory layer, one command catalogue, deterministic
  dispatch, interfaces as views, LLM as a bounded component. Code, WALL, and
  README agree on the substance.
- **Healthy?** Yes. Clean tree, 315 passing tests, no TODOs, coherent
  history, steady focused evolution.
- **Most important risks:** WUI exposure without auth; LLM dependence for
  routing/evaluation; documentation drift on the mind-map interface. None block
  further feature work.
- **Next steps / refactoring:** no major refactoring warranted. Small doc
  alignment and the near-term items in §15 are the appropriate next work.
- **Realistic ceiling:** this codebase can absorb considerably more capability
  without a structural change, provided the "interfaces are views" and
  "deterministic for persistent state" rules continue to be respected.

---

*Verified during this audit: `git status` clean; `pytest` collects 315 tests;
`node --check src/alf/web/static/mindmaps.js` passes; `git diff --check` clean.
No application code was modified to produce this document.*