"""
ALF Textual user interface.

Provides the interactive terminal front end for ALF's capabilities.
The TUI delegates application logic to the underlying ALF modules and
is responsible for presentation, user interaction, and workspace state.
"""

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Checkbox,
    Header,
    Label,
    ListItem,
    ListView,
    Static,
    TextArea,
)

from alf.command_catalogue import commands
from alf.memory import (
    archive_memory,
    delete_memory,
    get_memories,
    get_memory,
    restore_memory,
    update_memory,
)
from alf.tui.calc_tui import CalcTUI
from alf.tui.question_tui import QuestionTUI
from alf.tui.remember_tui import RememberTUI


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
    #memories-workspace
    {
        height: 1fr;
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
                yield QuestionTUI(id="question-workspace")
                yield CalcTUI(id="calc-workspace")
                yield RememberTUI(id="remember-workspace")

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


    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.exit()
            return

        if event.button.id == "memory-edit":
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


    def show_navigation_command(self, command: str) -> None:
        if command == "question":
            self.show_question()

        elif command == "calc":
            self.show_calc()

        elif command == "remember":
            self.show_remember()

        elif command == "memories":
            self.show_memories()


    def on_list_view_highlighted(
        self,
        event: ListView.Highlighted,
    ) -> None:
        if event.list_view.id != "navigation":
            return

        if event.item is None:
            return

        command = event.item.id.removeprefix("navigation-")
        self.show_navigation_command(command)


    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "navigation":
            command = event.item.id.removeprefix("navigation-")
            self.show_navigation_command(command)
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
