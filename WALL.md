# WALL

Working notes only.

This document is intentionally temporary.

It records design direction, current priorities and architectural boundaries.
Once an idea becomes established it should move into ALF's persistent memory and be removed from this file.

## Current priorities

## Memory

ALF's memory system provides persistent, identifiable records that preserve
the evolution of knowledge without modifying existing memories.

Current capabilities:

- Persistent memory stored in SQLite.
- Permanent memory IDs.
- Soft deletion using a status field.
- Commands to forget, restore and review memories.
- Memories can reference previous memories to preserve history.
- Relationships between memories are supported.
- Forgotten memories retain their identity.
- Existing memories are not modified when new memories are created.

Design intent:

- Memories are append-only records.
- Relationships are deliberately simple for now.
- Richer relationship types are deferred until a concrete use case requires them.

Future:

- Add migration support when the schema changes.
- Migrations should be applied sequentially using the database schema version.
- Do not introduce migration machinery until the first schema change requires it.

## Presentation

Presentation is responsible only for displaying information.

Rules:

- Business logic belongs outside renderers.
- Renderers receive structured data, not formatted strings.
- Avoid capability-specific logic inside presentation.
- Never expose Python implementation details to the user.

## Architecture

ALF is composed of self-describing subsystems.
Each subsystem owns its own knowledge and advertises its capabilities.
Interfaces consume those capabilities rather than maintaining duplicated knowledge.
Keep modules focused on a single responsibility.

Current direction:

- identity.py — ALF identity
- memory.py — persistent memory
- presentation.py — user output
- status.py — runtime status
- system.py — operating system information
- git.py — repository awareness
- commands.py — command registry, dispatch and metadata

Prefer simple modules over clever abstractions.
Capability discovery currently identifies reporting subsystems.
Future introspection may distinguish between capability-reporting modules and internal helper modules.

Privilege boundary: ALF must not autonomously invoke sudo, elevate privileges,
or execute commands requiring elevated privileges. When privileged information
is required, ALF may explain that the information requires a privileged
operation, but must not turn the required command into an instruction for the
user.

A question may require multiple capabilities, and ALF must not let a harmless part of a question legitimise a dangerous part.

Capabilities produce evidence. The LLM interprets evidence into an answer. Presentation layers render the answer.

### System awareness and interfaces

ALF's system capability is defined by the **interfaces it is permitted to inspect**, rather than by a hard-coded list of system components or resources.

`system.py` should not attempt to maintain a fixed inventory of the machine. Instead, it provides controlled access to explicitly permitted system interfaces. This allows ALF's system awareness to grow without changing the definition of the `system` category.

The distinction is:

- **Interfaces** — what ALF is permitted to inspect.
- **System information** — what ALF has obtained from those interfaces.
- **Presentation** — how that information is formatted for the user.
- **LLM** — interprets the available information and explains the result.

The system capability should therefore advertise its permitted `interfaces`, rather than presenting a fixed snapshot as the definition of the capability.

ALF must never be given unrestricted shell execution through the system capability. Interfaces are explicit and controlled. Where obtaining information requires privileged access, ALF must not execute `sudo` or direct the user to perform an action. It may explain that the information requires a privileged operation and, where appropriate, describe the command that could be used without presenting it as an instruction.

The LLM should remain replaceable. System-interface descriptions and prompts must therefore use general, model-independent language and should not depend on behaviour specific to the current local model.

This approach keeps `system` as a category of capability rather than a hard-coded inventory of what ALF currently knows about the machine.

### User-directed actions

ALF may explain that an action is possible or that particular information
requires a privileged operation.

ALF must not execute privileged actions itself.

ALF should not present commands requiring privileged access as instructions for
the user to carry out. If such a command is mentioned, it should be described
as an example of the operation that would be required, not as a requested or
recommended action.

ALF must also never imply that an action has occurred when it has not.

### Answer routing

ALF is responsible for deciding how a question should be answered.

The LLM is a replaceable reasoning and presentation component, not ALF's source of truth.

ALF may answer using:

- system information
- stored memory
- external research
- the LLM's general knowledge
- a combination of these sources

ALF may also decline to answer when no suitable capability or reliable source is available. An honest limitation is a valid outcome, not a failure.

The routing mechanism should remain small, explicit and testable. Do not introduce confidence scoring, secondary LLM judges, semantic classification or other additional machinery unless simpler routing proves inadequate.

The router should determine what evidence or capability is required before asking the LLM to formulate the final response.

## Memory relationships

- Do not overwrite old memories.
- Allow newer memories to supersede older ones.
- Preserve history.
- Expose relationships in future UI.

## Intelligence

Current priority is building infrastructure.

Natural-language reasoning, planning and higher intelligence come later.

First make ALF:

- reliable
- understandable
- maintainable
- predictable

### Knowledge routing

ALF should determine which knowledge sources are appropriate for a question before invoking the LLM.

Memory should be considered before external research where appropriate.

Knowledge-source selection should be deterministic and implemented by ALF rather than delegated to the LLM.

The LLM interprets and synthesises information supplied by ALF; it does not control ALF's information flow.

Potential knowledge sources include:

- Persistent memory
- Current system information
- Repository information
- Fresh external research
- The local LLM's existing knowledge

The knowledge-routing layer should remain explicit, small and testable.

Search architecture: Use the local search service as ALF's general web-search interface. Do not create a separate Wikipedia search layer unless a specific requirement emerges that the general search service cannot satisfy.

## Data

User data belongs in the user data directory.

Examples:

- SQLite database
- identity.toml
- future configuration

The project directory should contain only source code and project assets.

## Development principles

When uncertain:

- Choose the simpler design.
- Prefer explicit code over abstraction.
- Preserve backwards compatibility where practical.
- Keep changes small and testable.
- Refactor only after duplication becomes obvious.

If something is difficult to explain, it is probably too complicated.

## Long-term vision

ALF is not intended to become another chatbot.

It is intended to become a long-lived personal computing companion whose knowledge accumulates over years.

The memory system should preserve not only facts, but the reasoning, decisions and evolution of ideas that produced them.

## Future CLI improvements

- Current help output is suitable for early development.
- As commands gain options, consider hierarchical help:
- Avoid turning top-level help into a full command reference.
- Support `alf command --help`
- Consider `alf memory <id> --history`
- Improve invalid argument messages
- Consider command argument parsing layer

## Future interface direction

As ALF grows, consider:

- grouped commands for discoverability
- interactive shell mode
- natural language command interpretation

The CLI should remain a stable foundation rather than requiring users to memorise commands.

## Command registry direction

Future interfaces should consume command metadata rather than duplicate command knowledge.

## Health system

ALF should be able to inspect its own internal health.

Initial scope:

Health system

- Audit capability providers
- Report self-describing subsystems
- Report non-reporting modules separately
- Detect malformed capability metadata
- Detect module import failures

Health checks should consume subsystem self-description rather than duplicate subsystem knowledge.
Health reports should record complete subsystem state, but user-facing health output should prioritise actionable problems over normal operation.
Future:

- Database integrity checks
- Configuration validation
- Dependency checks
- Migration status
