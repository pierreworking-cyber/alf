import asyncio

from textual.widgets import ListView, RadioSet

from alf.command_catalogue import commands
from alf.tui import ALFTUI, DeleteMemoryConfirm


def make_sample_memory(memory_id=7, content=None, status="active"):
    return {
        "id": memory_id,
        "created": "2026-01-01 00:00:00",
        "category": "note",
        "status": status,
        "content": content or "A memory that survives the test session.",
        "previous_memory_id": None,
        "related_memory_ids": None,
    }


def make_memory_fakes(
    monkeypatch,
    memories=None,
    remember_result=True,
    related_candidates=(),
):
    """Install fake memory functions so TUI tests avoid the real database.

    Mutation calls are recorded on the returned store so tests can assert
    what the TUI asked ALF to do.
    """

    if memories is None:
        memories = [make_sample_memory()]

    store = {
        "memories": memories,
        "deleted": [],
        "remembered": [],
        "updated": [],
        "archived": [],
        "restored": [],
    }

    async def fake_sleep(_seconds):
        return None

    def fake_find_related_memory_candidates(content, limit=5):
        return list(related_candidates)

    def fake_get_memories(options=None):
        if options is not None and options.get("include_archived"):
            return list(store["memories"])

        return [
            memory
            for memory in store["memories"]
            if memory["status"] != "archived"
        ]

    def fake_get_memory(memory_id):
        return next(
            (memory for memory in store["memories"] if memory["id"] == memory_id),
            None,
        )

    def fake_delete_memory(memory_id):
        store["deleted"].append(memory_id)
        store["memories"] = [
            memory for memory in store["memories"] if memory["id"] != memory_id
        ]
        return True

    def fake_remember(
        category,
        content,
        previous_memory_id=None,
        related_memory_ids=None,
    ):
        store["remembered"].append(
            (category, content, previous_memory_id, related_memory_ids)
        )
        return remember_result

    def fake_update_memory(memory_id, content):
        store["updated"].append((memory_id, content))

        for memory in store["memories"]:
            if memory["id"] == memory_id:
                memory["content"] = content

        return True

    def fake_archive_memory(memory_id):
        store["archived"].append(memory_id)

        for memory in store["memories"]:
            if memory["id"] == memory_id:
                memory["status"] = "archived"

        return True

    def fake_restore_memory(memory_id):
        store["restored"].append(memory_id)

        for memory in store["memories"]:
            if memory["id"] == memory_id:
                memory["status"] = "active"

        return True

    monkeypatch.setattr("alf.tui.get_memories", fake_get_memories)
    monkeypatch.setattr("alf.tui.get_memory", fake_get_memory)
    monkeypatch.setattr("alf.tui.delete_memory", fake_delete_memory)
    monkeypatch.setattr("alf.tui.remember", fake_remember)
    monkeypatch.setattr("alf.tui.update_memory", fake_update_memory)
    monkeypatch.setattr("alf.tui.archive_memory", fake_archive_memory)
    monkeypatch.setattr("alf.tui.restore_memory", fake_restore_memory)
    monkeypatch.setattr(
        "alf.tui.find_related_memory_candidates",
        fake_find_related_memory_candidates,
    )
    monkeypatch.setattr("alf.tui.asyncio.sleep", fake_sleep)

    return store


def test_calculator_passes_selected_options(monkeypatch):
    captured = {}

    def fake_calculate(expression, symbolic=False, places=3):
        captured["arguments"] = (expression, symbolic, places)
        return "test result"

    monkeypatch.setattr("alf.tui.calculate", fake_calculate)

    async def run_test():
        app = ALFTUI()

        async with app.run_test() as pilot:
            app.show_calc()
            await pilot.pause()

            input_widget = app.query_one("#calc-input")
            input_widget.value = "22/7"

            places = app.query_one("#calc-places")
            places.value = 5

            app.calculate_expression()

            assert captured["arguments"] == ("22/7", False, 5)
            assert "test result" in (
                app.query_one("#calc-history").render().plain
            )

    asyncio.run(run_test())


def test_calculator_passes_symbolic_mode(monkeypatch):
    captured = {}

    def fake_calculate(expression, symbolic=False, places=3):
        captured["arguments"] = (expression, symbolic, places)
        return "symbolic result"

    monkeypatch.setattr("alf.tui.calculate", fake_calculate)

    async def run_test():
        app = ALFTUI()

        async with app.run_test() as pilot:
            app.show_calc()
            await pilot.pause()

            input_widget = app.query_one("#calc-input")
            input_widget.value = "x^2 + 1"

            await pilot.click("#calc-symbolic")
            await pilot.pause()

            mode = app.query_one("#calc-mode", RadioSet)

            assert mode.pressed_index == 1
            assert app.query_one("#calc-places").disabled

            app.calculate_expression()

            assert captured["arguments"] == ("x^2 + 1", True, 3)
            assert "symbolic result" in (
                app.query_one("#calc-history").render().plain
            )

