from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Button,
    Checkbox,
    Header,
    Label,
    ListItem,
    ListView,
    Select,
    Static,
    TextArea,
)

from alf.command_catalogue import commands
from alf.memory import archive_memory, get_memories, get_memory, update_memory


class ALFTUI(App):
    """Minimal Textual playground."""

    CSS = """
    Horizontal {
        height: 1fr;
    }

    #navigation {
        width: 15%;
        border: solid yellow;
    }

    #memories-list {
        width: 55%;
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

    #question-workspace,
    #remember-workspace,
    #memories-workspace {
        height: 1fr;
    }

    #question-input {
        height: 3;
    }

    #question-controls {
        height: 3;
    }

    #answer {
        height: 1fr;
        border: solid blue;
        padding: 1 2;
    }

    #answer-ok {
        display: none;
    }

    #remember-category {
        height: 3;
    }

    #remember-input {
        height: 1fr;
    }

    #remember-guidance {
        height: 3;
    }

    #remember-save {
        height: 3;
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

        with Horizontal():
            yield ListView(
                *[
                    ListItem(
                        Label(commands[command]["tui"]["title"]),
                        id=f"navigation-{command}",
                    )
                    for command in ("question", "remember", "memories")
                ],
                id="navigation",
            )

            with Vertical():

                with Vertical(id="question-workspace"):
                    question_tui = commands["question"]["tui"]

                    yield Static(
                        question_tui["title"],
                        classes="workspace-title",
                    )

                    yield TextArea(
                        id="question-input",
                        placeholder=question_tui["description"],
                    )

                    with Horizontal(id="question-controls"):
                        yield Checkbox("Detailed answer", id="detailed-answer")
                        yield Button("Ask", id="ask")

                    yield Static(
                        question_tui["guidance"],
                        id="guidance",
                    )

                    yield Static(
                        "Your answer will appear here.",
                        id="answer",
                    )

                    yield Static(
                        "Source: —",
                        id="answer-source",
                    )

                    yield Button("OK", id="answer-ok")

                with Vertical(id="remember-workspace"):
                    remember_tui = commands["remember"]["tui"]

                    yield Static(
                        remember_tui["title"],
                        classes="workspace-title",
                    )

                    yield Select(
                        [
                            ("Note", "note"),
                            ("Preference", "preference"),
                            ("Decision", "decision"),
                        ],
                        prompt="Choose a category",
                        id="remember-category",
                    )

                    yield TextArea(
                        id="remember-input",
                        placeholder=remember_tui["description"],
                    )

                    yield Static(
                        remember_tui["guidance"],
                        id="remember-guidance",
                    )

                    yield Button("Remember", id="remember-save")


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
                                yield Button("Relate", id="memory-relate")
                                yield Button("Archive", id="memory-archive")
                                yield Button("Forget", id="memory-forget")

                            with Horizontal(id="memory-edit-actions"):
                                yield Button("Save", id="memory-save")
                                yield Button("Cancel", id="memory-cancel")


    def on_mount(self) -> None:
        navigation = self.query_one("#navigation", ListView)
        navigation.index = 0
        navigation.focus()

        self.show_question()


    def show_memory(self, memory_id: str) -> None:
        memory = get_memory(int(memory_id))

        if memory is None:
            return

        details = self.query_one("#details", Static)

        related = memory["related_memory_ids"] or "None"

        details.update(
            f"Memory {memory['id']}\n\n"
            f"Category: {memory['category']}\n\n"
            f"{memory['content']}\n\n"
            f"Related: {related}"
        )

    def show_workspace(self, workspace_id: str) -> None:
        question_workspace = self.query_one("#question-workspace")
        remember_workspace = self.query_one("#remember-workspace")
        memories_workspace = self.query_one("#memories-workspace")

        question_workspace.display = workspace_id == "question"
        remember_workspace.display = workspace_id == "remember"
        memories_workspace.display = workspace_id == "memories"


    def show_question(self) -> None:
        self.show_workspace("question")


    def show_memories(self) -> None:
        self.show_workspace("memories")


    def show_remember(self) -> None:
        self.show_workspace("remember")


    def ask_question(self) -> None:
        question = self.query_one("#question-input", TextArea).text

        if not question.strip():
            return

        detailed = self.query_one("#detailed-answer", Checkbox).value

        answer = self.query_one("#answer", Static)
        source = self.query_one("#answer-source", Static)
        ok_button = self.query_one("#answer-ok", Button)

        if detailed:
            answer.update(
                "This is a more detailed temporary ALF answer. "
                "The real question machinery will eventually appear here."
            )
        else:
            answer.update(
                "This is a temporary ALF answer. "
                "The real question machinery will eventually appear here."
            )

        source.update("Source: Temporary playground response")

        ok_button.display = True

    def clear_question(self) -> None:
        self.query_one("#question-input", TextArea).text = ""
        self.query_one("#answer", Static).update(
            "Your answer will appear here."
        )
        self.query_one("#answer-source", Static).update("Source: —")
        self.query_one("#answer-ok", Button).display = False


    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ask":
            self.ask_question()

        elif event.button.id == "answer-ok":
            self.clear_question()

        elif event.button.id == "memory-edit":
            self.action_edit_memory()

        elif event.button.id == "memory-cancel":
            self.cancel_memory_edit()

        elif event.button.id == "memory-save":
            await self.save_memory_edit()

        elif event.button.id == "memory-archive":
            selected = self.query_one("#memories", ListView).highlighted_child

            if selected is None:
                return

            memory_id = selected.id.removeprefix("memory-")
            archive_memory(int(memory_id))
            await self.refresh_memories()
    async def refresh_memories(self) -> None:
        options = {
            "category": None,
            "include_archived": self.query_one(
                "#memories-all",
                Checkbox,
            ).value,
            "group": None,
        }

        memories = get_memories(options)

        list_view = self.query_one("#memories", ListView)
        await list_view.clear()

        for memory in memories:
            memory_id = str(memory["id"])

            await list_view.append(
                ListItem(
                    Label(
                        f"{memory_id}  "
                        f"{memory['category']:<9} "
                        f"{memory['content']}"
                    ),
                    id=f"memory-{memory_id}",
                )
            )


    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "navigation":
            command = event.item.id.removeprefix("navigation-")

            if command == "question":
                self.show_question()

            elif command == "remember":
                self.show_remember()

            elif command == "memories":
                self.show_memories()

            return

        if event.list_view.id != "memories":
            return

        memory_id = event.item.id.removeprefix("memory-")
        self.show_memory(memory_id)

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
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


    async def refresh_memory_list(self) -> None:
        memories = self.query_one("#memories", ListView)

        await memories.clear()

        current_memories = get_memories(self.get_memory_query_options())

        for memory in current_memories:
            memory_id = str(memory["id"])

            await memories.append(
                ListItem(
                    Label(
                        f"{memory_id}  "
                        f"{memory['category']:<9} "
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
