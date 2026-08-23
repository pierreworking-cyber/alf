# ALF Architectural Principles

## Purpose

ALF is Peter's long-term local computing companion.

This document describes the architectural principles and design intentions that currently govern ALF development.

It is an architectural guide, not a historical record and not an immutable constitution.

ALF is an evolving system. Development experience, experimentation and newly discovered requirements may invalidate earlier decisions. When that happens, the architecture should be deliberately revised rather than preserving an obsolete rule merely for consistency.

The purpose of this document is therefore to describe **the ALF we are currently trying to build**.

---

# 1. Core principles

ALF should favour:

* **Correctness over speed**
* **Tools and evidence over unsupported guesses**
* **Records over assumed memories**
* **Simplicity over unnecessary complexity**
* **Clear ownership over duplicated application logic**
* **Useful interaction over interface uniformity**
* **Evolution over attachment to obsolete decisions**

These principles apply to the system as a whole.

They do not require every interface to behave identically.

---

# 2. ALF owns the application

ALF is the application.

The CLI, TUI, web interface and future interfaces are front-ends to ALF rather than separate applications.

The underlying application owns:

* persistent state;
* identity;
* memory;
* memory relationships;
* command semantics;
* capability information;
* research and evidence retrieval;
* routing and application decisions;
* interaction with the local LLM;
* system and repository information.

An interface should not independently redefine these things.

Where several interfaces perform the same underlying operation, the operation should have the same semantics regardless of which interface initiated it.

Interfaces may, however, provide different workflows for reaching those operations.

---

# 3. Interfaces are specialised views

ALF does not require every capability to be exposed through every interface.

Different interfaces are appropriate for different kinds of interaction.

The current interfaces are:

* **CLI** — fast, deterministic, scriptable and suitable for direct commands;
* **Textual TUI** — interactive terminal exploration and workflows;
* **Web** — richer interactive presentation and browser-based workflows.

Future interfaces may include visual or spatial interfaces that are fundamentally different from the terminal interfaces.

The existence of a CLI does not require every future capability to have an equally good CLI representation.

Likewise, a capability being available in the web interface does not imply that it should be forced into the TUI.

The correct question is:

> What is the best interaction for this capability in this medium?

The application semantics remain shared even when the interaction is not.

---

# 4. Interfaces must not duplicate application rules

Although interfaces may provide different workflows, they should not independently maintain competing definitions of ALF's capabilities.

For example:

* memory categories belong to the memory system;
* command metadata belongs to the command catalogue;
* capabilities belong to capability discovery;
* memory validation belongs in the appropriate application layer;
* interface-specific presentation belongs in the interface.

A new interface should consume ALF's existing application information rather than creating a second registration system wherever practical.

This principle exists to prevent interface drift.

It does **not** require identical interfaces.

---

# 5. The CLI

The CLI is the primary deterministic interface and remains an important reference implementation for direct ALF operations.

Commands should have:

* explicit semantics;
* predictable argument handling;
* deterministic dispatch;
* useful error messages;
* no dependence on natural-language guessing for command selection.

Command prefixes may be accepted when they resolve unambiguously.

Natural-language interpretation should not be silently substituted for deterministic command dispatch.

The CLI should remain capable of performing the core application operations for which a command-line interaction is appropriate.

It does not need to expose every visual, spatial or highly interactive capability of ALF.

---

# 6. The TUI and Web interfaces

The TUI and web interface are not alternate implementations of ALF.

They are specialised front-ends to the same application.

They may provide workflows that would be cumbersome or inappropriate in the CLI.

For example, interactive memory exploration, related-memory surfacing, editing workflows and contextual suggestions can be natural in a graphical or terminal UI while being awkward in a conventional command-line command.

This is acceptable.

A useful interface is more important than artificial feature parity.

---

# 7. Visual and spatial interaction

ALF should be allowed to develop capabilities whose natural representation is visual or spatial.

Examples may include:

* mind maps;
* memory relationship graphs;
* knowledge maps;
* timelines;
* visual exploration of related information;
* other spatial representations of ALF's state.

Such capabilities should not be forced into the CLI merely to maintain theoretical interface parity.

A mind map, for example, is fundamentally a spatial interaction. A graphical interface may therefore be the appropriate place to create and explore it.

The underlying information and relationships remain owned by ALF.

The visual representation is an interface to that information.

---

# 8. Persistent memory

Memory is a first-class part of ALF.

Memory is persistent application state rather than conversational context assumed by the LLM.

The memory system currently supports categories including:

* note;
* fact;
* decision;
* preference.

Memory operations include creation, searching, editing, history, relationships, archiving and permanent deletion.