def test_calculator_example_selects_symbolic_mode():
    async def run_test():
        app = ALFTUI()

        async with app.run_test() as pilot:
            app.show_calc()
            await pilot.pause()

            examples = app.query_one("#calc-symbolic-examples")
            item = examples.query_one("#calc-example-symbolic-0")

            app.on_list_view_selected(
                type(
                    "Event",
                    (),
                    {
                        "list_view": examples,
                        "item": item,
                    },
                )()
            )

            await pilot.pause()

            mode = app.query_one("#calc-mode", RadioSet)

            assert mode.pressed_index == 1
            assert app.query_one("#calc-places").disabled
            assert (
                app.query_one("#calc-input").value
                == "solve(x^2 - 4, x)"
            )

    asyncio.run(run_test())


def test_memory_delete_does_not_happen_immediately(monkeypatch):
    store = make_memory_fakes(monkeypatch)

    async def run_test():
        app = ALFTUI()

        async with app.run_test() as pilot:
            app.show_memories()
            await pilot.pause()

            app.query_one("#memories", ListView).index = 0

            await pilot.click("#memory-delete")

            assert store["deleted"] == []
            assert isinstance(app.screen, DeleteMemoryConfirm)

    asyncio.run(run_test())


def test_memory_delete_cancel_leaves_memory_intact(monkeypatch):
    store = make_memory_fakes(monkeypatch)

    async def run_test():
        app = ALFTUI()

        async with app.run_test() as pilot:
            app.show_memories()
            await pilot.pause()

            app.query_one("#memories", ListView).index = 0

            await pilot.click("#memory-delete")
            await pilot.click("#delete-cancel")
            await pilot.pause()

            assert store["deleted"] == []
            assert not isinstance(app.screen, DeleteMemoryConfirm)

    asyncio.run(run_test())


def test_memory_delete_confirm_performs_deletion(monkeypatch):
    store = make_memory_fakes(monkeypatch)

    async def run_test():
        app = ALFTUI()

        async with app.run_test() as pilot:
            app.show_memories()
            await pilot.pause()

            app.query_one("#memories", ListView).index = 0

            await pilot.click("#memory-delete")
            await pilot.click("#delete-permanent")
            await pilot.pause()

            assert store["deleted"] == [7]
            assert not isinstance(app.screen, DeleteMemoryConfirm)

    asyncio.run(run_test())


def test_initial_navigation_shows_question_workspace(monkeypatch):
    make_memory_fakes(monkeypatch)

    async def run_test():
        app = ALFTUI()

        async with app.run_test() as pilot:
            await pilot.pause()

            navigation = app.query_one("#navigation", ListView)

            assert navigation.index == 0
            assert app.query_one("#question-workspace").display
            assert not app.query_one("#calc-workspace").display
            assert not app.query_one("#remember-workspace").display
            assert not app.query_one("#memories-workspace").display
            assert (
                app.query_one("#footer-guidance").render().plain
                == commands["question"]["tui"]["guidance"]
            )

    asyncio.run(run_test())


def test_navigation_round_trip_switches_workspaces(monkeypatch):
    make_memory_fakes(monkeypatch)

    async def run_test():
        app = ALFTUI()

        async with app.run_test() as pilot:
            navigation = app.query_one("#navigation", ListView)

            await pilot.press("down", "down", "down")
            await pilot.pause()

            assert navigation.index == 3
            assert app.query_one("#memories-workspace").display
            assert not app.query_one("#question-workspace").display
            assert (
                app.query_one("#footer-guidance").render().plain
                == commands["memories"]["tui"]["guidance"]
            )

            await pilot.press("up", "up", "up")
            await pilot.pause()

            assert navigation.index == 0
            assert app.query_one("#question-workspace").display
            assert not app.query_one("#memories-workspace").display
            assert (
                app.query_one("#footer-guidance").render().plain
                == commands["question"]["tui"]["guidance"]
            )

    asyncio.run(run_test())


def test_remember_save_calls_application_and_clears_input(monkeypatch):
    store = make_memory_fakes(monkeypatch)

    async def run_test():
        app = ALFTUI()

        async with app.run_test() as pilot:
            app.show_remember()
            await pilot.pause()

            app.query_one("#remember-category").value = "preference"
            app.query_one("#remember-input").text = "User prefers terse answers."

            await pilot.click("#remember-save")
            await pilot.pause()

            assert store["remembered"] == [
                (
                    "preference",
                    "User prefers terse answers.",
                    None,
                    None,
                )
            ]
            assert (
                app.query_one("#remember-status").render().plain
                == "Memory saved."
            )
            assert app.query_one("#remember-input").text == ""
            assert len(app.query_one("#remember-related").children) == 0

    asyncio.run(run_test())


