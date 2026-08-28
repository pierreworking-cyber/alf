# ALF Code Review

Audit of the ALF codebase with special focus on the mind-map feature (desktop/touch
controls, add/edit/delete nodes, canvas drag, save/notification, load, categories).

Scope decisions: documentation, README, docstrings, comments, LLM code/Ollama
integration, `llm.py`, and prompts were excluded. Every finding below was verified
against the source and, where possible, reproduced with the project's own test suite
or a small script (see "Verification performed").

Severity scale: High = breaks a shipped feature/install for some users; Medium = wrong
behaviour a user will hit; Low = edge case or hygiene.

---

## 1. Confirmed Errors

### 1.1 `alf web` crashes on a fresh install: waitress is not a declared dependency

- **Severity:** High
- **File:** `src/alf/web/__init__.py:34` (import); `pyproject.toml:10-15` (deps); `src/alf.egg-info/requires.txt:1-4`
- **Problem:** `from waitress import serve` imports waitress unconditionally, but `[project] dependencies` only lists rich, sympy, flask, textual, and `requires.txt` mirrors that. waitress (3.0.2) is present in `.venv` only because it was installed manually. `alf web` (commands.py:654-655) → `web.main()` → `serve(...)` (web/__init__.py:528-532).
- **Why it matters:** `pip install .` into a clean environment leaves `alf web` dead on arrival with `ModuleNotFoundError: No module named 'waitress'`.
- **Suggested fix:** add `"waitress"` to `dependencies`, or serve with Flask's built-in/WSGI server and drop the extra dependency.

**Fix applied (finding 1.1 only).** `waitress` was declared as a normal runtime dependency; no other files were changed, and the serving architecture (`web.main()` → waitress `serve(app, host="0.0.0.0", port=5000, threads=4)`) is untouched.

- **Dependency declaration (pyproject.toml:10-16):**
  ```toml
  dependencies = [
      "rich",
      "sympy",
      "flask",
      "textual",
      "waitress",
  ]
  ```
- **Test suite** (`.venv/bin/python -m pytest -q`): 267 passed, 5 failed. 4 failures are the pre-existing finding 1.7 memory-category tests; the 5th (`tests/test_question_cli_errors.py::test_generate_uses_timeout`, timeout 60 vs expected 10) is a pre-existing failure in excluded LLM code (`alf/llm.py`, uncommitted local edits predating this task). None relate to the waitress declaration.
- **Clean-wheel installation:** wheel + sdist built with `python -m build` (isolated setuptools 84.0.0) from a pristine copy of the working tree. Wheel METADATA now carries `Requires-Dist: waitress`. Installing `alf-0.2.0-py3-none-any.whl` into a fresh venv outside the project automatically pulled `waitress-3.0.2` (`Collecting waitress (from alf==0.2.0)`); waitress was **not** installed manually. `pip show alf` → `Requires: flask, rich, sympy, textual, waitress`.
- **`alf web` in the clean environment:** `from alf.web import main` imports cleanly (no `ModuleNotFoundError`). `alf web` runs the full startup path and reaches waitress `serve(...)`; it only stops with `OSError: [Errno 98] Address already in use`, because an existing `alf web` (pipx, pid 44421) already owns :5000 — an environmental port conflict, not a dependency problem. A genuine waitress `create_server`/`run()` from the installed wheel on a free port served HTTP end-to-end: `/static/nonexistent.css` → 404, `/` and `/calc` → 500 `TemplateNotFound` (the separate, unresolved finding 1.2); server then closed cleanly. The 1.1 crash (`ModuleNotFoundError: No module named 'waitress'` on a fresh install) is resolved.

### 1.2 Wheels omit all web templates and static assets

- **Severity:** High (for non-editable installs)
- **File:** `pyproject.toml:20-21`; `src/alf.egg-info/SOURCES.txt:36`
- **Problem:** `[tool.setuptools.package-data]` includes only `identity.toml`. `SOURCES.txt` lists `src/alf/web/__init__.py` but no `web/templates/*` and no `web/static/*` (CSS, JS, and the vendored `static/jsmind/*`). The whole web tree is therefore absent from any built wheel/sdist.
- **Why it matters:** under the current editable install the source tree is used and everything renders (verified: `GET /`, `/calc`, `/mindmaps` all 200). A source-installed wheel deployment would fail with Jinja `TemplateNotFound` and 404s on `/static/...` — the entire web UI breaks.
- **Suggested fix:** `[tool.setuptools.package-data] alf = ["identity.toml", "web/templates/*", "web/static/*", "web/static/jsmind/*"]` (and regenerate egg-info before publishing).

**Fix applied (finding 1.2 only).** Packaging change, setuptools `package-data` in `pyproject.toml:21-27` (was `alf = ["identity.toml"]`):

```toml
[tool.setuptools.package-data]
alf = [
    "identity.toml",
    "web/templates/*",
    "web/static/*",
    "web/static/jsmind/*",
]
```

The three web trees are each flat (6 templates, 3 top-level static files, 3 jsMind files), so covering each directory with one glob includes everything recursively. No application code, routes, or templates were changed; egg-info was regenerated only as an automatic consequence of the normal build.

