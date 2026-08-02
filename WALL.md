# ALF Development Wall

Ideas and possibilities for future development.
Not commitments. Not a schedule.

---
## Principles

- Separate discourse from direction.

---

## Architecture

- Move runtime data from project directory to user data directory
- Separate configuration from identity
- Add application logging
- Review current module responsibilities
- Decide whether ALF runs as:
  - manual application
  - user service
  - daemon
- Improve error handling for missing external tools
- Consider automatic capability discovery
- Improve error handling for missing external tools
- Improve capability reporting
- Capability providers
  - Modules advertise capabilities through a standard interface
  - Capability system discovers providers dynamically
  - Providers are responsible for their own state reporting
  
## Memory

- Forget/delete commands
- Memory search
- Duplicate detection
- Memory metadata
- Memory maintenance tools

---

## Intelligence

- Local AI integration
- Natural conversation layer
- Automatic capability reporting
- Capability providers
  - Each module is responsible for reporting its own capability and state
  - Central capability system discovers and aggregates providers
  - Initial dynamic discovery implemented
  
  ---

## Interfaces

- SSH access from MacBook Pro

---

## Future Architecture
- Consider replacing WALL.md with structured project database
  Possible fields:
    - importance
    - difficulty
    - complexity
    - status
    - dependencies
    - notes
- Remote ALF client
- Possible graphical interface
- Voice interface
- Capability providers should report their own state.
---

## Personality

- Terminal presentation improvements
- Configurable greeting style
- Optional personality settings