def test_remember_empty_content_is_rejected(monkeypatch):
    store = make_memory_fakes(monkeypatch)

    async def run_test():
        app = ALFTUI()

        async with app.run_test() as pilot:
            app.show_remember()
            await pilot.pause()

            app.query_one("#remember-input").text = "   "

            await pilot.click("#remember-save")
            await pilot.pause()

            assert store["remembered"] == []
            assert (
                app.query_one("#remember-status").render().plain
                == "Please enter something to remember."
            )

            app.query_one("#remember-input").text = "A new memory."
            await app.save_remembered_memory()
            await pilot.pause()

            assert store["remembered"] == [
                ("note", "A new memory.", None, None)
            ]
            assert (
                app.query_one("#remember-status").render().plain
                == "Memory saved."
            )

    asyncio.run(run_test())


def test_memories_select_shows_selected_details(monkeypatch):
    make_memory_fakes(
        monkeypatch,
        memories=[
            make_sample_memory(7, content="First memory."),
            make_sample_memory(12, content="Second memory."),
        ],
    )

    async def run_test():
        app = ALFTUI()

        async with app.run_test() as pilot:
            app.show_memories()
            await pilot.pause()

            await pilot.click("#memory-12")
            await pilot.pause()

            details = app.query_one("#details").render().plain

            assert "Memory 12" in details
            assert "Second memory." in details
            assert "First memory." not in details
            assert (
                app.query_one("#memory-archive").label.plain
                == "Archive"
            )

    asyncio.run(run_test())


def test_memories_edit_save_updates_memory(monkeypatch):
    store = make_memory_fakes(
        monkeypatch,
        memories=[make_sample_memory(7, content="Original content.")],
    )

    async def run_test():
        app = ALFTUI()

        async with app.run_test() as pilot:
            app.show_memories()
            await pilot.pause()

            await pilot.click("#memory-7")
            await pilot.pause()
            await pilot.click("#memory-edit")
            await pilot.pause()

            editor = app.query_one("#memory-editor")

            assert editor.text == "Original content."
            assert editor.display

            editor.text = "Updated content."

            await pilot.click("#memory-save")
            await pilot.pause()

            assert store["updated"] == [(7, "Updated content.")]
            assert "Updated content." in (
                app.query_one("#details").render().plain
            )
            assert not editor.display
            assert app.query_one("#details").display

    asyncio.run(run_test())


def test_memories_edit_cancel_does_not_update(monkeypatch):
    store = make_memory_fakes(
        monkeypatch,
        memories=[make_sample_memory(7, content="Original content.")],
    )

    async def run_test():
        app = ALFTUI()

        async with app.run_test() as pilot:
            app.show_memories()
            await pilot.pause()

            await pilot.click("#memory-7")
            await pilot.pause()
            await pilot.click("#memory-edit")
            await pilot.pause()

            editor = app.query_one("#memory-editor")
            editor.text = "Should not be saved."

            await pilot.click("#memory-cancel")
            await pilot.pause()

            assert store["updated"] == []
            assert "Original content." in (
                app.query_one("#details").render().plain
            )
            assert not editor.display
            assert app.query_one("#details").display

    asyncio.run(run_test())


def test_memories_archive_calls_archive_and_removes_from_active_list(
    monkeypatch,
):
    store = make_memory_fakes(
        monkeypatch,
        memories=[make_sample_memory(7, content="To be archived.")],
    )

    async def run_test():
        app = ALFTUI()

        async with app.run_test() as pilot:
            app.show_memories()
            await pilot.pause()

            await pilot.click("#memory-7")
            await pilot.pause()
            await pilot.click("#memory-archive")
            await pilot.pause()

            assert store["archived"] == [7]
            assert store["memories"][0]["status"] == "archived"
            assert not any(
                child.id == "memory-7"
                for child in app.query_one("#memories").children
            )

    asyncio.run(run_test())


def test_memories_restore_makes_memory_active_again(
    monkeypatch,
):
    store = make_memory_fakes(
        monkeypatch,
        memories=[
            make_sample_memory(7, content="Archived memory.", status="archived")
        ],
    )

    async def run_test():
        app = ALFTUI()

        async with app.run_test() as pilot:
            app.show_memories()
            await pilot.pause()

            await pilot.click("#memories-all")
            await pilot.pause()

            assert any(
                child.id == "memory-7"
                for child in app.query_one("#memories").children
            )

            await pilot.click("#memory-7")
            await pilot.pause()

            assert (
                app.query_one("#memory-archive").label.plain
                == "Restore"
            )

            await pilot.click("#memory-archive")
            await pilot.pause()

            assert store["restored"] == [7]
            assert store["memories"][0]["status"] == "active"
            assert any(
                child.id == "memory-7"
                for child in app.query_one("#memories").children
            )

    asyncio.run(run_test())