- **Wheel contents** (`unzip -l alf-0.2.0-py3-none-any.whl`, `alf/web/`): `templates/calc.html home.html memories.html mindmaps.html question.html remember.html`; `static/style.css mindmaps.css mindmaps.js`; `static/jsmind/jsmind.css jsmind.draggable-node.js jsmind.js` — all present alongside `alf/web/__init__.py`. The sdist contains the same files under `src/alf/web/…`.
- **Clean-environment installation:** wheel + sdist built with `python -m build` (isolated setuptools 84.0.0) from a pristine copy of the working tree. The wheel installed into a fresh venv outside the project; `find site-packages/alf/web` confirms `templates/` (6 files), `static/` (3 files), and `static/jsmind/` (3 files) are physically present in the installed package.
- **Web route verification** (installed package's Flask test client, `TESTING=True`; `/mindmaps` DB isolated to a fresh temp DB so no user data was touched):
  - `GET /` → **200**
  - `GET /calc` → **200**
  - `GET /mindmaps` → **200**
  - No `TemplateNotFound` anywhere.
- **Static asset verification** (same installed package): `/static/style.css`→**200** (5649 B), `/static/mindmaps.js`→**200** (19239 B), `/static/jsmind/jsmind.js`→**200** (51084 B), `/static/jsmind/jsmind.css`→**200** (8046 B). No 404s.
- **Test suite** (`.venv/bin/python -m pytest -q`): 267 passed, 5 failed — the same pre-existing failures as before this change (4× finding 1.7 memory-category tests, 1× `test_generate_uses_timeout` in excluded LLM code). No new failures introduced; none were attempted to be fixed.
- **Conclusion:** finding 1.2 is **fixed and verified** — a clean (non-editable) wheel install now ships the full web UI and serves the pages and assets successfully.

### 1.3 Version-4 migration silently skips the v5 position step → `no such column: position`

- **Severity:** High (any database still on schema version 4)
- **File:** `src/alf/memory.py:127` (`version == 4` branch), `memory.py:247` (`version == 5` branch), `memory.py:276` (stamps 6)
- **Problem:** `version` is read once and the branches are equality checks. A database at exactly version 4 runs the v4 mind-map rebuild but never hits `if version == 5`, so `ADD COLUMN position` and the Uncategorised-first position backfill are skipped — yet `user_version` is written as 6. Reproduced: migrate a v4 schema → `PRAGMA user_version` = 6, `PRAGMA table_info(mindmap_categories)` = `[id, name, status, created, modified]` (no `position`), and `get_mindmap_categories()` raises `OperationalError: no such column: position`.
- **Why it matters:** any user on the previous schema has their DB stamped "current" while every Mind Maps page/category operation crashes (`/mindmaps`, create, reorder). The existing migration test misses it: `test_database_migrates_mindmaps_from_version_four` (tests/test_memory.py:92-241) asserts the category conversion and version only, never the column.
- **Suggested fix:** restructure as sequential ranged steps (`if version < 5: add column`, `if version < 6: backfill / ensure Uncategorised`), or loop "apply next migration" until `SCHEMA_VERSION`. Add a test asserting the `position` column exists after a v4 migration.

**Fix applied (finding 1.3 only).** The migration sequence in `src/alf/memory.py` was the problem: `version` is snapshotted once and each step is an equality check, so a v4 database ran the `version == 4` mind-map rebuild but never re-checked `version == 5`. The fix advances the snapshot after completing the v4 step — the last statement of the `version == 4` block is now `version = 5`, so the subsequent `version == 5` block legitimately runs (position column + Uncategorised-first backfill) before the `PRAGMA user_version = {SCHEMA_VERSION}` stamp. Only the version-4 path changes; fresh installs (v0), v1, genuine v5 (none left durable by this pipeline — the stamp always jumps to 6), and v6 keep identical behaviour. No refactor or new structure introduced.

- **Original reproduction result** (before the fix, deliberately built v4 DB in a temp path): `PRAGMA user_version` 4 → **6**, `mindmap_categories` columns `[id, name, status, created, modified]` (no `position`), existing categories/mindmaps/documents intact, and `get_mindmap_categories()` → `OperationalError: no such column: position`.
- **Migration state after fix** (same deliberately built v4 DB): `user_version` = **6** = `SCHEMA_VERSION`; `mindmap_categories` columns now `[id, name, status, created, modified, position]`; existing category/mindmap/document data intact; `get_mindmap_categories()` returns `[{'name': 'Uncategorised', 'position': 0, ...}]` with no error.
- **Regression test (strengthened):** `test_database_migrates_mindmaps_from_version_four` (tests/test_memory.py) now builds a v4 DB with a second mind map in a second category ("House") to exercise backfill ordering, and asserts: `"position" in mindmap_categories` columns, `position` values `[("Uncategorised", 0), ("House", 1)]`, existing mind map/document data preserved, and `memory.get_mindmap_categories()` returns both categories with the correct `position`. It catches the original bug (assertion would fail with the old code: no `position` column).
- **Test suite** (`.venv/bin/python -m pytest -q`): **267 passed, 5 failed** — identical pre-existing failures as before this change (4× finding 1.7 memory-category tests, 1× `test_generate_uses_timeout` in excluded LLM code); none introduced, none fixed.
- **Conclusion:** the v4 → current migration now applies every required step (category rebuild → `position` column + backfill → stamp 6), schema and data are correct, and category retrieval works.

### 1.4 Advertised calculator examples always fail (`abs`, `gcd`, `simplify`)

- **Severity:** Medium
- **File:** `src/alf/command_catalogue.py:59-60` and `:69`; `src/alf/calc.py:58-73` (`LOCAL_DICT`), `calc.py:76-85` (`_validate_functions`)
- **Problem:** the "Functions" examples `alf calc "abs(-42)"` and `alf calc "gcd(84, 18)"`, and the symbolic example `alf calc "simplify((x^2 - 1)/(x - 1))"`, are advertised in the CLI, in the TUI examples list (tui.py:480-531), and as clickable buttons on the web calc page (calc.html:188-213). `_validate_functions` rejects any called function not in `LOCAL_DICT`, which has none of abs/gcd/simplify. Verified: all three raise `CalculationError: unsupported expression`.
- **Why it matters:** every interface surfaces examples that always fail — the number one "doesn't work" impression a user gets from the calculator.
- **Suggested fix:** either add `abs`, `gcd`, `simplify` (etc., from `sympy`) to `LOCAL_DICT` and the degree-mode wrapper, or replace the examples with supported ones.

**Fix applied (finding 1.4 only).** Interpretation: the examples are **intended to be supported**, not wrong. `abs`, `gcd`, and `simplify` are standard, safe SymPy operations; they are advertised uniformly across the CLI catalogue (command_catalogue.py:59-60, :69), the TUI symbolic examples list, and the web calc page — which is exactly the review's suggested option "a". Removing them from every surface would have been a larger and less coherent change than adding them to the existing explicit whitelist.

- **Reproduction of the original failures** (before the fix): internal `calculate("abs(-42)")`, `calculate("gcd(84, 18)")`, and `calculate("simplify((x^2 - 1)/(x - 1))", symbolic=True)` all raised `CalculationError: unsupported expression`; the real CLI (`alf calc "abs(-42)"`, `'alf calc "gcd(84, 18)"'`, `alf calc "simplify((x^2 - 1)/(x - 1))" --symbolic`) printed `✗ Could not calculate expression: unsupported expression`.
- **Exactly what changed:** `src/alf/calc.py` only. Added the SymPy imports `Abs`, `gcd`, `simplify` and the three whitelist entries `"abs": Abs`, `"gcd": gcd`, `"simplify": simplify` in `LOCAL_DICT`. `_validate_functions` is unchanged and remains an explicit whitelist; the degree-mode wrapper inherits the new entries (all three are trig-independent); no web/TUI/catalogue code changed because the examples already exist there and derive from the same catalogue.
- **Mode handling:** `abs`/`gcd` are used numerically; `simplify` returns a symbolic result, so in numeric mode it yields "invalid numeric entry" — identical to the existing convention for `solve`/`diff`/`integrate` (which are also shared across modes; symbolic results are never leaked into the numeric UI).
- **Regression tests added (`tests/test_calc.py`):** `test_advertised_abs_and_gcd_functions` (`abs(-42) == 42.0`, `gcd(84, 18) == 6.0`), `test_advertised_simplify_function` (`simplify((x^2 - 1)/(x - 1))` symbolic `== x + 1`), and `test_unrelated_unsupported_function_is_still_rejected` (`floor`, `sec`, `cosh` all raise `CalculationError`), alongside the existing `test_unknown_function_is_rejected` (`arctan`).
- **Verification of all three advertised examples:** CLI numeric `alf calc "abs(-42)"` → `42.0`, `alf calc "gcd(84, 18)"` → `6.0`; CLI symbolic `alf calc "simplify((x^2 - 1)/(x - 1))" --symbolic` → `x + 1`. Web `POST /calc` (Flask test client) → all **200** with results `42.0`, `6.0`, `x + 1`. Internal `calculate()` returns the same values.
- **Boundary intact:** `alf calc "floor(2.7)"` and `alf calc "sec(0)"` still fail with `unsupported expression` on the CLI; the added rejection tests also pass. No arbitrary function names or unrestricted SymPy evaluation were introduced.
- **Test suite** (`.venv/bin/python -m pytest -q`): **270 passed, 5 failed** — the identical pre-existing failures (4× finding 1.7 memory-category tests, 1× `test_generate_uses_timeout` in excluded LLM code). `tests/test_calc.py`: 17 passed (3 new). Ruff clean on both changed files.

### 1.5 Saving a map always returns it to "Uncategorised"

- **Severity:** Medium
- **File:** `src/alf/web/static/mindmaps.js:225` (hardcoded `category: "Uncategorised"`); `src/alf/web/__init__.py:420-426`; `src/alf/memory.py:759-789` (`update_mindmap`)
- **Problem:** the save payload always sends `category: "Uncategorised"` regardless of the open map's actual category. Reproduced end-to-end via the Flask test client: create map (Uncategorised) → `POST /mindmaps/<id>/move` to "House" (stored under House) → `POST /mindmaps/save` → the map is back in Uncategorised. None of the move/reorder tooling tracks a category for the open map.
- **Why it matters:** a user who organises maps into categories loses that organisation every time they edit and save; the sidebar also desyncs from the server until a reload.
- **Suggested fix:** track the open map's category (use the value returned when loading it, mindmaps.js:655-660) and send it on save; or omit `category` for in-place updates and only set it on create.

**Fix applied (finding 1.5 only).** The client now tracks the open map's category and sends it on save (the review's primary suggested fix). All changes are in `src/alf/web/static/mindmaps.js`; no server or memory-layer code was changed.

