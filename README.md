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
- Git repository awareness
- Persistent memory using SQLite
- Categorised knowledge storage
- Command discovery
- Capability discovery and self-description
- Self-inspection through the `health` command

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

- `alf about` — Explain what ALF is
- `alf hello` — Show a welcome message
- `alf help` — List available commands
- `alf memories` — Recall stored memories
- `alf remember <category> "text"` — Store a memory
- `alf health` — Check ALF internal health
- `alf status` — Show system information
- `alf version` — Show ALF version

## Memory

ALF stores persistent memories using SQLite.

Memory entries currently support categories:

- `note`
- `fact`
- `decision`
- `preference`

Example:

```text
alf remember preference "Peter prefers structured data"
```

ALF's memory database is kept separate from source code and is not stored in version control.

## Data storage

ALF separates:

- Source code — managed by Git
- Configuration — stored in TOML files
- Runtime data — stored separately in SQLite

This separation allows ALF's code and personal data to evolve independently.

## Design approach

ALF is built around small, independent capabilities.

Where practical, components describe themselves rather than maintaining separate registration lists.

Examples:

- Commands provide metadata describing available actions
- Subsystems can advertise capabilities
- Health checks inspect ALF's internal structure
- Runtime data is kept separate from source code

The goal is not to create a complex framework, but to keep ALF understandable as it grows.

## Current limitations

ALF is still early in development.

Current limitations:
(.venv) peter@bazzite:~/Projects/alf$ git diff
diff --git a/README.md b/README.md
index c46d9cf..f790fb9 100644
--- a/README.md
+++ b/README.md
@@ -24,10 +24,12 @@ ALF is designed as a personal computing companion that owns its identity, tools,
 ALF currently has:
 
 - System awareness
+- Git repository awareness
 - Persistent memory using SQLite
 - Categorised knowledge storage
 - Command discovery
 - Self-description through the `about` command
+- Self-inspection through the `health` command
 
 ## Running ALF
 
@@ -53,6 +55,9 @@ Current commands include:
 - `alf memories` — Recall stored memories
 - `alf remember <category> "text"` — Store a memory
 - `alf status` — Show system information
+- `alf health` — Check ALF internal health
+- `alf status` — Show system information
+- `alf version` — Show ALF version
 
 ## Memory
 
@@ -83,31 +88,20 @@ ALF separates:
 
 This separation allows ALF's code and personal data to evolve independently.
 
-## Architecture
+## Design approach
 
-Current structure:
+ALF is built around small, independent capabilities.
 
-```text
+Where practical, components describe themselves rather than maintaining separate registration lists.
 
-ALF
- |
- +-- Identity
- |      |
- |      +-- identity.toml
- |
- +-- Commands
- |      |
- |      +-- Command registry
- |
- +-- Memory
- |      |
- |      +-- SQLite database
- |
- +-- System awareness
-        |
-        +-- Operating system information
+Examples:
 
-```
+- Commands provide metadata describing available actions
+- Subsystems can advertise capabilities
+- Health checks inspect ALF's internal structure
+- Runtime data is kept separate from source code
+
+The goal is not to create a complex framework, but to keep ALF understandable as it grows.
 
 ## Current limitations
 
@@ -126,7 +120,6 @@ Current limitations:
 Potential future developments:
 
 - Move runtime data to a standard user data location
-- Automatic capability reporting
 - Improved conversation interface
 - Memory search and maintenance tools
 - Local AI integration
diff --git a/WALL.md b/WALL.md
index 2afb680..e94fbdc 100644
--- a/WALL.md
+++ b/WALL.md
@@ -181,6 +181,7 @@ ALF should be able to inspect its own internal health.
 Initial scope:
 
 Health system
+
 - Audit capability providers
 - Report self-describing subsystems
 - Report non-reporting modules separately

- Limited conversation ability
- No natural language understanding
- No autonomous planning
- No external integrations
- Limited memory management tools

## Future milestones

Potential future developments:

- Move runtime data to a standard user data location
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
