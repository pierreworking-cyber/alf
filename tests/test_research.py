from alf.research import (
    build_documents,
    build_source_diverse_pool,
    domain,
    rank_passages,
    select_evidence,
    split_into_passages,
)


def test_domain_normalises_www():
    assert domain("https://www.gov.uk/example") == "gov.uk"


def test_split_into_passages_respects_word_limit():
    text = " ".join(f"word{i}" for i in range(250))

    passages = split_into_passages(text, max_words=100)

    assert len(passages) == 3
    assert len(passages[0].split()) == 100
    assert len(passages[1].split()) == 100
    assert len(passages[2].split()) == 50


def test_split_into_passages_handles_empty_text():
    assert split_into_passages("") == []


def test_rank_passages_puts_relevant_passage_first():
    documents = [
        {
            "title": "Irrelevant",
            "url": "https://example.com/irrelevant",
            "domain": "example.com",
            "passages": [
               "Germany's largest city is Berlin, located in the northeastern part of the country.",],
        },
        {
            "title": "Relevant",
            "url": "https://example.org/relevant",
            "domain": "example.org",
            "passages": [
                "Paris is the capital city of France and serves as the country's political centre.",
            ],
        },
    ]

    ranked = rank_passages(
        "What is the capital of France?",
        documents,
    )

    assert ranked[0]["domain"] == "example.org"
    assert "Paris" in ranked[0]["text"]


def test_rank_passages_handles_no_passages():
    assert rank_passages(
        "What is the capital of France?",
        [],
    ) == []


def test_source_diverse_pool_keeps_multiple_domains():
    documents = [
        {
            "title": "Source A",
            "url": "https://a.example/1",
            "domain": "a.example",
            "passages": [
                "France has a population of about 68 million people.",
            ],
        },
        {
            "title": "Source B",
            "url": "https://b.example/1",
            "domain": "b.example",
            "passages": [
                "Paris is the capital city of France.",
            ],
        },
    ]

    ranked = rank_passages(
        "What is the capital of France?",
        documents,
    )

    selected = build_source_diverse_pool(
        documents,
        ranked,
    )

    domains = {candidate["domain"] for candidate in selected}

    assert "a.example" in domains
    assert "b.example" in domains


def test_source_diverse_pool_does_not_duplicate_domains():
    documents = [
        {
            "title": "Source A",
            "url": "https://a.example/1",
            "domain": "a.example",
            "passages": [
                "France has a population of about 68 million people.",
                "Paris is the capital city of France.",
            ],
        },
        {
            "title": "Source B",
            "url": "https://b.example/1",
            "domain": "b.example",
            "passages": [
                "Paris is the capital city of France.",
            ],
        },
    ]

    ranked = rank_passages(
        "What is the capital of France?",
        documents,
    )

    selected = build_source_diverse_pool(
        documents,
        ranked,
    )

    domains = [candidate["domain"] for candidate in selected]

    assert len(domains) == len(set(domains))


def test_build_documents_skips_failed_fetch(monkeypatch):
    results = [
        {
            "title": "Good",
            "url": "https://good.example/page",
        },
        {
            "title": "Bad",
            "url": "https://bad.example/page",
        },
    ]

    def fake_fetch(url):
        if "bad.example" in url:
            raise OSError("fetch failed")
        return "This page contains useful information."

    monkeypatch.setattr(
        "alf.research.fetch_and_extract",
        fake_fetch,
    )

    documents = build_documents(results)

    assert len(documents) == 1
    assert documents[0]["domain"] == "good.example"


def test_select_evidence_returns_requested_candidates():
    candidates = [
        {"domain": "a.example", "text": "A"},
        {"domain": "b.example", "text": "B"},
        {"domain": "c.example", "text": "C"},
    ]

    evaluation = {
        "supporting_candidates": [1, 3],
    }

    selected = select_evidence(
        candidates,
        evaluation,
    )

    assert selected == [
        candidates[0],
        candidates[2],
    ]


def test_select_evidence_returns_empty_for_no_support():
    candidates = [
        {"domain": "a.example", "text": "A"},
    ]

    evaluation = {
        "supporting_candidates": [],
    }

    assert select_evidence(
        candidates,
        evaluation,
    ) == []

 
def test_evaluate_evidence_passes_question_and_candidates(monkeypatch):
    from alf.research import evaluate_evidence

    captured = {}

    def fake_generate_json(prompt):
        captured["prompt"] = prompt
        return {
            "answer": "Paris",
            "confidence": "high",
            "supporting_candidates": [1],
            "rejected_candidates": [2],
            "reason": "Candidate 1 directly supports the answer.",
        }

    monkeypatch.setattr(
        "alf.research.generate_json",
        fake_generate_json,
    )

    candidates = [
        {
            "domain": "gov.example",
            "title": "Official information",
            "url": "https://gov.example/paris",
            "text": "Paris is the capital of France.",
        },
        {
            "domain": "example.com",
            "title": "Unrelated information",
            "url": "https://example.com/page",
            "text": "Berlin is the capital of Germany.",
        },
    ]

    result = evaluate_evidence(
        "What is the capital of France?",
        candidates,
    )

    assert "What is the capital of France?" in captured["prompt"]
    assert "Paris is the capital of France." in captured["prompt"]
    assert "Berlin is the capital of Germany." in captured["prompt"]
    assert result["supporting_candidates"] == [1]
    assert result["rejected_candidates"] == [2]


