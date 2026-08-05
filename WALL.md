# WALL

Working notes only.

This document is intentionally temporary.

It records design direction, current priorities and architectural boundaries.
Once an idea becomes established it should move into ALF's persistent memory and be removed from this file.

## Current priorities

## Memory

- Implement soft deletion using a status field.
- Add commands to forget, restore and review memories.
- Preserve permanent memory IDs.
- Introduce relationships between memories rather than editing old ones.

Possible relationship types:

- related_to
- parent_of
- follows
- reviews
- supersedes
- derived_from

Implementation deferred until memory identity model is reviewed

## Memory history

ALF memories may optionally reference a previous memory.

Current implementation:

- Memories contain an optional `previous_memory_id`
- New memories can preserve the history of changing knowledge
- Existing memories are not modified when new memories are created
- Relationships are currently one-directional
- previous_memory_id is implemented
- richer relationships are deferred
- ALF preserves memory evolution by creating new records linked to previous memories rather than editing existing records.
- ALF memories are append-only records. New memories may reference previous memories to preserve the evolution of knowledge without modifying history.

Design intent:

- Preserve historical context rather than overwrite old knowledge
- Avoid a complex relationship graph in early versions
- Allow future interfaces to present memory evolution

Future considerations:

- Memory history views
- Schema versioning and migrations
- Richer relationship types if required
- exploration of relationship traversal

## Memory schema evolution

Current:

- Development database may require manual changes

Future:

- Add schema version tracking
- Add migration support when ALF becomes persistent across upgrades

## Presentation

Presentation is responsible only for displaying information.

Rules:

- Business logic belongs outside renderers.
- Renderers receive structured data, not formatted strings.
- Avoid capability-specific logic inside presentation.
- Never expose Python implementation details to the user.

## Architecture

Keep modules focused on a single responsibility.

Current direction:

- identity.py — ALF identity
- memory.py — persistent memory
- presentation.py — user output
- status.py — runtime status
- system.py — operating system information
- git.py — repository awareness
- commands.py — command dispatch

Prefer simple modules over clever abstractions.

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
