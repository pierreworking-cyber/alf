"""
ALF Textual user interface.

Provides the interactive terminal front end for ALF's capabilities.
The TUI delegates application logic to the underlying ALF modules and
is responsible for presentation, user interaction, and workspace state.
"""

import asyncio

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Checkbox,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    RadioButton,
    RadioSet,
    Select,
    Static,
    TextArea,
)

from alf.calc import CalculationError, calculate
from alf.command_catalogue import commands
from alf.memory import (
    archive_memory,
    delete_memory,
    find_related_memory_candidates,
    get_memories,
    get_memory,
    remember,
    restore_memory,
    update_memory,
)
from alf.question import answer_question


class DeleteMemoryConfirm(ModalScreen):
    """Confirmation dialog before permanently deleting a memory."""

    CSS = """
    DeleteMemoryConfirm {
        align: center middle;
    }

    #delete-confirm {
        width: 62;
        height: auto;
        padding: 1 2;
        border: thick $error;
        background: $surface;
        layout: vertical;
    }

    #delete-confirm-message {
        width: 100%;
        height: auto;
        padding: 0 1 1 1;
    }

    #delete-confirm-buttons {
        width: 100%;
        height: 3;
        align: center middle;
    }

    #delete-confirm-buttons Button {
        width: 18;
        margin: 0 1;
    }
    """

    BINDINGS = [
        ("escape", "cancel_delete", "Cancel"),
    ]

    def __init__(self, memory_id: int) -> None:
        super().__init__()
        self._memory_id = memory_id

    def compose(self) -> ComposeResult:
        with Vertical(id="delete-confirm"):
            yield Static(
                f"Permanently delete memory {self._memory_id}?\n"
                "This cannot be undone.",
                id="delete-confirm-message",
            )
            with Horizontal(id="delete-confirm-buttons"):
                yield Button("Cancel", id="delete-cancel")
                yield Button("Delete", id="delete-permanent", variant="error")

    def on_mount(self) -> None:
        self.query_one("#delete-cancel", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "delete-permanent":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_cancel_delete(self) -> None:
        self.dismiss(False)


class ALFTUI(App):
    """Minimal Textual playground."""

    CSS = """
    Screen {
        layout: vertical;
        scrollbar-size: 1 1;
    }




    #main {
        height: 1fr;
    }

    #navigation {
        width: 12%;
        border: solid yellow;
    }

    #navigation ListItem.--highlight {
        text-style: bold;
    }

    #workspace {
        width: 88%;
        height: 1fr;
    }

    .workspace-title {
        height: 3;
        content-align: left middle;
    }

    #remember-workspace {
        height: 1fr;
    }

    #remember-input {
        height: 1fr;
        border: solid blue;
    }

    #remember-controls {
        height: 3;
        margin-top: 0;
        border: solid blue;
        align: left middle;
    }

    #remember-category {
        width: 14;
        height: 3;
    }

    #remember-save {
        width: auto;
        height: 1;
        margin-left: 2;
    }

    #remember-related-title {
        height: 2;
        margin-top: 1;
        border-bottom: solid $border-blurred;
    }

    #remember-related {
        height: 8;
        border: solid blue;
        padding: 1 2;
    }

    #remember-related Horizontal {
        width: 100%;
        height: auto;
    }

    #remember-related Checkbox {
        width: auto;
        height: auto;
    }

    #remember-related Label {
        width: 1fr;
        height: auto;
        text-wrap: nowrap;
    }

    #remember-related ListItem {
        border-bottom: solid grey;
        padding-bottom: 1;
    }

    #memories-list {
        width: 55%;
    }

    #memory-view-actions Button {
        margin-right: 1;
    }

    #memories {
        width: 100%;
        border: solid green;
    }

    #memories Label {
        width: 100%;
        height: auto;
    }

    #memories ListItem {
        border-bottom: solid grey;
        padding-bottom: 1;
    }

    #memory-detail {
        width: 45%;
    }

    #footer {
        height: 3;
        align: right middle;
    }

    #footer-guidance {
        width: 1fr;
        padding: 1 2;
    }

    #quit {
        width: 10;
    }

    Button {
        height: 1;
        border: none;
        padding: 0 1;
    }
    #question-workspace,
    #remember-workspace,
    #memories-workspace,
    #calc-workspace {
        height: 1fr;
    }

    #calc-workspace {
        layout: horizontal;
    }

    #calc-left {
        width: 55%;
        border: solid green;
        padding: 0 2;
    }

    #calc-right {
        width: 45%;
        border: solid blue;
        padding: 1 2;
    }

    #calc-left .workspace-title {
        height: 1;
    }

    #calc-input {
        height: 3;
    }

    #calc-options {
        height: 1;
        align: left middle;
    }

    #calc-mode {
        width: auto;
        height: auto;
        layout: horizontal;
    }

    #calc-precision {
        width: 1fr;
        height: 3;
        align: right middle;
    }

    #calc-mode RadioButton {
        width: auto;
    }


    #calc-options Label {
        width: auto;
        margin-left: 1;
        margin-right: 1;
    }

    #calc-places {
        width: 10;
        height: 3;
    }

    #calc-controls {
        height: 3;
        border: solid blue;
        align: left middle;
    }

    #calc-controls Button {
        width: 1fr;
    }

    #calc-result {
        height: 1fr;
        border: solid blue;
        padding: 1 2;
    }

    #calc-examples,
    #calc-symbolic-examples {
        height: auto;
        margin: 0 1;
    }

    .calc-example-heading {
        height: 2;
        margin: 1 1 0 1;
        border-bottom: solid $border-blurred;
    }

    #question-input {
        height: 3;
        border: solid blue;
    }

    #question-controls {
        height: 3;
        margin-top: 0;
        border: solid blue;
        align: left top;
    }

    #detailed-answer-control {
        width: auto;
        height: 1;
    }

    #ask {
        margin-left: 2;
    }

    #question-status {
        width: 1fr;
        height: 3;
        padding: 0 2;
        content-align: left top;
    }

    #answer {
        height: 1fr;
        border: solid blue;
        padding: 1 2;
    }

    #answer-ok {
        display: none;
    }

    #details {
        width: 1fr;
        border: solid blue;
        padding: 1 2;
    }

    #memory-editor {
        display: none;
    }

    #memory-actions {
        width: 1fr;
        height: 3;
    }

    #memory-view-actions {
        width: 1fr;
        height: 3;
        layout: grid;
        grid-size: 4 1;
    }

    #memory-view-actions Button {
        width: 100%;
    }

    #memory-edit-actions {
        display: none;
    }
    """

    editing_memory_id: str | None = None


    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="main"):
            yield ListView(
                *[
                    ListItem(
                        Label(commands[command]["tui"]["title"]),
                        id=f"navigation-{command}",
                    )
                    for command in ("question", "calc", "remember", "memories")
                ],
                id="navigation",
            )

            with Vertical(id="workspace"):

                with Vertical(id="question-workspace"):
                    question_tui = commands["question"]["tui"]

                    yield Static(
                        question_tui["title"],
                        classes="workspace-title",
                    )

                    yield Input(
                        id="question-input",
                        placeholder=question_tui["description"],
                    )

                    with Horizontal(id="question-controls"):
                        with Horizontal(id="detailed-answer-control"):
                            yield Checkbox(
                                "Detailed answer",
                                id="detailed-answer",
                                compact=True,
                        )
                        yield Button("Ask", id="ask")
                        yield Static(
                            "Ready",
                            id="question-status",
                        )

                    with VerticalScroll(id="answer"):
                        yield Static(
                            "Your answer will appear here.",
                            id="answer-text",
                        )

                    yield Static(
                        "Source: —",
                        id="answer-source",
                    )

                    yield Button("OK", id="answer-ok")

                with Horizontal(id="calc-workspace"):
                    calc_tui = commands["calc"]["tui"]
  
                    with Vertical(id="calc-left"):
                        yield Static(
                            calc_tui["title"],
                            classes="workspace-title",
                        )
  
                        yield Input(
                            id="calc-input",
                            placeholder=calc_tui["description"],
                        )
  
                        with Horizontal(id="calc-options"):
                            with RadioSet(
                                id="calc-mode",
                                compact=True,
                                ):
                                yield RadioButton(
                                    "Numeric",
                                    value=True,
                                )
                                yield RadioButton(
                                    "Symbolic",
                                    id="calc-symbolic",
                                )
  
                            with Horizontal(id="calc-precision"):
                                yield Label("Dec:")
                                yield Select(
                                    [
                                        ("1", 1),
                                        ("2", 2),
                                        ("3", 3),
                                        ("4", 4),
                                        ("5", 5),
                                        ("6", 6),
                                        ("7", 7),
                                        ("8", 8),
                                        ("9", 9),
                                        ("10", 10),
                                    ],
                                    value=3,
                                    id="calc-places",
                                    compact=True,
                                )
  
                        with Horizontal(id="calc-controls"):
                            yield Button(
                                "Calculate",
                                id="calc-button",
                            )
                            yield Button(
                                "Clear",
                                id="calc-clear",
                            )
  
                        with VerticalScroll(id="calc-result"):
                            yield Static(
                                "The result will appear here.",
                                id="calc-history",
                            )
  
                    with Vertical(id="calc-right"):

                        yield Static(
                            "Try some numerical calculations",
                            classes="calc-example-heading",
                        )

                        example_index = 0

                        numerical_items = []

                        for group, examples in commands["calc"]["examples"].items():
                            if group == "Symbolic mathematics":
                                continue

                            numerical_items.append(
                                ListItem(
                                    Label(group),
                                    classes="calc-example-heading",
                                )
                            )

                            for example in examples:
                                numerical_items.append(
                                    ListItem(
                                        Label(
                                            example.removeprefix('alf calc "')
                                            .removesuffix('"')
                                        ),
                                        id=f"calc-example-{example_index}",
                                    )
                                )
                                example_index += 1

                        yield ListView(
                            *numerical_items,
                            id="calc-examples",
                        )

                        yield Static(
                            "Explore symbolic mathematics",
                            classes="calc-example-heading",
                        )

                        symbolic_items = []

                        for index, example in enumerate(
                            commands["calc"]["examples"]["Symbolic mathematics"]
                        ):
                            symbolic_items.append(
                                ListItem(
                                    Label(
                                        example.removeprefix('alf calc "')
                                        .removesuffix('"')
                                    ),
                                    id=f"calc-example-symbolic-{index}",
                                )
                            )

                        yield ListView(
                            *symbolic_items,
                            id="calc-symbolic-examples",
                        )
  
                with Vertical(id="remember-workspace"):
                    remember_tui = commands["remember"]["tui"]

                    yield Static(
                        remember_tui["title"],
                        classes="workspace-title",
                    )

                    yield TextArea(
                        id="remember-input",
                        placeholder=remember_tui["description"],
                    )

                    with Horizontal(id="remember-controls"):
                        yield Button(
                            "Save",
                            id="remember-save",
                        )
                        yield Select(
                            [
                                ("Note", "note"),
                                ("Preference", "preference"),
                                ("Decision", "decision"),
                                ("Fact", "fact"),
                            ],
                            value="note",
                            id="remember-category",
                            compact=True,
                        )

                    yield Static(
                        "Ready",
                        id="remember-status",
                    )

                    yield Static(
                        "Related memories",
                        id="remember-related-title",
                    )

                    yield ListView(
                        id="remember-related",
                    )

                with Horizontal(id="memories-workspace"):
                    with Vertical(id="memories-list"):
                        yield Checkbox(
                            "Show archived",
                            id="memories-all",
                        )

                        yield ListView(
                            *[
                                ListItem(
                                    Label(
                                        f"{memory['id']}  "
                                        f"{memory['category']:<9} "
                                        f"{'* ' if memory['status'] != 'active' else ''}"  # noqa: E501
                                        f"{memory['content']}"
                                    ),
                                    id=f"memory-{memory['id']}",
                                )
                                for memory in get_memories()
                            ],
                            id="memories",
                        )

                    with Vertical(id="memory-detail"):
                        yield Static(
                            "Select a memory",
                            id="details",
                        )

                        yield TextArea(
                            id="memory-editor",
                        )

                        with Horizontal(id="memory-actions"):
                            with Horizontal(id="memory-view-actions"):
                                yield Button("Edit", id="memory-edit")
                                yield Button("Archive", id="memory-archive")
                                yield Button("Delete", id="memory-delete")

                            with Horizontal(id="memory-edit-actions"):
                                yield Button("Save", id="memory-save")
                                yield Button("Cancel", id="memory-cancel")
        with Horizontal(id="footer"):
            yield Static(
                "",
                id="footer-guidance",
            )
            yield Button("Quit", id="quit")


    def on_mount(self) -> None:
        self.calc_history = []
        navigation = self.query_one("#navigation", ListView)
        navigation.index = 0
        navigation.focus()

        self.show_question()


    def show_memory(self, memory_id: str) -> None:
        memory = get_memory(int(memory_id))

        if memory is None:
            return

        details = self.query_one("#details", Static)

        archive_button = self.query_one(
            "#memory-archive",
            Button,
        )

        if memory["status"] == "archived":
            archive_button.label = "Restore"
        else:
            archive_button.label = "Archive"

        related = memory["related_memory_ids"] or "None"

        details.update(
            f"Memory {memory['id']}\n\n"
            f"Category: {memory['category']}\n\n"
            f"{memory['content']}\n\n"
            f"Related: {related}"
        )

    def show_workspace(self, workspace_id: str) -> None:
        question_workspace = self.query_one("#question-workspace")
        calc_workspace = self.query_one("#calc-workspace")
        remember_workspace = self.query_one("#remember-workspace")
        memories_workspace = self.query_one("#memories-workspace")
        footer_guidance = self.query_one("#footer-guidance", Static)

        question_workspace.display = workspace_id == "question"
        calc_workspace.display = workspace_id == "calc"
        remember_workspace.display = workspace_id == "remember"
        memories_workspace.display = workspace_id == "memories"

        footer_guidance.update(commands[workspace_id]["tui"]["guidance"])


    def show_question(self) -> None:
        self.show_workspace("question")


    def show_calc(self) -> None:
        self.show_workspace("calc")


    def show_memories(self) -> None:
        self.show_workspace("memories")


    def show_remember(self) -> None:
        self.show_workspace("remember")


    def ask_question(self) -> None:
        question = self.query_one("#question-input", Input).value

        if not question.strip():
            return

        detailed = self.query_one("#detailed-answer", Checkbox).value

        status = self.query_one("#question-status", Static)
        answer = self.query_one("#answer-text", Static)
        source = self.query_one("#answer-source", Static)
        ok_button = self.query_one("#answer-ok", Button)

        status.update("Asking local language model…")
        answer.update("Waiting for answer…")
        source.update("Source: Local language model")
        ok_button.display = False
        self.query_one("#ask", Button).disabled = True

        self.ask_question_worker(
            question,
            detailed,
        )

    @work(thread=True)
    def ask_question_worker(
        self,
        question: str,
        detailed: bool,
    ) -> None:

        def report_progress(message: str) -> None:
            self.call_from_thread(
                self.update_question_status,
                message,
            )

        try:
            result = answer_question(
                question,
                verbose=detailed,
                progress=report_progress,
            )
        except Exception as error:
            self.call_from_thread(
                self.show_question_error,
                str(error),
            )
            return

        self.call_from_thread(
            self.show_question_answer,
            result,
        )

    def update_question_status(self, message: str) -> None:
        self.query_one("#question-status", Static).update(message)

    def show_question_answer(self, result) -> None:
        self.query_one("#question-status", Static).update("Complete")
        self.query_one("#answer-text", Static).update(result.answer)

        source = result.source or "No reliable source"
        self.query_one("#answer-source", Static).update(
            f"Source: {source}"
        )

        self.query_one("#answer-ok", Button).display = True
        self.query_one("#ask", Button).disabled = False

    def show_question_error(self, error: str) -> None:
        self.query_one("#question-status", Static).update("Failed")
        self.query_one("#answer-text", Static).update(
            "I couldn't get an answer to the question."
        )
        self.query_one("#answer-source", Static).update(
            f"Error: {error}"
        )
        self.query_one("#answer-ok", Button).display = True
        self.query_one("#ask", Button).disabled = False



    def clear_question(self) -> None:
        self.query_one("#question-input", Input).value = ""
        self.query_one("#answer-text", Static).update(
            "Your answer will appear here."
        )
        self.query_one("#answer-source", Static).update("Source: —")
        self.query_one("#answer-ok", Button).display = False


    async def on_input_submitted(
        self,
        event: Input.Submitted,
    ) -> None:
        if event.input.id == "question-input":
            self.ask_question()

        elif event.input.id == "calc-input":
            self.calculate_expression()


    def calculate_expression(self) -> None:
        expression = self.query_one("#calc-input", Input).value.strip()

        if not expression:
            return

        mode = self.query_one("#calc-mode", RadioSet)
        symbolic = mode.pressed_button.label.plain == "Symbolic"

        places = self.query_one("#calc-places", Select).value

        try:
            calculation = calculate(
                expression,
                symbolic=symbolic,
                places=places,
            )
        except CalculationError as error:
            self.calc_history.append(
                f"{expression}\n{error}"
            )
        else:
            self.calc_history.append(
                f"{expression}\n{calculation}"
            )

        self.query_one("#calc-history", Static).update(
            "\n\n".join(self.calc_history)
        )
        self.query_one("#calc-input", Input).value = ""
        self.query_one("#calc-input", Input).focus()


    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.radio_set.id != "calc-mode":
            return

        symbolic = event.pressed.label.plain == "Symbolic"

        self.query_one("#calc-places", Select).disabled = symbolic


    def clear_calculation(self) -> None:
        self.calc_history.clear()
        self.query_one("#calc-input", Input).value = ""
        self.query_one("#calc-history", Static).update(
            "The result will appear here."
        )
        self.query_one("#calc-input", Input).focus()


    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if event.text_area.id != "remember-input":
            return

        content = event.text_area.text.strip()

        if not content:
            self.clear_related_memories()
            return

        self.update_related_memories(content)

    def clear_related_memories(self) -> None:
        related = self.query_one("#remember-related", ListView)
        related.clear()


    @work(exclusive="related-memory-search")
    async def update_related_memories(self, content: str) -> None:
        await asyncio.sleep(0.75)

        candidates = find_related_memory_candidates(content)

        related = self.query_one("#remember-related", ListView)
        await related.clear()

        for memory in candidates:
            await related.append(
                ListItem(
                    Horizontal(
                        Checkbox(
                            id=f"related-memory-{memory['id']}",
                            compact=True,
                        ),
                Label(
                    f"{memory['id']}  "
                    f"{memory['category']:<9} "
                    f"{'* ' if memory['status'] != 'active' else ''}"
                    f"{memory['content']}"
                ),
                    ),
                    id=f"related-memory-item-{memory['id']}",
                )
            )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.exit()
            return

        if event.button.id == "ask":
            self.ask_question()

        elif event.button.id == "calc-button":
            self.calculate_expression()

        elif event.button.id == "calc-clear":
            self.clear_calculation()

        elif event.button.id == "answer-ok":
            self.clear_question()

        elif event.button.id == "remember-save":
            await self.save_remembered_memory()

        elif event.button.id == "memory-edit":
            self.action_edit_memory()

        elif event.button.id == "memory-save":
            await self.save_memory_edit()

        elif event.button.id == "memory-cancel":
            self.cancel_memory_edit()
        elif event.button.id == "memory-archive":
            selected = self.query_one("#memories", ListView).highlighted_child

            if selected is None:
                return

            memory_id = selected.id.removeprefix("memory-")
            memory = get_memory(int(memory_id))

            if memory is None:
                return

            if memory["status"] == "archived":
                restore_memory(int(memory_id))
            else:
                archive_memory(int(memory_id))

            await self.refresh_memory_list()

        elif event.button.id == "memory-delete":
            selected = self.query_one("#memories", ListView).highlighted_child

            if selected is None:
                return

            memory_id = int(selected.id.removeprefix("memory-"))
            self.confirm_and_delete_memory(memory_id)

    async def save_remembered_memory(self) -> None:
        category = self.query_one("#remember-category", Select).value
        content = self.query_one("#remember-input", TextArea).text.strip()

        status = self.query_one("#remember-status", Static)

        if category is Select.BLANK:
            status.update("Please choose a memory category.")
            return

        if not content:
            status.update("Please enter something to remember.")
            return

        related = self.query_one("#remember-related", ListView)
        related_memory_ids = [
            item.query_one(Checkbox).id.removeprefix("related-memory-")
            for item in related.children
            if item.query_one(Checkbox).value
        ]

        result = remember(
            category,
            content,
            related_memory_ids=",".join(related_memory_ids) or None,
        )

        if result is not True:
            status.update("I couldn't save that memory.")
            return

        self.query_one("#remember-input", TextArea).text = ""
        self.clear_related_memories()
        status.update("Memory saved.")

        await self.refresh_memory_list()


    def on_list_view_highlighted(
        self,
        event: ListView.Highlighted,
    ) -> None:
        if event.list_view.id != "navigation":
            return

        if event.item is None:
            return

        command = event.item.id.removeprefix("navigation-")

        if command == "question":
            self.show_question()

        elif command == "calc":
            self.show_calc()

        elif command == "remember":
            self.show_remember()

        elif command == "memories":
            self.show_memories()


    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "navigation":
            command = event.item.id.removeprefix("navigation-")

            if command == "question":
                self.show_question()

            elif command == "calc":
                self.show_calc()

            elif command == "remember":
                self.show_remember()

            elif command == "memories":
                self.show_memories()

            return

        if event.list_view.id in {
            "calc-examples",
            "calc-symbolic-examples",
        }:
            label = event.item.query_one(Label)
            expression = str(label.content)

            symbolic = event.list_view.id == "calc-symbolic-examples"

            mode = self.query_one("#calc-mode", RadioSet)

            if symbolic and mode.pressed_index == 0:
                mode.query_one("#calc-symbolic", RadioButton).value = True
            elif not symbolic and mode.pressed_index == 1:
                mode.query_one(RadioButton).value = True

            input_widget = self.query_one("#calc-input", Input)
            input_widget.value = expression
            input_widget.focus()
            return

        if event.list_view.id != "memories":
            return

        if event.item is None:
            return

        memory_id = event.item.id.removeprefix("memory-")
        self.show_memory(memory_id)


    def action_edit_memory(self) -> None:
        selected = self.query_one("#memories", ListView).highlighted_child

        if selected is None:
            return

        memory_id = selected.id.removeprefix("memory-")
        memory = get_memory(int(memory_id))

        if memory is None:
            return

        self.editing_memory_id = memory_id

        details = self.query_one("#details", Static)
        editor = self.query_one("#memory-editor", TextArea)
        view_actions = self.query_one("#memory-view-actions")
        edit_actions = self.query_one("#memory-edit-actions")

        editor.text = memory["content"]

        details.display = False
        editor.display = True
        view_actions.display = False
        edit_actions.display = True

        editor.focus()


    def cancel_memory_edit(self) -> None:
        details = self.query_one("#details", Static)
        editor = self.query_one("#memory-editor", TextArea)
        view_actions = self.query_one("#memory-view-actions")
        edit_actions = self.query_one("#memory-edit-actions")

        details.display = True
        editor.display = False
        view_actions.display = True
        edit_actions.display = False

        editor.text = ""
        details.focus()


    async def save_memory_edit(self) -> None:
        if self.editing_memory_id is None:
            return

        editor = self.query_one("#memory-editor", TextArea)
        memory_id = self.editing_memory_id

        update_memory(int(memory_id), editor.text)

        await self.refresh_memory_list()
        self.show_memory(memory_id)
        self.cancel_memory_edit()


    def get_memory_query_options(self) -> dict:
        return {
            "category": None,
            "include_archived": self.query_one(
                "#memories-all",
                Checkbox,
            ).value,
            "group": None,
        }


    @work
    async def confirm_and_delete_memory(self, memory_id: int) -> None:
        """Confirm a permanent deletion before performing it.

        The memory is deleted only when the user explicitly confirms.
        """

        confirmed = await self.push_screen_wait(DeleteMemoryConfirm(memory_id))

        if confirmed is not True:
            return

        delete_memory(memory_id)
        await self.refresh_memory_list()

    async def refresh_memory_list(self) -> None:
        memories = self.query_one("#memories", ListView)

        await memories.clear()

        current_memories = get_memories(self.get_memory_query_options())

        for memory in current_memories:
            memory_id = str(memory["id"])

            await memories.append(
                ListItem(
                    Label(
                        f"{memory['id']}  "
                        f"{memory['category']:<9} "
                        f"{'* ' if memory['status'] != 'active' else ''}"
                        f"{memory['content']}"
                    ),
                    id=f"memory-{memory_id}",
                )
            )

        if self.editing_memory_id is not None:
            for index, memory in enumerate(current_memories):
                if str(memory["id"]) == self.editing_memory_id:
                    memories.index = index
                    break

        memories.focus()


    async def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id != "memories-all":
            return

        await self.refresh_memory_list()


def main() -> None:
    ALFTUI().run()


if __name__ == "__main__":
    main()
