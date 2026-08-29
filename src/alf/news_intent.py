"""
Deterministic News question interpretation for ALF.

Recognises and interprets questions that ask about recent news for a
topic, without consulting the language model. Recognition is
deliberately conservative: a question is treated as News only when it
is question shaped, names an identifiable topic, and carries an
explicit recent time window or clear current-events vocabulary.
Ordinary factual questions fall through to ALF's existing routing so
they keep their usual routes.

The module owns the News time-window grammar and topic-term extraction
used by the router, the question engine, and the development CLI query
command.
"""

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

NEWS_DEFAULT_WINDOW_DAYS = 7

MAX_WINDOW_DAYS = 366

_UNIT_DAYS = {
    "hour": 1 / 24,
    "hours": 1 / 24,
    "day": 1,
    "days": 1,
    "week": 7,
    "weeks": 7,
    "month": 30,
    "months": 30,
}

_RELATIVE_WINDOW = re.compile(
    r"\b("
    r"in the last|over the last|during the last|for the last|"
    r"within the last|last|past|previous"
    r")\s+(\d+)\s+(hour|hours|day|days|week|weeks|month|months)\b",
    re.IGNORECASE,
)

_AGO_WINDOW = re.compile(
    r"\b(\d+)\s+(hour|hours|day|days|week|weeks|month|months)\s+ago\b",
    re.IGNORECASE,
)

_TODAY = re.compile(r"\btoday\b", re.IGNORECASE)

_YESTERDAY = re.compile(r"\byesterday\b", re.IGNORECASE)

_THIS_WEEK = re.compile(r"\bthis week\b", re.IGNORECASE)

_RECENTLY = re.compile(r"\b(recently|lately|of late)\b", re.IGNORECASE)

_QUESTION_LEAD = re.compile(
    r"^\s*(?:what|when|which|who|where|why|how|is|are|was|were|"
    r"does|did|has|have)\b",
    re.IGNORECASE,
)

_NEWS_MARKERS = re.compile(
    r"\b(?:news|headline|headlines|happened|happening|been up to|"
    r"going on|developments?)\b",
    re.IGNORECASE,
)

_MEMORY_GUARD = re.compile(
    r"\b(?:did we|did i|have we|we decided|we decide|we discussed|"
    r"we said|you said|you told|you mentioned|you discussed|"
    r"do you remember|do you recall)\b",
    re.IGNORECASE,
)

_YEAR_REFERENCE = re.compile(r"\b(?:19|20)\d{2}\b")

_MONTH_DAY_REFERENCE = re.compile(
    r"\b(?:january|february|march|april|may|june|july|august|"
    r"september|october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?\b",
    re.IGNORECASE,
)

_TOPIC_STOP_WORDS = frozenset(
    """
    a about after again against all am an and any are around as at
    be been being before but by can could did do does doing for from
    had has have having how i if in into is it its just may might more
    most my of off on only or our over shall should so some than that
    the their them then there these they this those through to under us
    was we were what when where which who whom why will with would you
    your been latest recent recently today yesterday last past previous
    ago news headline headlines happened happening happen happens
    occurred going on story stories said say says told update updates
    announced announcement coverage discussed discuss reporting report
    reports reported current week weeks day days hour hours month months
    year years monday tuesday wednesday thursday friday saturday sunday
    january february march april may june july august september october
    november december progress progressed progressing developments
    development up to doing
    """.split()
)


@dataclass(frozen=True)
class NewsWindow:
    """
    A News time window describing the question's requested recency.

    Attributes:
        start: The inclusive window start, or ``None`` when open-ended.
        end: The inclusive window end, or ``None`` when open-ended.
        days: The window length in whole days for display, or ``None``
            when the window is not a whole number of days.
    """

    start: datetime | None
    end: datetime | None
    days: int | None


@dataclass(frozen=True)
class NewsIntent:
    """
    A deterministically interpreted News question.

    Attributes:
        topics: The significant topic terms, in order.
        window: The requested recency window.
        original: The question as entered by the user.
    """

    topics: tuple[str, ...]
    window: NewsWindow
    original: str


def normalize_text(text):
    """
    Normalise text for topic matching.

    Text is lowercased and apostrophes are stripped so possessives such
    as "Alzheimer's" match their stems ("alzheimers").
    """

    return text.lower().replace("'", "").replace("’", "")


