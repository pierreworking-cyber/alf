# ALF

ALF is Peter's local computing companion.

## Philosophy

The LLM is replaceable.

ALF is not.

ALF exists to be useful, not impressive.

ALF is designed as a personal computing companion that owns its identity, tools, memory, and workflow. The intelligence layer may change over time, but ALF's purpose remains consistent.

## Principles

* Correctness over speed
* Tools over guesses
* Records over assumed memories
* Simplicity over unnecessary complexity

## Current capabilities

ALF currently has:

* System awareness
* Git repository awareness
* Persistent memory using SQLite
* Categorised knowledge storage
* Command discovery
* Capability discovery and self-description
* Self-inspection through the `health` command

## Running ALF

After activating the Python environment:

```text
alf
```

ALF can also be run with specific commands:

```text
alf help
```

to display available commands.

Current commands include:

* `alf about` — Explain what ALF is
* `alf archive <id>` — Archive a memory
* `alf categories` — Show memory categories
* `alf forget <id>` — Forget a memory while preserving its identity
* `alf health` — Show ALF internal health information
* `alf help [command]` — Show command help
* `alf history <id>` — Show memory history
* `alf memories` — Recall previous memories
* `alf memory <id>` — Show a single memory
* `alf remember <category> "text" [--relate <id>]` — Add a memory
* `alf search "text"` — Search memories
* `alf version` — Show ALF version

## Memory

ALF stores persistent memories using SQLite.

Memory entries currently support categories:

* `note`
* `fact`
* `decision`
* `preference`

Memories have permanent IDs and retain their identity when forgotten.

New memories can reference previous memories, allowing ALF to preserve the evolution of knowledge without modifying existing records.

Example:

```text
alf remember preference "Peter prefers structured data"
```

ALF's memory database is kept separate from source code and is not stored in version control.

## Data storage

ALF separates:

* Source code — managed by Git
* Configuration — stored in TOML files
* Runtime data — stored separately in SQLite

This separation allows ALF's code and personal data to evolve independently.

## Design approach

ALF is built around small, independent capabilities.

Where practical, components describe themselves rather than maintaining separate registration lists.

Examples:

* Commands provide metadata describing available actions
* Subsystems can advertise capabilities
* Health checks inspect ALF's internal structure
* Runtime data is kept separate from source code

The goal is not to create a complex framework, but to keep ALF understandable as it grows.

## Current limitations

ALF is still early in development.

Current limitations:

* Limited conversation ability
* No natural language understanding
* No autonomous planning
* No external integrations

## Future milestones

Potential future developments:

* Move runtime data to a standard user data location
* Improved conversation interface
* Better separation of configuration and identity
* Terminal personality enhancements 🌈
* Local AI integration

## Project status

Version: 0.1

ALF is learning.

The goal is not to create another chatbot.

The goal is to create a personal computing companion that is reliable, understandable, and evolves alongside its owner.