- **What changed:**
  - Added a module-level `currentMindmapCategory` (default `"Uncategorised"`), next to `currentMindmapId`.
  - Save payload (mindmaps.js:225) sends `category: currentMindmapCategory` instead of the hardcoded `"Uncategorised"`.
  - The map-load handler (mindmaps.js:660-661) now also sets `currentMindmapCategory = savedMindmap.category` from `GET /mindmaps/<id>` (the response already includes the category name), exactly as the review suggested.
  - The drag-to-category drop handler (mindmaps.js:466-467) updates `currentMindmapCategory` when the moved map is the currently-open one, so a save right after a drag-move no longer reverts it.
  - The "new mindmap" and archive-of-open-map handlers reset `currentMindmapCategory` back to `"Uncategorised"` alongside `currentMindmapId = null`.
- **Verification (Flask test client, temp DB):** created a map in "House"; `GET /mindmaps/<id>` returns `category: "House"`; reproducing the review's exact sequence — save-as-new (Uncategorised) → `POST /mindmaps/<id>/move` to House → `POST /mindmaps/save` sending the category captured from GET — the map **stays in House** after save (previously it reverted to Uncategorised). New maps (no id) still default to Uncategorised. `node --check` on the JS passes; the change is client-side only.
- **Test suite** (`.venv/bin/python -m pytest -q`): **270 passed, 5 failed** — identical pre-existing failures (4× finding 1.7 memory-category tests, 1× `test_generate_uses_timeout` in excluded LLM code). No new failures.

### 1.6 Duplicate `id="jsmind-container"`

- **Severity:** Medium (confirmed defect; layout effect)
- **File:** `src/alf/web/templates/mindmaps.html:120-121`; `src/alf/web/static/mindmaps.css:387-393`
- **Problem:** two `<div id="jsmind-container">` elements exist. `getElementById` (mindmaps.js:16) binds jsMind to the first; the second is dead markup that still matches the `#jsmind-container { height: 100% }` rule and occupies an extra full-height block in the editor column.
- **Why it matters:** invalid HTML (non-unique id) and a phantom layout block under the map; jsmind derives its canvas size from that container, so it can interfere with editor height (see Potential 4.1).
- **Suggested fix:** remove one of the two divs.

**Fix applied (finding 1.6 only).** Removed the duplicate second `<div id="jsmind-container"></div>` from `src/alf/web/templates/mindmaps.html` (the phantom block below the bound container). The remaining single container is the first element, so `getElementById` in mindmaps.js binds jsMind to it exactly as before; the extra full-height block matching `#jsmind-container { height: 100% }` (mindmaps.css:387-393) is gone.

- **Verification:** `rg -c 'id="jsmind-container"' mindmaps.html` → `1`; the rendered `GET /mindmaps` page (Flask test client, temp DB) returns **200** and contains exactly one `id="jsmind-container"`.
- **Test suite** (`.venv/bin/python -m pytest -q`): **270 passed, 5 failed** — identical pre-existing failures (4× finding 1.7 memory-category tests, 1× `test_generate_uses_timeout` in excluded LLM code). No new failures.

### 1.7 The test suite fails 4 tests around mind map categories

- **Severity:** Medium
- **File:** `tests/test_memory.py:468-478`, `:481-491`, `:494-506`
- **Problem:** `test_archive_mindmap_category`/`test_archive_missing_mindmap_category` call `memory.archive_mindmap_category(...)` which does not exist (AttributeError). `test_delete_mindmap_category`/`test_delete_mindmap_category_deletes_maps` expect `delete_mindmap_category` to return True (and delete the maps) even when no "Uncategorised" row exists — the implementation returns False unless "Uncategorised" exists, and moves maps to it rather than deleting them (memory.py:501-559).
- **Why it matters:** `pytest` currently reports `4 failed, 268 passed`. Either the tests drifted from behaviour or behaviour regressed; the delete contract (move-to-Uncategorised vs delete maps) is explicitly undecided.
- **Suggested fix:** decide the semantics ([1.1 in Likely Bugs] below suggests bootstrapping Uncategorised at init), then either restore an archive-category function + tests or remove the stale tests and align the delete tests with the chosen contract.

