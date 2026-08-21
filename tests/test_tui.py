import asyncio

from textual.widgets import RadioSet

from tui.tui import ALFTUI


def test_calculator_passes_selected_options(monkeypatch):
    captured = {}

    def fake_calculate(expression, symbolic=False, places=3):
        captured["arguments"] = (expression, symbolic, places)
        return "test result"

    monkeypatch.setattr("tui.tui.calculate", fake_calculate)

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

    monkeypatch.setattr("tui.tui.calculate", fake_calculate)

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
            item = examples.query_one("#calc-example-4")

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
