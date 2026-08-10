"""
ALF command catalogue.

Contains command metadata exposed by ALF.
"""

commands = {
    "help": {
        "id": "command.help",
        "help": "Show command help.",
        "usage": "alf help [command]",
        "examples": [
            "alf help",
            "alf help search",
            "alf help remember",
        ],
    },
    "remember": {
        "id": "memory.add",
        "help": "Add a memory.",
        "usage": 'alf remember <category> "text" [--relate <ids>]',
        "notes": [
            "View available categories with: alf categories",
            "Relate this memory to existing memory IDs.",
        ],
        "examples": [
            'alf remember preference "Peter prefers dogs"',
            'alf remember preference "Peter prefers Labradors" --relate 4,12',
        ],
    },
    "memories": {
        "id": "memory.list",
        "help": "Recall previous memories.",
        "usage": "alf memories",
        "options": {
            "--all": "Include archived memories.",
            "--category <name>": "Restrict results to a memory category.",
            "--group <name>": "Group memories by a field.",
        },
        "examples": [
            "alf memories",
            "alf memories --all",
            "alf memories --category preference",
            "alf memories --group category",
        ],
    },
    "categories": {
        "id": "memory.categories",
        "help": "Show memory categories.",
        "usage": "alf categories",
    },
    "memory": {
        "id": "memory.show",
        "help": "Show a single memory.",
        "usage": "alf memory <id>",
        "examples": [
            "alf memory 11",
        ],
    },
    "history": {
        "id": "memory.history",
        "help": "Show memory history.",
        "usage": "alf history <id>",
        "examples": [
            "alf history 11",
        ],
    },
    "health": {
        "id": "system.health",
        "help": "Show ALF internal health information.",
        "usage": "alf health [--details]",
        "options": {
            "--details": "Show detailed health information.",
        },
    },
    "about": {
        "id": "identity.about",
        "help": "Explain what ALF is.",
        "usage": "alf about [--details]",
        "options": {
            "--details": "Show extended identity information.",
        },
        "examples": [
            "alf about",
            "alf about --details",
        ],
    },
    "archive": {
        "id": "memory.archive",
        "help": "Archive a memory.",
        "usage": "alf archive <id>",
        "examples": [
            "alf archive 11",
        ],
    },
    "forget": {
        "id": "command.forget",
        "help": "Forget a memory while preserving its identity.",
        "usage": "alf forget <id>",
        "examples": [
            "alf forget 12",
        ],
    },
    "version": {
        "id": "identity.version",
        "help": "Show ALF version.",
        "usage": "alf version",
    },
    "search": {
        "id": "memory.search",
        "help": "Search memories.",
        "usage": 'alf search "text"',
        "options": {
            "--all": "Include archived memories.",
            "--category <name>": "Restrict results to a memory category.",
        },
        "examples": [
            "alf search bananas",
            "alf search bananas --all",
            "alf search Peter --category preference",
        ],
    },
    "question": {
        "id": "llm.question",
        "help": "Ask ALF a question.",
        "usage": 'alf question "text"',
        "examples": [
            'alf question "What is the capital of Morocco?"',
            'alf question "Why does the Moon look larger near the horizon?"',
        ],
    },
}