Memory semantics should remain explicit.

In particular:

* creating a new memory/revision is part of the memory-history model;
* editing an existing memory is an explicit in-place operation;
* archiving is distinct from deletion;
* permanent deletion is irreversible;
* deletion does not rewrite historical records or silently repair references that are intentionally retained by the memory model.

The memory database is authoritative for persistent memory.

---

# 9. Memory relationships

Memories may be related to one another.

Relationships are application data, not merely annotations produced for presentation.

Interfaces may surface relationships differently.

For example:

* the CLI may display textual related-memory information;
* the TUI may allow interactive exploration;
* the web interface may present relationships visually;
* a future mind-map interface may represent relationships spatially.

The underlying relationship semantics remain shared.

---

# 10. The local LLM

The local LLM is a component of ALF, not the owner of ALF.

The LLM must not be treated as an authoritative source merely because it produces fluent answers.

The earlier model-qualification work established an important distinction:

> A model may be unsuitable as an independent knowledge provider while still being useful as an interpreter, analyser or classifier.

ALF therefore does not need to restrict the LLM to a single role.

The LLM may be used where it provides useful assistance, including:

* interpreting supplied evidence;
* analysing questions;
* classifying questions;
* assisting with routing;
* formulating research queries;
* interpreting retrieved information;
* composing responses;
* assisting interactive interfaces.

The LLM does not thereby become the authority over ALF's persistent state or factual evidence.

---

# 11. LLM authority and evidence

The LLM should not be treated as an independent authority merely because it can answer a question without external evidence.

Where factual evidence is required, ALF should obtain appropriate evidence and provide it to the LLM for interpretation.

The distinction is:

**ALF controls the evidence and application state.**

**The LLM assists with interpretation and interaction.**

The LLM may propose an interpretation or classification, but ALF should retain control over consequential application operations.

The use of an LLM for classification or routing is therefore not inherently contrary to the architecture.

It is acceptable when the LLM is being used as a component of ALF rather than being granted uncontrolled authority over ALF.

---

# 12. Question analysis and routing

Question handling may use multiple stages.

A question may require:

* memory;
* system information;
* repository information;
* external research;
* calculation;
* another ALF capability;
* or interpretation using the local LLM.

The routing system should select an appropriate path.

Routing may use deterministic rules, LLM-assisted analysis, or a combination of both.

The choice should be based on usefulness, reliability and simplicity rather than an absolute prohibition on one technique.

In particular, semantic classification by the LLM is permitted when it provides useful analysis that ALF cannot reasonably obtain more simply.

The LLM's routing decision should not be treated as an unquestionable authority.

ALF remains responsible for executing the resulting application behaviour.

---

# 13. Research and external evidence

External research exists to obtain evidence that is not reliably available from ALF's own records or local capabilities.

The user's original question should be preserved faithfully.

The research process may transform or analyse the question for search purposes, but meaningful information in the original wording should not be casually discarded.

Research sources are evidence sources, not authorities over ALF.

Wikipedia, web search and other sources may be used according to their usefulness for the particular question.

No individual source should automatically be treated as authoritative merely because it is the first source consulted.

Research should favour evidence appropriate to the question.

The LLM may assist in interpreting retrieved evidence, but should not be allowed to manufacture evidence that ALF did not obtain.

---

# 14. Answers

An ALF answer may be based on one or more forms of evidence, including:

* persistent memory;
* current system information;
* repository information;
* external research;
* calculations or other deterministic capabilities;
* local LLM interpretation.

The answer pipeline should make sensible use of available evidence.

Memory should be considered where it is relevant.

The LLM should interpret evidence selected or obtained by ALF rather than being treated as a replacement for the underlying evidence.

Where useful, ALF should make the provenance or nature of an answer understandable to the user.

---

# 15. The LLM qualification benchmark

The model-qualification work remains valuable.

The original Qwen 3:4b model was tested against a fixed 20-question factual knowledge corpus.

The qualification standard was deliberately strict: one substantive factual failure was sufficient to reject a model as an independent knowledge provider.

That test produced:

* 20 questions tested;
* 19 acceptable answers;
* 1 substantive failure;
* result: **rejected as an independent knowledge provider**.

The failed question concerned Python's `venv` module.

This result remains historical evidence about Qwen 3:4b and about the danger of treating fluent local-model output as authoritative knowledge.

ALF currently uses qwen3:8b.

The qualification of one model does not automatically qualify another model.

The benchmark should therefore remain available as a model-qualification and regression resource, and its executable state should be maintained if it is described as an active qualification mechanism.

The benchmark does not imply that an unqualified model cannot be used for interpretation, analysis, routing or other bounded roles.

