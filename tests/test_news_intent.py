from alf.news_intent import (
    NEWS_DEFAULT_WINDOW_DAYS,
    interpret_news_question,
    topic_terms,
)


def test_topic_terms_from_news_question():
    assert topic_terms("What is happening with SearXNG?") == ("searxng",)


def test_topic_terms_strip_possessives():
    assert topic_terms("What news about Alzheimer's research?") == (
        "alzheimers",
        "research",
    )


def test_topic_terms_return_at_most_four():
    assert len(topic_terms("one two three four five six seven eight")) == 4


def test_interpret_explicit_relative_window():
    intent = interpret_news_question(
        "What happened with SearXNG in the last 7 days?"
    )

    assert intent is not None
    assert intent.topics == ("searxng",)
    assert intent.window.days == 7


def test_interpret_ago_window():
    intent = interpret_news_question("What news about ALF 2 days ago?")

    assert intent is not None
    assert intent.topics == ("alf",)
    assert intent.window.days == 2


def test_interpret_defaults_for_recently():
    intent = interpret_news_question("What news on ALF recently?")

    assert intent is not None
    assert intent.window.days == NEWS_DEFAULT_WINDOW_DAYS


def test_interpret_defaults_for_news_vocabulary():
    intent = interpret_news_question("What news on SearXNG?")

    assert intent is not None
    assert intent.window.days == NEWS_DEFAULT_WINDOW_DAYS


def test_interpret_question_lead_required():
    assert interpret_news_question("SearXNG news") is None


def test_interpret_ignores_ambiguous_factual_question():
    assert interpret_news_question("Who is the current Prime Minister?") is None


def test_interpret_rejects_year_anchored_question():
    assert interpret_news_question("What happened with SearXNG in 2019?") is None


def test_interpret_rejects_memory_question():
    assert interpret_news_question("What did we decide about SearXNG?") is None


def test_interpret_rejects_topicless_question():
    assert interpret_news_question("What has happened recently?") is None