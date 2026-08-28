"""Web tests for the mind map category API."""

import pytest

from alf import memory
from alf.web import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(memory, "DATABASE", tmp_path / "web.db")
    return app.test_client()


def _create_category(client, name):
    response = client.post(
        "/mindmap-categories",
        json={"name": name, "status": "active"},
    )
    assert response.status_code == 200
    return response.get_json()["id"]


def _category_names():
    return [category["name"] for category in memory.get_mindmap_categories()]


def test_renaming_category_to_existing_name_returns_conflict(client):
    _create_category(client, "House")
    _create_category(client, "Events")

    response = client.patch(
        "/mindmap-categories/2",
        json={"name": "House", "status": "active"},
    )

    assert response.status_code == 409
    assert _category_names() == ["House", "Events"]


def test_renaming_category_to_uncategorised_returns_conflict_when_row_exists(
    client,
):
    memory.create_mindmap_category("Uncategorised")
    _create_category(client, "House")

    response = client.patch(
        "/mindmap-categories/2",
        json={"name": "Uncategorised", "status": "active"},
    )

    assert response.status_code == 409


def test_renaming_category_to_uncategorised_returns_conflict_without_row(
    client,
):
    _create_category(client, "House")

    response = client.patch(
        "/mindmap-categories/1",
        json={"name": "Uncategorised", "status": "active"},
    )

    assert response.status_code == 409


def test_renaming_category_succeeds(client):
    _create_category(client, "House")

    response = client.patch(
        "/mindmap-categories/1",
        json={"name": "Work", "status": "active"},
    )

    assert response.status_code == 200
    assert response.get_json() == {"updated": True}
    assert _category_names() == ["Work"]


def test_renaming_missing_category_returns_not_found(client):
    response = client.patch(
        "/mindmap-categories/9999",
        json={"name": "Work", "status": "active"},
    )

    assert response.status_code == 404


def _create_mindmap(client):
    _create_category(client, "House")

    response = client.post(
        "/mindmaps/save",
        json={
            "category": "House",
            "name": "Plans",
            "content": '{"meta":{"name":"Plans"},"format":"node_array","data":[]}',
        },
    )
    assert response.status_code == 200
    return response.get_json()["id"]


def test_deleting_mindmap_via_delete_endpoint(client):
    mindmap_id = _create_mindmap(client)

    response = client.post(f"/mindmaps/{mindmap_id}/delete")

    assert response.status_code == 200
    assert response.get_json() == {"deleted": True}
    assert memory.get_mindmap(mindmap_id) is None


def test_deleting_missing_mindmap_via_delete_endpoint(client):
    response = client.post("/mindmaps/9999/delete")

    assert response.status_code == 404


def test_old_mindmap_archive_endpoint_is_removed(client):
    created = _create_mindmap(client)

    response = client.post(f"/mindmaps/{created}/archive")

    assert response.status_code == 404