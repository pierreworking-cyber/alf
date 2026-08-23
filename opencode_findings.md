# ALF project review — findings

Reviewed 2026-08-23 against commit d4206ed ("Update project documentation").

Overall state: **healthy core, with drift accumulating at the edges.** The CLI
layer is well tested (234 tests pass), Ruff is clean, `git diff --check` is
clean, and the deterministic dispatch/memory core matches WALL.md closely.
The verified problems cluster in three areas: front-end parity (web/TUI
validation and presentation differ from the CLI), a broken retained benchmark,
and documentation drift around the question router and model qualification.
No changes were made to the project; every "verified" item below was
reproduced by execution against an isolated `HOME`
(`/tmp/opencode/...`), never against Peter's live data.

---

## 1. Bugs (verified by execution)

### 1.1 Missing `identity.toml` crashes ALF on startup, `version` and `about`

- Files: `src/alf/identity.py:27-30` (`get_identity`), called from
  `src/alf/main.py:29` (`show_status` → `get_status_information`),
  `commands.version_command`, `commands.about_command`, and
  `research.fetch`.
- Nothing creates or bootstraps `~/.local/share/alf/identity.toml`. On a
  fresh install, `alf` (default intro), `alf version` and `alf about` die
  with an unhandled traceback:

  ```
  FileNotFoundError: [Errno 2] No such file or directory:
      '.../.local/share/alf/identity.toml'
  ```

  while `alf memories` and `alf health` work. Verified by running the
  installed entry point with a clean `HOME`. Any command needing external
  research will also fail, because `research.fetch()` builds its User-Agent
  from `get_identity()`.
- Why it matters: the documented setup path (README §Running ALF) does not
  mention `identity.toml` at all, so a fresh environment is broken out of the
  box with a raw Python traceback — contrary to ALF's presentation rules.
- Repro: `HOME=$(mktemp -d) alf`

### 1.2 Non-interactive use crashes with `EOFError` after "Improper command structure"

- Files: `src/alf/presentation.py:86-91` (`pause`) and
  `presentation.py:94-108` (`render_command_structure_error`).
- Every structural command error prints "Press Return to continue..." and
  calls `input()`. When stdin is closed (piped output, scripts, cron),
  `input()` raises `EOFError` and ALF exits 1 with a full traceback after
  already printing the friendly error. Verified:

  ```
  $ alf calc -5 + 3 </dev/null
  ✗ Improper command structure.
  ...
  Press Return to continue...
  Traceback ... EOFError: EOF when reading a line   (exit=1)
  ```

- Why it matters: ALF becomes unusable in any non-TTY context, and the
  traceback contradicts the "never expose Python implementation details"
  presentation rule. A CLI error prompt that waits for Return is itself
  questionable UX for a non-interactive-first tool.
- Repro: `alf search -c preference Peter </dev/null`

### 1.3 Web `/remember` accepts arbitrary categories and stores them

- File: `src/alf/web/__init__.py:68-102` (`remember_memory`).
- The CLI validates categories through `resolve_category()`
  (`commands.py:265-273`), but the web route passes
  `request.form.get("category", "note")` straight into `memory.remember()`,
  which performs no category validation. Verified with the Flask test
  client:

  ```
  POST /remember  category="banana"  → 200
  DB now contains: (2, 'banana', 'web validation probe')
  ```

- Amplification: `render_grouped_memories()` (`presentation.py:271-293`)
  only iterates `MEMORY_CATEGORY_PRIORITY`; a memory with a non-standard
  category silently disappears from `alf memories --group category` output.
- Why it matters: interfaces behave differently, invalid data enters the
  persistent store, and grouped views can hide records. This is exactly the
  "front-ends should not contain duplicated application logic" boundary
  eroding — validation lives in the CLI handler, not in the application
  layer shared by all front-ends.
- Repro: `curl -d 'category=banana&content=x' http://127.0.0.1:5000/remember`

### 1.4 CLI `remember` stores empty memories

