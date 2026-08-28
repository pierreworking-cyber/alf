import asyncio

from textual.widgets import ListView, RadioSet

from alf.tui import ALFTUI, DeleteMemoryConfirm


def make_delete_fakes(monkeypatch):
    deleted = []

    def fake_get_memories(options=None):
        return [
            {
                "id": 7,
                "created": "2026-01-01 00:00:00",
                "category": "note",
                "status": "active",
                "content": "A memory that must survive confirmation.",
                "previous_memory_id": None,
                "related_memory_ids": None,
            }
        ]

    def fake_delete_memory(memory_id):
        deleted.append(memory_id)
        return True

    monkeypatch.setattr("alf.tui.get_memories", fake_get_memories)
    monkeypatch.setattr("alf.tui.delete_memory", fake_delete_memory)

    return deleted


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
    deleted = make_delete_fakes(monkeypatch)

    async def run_test():
        app = ALFTUI()

        async with app.run_test() as pilot:
            app.show_memories()
            await pilot.pause()

            app.query_one("#memories", ListView).index = 0

            await pilot.click("#memory-delete")

            assert deleted == []
            assert isinstance(app.screen, DeleteMemoryConfirm)

    asyncio.run(run_test())


def test_memory_delete_cancel_leaves_memory_intact(monkeypatch):
    deleted = make_delete_fakes(monkeypatch)

    async def run_test():
        app = ALFTUI()

        async with app.run_test() as pilot:
            app.show_memories()
            await pilot.pause()

            app.query_one("#memories", ListView).index = 0

            await pilot.click("#memory-delete")
            await pilot.click("#delete-cancel")
            await pilot.pause()

            assert deleted == []
            assert not isinstance(app.screen, DeleteMemoryConfirm)

    asyncio.run(run_test())


def test_memory_delete_confirm_performs_deletion(monkeypatch):
    deleted = make_delete_fakes(monkeypatch)

    async def run_test():
        app = ALFTUI()

        async with app.run_test() as pilot:
            app.show_memories()
            await pilot.pause()

            app.query_one("#memories", ListView).index = 0

            await pilot.click("#memory-delete")
            await pilot.click("#delete-permanent")
            await pilot.pause()

            assert deleted == [7]
            assert not isinstance(app.screen, DeleteMemoryConfirm)

    asyncio.run(run_test())
