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
- Improve capability reporting
- Capability providers
  - Modules advertise capabilities through a standard interface
  - Capability system discovers providers dynamically
  - Providers are responsible for their own state reporting
  - Initial dynamic discovery implemented
  - Consider module self-description
  - Allow ALF to understand its own internal structure
  - Separate module identity from user-facing capabilities
- Review small utility modules
  - Some modules may contain behaviour rather than a true domain responsibility
  - Revisit time.py / greeting ownership as ALF personality develops
  - Review naming of presentation functions as reports grow
    - describe_identity may become describe_about or similar
 - Review command metadata
  - Commands use namespaced IDs
  - Consider richer command descriptions and argument metadata
  - Allow ALF to explain command usage dynamically
  - Review naming consistency
    - Decide singular/plural conventions for IDs
    - Examples: command vs commands, memory vs memories
  - Usage strings should expose optional arguments
    - Consider richer command descriptions and argument metadata
    - Allow ALF to explain command usage dynamically
  - Review command catalogue structure
    - Consider whether discovered objects should use list-based representations
    - Keep lookup structures separate from presentation structures
  
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
  
  ---

## Interfaces

- SSH access from MacBook Pro
- Add expandable capability detail reporting
- Consider verbose output modes for structured capability information

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

## Capability system thoughts

- Capability identity should eventually be separate from display name
- Capability failures should be visible, not silently ignored
- Avoid unnecessary metadata requiring manual maintenance
- Consider optional dependency reporting
- Keep capability contracts flexible
- Capability machine identity should be separate from display name
- Capability discovery should preserve both available capabilities and discovery warnings