def test_evaluate_evidence_can_return_no_support(monkeypatch):
    from alf.research import evaluate_evidence

    monkeypatch.setattr(
        "alf.research.generate_json",
        lambda prompt: {
            "answer": "Insufficient evidence.",
            "confidence": "low",
            "supporting_candidates": [],
            "rejected_candidates": [1],
            "reason": "The candidate does not support the claim.",
        },
    )

    result = evaluate_evidence(
        "What was the official name of the fictional Ministry of Time?",
        [
            {
                "domain": "example.com",
                "title": "Unrelated page",
                "url": "https://example.com/page",
                "text": "This page discusses clocks and calendars.",
            },
        ],
    )

    assert result["supporting_candidates"] == []
    assert result["confidence"] == "low"

def test_evaluate_evidence_distinguishes_reported_theory_from_supported_claim(
    monkeypatch,
):
    import alf.research as research_module

    captured_prompt = {}

    def fake_generate_json(prompt):
        captured_prompt["prompt"] = prompt

        return {
            "answer": "The evidence supports multiple interacting causes.",
            "confidence": "high",
            "supporting_candidates": [1],
            "rejected_candidates": [2],
            "reason": (
                "Candidate 2 reports a historical theory but does not "
                "establish it as a current consensus."
            ),
        }

    monkeypatch.setattr(
        research_module,
        "generate_json",
        fake_generate_json,
    )

    candidates = [
        {
            "domain": "example.org",
            "title": "Modern historical synthesis",
            "url": "https://example.org/modern",
            "text": (
                "Modern scholarship identifies several interacting "
                "political, economic and environmental factors."
            ),
        },
        {
            "domain": "example-history.com",
            "title": "Historical theories",
            "url": "https://example-history.com/theories",
            "text": (
                "Gibbon argued that Christianity contributed to "
                "the decline of Rome."
            ),
        },
    ]

    evaluation = research_module.evaluate_evidence(
        "Why did the Roman Empire fall?",
        candidates,
    )

    assert evaluation["supporting_candidates"] == [1]
    assert evaluation["rejected_candidates"] == [2]

    assert (
        "merely mentioning" in captured_prompt["prompt"]
        or "reporting" in captured_prompt["prompt"]
    )


def test_evaluate_evidence_prompt_requires_claims_to_be_supported(
    monkeypatch,
):
    import alf.research as research_module

    captured_prompt = {}

    def fake_generate_json(prompt):
        captured_prompt["prompt"] = prompt

        return {
            "answer": "Insufficient evidence.",
            "confidence": "low",
            "supporting_candidates": [],
            "rejected_candidates": [1],
            "reason": "The source does not establish the claim.",
        }

    monkeypatch.setattr(
        research_module,
        "generate_json",
        fake_generate_json,
    )

    candidates = [
        {
            "domain": "example.com",
            "title": "A weak claim",
            "url": "https://example.com/claim",
            "text": (
                "Some people believe that X caused the event."
            ),
        },
    ]

    evaluation = research_module.evaluate_evidence(
        "What caused the event?",
        candidates,
    )

    assert evaluation["supporting_candidates"] == []
    assert evaluation["confidence"] == "low"

    prompt = captured_prompt["prompt"]

    assert "does NOT establish" in prompt
    assert "disputed" in prompt
    assert "speculative" in prompt    

def test_build_source_diverse_pool_excludes_zero_score_candidates():
    import alf.research as research_module

    documents = [
        {
            "domain": "relevant.example",
            "title": "Relevant source",
            "url": "https://relevant.example/article",
            "passages": [
                "The Roman Empire experienced political instability."
            ],
        },
        {
            "domain": "irrelevant.example",
            "title": "Irrelevant source",
            "url": "https://irrelevant.example/article",
            "passages": [
                "This page is about World War II and nothing else."
            ],
        },
    ]

    ranked_passages = [
        {
            "domain": "relevant.example",
            "title": "Relevant source",
            "url": "https://relevant.example/article",
            "text": "The Roman Empire experienced political instability.",
            "score": 5.0,
        },
        {
            "domain": "irrelevant.example",
            "title": "Irrelevant source",
            "url": "https://irrelevant.example/article",
            "text": "This page is about World War II and nothing else.",
            "score": 0.0,
        },
    ]

    selected = research_module.build_source_diverse_pool(
        documents,
        ranked_passages,
    )

    domains = [candidate["domain"] for candidate in selected]

    assert "relevant.example" in domains
    assert "irrelevant.example" not in domains


def test_search_web_rejects_duckduckgo_ad_redirects(monkeypatch):
    import alf.research as research_module

    html = """
    <div class="result">
        <a class="result__a"
           href="https://example.com/good-page">
            Good result
        </a>
    </div>

    <div class="result">
        <a class="result__a"
           href="https://duckduckgo.com/y.js?ad_domain=example.com">
            Advert
        </a>
    </div>
    """

    class FakeResponse:
        def read(self):
            return html.encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(
        research_module,
        "urlopen",
        lambda *args, **kwargs: FakeResponse(),
    )

    results = research_module.search_web(
        "Why did the Roman Empire fall?"
    )

    urls = [result["url"] for result in results]

    assert "https://example.com/good-page" in urls
    assert not any(
        url.startswith("https://duckduckgo.com/")
        for url in urls
    )    
