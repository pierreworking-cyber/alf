"""
ALF LLM knowledge qualification corpus.

These questions are used to determine whether the configured local LLM
is reliable enough to act as a general knowledge provider for ALF.

The corpus is deliberately independent of the LLM being tested.
"""

KNOWLEDGE_TESTS = [
    # ------------------------------------------------------------------
    # Core factual knowledge
    # ------------------------------------------------------------------

    {
        "question": "What is the capital of France?",
        "expected": ["Paris"],
        "type": "exact",
    },
    {
        "question": "What is the chemical symbol for gold?",
        "expected": ["Au"],
        "type": "exact",
    },
    {
        "question": "How many sides does a hexagon have?",
        "expected": ["6", "six", "A hexagon has six sides"],
        "type": "exact",
    },
    {
        "question": "Who wrote Pride and Prejudice?",
        "expected": ["Jane Austen"],
        "type": "exact",
    },
    {
        "question": "What is the largest planet in the Solar System?",
        "expected": ["Jupiter"],
        "type": "exact",
    },

    # ------------------------------------------------------------------
    # Science
    # ------------------------------------------------------------------

    {
        "question": "What is the chemical formula for water?",
        "expected": ["H2O", "H₂O"],
        "type": "exact",
    },
    {
        "question": "What is the speed of light in a vacuum?",
        "expected": [
            "299792458 m/s",
            "299,792,458 m/s",
            "299792458 metres per second",
            "299,792,458 metres per second",
            "299792458 meters per second",
            "299,792,458 meters per second",
        ],
        "type": "contains",
    },
    {
        "question": "Which planet is known for its prominent ring system?",
        "expected": ["Saturn"],
        "type": "exact",
    },
    {
        "question": "What force causes objects to fall toward Earth?",
        "expected": ["gravity", "gravitational force"],
        "type": "contains",
    },
    {
        "question": "How many pairs of chromosomes does a typical human have?",
        "expected": ["23 pairs", "23"],
        "type": "contains",
    },

    # ------------------------------------------------------------------
    # History and geography
    # ------------------------------------------------------------------

    {
        "question": "In what year did World War II end?",
        "expected": ["1945"],
        "type": "contains",
    },
    {
        "question": "What is the capital of Australia?",
        "expected": ["Canberra"],
        "type": "exact",
    },
    {
        "question": "What is the longest river entirely within the United Kingdom?",
        "expected": ["River Severn", "Severn"],
        "type": "contains",
    },
    {
        "question": "In which country is Machu Picchu located?",
        "expected": ["Peru"],
        "type": "exact",
    },
    {
        "question": "Who was the first person to walk on the Moon?",
        "expected": ["Neil Armstrong"],
        "type": "exact",
    },

    # ------------------------------------------------------------------
    # Computing and Python
    # ------------------------------------------------------------------

    {
        "question": "What does CPU stand for?",
        "expected": ["Central Processing Unit"],
        "type": "contains",
    },
    {
        "question": "What does pytest -q mean?",
        "expected": [
            "quiet mode",
            "quiet output",
            "runs pytest in quiet mode",
            "pytest in quiet mode",
        ],
        "type": "contains",
    },
    {
        "question": "What data type does Python's len() function return?",
        "expected": ["int", "integer"],
        "type": "contains",
    },
    {
        "question": "What does Python's venv module provide?",
        "expected": [
            "virtual environment",
            "isolated virtual environment",
            "isolated Python environment",
            "isolated Python environments",
        ],
        "type": "contains",
    },
    {
        "question": "What does HTTP stand for?",
        "expected": ["Hypertext Transfer Protocol"],
        "type": "exact",
    },
]
