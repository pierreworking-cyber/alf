"""
Initial ALF interpreter qualification corpus.

This corpus evaluates the local LLM as an interpreter of user questions,
rather than as an independent source of factual knowledge.

The first version is deliberately small and exploratory. Results will be
reviewed before the corpus and its evaluation rules are considered stable.
"""

INTERPRETER_TESTS = [
    {
        "id": "01",
        "name": "clear question — pass through",
        "question": "What are microbes?",
        "mode": "preserve",
        "required": ["What are microbes?"],
    },
    {
        "id": "02",
        "name": "clear technical question — pass through",
        "question": "What does Python's venv module provide?",
        "mode": "preserve",
        "required": ["What does Python's venv module provide?"],
    },
    {
        "id": "03",
        "name": "awkward wording — reformulate",
        "question": (
            'Why do some Python function structures terminate elements with "," '
            "and some do not?"
        ),
        "mode": "reformulate",
        "required": ["Python", ","],
    },
    {
        "id": "04",
        "name": "specific terminology — preserve",
        "question": "Why does Python use trailing commas in function calls?",
        "mode": "preserve",
        "required": ["Python", "trailing commas", "function calls"],
    },
    {
        "id": "05",
        "name": "command option as subject matter",
        "question": "What Linux commands have the switch -v?",
        "mode": "preserve",
        "required": ["Linux", "-v"],
    },
    {
        "id": "06",
        "name": "pytest option as subject matter",
        "question": "What does pytest -q mean?",
        "mode": "preserve",
        "required": ["pytest", "-q"],
    },
    {
        "id": "07",
        "name": "quoted punctuation",
        "question": 'Why does Python use "," in function calls?',
        "mode": "preserve",
        "required": ["Python", '","'],
    },
    {
        "id": "08",
        "name": "technical identifier with apostrophe",
        "question": "What does Python's len() function return?",
        "mode": "preserve",
        "required": ["Python", "len()"],
    },
    {
        "id": "09",
        "name": "awkward research wording — reformulate",
        "question": (
            "Why moon looks bigger with eyes but small in smartphone photograph?"
        ),
        "mode": "reformulate",
        "required": ["moon", "eye", "smartphone", "photograph"],
    },
    {
        "id": "10",
        "name": "ambiguous question",
        "question": "Why does it do that?",
        "mode": "reformulate",
        "required": [],
    },
]
