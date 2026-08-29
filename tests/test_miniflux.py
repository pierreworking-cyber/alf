import io
from urllib.error import HTTPError, URLError

import pytest

from alf import miniflux
from alf.miniflux import DEFAULT_TIMEOUT, Miniflux, MinifluxError
from tests.fake_miniflux import FakeMiniflux


@pytest.fixture
def fake():
    return FakeMiniflux()


@pytest.fixture
def client(fake):
    return Miniflux(
        "http://miniflux.test",
        "test-api-key",
        transport=fake.transport(),
    )


def test_version_returns_raw_version(fake, client):
    assert client.version() == {"version": "2.3.3"}


def test_requests_send_api_key_and_user_agent(fake, client):
    client.get_categories()

    request = fake.requests[0]

    assert request["method"] == "GET"
    assert request["path"] == "/v1/categories"
    assert request["headers"]["X-Auth-Token"] == "test-api-key"
    assert request["headers"]["User-Agent"] == "alf-news/0.3.0"


def test_base_url_trailing_slash_is_normalised(fake):
    client = Miniflux(
        "http://miniflux.test/",
        "test-api-key",
        transport=fake.transport(),
    )

    client.version()

    assert fake.requests[0]["path"] == "/v1/version"


def test_me_confirms_authenticated_user(fake, client):
    assert client.me() == {"id": 1, "username": "alf"}


def test_get_categories_returns_list(fake, client):
    fake.add_category("Politics")
    fake.add_category("World")

    assert [c["title"] for c in client.get_categories()] == [
        "Politics",
        "World",
    ]


def test_create_category_sends_title_payload(fake, client):
    category = client.create_category("Science")

    assert category["id"] == 1
    assert category["title"] == "Science"

    request = fake.requests[-1]

    assert request["payload"] == {"title": "Science"}
    assert request["headers"]["Content-Type"] == "application/json"


def test_create_category_requires_title(fake, client):
    with pytest.raises(MinifluxError) as excinfo:
        client.create_category("")

    assert "400" in str(excinfo.value)


def test_create_feed_returns_feed_with_category(fake, client):
    category = client.create_category("World")

    feed = client.create_feed(
        "https://www.bbc.co.uk/feeds/world.xml",
        category["id"],
    )

    assert feed["id"] == 1
    assert feed["feed_url"] == "https://www.bbc.co.uk/feeds/world.xml"
    assert feed["category_id"] == category["id"]

    assert fake.requests[-1]["payload"] == {
        "feed_url": "https://www.bbc.co.uk/feeds/world.xml",
        "category_id": 1,
    }


def test_create_feed_rejects_duplicates(fake, client):
    category = client.create_category("World")
    feed_url = "https://www.bbc.co.uk/feeds/world.xml"

    client.create_feed(feed_url, category["id"])

    with pytest.raises(MinifluxError) as excinfo:
        client.create_feed(feed_url, category["id"])

    assert "already exists" in str(excinfo.value)


def test_get_feeds_lists_and_filters_by_category(fake, client):
    world = client.create_category("World")
    sport = client.create_category("Sport")

    client.create_feed("https://example.com/world", world["id"])
    client.create_feed("https://example.com/football", sport["id"])

    all_feeds = client.get_feeds()

    assert [f["feed_url"] for f in all_feeds] == [
        "https://example.com/world",
        "https://example.com/football",
    ]

    sport_feeds = client.get_feeds(category_id=sport["id"])

    assert [f["feed_url"] for f in sport_feeds] == [
        "https://example.com/football",
    ]
    assert fake.requests[-1]["path"] == f"/v1/categories/{sport['id']}/feeds"


def test_refresh_then_get_entries_returns_newest_first(fake, client):
    category = client.create_category("World")
    feed = client.create_feed("https://example.com/feed", category["id"])

    fake.schedule_entries(
        feed["id"],
        [
            {
                "title": "Old story",
                "url": "https://example.com/old",
                "published_at": 100,
            },
            {
                "title": "New story",
                "url": "https://example.com/new",
                "published_at": 300,
            },
        ],
    )

    assert client.refresh_feed(feed["id"]) is None

    entries = client.get_entries(category_id=category["id"])

    assert [e["title"] for e in entries] == ["New story", "Old story"]
    assert entries[0]["feed_id"] == feed["id"]
    assert entries[0]["published_at"] == "1970-01-01T00:05:00Z"


def test_refreshing_twice_does_not_reemit_entries(fake, client):
    category = client.create_category("World")
    feed = client.create_feed("https://example.com/feed", category["id"])

    fake.schedule_entries(
        feed["id"],
        [{"title": "Only story", "url": "https://example.com/only"}],
    )

    client.refresh_feed(feed["id"])
    client.refresh_feed(feed["id"])

    entries = client.get_entries(category_id=category["id"])

    assert [e["id"] for e in entries] == [1]


