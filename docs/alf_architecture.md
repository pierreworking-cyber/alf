# ALF Architecture

> This diagram is a mental model of ALF's architecture.
>
> It is not a complete dependency graph.
>
> Update it when the architecture changes, not every commit.

```mermaid
flowchart TD

    P[Peter] --> T[Terminal]
    T --> M[main.py]

    M --> R["commands.run()"]

    R --> CMD["commands.py<br/>Command registry + metadata"]

    CMD --> FUNC["Command functions"]

    FUNC --> PRE["presentation.py"]

    TOML["identity.toml"] --> ID["identity.py"]

    ID --> ABOUT["get_about_information()"]

    CAP["capabilities.py"] --> DISC["discover_capabilities()"]

    DISC --> MEM["memory.py"]
    DISC --> SYS["system.py"]
    DISC --> GIT["git.py"]
    DISC --> CMD

    MEM --> SQLITE["SQLite database"]

    ABOUT --> DISC
    ABOUT --> PRE

    PRE --> OUT["ALF terminal output"]
```

## Core idea

ALF subsystems advertise themselves through capabilities.

A subsystem does not need to be manually registered.

It provides:

```python
def get_capability():
    ...
```

and ALF discovers it.

Current capability providers:

- `commands.py`
- `memory.py`
- `system.py`
- `git.py`

## Design principle

ALF should consume metadata rather than duplicate knowledge.

Interfaces should ask ALF:

> "What can you do?"

rather than maintain their own list of capabilities.
