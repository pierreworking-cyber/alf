import pytest

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


@pytest.mark.parametrize(
    ("number", "days"),
    [
        ("one", 1),
        ("two", 2),
        ("three", 3),
        ("four", 4),
        ("five", 5),
        ("six", 6),
        ("seven", 7),
    ],
)
def test_interpret_spelled_out_relative_window(number, days):
    intent = interpret_news_question(
        f"What happened with SearXNG in the last {number} days?"
    )

    assert intent is not None
    assert intent.topics == ("searxng",)
    assert intent.window.days == days


def test_interpret_spelled_out_relative_window_keeps_digit_behaviour():
    intent = interpret_news_question(
        "What happened with SearXNG in the last 2 days?"
    )

    assert intent is not None
    assert intent.topics == ("searxng",)
    assert intent.window.days == 2


def test_interpret_spelled_out_number_not_left_in_topic():
    intent = interpret_news_question(
        "What happened with SearXNG in the last two days?"
    )

    assert intent is not None
    assert intent.topics == ("searxng",)
    assert "two" not in intent.topics


def test_interpret_spelled_out_ago_window():
    intent = interpret_news_question("What news about ALF three days ago?")

    assert intent is not None
    assert intent.topics == ("alf",)
    assert intent.window.days == 3


def test_interpret_any_news_with_recent_window():
    intent = interpret_news_question("Any news about Trump recently?")

    assert intent is not None
    assert intent.topics == ("trump",)
    assert intent.window.days == NEWS_DEFAULT_WINDOW_DAYS


def test_interpret_any_news_on_topic():
    intent = interpret_news_question("Any news on Trump?")

    assert intent is not None
    assert intent.topics == ("trump",)
    assert intent.window.days == NEWS_DEFAULT_WINDOW_DAYS


def test_interpret_any_lead_requires_news_construction():
    assert interpret_news_question("Any chance of rain today?") is None
    assert interpret_news_question("Any idea what the weather is like?") is None


def test_interpret_person_question_with_explicit_window_is_news():
    intent = interpret_news_question(
        "What has Trump been up to in the last two days?"
    )

    assert intent is not None
    assert intent.topics == ("trump",)
    assert intent.window.days == 2


def test_interpret_person_said_recently_rejected():
    assert interpret_news_question(
        "What has Boris Johnson said recently about the economy?"
    ) is None


def test_interpret_person_been_up_to_recently_rejected():
    assert interpret_news_question(
        "What has Boris Johnson been up to recently?"
    ) is None


def test_interpret_person_yesterday_rejected():
    assert interpret_news_question("What did Boris Johnson do yesterday?") is None


def test_interpret_current_treatment_rejected():
    assert interpret_news_question(
        "What is the current treatment for Alzheimer's?"
    ) is None


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