def test_get_entries_filters_by_published_after(fake, client):
    category = client.create_category("World")
    feed = client.create_feed("https://example.com/feed", category["id"])

    fake.schedule_entries(
        feed["id"],
        [
            {
                "title": "First",
                "url": "https://example.com/first",
                "published_at": 100,
            },
            {
                "title": "Second",
                "url": "https://example.com/second",
                "published_at": 200,
            },
            {
                "title": "Third",
                "url": "https://example.com/third",
                "published_at": 300,
            },
        ],
    )

    client.refresh_feed(feed["id"])

    entries = client.get_entries(
        category_id=category["id"],
        published_after=200,
    )

    assert [e["title"] for e in entries] == ["Third", "Second"]
    assert fake.requests[-1]["query"]["published_after"] == "200"


def test_get_entries_paginates(fake, client):
    category = client.create_category("World")
    feed = client.create_feed("https://example.com/feed", category["id"])

    fake.schedule_entries(
        feed["id"],
        [
            {
                "title": f"Story {number}",
                "url": f"https://example.com/{number}",
            }
            for number in range(1, 6)
        ],
    )

    client.refresh_feed(feed["id"])

    first = client.get_entries(limit=2)
    second = client.get_entries(limit=2, offset=2)

    assert [e["id"] for e in first] == [5, 4]
    assert [e["id"] for e in second] == [3, 2]
    assert "limit" in fake.requests[-1]["query"]


def test_refresh_unknown_feed_raises(fake, client):
    with pytest.raises(MinifluxError) as excinfo:
        client.refresh_feed(999)

    assert "404" in str(excinfo.value)
    assert "Feed not found" in str(excinfo.value)


def test_bad_api_key_raises_authentication_error(fake):
    client = Miniflux(
        "http://miniflux.test",
        "wrong-key",
        transport=fake.transport(),
    )

    with pytest.raises(MinifluxError) as excinfo:
        client.get_categories()

    assert "401" in str(excinfo.value)


def test_connection_failure_raises_miniflux_error():
    def unreachable(method, url, headers, payload, timeout):
        raise MinifluxError("Could not connect to Miniflux: refused")

    client = Miniflux(
        "http://miniflux.test",
        "test-api-key",
        transport=unreachable,
    )

    with pytest.raises(MinifluxError, match="refused"):
        client.version()


def test_invalid_response_body_raises_miniflux_error():
    def broken(method, url, headers, payload, timeout):
        return 200, b"<html>not json</html>"

    client = Miniflux(
        "http://miniflux.test",
        "test-api-key",
        transport=broken,
    )

    with pytest.raises(MinifluxError, match="invalid response"):
        client.version()


def test_default_transport_returns_http_error_status(monkeypatch):
    body = b'{"error_message": "Feed not found"}'

    def raise_http_error(*args, **kwargs):
        raise HTTPError(
            "http://miniflux.test/v1/feeds/1/refresh",
            404,
            "Not Found",
            {},
            io.BytesIO(body),
        )

    monkeypatch.setattr(miniflux, "urlopen", raise_http_error)

    status, response = miniflux._default_transport(
        "PUT",
        "http://miniflux.test/v1/feeds/1/refresh",
        {},
        None,
        DEFAULT_TIMEOUT,
    )

    assert status == 404
    assert response == body


def test_default_transport_maps_connection_errors(monkeypatch):
    def raise_connection_error(*args, **kwargs):
        raise URLError("connection refused")

    monkeypatch.setattr(miniflux, "urlopen", raise_connection_error)

    with pytest.raises(MinifluxError, match="Could not connect"):
        miniflux._default_transport(
            "GET",
            "http://miniflux.test/v1/version",
            {},
            None,
            DEFAULT_TIMEOUT,
        )


def test_purged_entries_reuse_miniflux_ids(fake, client):
    category = client.create_category("World")
    feed = client.create_feed("https://example.com/feed", category["id"])

    fake.schedule_entries(
        feed["id"],
        [{"title": "First run", "url": "https://example.com/a"}],
    )

    client.refresh_feed(feed["id"])

    assert [e["id"] for e in client.get_entries()] == [1]

    fake.purge_entries()

    fake.schedule_entries(
        feed["id"],
        [{"title": "Second run", "url": "https://example.com/b"}],
    )

    client.refresh_feed(feed["id"])

    entries = client.get_entries()

    assert [e["id"] for e in entries] == [1]
    assert entries[0]["title"] == "Second run"


def test_fake_rejects_requests_without_api_key():
    fake = FakeMiniflux(api_key="secret")

    status, body = fake.handle(
        "GET",
        "/v1/categories",
        headers={},
        payload=None,
    )

    assert status == 401
    assert body["error_message"] == "Authentication failure"