def topic_terms(text):
    """
    Return the significant topic terms from a phrase.

    Terms are normalised, lowercased, and filtered for stop words and
    request vocabulary. At most four terms are returned.

    Args:
        text: The phrase to extract topic terms from.

    Returns:
        A tuple of topic terms in order of appearance.
    """

    terms = []
    seen = set()

    for token in re.findall(r"[a-z0-9]+", normalize_text(text)):
        if token.isdigit() or token in _TOPIC_STOP_WORDS:
            continue

        if token in seen:
            continue

        seen.add(token)
        terms.append(token)

        if len(terms) == 4:
            break

    return tuple(terms)


def interpret_news_question(question):
    """
    Recognise and interpret a News question.

    Recognition is deterministic and conservative. A question is treated
    as News only when it is question shaped, expresses recent news for an
    identifiable topic, and does not look like a memory question or a
    question anchored to a specific past date.

    Args:
        question: The user's question.

    Returns:
        A ``NewsIntent`` when the question clearly asks about recent news
        for a topic; otherwise ``None`` so the question is routed
        normally.
    """

    text = " ".join(question.split())

    if not text or not _QUESTION_LEAD.match(text):
        return None

    if _MEMORY_GUARD.search(text):
        return None

    if _has_past_date(text):
        return None

    now = datetime.now(UTC)

    interpretation = _interpret_window(text, now)

    if interpretation is None:
        return None

    window, remaining = interpretation

    topics = topic_terms(remaining)

    if not topics:
        return None

    return NewsIntent(topics=topics, window=window, original=question)


def _has_past_date(text):
    """
    Return whether the text references a specific past date.

    Questions anchored to specific past dates or years are treated as
    historical rather than recent-news questions, so they are not routed
    to News.
    """

    return (
        _YEAR_REFERENCE.search(text) is not None
        or _MONTH_DAY_REFERENCE.search(text) is not None
    )


def _interpret_window(text, now):
    """
    Resolve an explicit recency window, or default for news vocabulary.

    Returns a ``(NewsWindow, remaining text)`` pair when the question's
    window is known, otherwise ``None``.
    """

    match = _RELATIVE_WINDOW.search(text)

    if match:
        days = int(match.group(2)) * _UNIT_DAYS[match.group(3)]

        if 0 < days <= MAX_WINDOW_DAYS:
            return (
                _window(now - timedelta(days=days), now, days),
                _trim(text, match),
            )

    match = _AGO_WINDOW.search(text)

    if match:
        days = int(match.group(1)) * _UNIT_DAYS[match.group(2)]

        if 0 < days <= MAX_WINDOW_DAYS:
            return (
                _window(now - timedelta(days=days), now, days),
                _trim(text, match),
            )

    match = _TODAY.search(text)

    if match:
        start = _start_of_day(now)
        return NewsWindow(start, now, 0), _trim(text, match)

    match = _YESTERDAY.search(text)

    if match:
        start = _start_of_day(now) - timedelta(days=1)
        return NewsWindow(start, now, 1), _trim(text, match)

    match = _THIS_WEEK.search(text)

    if match:
        start = _start_of_week(now)
        return (
            NewsWindow(start, now, (now - start).days),
            _trim(text, match),
        )

    match = _RECENTLY.search(text)

    if match:
        start = now - timedelta(days=NEWS_DEFAULT_WINDOW_DAYS)
        return (
            NewsWindow(start, now, NEWS_DEFAULT_WINDOW_DAYS),
            _trim(text, match),
        )

    if _NEWS_MARKERS.search(text):
        start = now - timedelta(days=NEWS_DEFAULT_WINDOW_DAYS)
        return NewsWindow(start, now, NEWS_DEFAULT_WINDOW_DAYS), text

    return None


def _window(start, end, days):
    """
    Build a NewsWindow, keeping whole days for display.
    """

    display = round(days) if days >= 1 else None

    return NewsWindow(start, end, display)


def _start_of_day(value):
    return value.replace(hour=0, minute=0, second=0, microsecond=0)


def _start_of_week(value):
    return _start_of_day(value) - timedelta(days=_start_of_day(value).weekday())


def _trim(text, match):
    return " ".join(
        (text[: match.start()] + " " + text[match.end():]).split()
    )