---

# 16. Deterministic application behaviour

Determinism remains important where ALF is making application decisions or manipulating persistent state.

Examples include:

* command dispatch;
* memory storage;
* memory deletion;
* memory history;
* database operations;
* capability registration;
* system operations;
* repository operations.

The presence of an LLM elsewhere in the pipeline does not justify making these operations unpredictable.

Where an operation has important persistent consequences, ALF should retain explicit control over the operation.

---

# 17. Command vocabulary and metadata

The command catalogue is the central source of command metadata.

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
* `question`;
* `tui`;
* `web`.

Future interfaces should consume command and capability metadata rather than maintaining independent descriptions of ALF's functionality wherever practical.

The catalogue describes application commands.

It does not require every future interface to expose every command in the same form.

---

# 18. Capability discovery and self-description

ALF should be able to describe its own capabilities.

Capability discovery should be derived from the actual application rather than maintained as a disconnected list of claims.

The `health` command should provide useful information about the operational state of ALF.

The `about` interface should describe ALF's identity and available capabilities.

Self-description is valuable because ALF is intended to be a long-lived system that can evolve without requiring every interface to be manually rewritten whenever a capability changes.

---

# 19. Identity and configuration

ALF has a persistent identity distinct from transient runtime state.

Identity, configuration and application data should have clear ownership and locations.

Runtime data should not accidentally become part of the source repository.

Fresh installations should be capable of establishing the persistent state required for normal operation without relying on undocumented manual preparation.

---

# 20. Data boundaries

Source code belongs in the repository.

Persistent user data belongs outside the source tree.

Examples of persistent runtime data include:

* the ALF SQLite database;
* identity information;
* runtime configuration;
* logs;
* other machine-local application state.

Generated build artefacts, caches and experiment output should not be confused with source or architectural records.

Temporary development artefacts should be removed when they are no longer useful.

---

# 21. Testing

Tests should protect actual application behaviour and important architectural guarantees.

The normal test suite should remain fast enough to run frequently.

Long-running, model-dependent or qualification-specific experiments may be maintained separately from the ordinary suite.

However, if a benchmark is described as an active safeguard or qualification mechanism, it should remain executable and its broken state should not be silently hidden.

Tests should evolve with the architecture.

A test that protects an obsolete design decision is a liability rather than a safeguard.

---

# 22. Development workflow

ALF development should favour deliberate, incremental change.

Before changing code:

* understand the relevant architecture;
* inspect the actual implementation;
* identify the precise file and function involved;
* consider the effect on other interfaces and application layers.

Changes should normally be made one coherent piece at a time.

After a change:

* run Ruff;
* run the relevant tests;
* run the full test suite when appropriate;
* run `git diff --check`;
* inspect the resulting diff;
* verify that documentation still describes the current system.

A clean test suite is necessary but not sufficient.

Architectural coherence also requires checking whether the code, documentation and interfaces still agree with the current design.

---

# 23. Documentation as a living architectural record

WALL.md is the current architectural statement for ALF.

It should describe the architecture we currently believe in, not preserve obsolete decisions merely because they were once made.

When development deliberately changes an architectural assumption, WALL.md should be updated as part of that change.

Historical decisions can be preserved elsewhere when their history is useful.

They should not remain in WALL.md as active prohibitions unless we still believe them.

---

# 24. Architectural evolution

ALF is expected to change as we learn.

Earlier assumptions should be revisited when experience demonstrates that they are no longer useful.

In particular:

* an interface rule may change when a new interface exposes a better interaction;
* an LLM restriction may change when experimentation demonstrates a useful bounded role;
* a routing design may change when actual usage demonstrates a better approach;
* a capability may move to a more appropriate interface;
* a previously simple mechanism may be replaced when its limitations become significant.

The correct response to such changes is deliberate architectural revision.

The goal is not consistency with ALF's past.

The goal is coherence with **the ALF we are building now**.

---

# 25. Future direction

ALF should remain a single local application with multiple appropriate ways of interacting with it.

The long-term system may include:

* deterministic command-line interaction;
* interactive terminal workflows;
* browser-based interaction;
* visual exploration;
* mind maps;
* relationship graphs;
* richer memory navigation;
* additional forms of knowledge representation.

These should not become separate applications with separate truths.

They should become different ways of experiencing the same underlying ALF system.

The central architectural principle is therefore:

> **ALF owns the application; interfaces provide appropriate ways to interact with it.**

And alongside that:

> **The LLM is a useful component of ALF, but it is not ALF's authority.**

And finally:

> **Architecture is allowed to evolve when experience shows that an earlier assumption was wrong.**