- File: `src/alf/commands.py:214-290` (`remember_command`); content is
  stripped but never checked for emptiness.
- Verified: `alf remember note ""` succeeds and stores a memory whose
  content is the empty string (renders as a bare `(id: N) …[note][active]`
  line). The web interface rejects empty content
  (`web/__init__.py:82-83`), as does the TUI (`tui.py:945-947`).
- Why it matters: interface-parity violation and permanent junk records
  (deletion is the only remedy).

### 1.5 The retained LLM knowledge-qualification benchmark is broken

- File: `tests/test_llm_knowledge.py:47` calls `llm._generate(...)`;
  `src/alf/llm.py` renamed `_generate` → `generate` in commit 9b6515a
  ("Add system and memory question routing", 2026-08-23) without updating
  this file.
- Verified: `.venv/bin/pytest tests/test_llm_knowledge.py` → all 20 tests
  fail immediately with
  `AttributeError: module 'alf.llm' has no attribute '_generate'`
  (before any Ollama call). The ordinary run masks this because
  `pyproject.toml:33` adds `--ignore=tests/test_llm_knowledge.py`.
- Why it matters: WALL.md ("The qualification corpus and test are retained
  as an explicit model-qualification benchmark") and README ("The
  qualification benchmark is retained for evaluating future models") both
  promise a working benchmark. It cannot currently run at all, so the
  stated gate for adopting future models does not exist in practice.

### 1.6 Calculator rejects any expression starting with `-` (leading unary minus)

- File: `src/alf/commands.py:123-131` (`calc_command`): any argument
  starting with `-` is treated as an option, so the expression can never
  begin with a minus sign. Verified both forms fail:

  ```
  alf calc -5 + 3     → Improper command structure
  alf calc "-5 + 3"   → Improper command structure (single quoted arg)
  ```

  while `alf calc "5 * (-3)"` works. There is no way to evaluate e.g.
  `-sqrt(2)` or a leading negative operand.
- Why it matters: silent capability gap in a core deterministic command;
  the help text gives no hint.

### 1.7 `search` rejects option-before-term ordering (unlike `remember`)

- File: `src/alf/commands.py:351-365` (`search_command`) always treats
  `arguments[0]` as the term, then parses remaining args as options.
- Verified: `alf search Peter --category preference` works, but
  `alf search -c preference Peter` fails with "Improper command structure".
  `remember` explicitly supports both orders (catalogue note: "Options may
  appear before or after the memory text"); `search` does not, and its help
  does not say so.
- Secondary defect exposed by the same repro: the error says
  "See: alf help **memories**" because `parse_memory_query_options()`
  (`commands.py:293-337`) hardcodes `"memories"` in its error rendering
  even when invoked from `search`.

---

## 2. Dead / broken code paths

### 2.1 `capabilities.get_capabilities()` is never called

- File: `src/alf/capabilities.py:56-69`. Defined, documented, and tested by
  nothing; the only consumer path uses `discover_capabilities()`
  (via `identity.get_about_information`). Confirmed by repo-wide grep.
- Harmless, but it advertises a second discovery API that nothing uses —
  candidate for removal or for becoming the single entry point.

### 2.2 Web home page links to a Memories workspace that does not exist

- File: `src/alf/web/templates/home.html:112-116`: the "Memories" card
  links to `href="#"`. There is no `/memories` route in
  `src/alf/web/__init__.py`.
- The card presents a capability ALF's web interface does not have; clicking
  it reloads the home page. Either the workspace is pending (then the card
  should say so) or the card should go.

---

## 3. Consistency issues within the codebase

### 3.1 Question routing is LLM semantic classification, contradicting WALL.md

- Code: `src/alf/router.py:6-9` (`route`) delegates entirely to
  `classifier.classify()` (`classifier.py:32-93`), which prompts the LLM
  with few-shot examples and returns a `Route`.
- WALL.md (authority) says, in *Question and knowledge routing*:
  "Knowledge-source selection should be deterministic and implemented by ALF
  rather than delegated to the LLM… Do not introduce confidence scoring,
  secondary LLM judges, **semantic classification** or similar machinery
  unless simpler routing proves inadequate."
- The implementation is precisely single-judge LLM semantic classification.
  Commit 66dceb5 ("architecture: add LLM-assisted question classification")
  introduced it deliberately, so the code likely reflects the newer intent —
  but WALL.md was never reconciled. One of the two must change; until then
  the architectural authority describes a system that does not exist.
- Related drift: the classifier depends on Ollama being up, so `route()`
  fails whenever the LLM service is down — meaning even memory/system
  questions need the LLM merely to be *routed*. Worth an explicit decision.

### 3.2 Front-ends hardcode the memory-category list

- `src/alf/tui.py:556-566` (TUI `Select`) and
  `src/alf/web/templates/remember.html:99-127` (hardcoded `<option>`s) each
  duplicate `VALID_MEMORY_CATEGORIES` (`memory.py:26-31`) instead of
  consuming `get_memory_categories()` (which exists precisely for this).
- Adding a category in `memory.py` would silently not appear in either
  front-end. This contradicts WALL.md ("Interfaces should consume those
  capabilities rather than maintaining independent registration lists") and
  README ("Future interfaces should consume ALF's existing command and
  capability metadata"). The web *calc* page shows the right pattern: it
  reads examples from `command_catalogue`.

### 3.3 Answer metadata is presented differently in each interface

- Source labels: CLI title-cases raw values (`presentation.py:316-317`) →
  "Source: Llm" (verified; should sensibly be "LLM"); web/TUI print the raw
  value ("Source: llm"), except TUI pre-fills "Local language model".
- The interpreted research question ("Question interpreted as: …") is shown
  only by the CLI (`render_question`); web and TUI receive
  `result.research_question` and discard it. Given WALL.md's emphasis on
  preserving and surfacing the original question, hiding the interpretation
  in two of three interfaces is inconsistent.
- Verified live: research-route answer displayed "Source: Wikipedia" (CLI)
  with an interpretation line; web would show "wikipedia" only.

### 3.4 TUI calculator lacks angle-mode support

- `src/alf/tui.py:791-822` calls `calculate()` without `angle_mode`; there
  is no degrees/radians control. CLI and web both support `--degrees` /
  angle selection. Same expression, different answers depending on
  interface (`sin(90)` = 0.89 rad vs 1.0 deg).

### 3.5 `delete_memories` docstring describes behaviour that was deliberately removed

- File: `src/alf/memory.py:871-875`: "Delete multiple memories while
  **repairing their histories and relationships**."
- The implementation (and `test_delete_memory_leaves_history_and_relationship_references`,
  `test_memory.py:1010+`) deliberately leaves dangling
  `previous_memory_id`/`related_memory_ids`, matching WALL.md §Deletion
  ("Deletion does not rewrite references"). The docstring is a stale relic
  of the pre-WALL deletion design and misleads maintainers.

### 3.6 Memory search ignores the maintained FTS index

- `memory.search_memories()` (`memory.py:391-441`) uses SQL `LIKE`, while
  the `memory_fts` FTS5 table is built, migrated, and kept in sync
  (insert/update/delete hooks) and used by the question engine
  (`find_relevant_memories`). Not a bug, but the user-facing `alf search`
  gets substring scanning while the expensive index serves only internal
  candidates — worth either using FTS in `search` or documenting why not.

---

## 4. Documentation vs code

### 4.1 README implies the *configured* model failed qualification; WALL says otherwise

- README:163-167: "The configured local Qwen model was deliberately tested
  against a factual knowledge qualification benchmark and was rejected…"
- WALL.md:120-127 (more specific, and consistent with history/benchmarks):
  **Qwen 3:4b** was tested and rejected; "ALF currently configures
  qwen3:8b. The current model has not yet been independently qualified."
  Code agrees (`llm.py:20`, `OLLAMA_MODEL = "qwen3:8b"`).
- README's wording suggests the running model was rejected, which
  contradicts WALL and understates an open risk (the live model is
  unqualified). README should be corrected to match WALL.

### 4.2 Both documents overstate benchmark readiness

- WALL.md:143-147 and README:167 claim the qualification corpus/test are
  retained for future models. As shown in 1.5, the retained test cannot
  run (`llm._generate` no longer exists). Documentation describes a safety
  mechanism that is currently inoperative.

### 4.3 `identity.toml` is undocumented despite being a hard requirement

- README §Data storage mentions only `alf.db`. WALK.md §Data boundaries
  lists "identity data" generically. Nothing tells a new machine that
  `~/.local/share/alf/identity.toml` must exist before `alf`, `alf version`
  or `alf about` will start (see 1.1). Either document it or make ALF
  bootstrap/default it.

### 4.4 WALL.md routing doctrine vs implemented router

- Covered in 3.1; listed here because it is fundamentally a
  documentation-vs-code contradiction on an architectural rule, in the
  document designated as authoritative. Also note WALL's own hedge
  ("routing … should remain … deterministic") is what the code violates.

### 4.5 Command catalogue omits short options for `memories`/`search`

- `command_catalogue.py` documents `-c/-a/-g` only for `remember` and
  `-p/--places` for `calc`; `memories`/`search` list only long options even
  though the parser accepts `-a`, `-c`, `-g` (`commands.py:301-329`, verified
  by `tests/test_command_dispatch.py:369-452`). Minor self-description gap in
  the component meant to be the single source of command truth.

### 4.6 `benchmarks/overview.md` contains a demonstrably wrong example

- Line 24-33: claims `alf mem` resolves to `memory`. Verified: `alf mem`
  is ambiguous ("Similar options: alf memories, alf memory") because both
  commands share the prefix. The file is git-ignored local notes (under
  "#Notes") living in `benchmarks/`, describing CLI architecture — stale
  content in a misleading location.

---

## 5. Robustness gaps

### 5.1 Fixed 10 s LLM timeout may truncate legitimate answers

- `llm.generate()` (`llm.py:51`) hardcodes `timeout=10`. Live verification:
  a verbose research answer took ~21 s end-to-end across several calls, each
  individually under 10 s, but a single slow 8B generation (long
  `--verbose` answer, large evidence payload in `evaluate_research`, or a
  cold-loaded model) can exceed 10 s, turning a recoverable slowness into
  "I couldn't get an answer to the question." Static concern informed by
  timing runs, not reproduced as a failure. Consider a longer or
  configurable timeout for generation calls specifically.

### 5.2 `search` terms are interpolated into LIKE patterns unescaped

- `memory.search_memories` (`memory.py:416`): `%` and `_` in the user term
  act as wildcards (`alf search 100%` matches unrelated rows). Cosmetic
  correctness issue only; static analysis.

### 5.3 Broad `except Exception` around the question engine hides root causes

- `commands.question_command` (`commands.py:618-619`),
  `web/__init__.py:54`, `tui.py:731`. Intentional per commit 72e69cb, and
  the right user-facing outcome — but it also swallows genuine programming
  errors (e.g. a `TypeError` in rendering) as "couldn't get an answer",
  with the detail visible only in web (`source = f"Error: {error}"`) and
  TUI, not the CLI. Acceptable trade-off; flagging so it stays a decision
  rather than an accident.

---

## 6. Stale artifacts / housekeeping

### 6.1 Orphaned `__pycache__` bytecode from deleted modules

- `src/alf/__pycache__/` contains compiled bytecode with no corresponding
  source: `diary.cpython-314.pyc` and `help.cpython-314.pyc` (both deleted
  in 9b6515a), `knowledge_router.cpython-314.pyc` (module removed earlier),
  and `web.cpython-314.pyc` (from before `web/` became a package).
- Git-ignored and invisible to `pkgutil` discovery, so harmless — but they
  are ghosts of removed architecture that can confuse greps/inspection of
  the tree. Safe to delete.

### 6.2 Empty ignored directories: `data/`, `docs/`, `logs/`

- All three are empty and git-ignored (`.gitignore:9-12`). They serve no
  current purpose (runtime data correctly lives in `~/.local/share/alf`).
  Harmless; candidates for removal unless intentionally kept as mount
  points.

### 6.3 Benchmark artifacts accumulate untracked in `benchmarks/`

- Ignored results total ~1.7 MB, including `torture_result1.txt` (~586 KB)
  and six near-duplicate `explain_routing_qwen3_8b_*.txt` runs from
  2026-08-16. Ignored, so low priority, but they are one-shot experiment
  output whose conclusions already live in WALL.md.
- Tracked scripts `benchmarks/run_interpreter.py` defaults
  `MODEL = "qwen3:4b"` (env-overridable) — fine for a historical experiment,
  but worth remembering the configured model is now qwen3:8b.

### 6.4 Local SearXNG config contains a secret key

- `.searxng/settings.yml` holds a hardcoded `secret_key`. Correctly
  git-ignored (`.gitignore:15`), so not a repository problem — just ensure
  it never becomes tracked, and note the web-research capability depends on
  this local service being up (`research.py:108`, verified reachable).

### 6.5 Tooling is not fully declared

- `pyproject.toml` declares runtime deps only. `pytest` and `basedpyright`
  are installed in `.venv` but undeclared; `ruff` is **not** in the venv at
  all (this review used system ruff 0.15.21). Not asking for new tooling —
  but the development workflow in WALL.md mandates Ruff, and the project
  venv cannot run it. A minimal dev-dependency declaration would make the
  documented workflow reproducible.

---

## Suggested priority

1. **Fix the retained qualification benchmark** (`tests/test_llm_knowledge.py`:
   `llm._generate` → `llm.generate`) or consciously retire it — WALL.md and
   README both rely on it as the model-adoption gate (1.5, 4.2).
2. **Stop the non-interactive crash**: make `pause()` tolerate closed stdin
   (or drop the interactive pause for CLI errors) (1.2).
3. **Bootstrap or document `identity.toml`**, so a fresh install doesn't
   traceback on `alf`/`version`/`about` (1.1, 4.3).
4. **Move memory validation into the shared layer**: validate category in
   web `/remember`, and reject empty content in the CLI `remember` (1.3, 1.4);
   ideally have web/TUI read categories from `get_memory_categories()` (3.2).
5. **Reconcile WALL.md with the LLM classifier** — update the routing doctrine
   or the code; also decide whether routing should work without Ollama (3.1).
6. **Calculator/search argument handling**: allow leading-negative
   expressions; accept options before the search term; fix the
   "help memories" pointer from `search` errors (1.6, 1.7).
7. Correct README's model-qualification paragraph to match WALL.md (4.1).
8. Small cleanups when convenient: delete orphaned `__pycache__` ghosts,
   fix the `delete_memories` docstring, resolve the dead Memories card,
   unify source-label rendering, remove `capabilities.get_capabilities()`,
   prune old benchmark output.

---

## Overall assessment

ALF's centre of gravity — deterministic dispatch, the SQLite memory layer,
the health/capability introspection, and the evidence-interpretation
pipeline — is coherent, well factored, and well tested, and it matches
WALL.md's philosophy almost everywhere it matters. The drift found here is
typical of rapid recent growth (nine substantive commits in the last two
days): front-end parity rules are asserted but not enforced (categories,
empty content, source labels, calc features), the question router quietly
became LLM-driven while WALL.md still forbids exactly that, and the
retained model-qualification benchmark — the project's stated safeguard for
its most important architectural bet — broke during last night's rename and
nobody noticed because the standard test run excludes it. None of these are
large; all of them are cheap to fix now and expensive to find later.