**Fix applied (finding 1.7 only).** Chosen semantics (and aligned with the review's 2.2 edge): deleting a category **moves its maps to `Uncategorised`** (data-preserving, matching the implementation's documented intent and the review's "move-to-Uncategorised" contract) rather than hard-deleting them, and `Uncategorised` is auto-created when missing so deletion works on a fresh database. The archive-category function is restored.

- **`src/alf/memory.py` changes:**
  - Added `archive_mindmap_category(category_id)` — soft-archives a category (`status = 'archived'`), returns `True`/`False`; rejects the reserved `Uncategorised` category (mirrors the delete guard).
  - `delete_mindmap_category` no longer returns `False` when no `Uncategorised` row exists: it auto-creates the `Uncategorised` row (position 0) and then moves the category's maps to it and deletes the category. Deleting `Uncategorised` itself still returns `False`.
- **Tests (`tests/test_memory.py`) aligned to the chosen contract and restored:**
  - `test_archive_mindmap_category` / `test_archive_missing_mindmap_category` now exercise the restored function (plus new `test_archive_uncategorised_category_is_rejected`).
  - `test_delete_mindmap_category` asserts the category is gone while `Uncategorised` remains (was: expected empty list / literal ids).
  - `test_delete_mindmap_category_deletes_maps` renamed to `test_delete_mindmap_category_moves_maps_to_uncategorised` — asserts the map survives under `Uncategorised` (was: expected maps hard-deleted).
- **Test suite** (`.venv/bin/python -m pytest -q`): **275 passed, 1 failed** — the 4 memory-category failures are gone; the single remaining failure is `test_generate_uses_timeout` in excluded LLM code (pre-existing, unrelated). `tests/test_memory.py`: 117 passed.

---

## 2. Likely Bugs

### 2.1 Category re-order updates the DOM one slot early on downward drags

- **Severity:** Medium
- **File:** `src/alf/web/static/mindmaps.js:411-424`
- **Problem:** on drop, `position` is computed as a coordinate in the list WITHOUT the dragged element, but `orderedCategories` still contains it. For upward drags `insertBefore(orderedCategories[position])` is correct; for downward drags it inserts the category before the element at the pre-removal index, one or more slots too early (a single-step move is a visual no-op). The server order is computed correctly (memory.py:377-452) and the request succeeds, so the persisted order diverges from the visible order until a reload.
- **Why it matters:** drag-reordering categories appears to "not work" for downward moves (or shows the old order) while the database silently changed.
- **Suggested fix:** for downward moves anchor one further, e.g. `insertBefore(draggedCategory, orderedCategories[newIndex + 1])` / append when the anchor is missing — or derive `newIndex` from the full list consistently.

**Fix applied (finding 2.1 only).** Still present and confirmed against the current code: `src/alf/web/static/mindmaps.js` drop handler computes `position` in the without-dragged-element coordinate space (matching the server, `memory.move_mindmap_category`), but the DOM update used `const newIndex = position` against `orderedCategories` which still contains the dragged element — so downward moves inserted one slot early (single-step downward = visual no-op/off-by-one). Server-side ordering was already correct.

- **Fix:** convert the DOM anchor to the with-dragged-element space, mirroring the coordinate spaces:
  `newIndex = position > draggedIndex ? position + 1 : position` (unchanged for upward/no-op moves, one slot further forward for downward moves, `append` when the anchor is past the end). No change to the position sent to the server or to `move_mindmap_category`.
- **Verification:** no JS test harness exists in this repo (only pytest; `node_modules` contains just prettier), so instead of a committed test the exact drop-handler computation was transcribed into a standalone Node script and cross-checked against the **real** `memory.move_mindmap_category` on a fresh per-scenario SQLite database:
  - 192 scenarios (sizes 3/4/6 categories, Uncategorised present and absent, all up / down / single-step / multi-position drop points).
  - The OLD logic produced a DOM order diverging from the resulting server order on **all 76 genuine downward moves** and was correct on every upward/no-op case, confirming the off-by-one.
  - The FIXED logic matched the server order in **all 192 scenarios**.
  - `node --check src/alf/web/static/mindmaps.js`: OK.
- **Tests:** no new committed test (see above — no JavaScript test infrastructure; adding one would be a redesign, out of scope).
- **Suite result** (`.venv/bin/python -m pytest -q`): **275 passed, 1 failed** — unchanged: the single failure is the pre-existing `test_generate_uses_timeout` in excluded LLM code.
- **Ruff:** `ruff` only supports Python; JS is checked with `node --check`. `ruff check tests`: all checks passed. (`ruff check src/alf/web/__init__.py` flags a pre-existing, pre-session `I001` import-order issue at line 34 — `from waitress import serve` — present at HEAD and unrelated to 2.1; not touched.)

### 2.2 Deleting an existing category returns 404 "not found" before "Uncategorised" exists

- **Severity:** Medium (edge case, wrong status)
- **File:** `src/alf/memory.py:525-534`; `src/alf/web/__init__.py:398-403`
- **Problem:** `delete_mindmap_category` returns False whenever no row named 'Uncategorised' exists, and the route turns that into 404. The "Uncategorised" row is only created lazily on the first map save (memory.py:584-602). On a fresh database where a user creates categories but hasn't saved a map yet, deleting a legitimately-existing category 404s and the UI state is left stale.
- **Why it matters:** a normal action fails with a misleading error and there is no way to recover except by creating a map first.
- **Suggested fix:** create the "Uncategorised" row at schema initialisation (and for migrated DBs during version<6 migration), or auto-create it inside `delete_mindmap_category` when missing.

**Resolved by the 1.7 fix (finding 2.1 task) — no further change.** The 1.7 change to `src/alf/memory.py` `delete_mindmap_category` (memory.py:535-558) auto-creates the `Uncategorised` row (status `active`, position 0) when none exists, then moves the deleted category's maps to it and deletes the category — instead of the previous `return False` when no `Uncategorised` row was present. The route (`src/alf/web/__init__.py:390-403`) now only 404s when the category id genuinely does not exist (memory returns `False` only for a missing row), which is the intended "not found" semantics.

- **Verification of the 2.2 scenario (fresh database, category created, no `Uncategorised` row yet) via the real Flask route:**
  1. fresh DB, `POST /mindmap-categories` "House" → 200, DB contains only `["House"]` (no `Uncategorised` row).
  2. `DELETE /mindmap-categories/1` → **200** `{"deleted": True}` (previously 404).
  3. DB after delete: `[("Uncategorised", 0)]` — the reserved row is bootstrapped at position 0.
  4. `DELETE /mindmap-categories/9999` still → 404 (correct).
- **Existing tests exercised:** `tests/test_memory.py` category coverage, including the 1.7-aligned `test_delete_mindmap_category`, `test_delete_mindmap_category_moves_maps_to_uncategorised`, `test_delete_missing_mindmap_category` — all pass (`tests/test_memory.py`: 117 passed).

### 2.3 Renaming a category to an existing name causes a 500

- **Severity:** Low/Medium
- **File:** `src/alf/memory.py:482-496`; `src/alf/web/__init__.py:378-387`
- **Problem:** `mindmap_categories.name` is UNIQUE. `update_mindmap_category` does not catch `sqlite3.IntegrityError` and the route does not map it, so renaming "Events" to "House" produces a raw 500. Renaming a category to "Uncategorised" (when that row exists) hits the same path, and the `_is_uncategorised_category` guard only protects the exact row currently named that.
- **Why it matters:** a normal user action crashes the request handler.
- **Suggested fix:** pre-check name uniqueness and the reserved name in the route/function and return 400/409.

**Fix applied (finding 2.3 only).** Still present — `update_mindmap_category` (memory.py) did a blind `UPDATE` into the UNIQUE `name` column, so renaming to an existing name (or to the reserved `Uncategorised` name) raised `sqlite3.IntegrityError` out through the route → raw 500.

- **`src/alf/memory.py`** `update_mindmap_category` now pre-checks before updating (no broad exception handler; the UNIQUE constraint is untouched):
  - a category named `Uncategorised` (reserved) can never be claimed by another row — returns the new sentinel `"duplicate"` when `name == "Uncategorised"`;
  - a different existing row already using `name` (`SELECT id WHERE name = ? AND id != ?`) — returns `"duplicate"`;
  - unchanged: `True` on success, `False` when the id does not exist.
- **`src/alf/web/__init__.py`** `update_mindmap_category_web` maps the sentinel to a client error: `"duplicate"` → **409** `{"error": "... name is already in use"}`; `False` → 404 (unchanged); success → 200 (unchanged). The reserved-row guard (`_is_uncategorised_category` → 400) is unchanged.
- **Tests added** (`tests/test_memory.py`, new `tests/test_web.py`):
  - memory: `test_update_mindmap_category_duplicate_name_is_rejected`, `test_update_mindmap_category_to_reserved_name_is_rejected` → `"duplicate"`.
  - web: `test_renaming_category_to_existing_name_returns_conflict` → 409 (+ DB unchanged), `test_renaming_category_to_uncategorised_returns_conflict_when_row_exists` → 409, `test_renaming_category_to_uncategorised_returns_conflict_without_row` (fresh DB, no `Uncategorised` row) → 409, `test_renaming_category_succeeds` → 200 + renamed, `test_renaming_missing_category_returns_not_found` → 404.
- **Verification:** `tests/test_web.py` + `tests/test_memory.py` → 124 passed. Earlier behaviour confirmed by failing only for the true collision cases.
- **Suite result** (`.venv/bin/python -m pytest -q`): **282 passed, 1 failed** — the single failure is the pre-existing, excluded `test_generate_uses_timeout` (LLM code). (+7 tests: 2 memory, 5 web.)
- **Ruff:** `ruff check src/alf/memory.py src/alf/web/__init__.py tests` → only the pre-existing `I001` import-order flag at `web/__init__.py:6` (present at HEAD, unrelated); nothing new from this change.

Note (not in scope, left as-is): `create_mindmap_category` still lets a duplicate category name raise `IntegrityError` (500) at creation time; this finding only concerns rename/update.

---

## 3. Inconsistencies / Technical Debt

### 3.1 Archive endpoint is a hard delete; `archive_mindmap()` and `DELETE /mindmaps/<id>` are dead code

- **Severity:** Low
- **File:** `src/alf/web/__init__.py:439-448` (archive route → `delete_mindmap`), `:503-512` (unused DELETE route); `src/alf/memory.py:842-865` (`archive_mindmap`, used only by tests)
- **Problem:** `POST /mindmaps/<id>/archive` is documented as "Delete a saved mind map" and hard-deletes. The JS drop target only ever calls `/archive` (mindmaps.js:496-501) and is labelled "Delete", so behaviour matches the UI — but there is both a true soft-archive function and a real DELETE route that nothing uses.
- **Why it matters:** confusing API surface; the soft-archive capability is unreachable.
- **Suggested fix:** pick one semantic — implement real soft archive end-to-end (and update the drop target), or rename the endpoint to `/delete` and remove `archive_mindmap` and the DELETE route.

**Design decision (recorded):** mind maps do not have an archive concept — "Archive" applies to Memories only. A mind map operation is a permanent **Delete**. **Resolved (finding 3.1 task)**: the mind-map `/archive` path was incorrectly named and is now `/delete`; the dead soft-archive path and the unused REST DELETE route were removed so there is a single mind-map delete operation.

- **Route rename** (`src/alf/web/__init__.py`): `POST /mindmaps/<id>/archive` → **`POST /mindmaps/<id>/delete`** (handler renamed `archive_mindmap_web` → `delete_mindmap_web`, same `delete_mindmap` semantics, same 200 `{"deleted": true}` / 404 shape). The only caller, the JS delete drop-target (`src/alf/web/static/mindmaps.js` drop handler), now POSTs `/mindmaps/${mindmapId}/delete`.
- **Dead code removed:**
  - `archive_mindmap()` (`memory.py`) — the mind-map soft-archive (sets `mindmaps.status = 'archived'`). Callers verified: no route or other production caller, only three tests — removed together with its tests. `archive_mindmap_category()` (category-level, restored under 1.7) is unrelated and untouched.
  - `DELETE /mindmaps/<id>` route — verified genuinely unused (mindmaps.js:636's `method: "DELETE"` is the category route; mindmaps.js:658 is the GET *load* route; nothing in Python/tests/templates calls it). It was an exact duplicate of the delete handler, so removing it leaves exactly one delete endpoint (no second competing delete implementation). Its removal is part of making the API consistent (single `POST /mindmaps/<id>/delete`); the handler body is preserved in the new route.
- **Tests changed** (`tests/test_memory.py`, `tests/test_web.py`):
  - removed `test_archive_mindmap` and `test_archive_missing_mindmap` (function deleted);
  - `test_get_mindmaps_excludes_archived` no longer depends on `archive_mindmap` — it sets the status directly through SQL to keep covering the `get_mindmaps()` defensive filter;
  - added `test_deleting_mindmap_via_delete_endpoint` (200, map gone), `test_deleting_missing_mindmap_via_delete_endpoint` (404), `test_old_mindmap_archive_endpoint_is_removed` (`POST /mindmaps/<id>/archive` → 404).
- **Stale references:** swept src/ and tests/ for mind-map `/archive` — none remain. All remaining "archive" references are Memories archive (web/commands/TUI/presentation/tests, untouched) and category archive `archive_mindmap_category` (untouched). No memory-archive behaviour was altered.
- **Verification:** `tests/test_web.py` + `tests/test_memory.py` → 125 passed; `node --check src/alf/web/static/mindmaps.js` OK; full suite `.venv/bin/python -m pytest -q` → **283 passed, 1 failed** (only the pre-existing, excluded `test_generate_uses_timeout`). Ruff on changed files: no new issues (only the pre-existing `I001` import-order flag at `web/__init__.py:6`, present at HEAD, not introduced by this change).

### 3.2 `commands["calc"]["tui"]["symbolic_examples"]` is never read

- **Severity:** Low
- **File:** `src/alf/command_catalogue.py:81-91`
- **Problem:** the TUI (tui.py:515-528) iterates `examples["Symbolic mathematics"]`, and the web (web/__init__.py:284) does too; the separate `tui.symbolic_examples` list is duplicated config with no consumers, so it can silently drift.
- **Suggested fix:** remove it, or have the TUI read it.

**Resolved — orphaned `tui.symbolic_examples` removed (finding 3.2 task, second pass).** The earlier "intentional duplication" record was revisited: further verification confirmed `commands["calc"]["tui"]["symbolic_examples"]` has **no active consumer anywhere in the project** — both the TUI symbolic list (tui.py) and the web symbolic flag (web/__init__.py) read the main `commands["calc"]["examples"]` dict. Being unreferenced configuration that could silently drift, the orphaned collection was removed.

- **Removed:** `commands["calc"]["tui"]["symbolic_examples"]` (9 entries) and the temporary explanatory comment above it, from `src/alf/command_catalogue.py`. The `calc` `tui` block now contains only `title`, `description`, `guidance`.
- **Retained unchanged:** the active `commands["calc"]["examples"]` collection (including the `Symbolic mathematics` group — still 9 entries) and all of its consumers (TUI `calc-examples` / `calc-symbolic-examples` lists, web `"symbolic"` flag). The local variable named `symbolic_examples` in `web/__init__.py:284` reads that main dict and is a consumer of the retained collection, not a reference to the removed key.
- **References search:** `grep -rn "symbolic_examples"` across `src/` and `tests/` — only the two `web/__init__.py` local-variable hits remain (main-collection consumer); nothing referenced the removed key.
- **Tests:** no existing test depended on the removed collection, so none were added or changed (confirmed by the unchanged suite result). The catalogue still loads with the expected structure.
- **Verification:** `commands` catalogue loads with `calc.tui` = `{title, description, guidance}`; full suite `.venv/bin/python -m pytest -q` → **283 passed, 1 failed** (only the pre-existing, excluded `test_generate_uses_timeout`); Ruff on the changed file: all checks passed.

### 3.3 memories.html dead conditional + dead CSS

- **Severity:** Low
- **File:** `src/alf/web/templates/memories.html:379-396`; `:177-194`
- **Problem:** inside the `{% if selected_memory.status == "active" %}` block the form `action` uses a nested ternary that can never pick "archived" (so it always posts to `archive_memory_web`); `#related-memory-editor` CSS matches no element (the field is `#related-memory-ids`, used at memory.html:349-354).
- **Why it matters:** future maintainers may trust the ternary as real branching logic.
- **Suggested fix:** hardcode the archive action; drop the unused CSS rule.

**Resolved (finding 3.3 task).** Both reported issues verified against the current template and routes, then cleaned up while preserving behaviour exactly.

- **Dead conditional — confirmed and simplified.** Inside the `{% if selected_memory.status == "active" %}` block (memories.html:378) the form `action` was the ternary `{% if selected_memory.status == 'archived' %}...restore...{% else %}...archive...{% endif %}`. Since that branch is only ever entered when `status == "active"`, the `'archived'` arm is unreachable and the action always resolved to `archive_memory_web` (`POST /memories/archive`). The real restore path (`restore_memory_web`, `POST /memories/restore`) lives in the matching `{% else %}` block (line 397-411). The `action` is now hardcoded to `{{ url_for('archive_memory_web') }}` — identical behaviour, no surrounding active/archived UI logic touched.
- **Dead CSS — confirmed and removed.** `#related-memory-editor` (+ its `:focus` rule) in the template's `<style>` block matched no element — the actual field is `id="related-memory-ids"` (memories.html:352), which already has its own rules (including `:focus`). A full search of templates/static confirmed the selector was otherwise unused. Both `#related-memory-editor` rules were removed; the duplicate behaviour they would have provided is fully covered by the `#related-memory-ids` rules.
- **Behaviour verification (Flask test client):** active memory page renders the archive form action (`/memories/archive`, no `/memories/restore`); archived memory page (via `archived=on`) renders the restore action (`/memories/restore`); list page renders. Archive action still posts to the archive route as before.
- **Tests:** none added/changed — template-only change, existing suite unaffected.
- **Verification result:** full suite `.venv/bin/python -m pytest -q` → **283 passed, 1 failed** (only the pre-existing, excluded `test_generate_uses_timeout`). No Python files changed, so Ruff was not applicable.

### 3.4 `get_mindmap_categories()` docstring vs implementation ordering

- **Severity:** Low
- **File:** `src/alf/memory.py:347-375`
- **Problem:** the docstring claims "Uncategorised first, followed by alphabetical order"; the query orders purely by `position`, which `create_mindmap_category` assigns by creation order (memory.py:317-322). So the real order is creation order.
- **Suggested fix:** make the SQL `ORDER BY position, name` (and decide whether positions should be recomputed), or correct the docstring.

**Resolved — documentation correction only (finding 3.4 task).** The implementation was already correct and unchanged: `get_mindmap_categories()` orders purely by the stored `position` column (`ORDER BY position`). Only the docstring was inaccurate ("Uncategorised first, followed by alphabetical order" — true of neither the query nor `create_mindmap_category`'s creation-order assignments).

- **Change made:** `src/alf/memory.py` `get_mindmap_categories()` docstring now reads "Return all mind map categories in their stored position order." No SQL, ordering behaviour, position assignment, or migration logic was touched; no other documentation changed.
- **Verification:** full suite `.venv/bin/python -m pytest -q` → **283 passed, 1 failed** (only the pre-existing, excluded `test_generate_uses_timeout`); Ruff on `memory.py`: all checks passed.

### 3.5 Local egg-info is stale

- **Severity:** Low
- **File:** `src/alf.egg-info/SOURCES.txt:36-53`
- **Problem:** the manifest lists only `web/__init__.py` for the web package (feeding Error 1.2) and lists nine test files that no longer exist (test_classifier, test_command_dispatch, test_identity, test_interpretation, test_llm, test_presentation, test_question, test_question_cli_errors, test_tui).
- **Why it matters:** masks the packaging gap and indicates the manifest predates the removal of those tests; anyone diffing it will be misled.
- **Suggested fix:** regenerate egg-info (clean build) and fix package-data.

**Resolved (finding 3.5 task).** `src/alf.egg-info` is generated packaging metadata (git-ignored via `*.egg-info/`), regenerated from the normal toolchain rather than hand-edited.

- **What was found:** the pre-existing `SOURCES.txt` was stale relative to the current tree — it listed only `src/alf/web/__init__.py` for the web package (the finding-1.2 gap: no `web/templates/*`, `web/static/*`, or `web/static/jsmind/*`) and predated the new `tests/test_web.py`. Note: the finding's claim that nine test files "no longer exist" (`test_classifier`, `test_command_dispatch`, `test_identity`, `test_interpretation`, `test_llm`, `test_presentation`, `test_question`, `test_question_cli_errors`, `test_tui`) is **not reproducible against the current tree** — all nine exist and are part of the passing suite; the manifest's real staleness was the missing web assets and the new test module.
- **How it was regenerated:** `python -m build` (setuptools/PEP 517 via `build 1.6.0`) run from the project root, regenerating `src/alf.egg-info/` in place. No manual edits to any generated file.
- **`SOURCES.txt` afterwards:** every non-egg-info entry resolves to an existing file (`missing entries: none`); the web package now list all 6 templates, 3 top-level static files, and 3 jsMind files; `tests/test_web.py` is listed; no stale/non-existent references remain.
- **Consistency with the 1.2 fix (intact, not altered):** `[tool.setuptools.package-data]` still `alf = ["identity.toml", "web/templates/*", "web/static/*", "web/static/jsmind/*"]`. Built wheel contains all 12 web asset files; sdist contains 15 web asset paths. Wheel `METADATA` still carries `Requires-Dist: waitress` (finding 1.1 intact).
- **Build/test results:** `python -m build` → `alf-0.2.0.tar.gz` + `alf-0.2.0-py3-none-any.whl` built successfully; full suite `.venv/bin/python -m pytest -q` → **283 passed, 1 failed** (only the pre-existing, excluded `test_generate_uses_timeout`). Ruff: no Python source files changed by this finding (egg-info is generated; Ruff not applicable to it). `git status` shows no egg-info or `dist/` churn (egg-info ignored; build artifacts removed after verification).

---

## 4. Potential Issues

### 4.1 Desktop Mind Maps canvas sizing is fragile

- **Severity:** Low/Medium (unverifiable without a browser)
- **File:** `src/alf/web/static/mindmaps.css:387-393`; `src/alf/web/static/mindmaps.css:136-140`; `mindmaps.html:120-121`
- **Problem:** `#jsmind-container { height: 100% }` resolves against `.mindmap-editor` (flex:1, no explicit height outside the <750px media query), so the canvas dimensions jsmind reads at `show()` depend on resolved flex height; with the duplicate container (Error 1.6) this becomes doubly ambiguous.
- **Why it matters:** the map could render at an unexpected height, unscrollable or clipped, on desktop.
- **Suggested fix:** give the editor an explicit height (or min-height) on desktop and remove the duplicate container.

### 4.2 No CSRF/auth on state-changing routes, and `alf web` binds 0.0.0.0

- **Severity:** Low
- **File:** `src/alf/web/__init__.py:528-532`; e.g. `:337-353`, `:405-437`, `:471-490`
- **Problem:** all create/update/delete endpoints accept JSON or form posts with no CSRF protection or authentication, and the server listens on all interfaces.
- **Why it matters:** anyone on the LAN can create/delete categories and maps, or drive the browser endpoints cross-origin.
- **Suggested fix:** bind 127.0.0.1 by default (or add a token), and add CSRF checks for state-changing requests.

### 4.3 Failed saves/moves are silent in the UI

- **Severity:** Low
- **File:** `src/alf/web/static/mindmaps.js:231-233`, `:407-409`, `:453-455`, `:503-505`
- **Problem:** every `if (!response.ok) return;` swallows the error with no notification, so after a failed save the overdue timeline looks as if it succeeded (and `currentMindmapId` is only updated on success — leaving a new map still marked "new").
- **Why it matters:** a dropped server means users think edits are persisted when they are not.
- **Suggested fix:** surface failures through the existing `#save-notification` (or a dedicated error banner).

### 4.4 Position handling relies on SQLite NULL ordering for lazy "Uncategorised"

- **Severity:** Low
- **File:** `src/alf/memory.py:584-602` (`create_mindmap` auto-creates the category without `position`); `memory.py:361` (`ORDER BY position`)
- **Problem:** a lazily-created "Uncategorised" row has `position NULL` and is special-cased by `move_mindmap_category` clamps and the JS drop logic. It happens to sort first, but any code path that assumes contiguous integer positions (the max+1 in `create_mindmap_category`, the +/-1 shift in `move_mindmap_category`) is subtly dependent on this.
- **Why it matters:** fragile; a future query/ordering change can silently break the Uncategorised-first invariant.
- **Suggested fix:** always assign an explicit position when the reserved category is created (bootstrapping it at init, as in 2.2, also fixes this).

---

## 5. Clean Areas

- **Memory core (`memory.py`):** `remember`, `search_memories`, `relate_memory`, history/related-memory walks, and FTS maintenance on update/delete are correctly implemented and well covered (the FTS delete/insert dance in `update_memory`/`delete_memory`, memory.py:1069-1113/1666-1693, is done properly). Only the mind-map area shows issues.
- **Calculator (`calc.py`):** the explicit `LOCAL_DICT` whitelist plus `_validate_functions`, the degrees wrapper, and the `CalculationError` boundary are a clean design; numeric/symbolic paths behave as documented (verified `solve`, `expand`, `2^8` etc. work; `10^500` yields `inf` gracefully).
- **Web routes (`web/__init__.py`):** consistent JSON error handling (400 validation, 404 not-found), proper integer/status/trim validation, and the three-click example-parsing loop for calc are tidy.
- **Question/Remember flows:** verified via the Flask test client (`GET /`, `/question`, `/remember`, `/memories`, `/calc`, `/mindmaps` all 200); the `this.submit()` patterns (question.html:237-251, remember.html:204-216) are not recursion bugs — `form.submit()` does not re-fire the submit event.
- **Mind Maps API round-trip:** category create/update/move/delete, map save/load/move/archive all respond with correct status codes and JSON (verified with the test client) whenever the "Uncategorised" row exists.
- **Test coverage overall:** 268 passing tests including FTS, migrations v1, memory relationships, and calc.

---

## Verification performed

| Check | Command / method | Result |
|---|---|---|
| Test suite | `.venv/bin/python -m pytest -q` | `268 passed, 4 failed` (see Error 1.7) |
| Calc examples | `calculate()` on `abs(-42)`, `gcd(84, 18)`, `simplify((x^2-1)/(x-1))` | all `CalculationError: unsupported expression` (Error 1.4) |
| Migration v4→6 | Built a v4 schema, ran `initialise_database` | `user_version=6` but no `position` column; `get_mindmap_categories()` → `OperationalError: no such column: position` (Error 1.3) |
| Save re-categorisation | Flask test client: save → move to House → save again | category returns to `Uncategorised` (Error 1.5) |
| Web routes & API | Flask test client (`GET /…` + JSON API calls) | all 200; API round-trips correct (Clean Areas) |
| Packaging | `pyproject.toml`, `egg-info/requires.txt`, `egg-info/SOURCES.txt`, `pip list` | waitress installed manually, absent from metadata (Errors 1.1, 1.2) |

---

## Verification: Finding 1.2 — Wheels omit all web templates and static assets

Re-verification pass. This is **verification only**; no project files or configuration
were changed. To avoid touching the project tree (including the local
`src/alf.egg-info`), the build was performed from a pristine copy created with
`git archive HEAD`. All work took place under `/tmp/opencode` and was deleted
afterwards (except these results).

### Build commands used

```sh
# 1. Isolated build tool (build 1.6.0) in a temp venv, outside the project
python3 -m venv /tmp/opencode/buildenv
/tmp/opencode/buildenv/bin/pip install build

# 2. Pristine copy of the tracked source (no pre-existing egg-info, no .venv)
mkdir -p /tmp/opencode/alf-src && git archive HEAD | tar -x -C /tmp/opencode/alf-src

# 3. Real wheel + sdist via the project's normal packaging pipeline
/tmp/opencode/buildenv/bin/python -m build --wheel --sdist \
    -o /tmp/opencode/alf-src/dist /tmp/opencode/alf-src
# -> succeeded: alf-0.2.0-py3-none-any.whl and alf-0.2.0.tar.gz
```

`python -m build` used an isolated environment with `setuptools==84.0.0` (the declared
build backend). No `pyproject.toml` or package-data configuration was modified.

### Files present in the wheel (`unzip -l alf-0.2.0-py3-none-any.whl`)

All Python modules under `alf/`, plus `alf/identity.toml` and
`alf/web/__init__.py`, plus `alf-0.2.0.dist-info/*`. Entire listing of the
`alf/web` contribution to the wheel:

```
alf/web/__init__.py
```

### Files absent from the wheel

- `alf/web/templates/*` — all six templates: `calc.html`, `home.html`,
  `memories.html`, `mindmaps.html`, `question.html`, `remember.html`
- `alf/web/static/*` — `mindmaps.css`, `mindmaps.js`, `style.css`
- `alf/web/static/jsmind/*` — `jsmind.css`, `jsmind.draggable-node.js`, `jsmind.js`

These directories exist in the source (`src/alf/web/templates`, `src/alf/web/static`)
and are tracked by git, but setuptools' `package-data` (`alf = ["identity.toml"]`,
pyproject.toml:20-21) does not include them, so `build_py`/`bdist_wheel` skip them.

### Files absent from the sdist (`tar -tzf alf-0.2.0.tar.gz | grep web`)

```
alf-0.2.0/src/alf/web/
alf-0.2.0/src/alf/web/__init__.py
```

The sdist likewise omits `templates/` and `static/`, so building a wheel from the
sdist reproduces the same broken wheel (there is no path that yields a complete web
package).

### Clean-environment installation result

```sh
python3 -m venv /tmp/opencode/cleanenv
/tmp/opencode/cleanenv/bin/pip install /tmp/opencode/alf-src/dist/alf-0.2.0-py3-none-any.whl
```

Install succeeded: `alf 0.2.0` in `site-packages`, with runtime deps resolved from
PyPI (Flask 3.1.3, sympy 1.14.0, textual 8.2.8, rich 15.0.0).

Inspected the installed package directly:

```
/tmp/opencode/cleanenv/lib/python3.14/site-packages/alf/web/
    __init__.py
    __pycache__/
```

No `templates/`, no `static/`. `app.jinja_loader.searchpath` points at
`<site-packages>/alf/web/templates`, which does not exist on disk.

Note: `waitress` was **additionally** installed into the clean venv so that
`from alf.web import app` would import at all — importing `alf.web` without it fails
with `ModuleNotFoundError: No module named 'waitress'` (that is finding **1.1**, not
1.2). waitress presence/absence has no bearing on the template/static outcome below,
which is driven by the files being physically absent from the installed package.

### Web-route test results

Flask test client (`TESTING=True`, `PROPAGATE_EXCEPTIONS=False`) against the app
imported from the installed wheel; `/mindmaps` data dir isolated to a temp DB so no
user data was touched:

| Route | Status | Cause |
|---|---|---|
| `GET /` | **500** | `jinja2.exceptions.TemplateNotFound: home.html` |
| `GET /calc` | **500** | `TemplateNotFound: calc.html` |
| `GET /mindmaps` | **500** | `TemplateNotFound: mindmaps.html` |
| `GET /static/style.css` | **404** | no `alf/web/static/` in site-packages |
| `GET /static/mindmaps.js` | **404** | no `alf/web/static/` in site-packages |
| `GET /static/jsmind/jsmind.js` | **404** | no `alf/web/static/jsmind/` in site-packages |
| `GET /static/jsmind/jsmind.css` | **404** | no `alf/web/static/jsmind/` in site-packages |

No page renders and no asset loads; every handled route 500s on template resolution.

### Conclusion: **Confirmed**

The wheel built through the project's normal `python -m build` pipeline contains only
`alf/web/__init__.py` from the web package — `templates/` and `static/` (including
`static/jsmind/`) are absent from both the wheel and the sdist. Installed into a clean
environment, the web application cannot load any template (`500 TemplateNotFound` on
`/`, `/calc`, `/mindmaps`) and serves no static assets (`404` on all `/static/*`).
The web UI is therefore unusable from any non-editable (wheel) installation, exactly
as the original finding stated. (The earlier editable-install checks passed because
editable installs read the assets straight from the source tree.)

No files were changed; temporary build/output/venv artefacts were removed afterwards.