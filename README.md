# ALF

ALF is Peter's local computing companion.

## Philosophy

The LLM is replaceable.

ALF is not.

ALF exists to be useful, not impressive.

ALF is designed as a personal computing companion that owns its identity, tools, memory, and workflow. The intelligence layer may change over time, but ALF's purpose remains consistent.

## Principles

- Correctness over speed
- Tools over guesses
- Records over assumed memories
- Simplicity over unnecessary complexity

## Current capabilities

ALF currently has:

- System awareness
- Persistent memory using SQLite
- Categorised knowledge storage
- Command discovery
- Self-description through the `about` command

## Running ALF

After activating the Python environment:

```bash
alf
```

ALF can also be run with specific commands:

```bash
alf help
```

to display available commands.

Current commands include:

- `alf about` — Explain what ALF is
- `alf hello` — Show a welcome message
- `alf help` — List available commands
- `alf memories` — Recall stored memories
- `alf remember <category> "text"` — Store a memory
- `alf status` — Show system information

## Memory

ALF stores persistent memories using SQLite.

Memory entries currently support categories:

- `note`
- `fact`
- `decision`
- `preference`

Example:

```bash
alf remember preference "Peter prefers structured data"
```

ALF's memory database is kept separate from source code and is not stored in version control.

## Data storage

ALF separates:

- Source code — managed by Git
- Configuration — stored in TOML files
- Runtime data — stored separately in SQLite

This separation allows ALF's code and personal data to evolve independently.

## Architecture

Current structure:

```
ALF
 |
 +-- Identity
 |      |
 |      +-- identity.toml
 |
 +-- Commands
 |      |
 |      +-- Command registry
 |
 +-- Memory
 |      |
 |      +-- SQLite database
 |
 +-- System awareness
        |
        +-- Operating system information
```

## Current limitations

ALF is still early in development.

Current limitations:

- Limited conversation ability
- No natural language understanding
- No autonomous planning
- No external integrations
- Limited memory management tools

## Future milestones

Potential future developments:

- Move runtime data to a standard user data location
- Automatic capability reporting
- Improved conversation interface
- Memory search and maintenance tools
- Local AI integration
- Better separation of configuration and identity
- Terminal personality enhancements 🌈

## Project status

Version: 0.1

ALF is learning.

The goal is not to create another chatbot.

The goal is to create a personal computing companion that is reliable, understandable, and evolves alongside its owner.

