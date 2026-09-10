from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Checkbox,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
    TextArea,
)

from alf.memory import (
    archive_memory,
    delete_memory,
    get_memories,
    get_memory,
    relate_memory,
    restore_memory,
    search_memories,
    update_memory,
)


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


class SearchMemoriesModal(ModalScreen):
    """Enter a search term for memories."""

    CSS = """
    SearchMemoriesModal {
        align: center middle;
    }

    #memory-search {
        width: 70;
        height: auto;
        padding: 1 2;
        border: thick $accent;
        background: $surface;
    }

    #memory-search-buttons {
        width: 100%;
        height: 3;
        align: center middle;
    }

    #memory-search-buttons Button {
        width: 20;
        margin: 0 1;
    }

    #memory-search-input {
        width: 100%;
        margin: 1 0;
    }
    """

    BINDINGS = [
        ("escape", "cancel_search", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="memory-search"):
            yield Label("Search memories")
            yield Input(
                placeholder="Enter search term",
                id="memory-search-input",
            )
            with Horizontal(id="memory-search-buttons"):
                yield Button("All memories", id="memory-search-all")
                yield Button("Cancel", id="memory-search-cancel")

    def on_mount(self) -> None:
        self.query_one("#memory-search-input", Input).focus()

    def action_cancel_search(self) -> None:
        self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        term = event.value.strip()

        if term:
            self.dismiss(term)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "memory-search-all":
            self.dismiss("")
        elif event.button.id == "memory-search-cancel":
            self.dismiss(None)

class RelateMemoryModal(ModalScreen):
    """Enter the ID of a memory to relate to the selected memory."""

    CSS = """
    RelateMemoryModal {
        align: center middle;
    }

    #memory-relate {
        width: 70;
        height: auto;
        padding: 1 2;
        border: thick $accent;
        background: $surface;
    }

    #memory-relate-input {
        width: 100%;
        margin: 1 0;
    }

    #memory-relate-buttons {
        width: 100%;
        height: 3;
        align: center middle;
    }

    #memory-relate-buttons Button {
        width: 20;
        margin: 0 1;
    }
    """

    BINDINGS = [
        ("escape", "cancel_relate", "Cancel"),
    ]

    def __init__(self, memory_id: int) -> None:
        super().__init__()
        self._memory_id = memory_id

    def compose(self) -> ComposeResult:
        with Vertical(id="memory-relate"):
            yield Label(
                f"Relate memory {self._memory_id} to:"
            )
            yield Input(
                placeholder="Memory ID",
                id="memory-relate-input",
            )
            with Horizontal(id="memory-relate-buttons"):
                yield Button("Relate", id="memory-relate-submit")
                yield Button("Cancel", id="memory-relate-cancel")

    def on_mount(self) -> None:
        self.query_one("#memory-relate-input", Input).focus()

    def action_cancel_relate(self) -> None:
        self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        memory_id = event.value.strip()

        if memory_id:
            self.dismiss(memory_id)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "memory-relate-submit":
            relate_input = self.query_one(
                "#memory-relate-input",
                Input,
            )
            memory_id = relate_input.value.strip()

            if memory_id:
                self.dismiss(memory_id)

        elif event.button.id == "memory-relate-cancel":
            self.dismiss(None)



class MemoriesTUI(Vertical):
    """Textual workspace for viewing and managing memories."""

    CSS = """
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

    #memory-detail {
        width: 45%;
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

    BINDINGS = [
        ("/", "search_memories", "Search"),
        ("r", "relate_memory", "Relate"),
    ]

    def compose(self) -> ComposeResult:
        with Horizontal():
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
                                f"{'* ' if memory['status'] != 'active' else ''}"
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

    @work
    async def action_search_memories(self) -> None:
        """Open the memory search dialog."""
        term = await self.app.push_screen_wait(
            SearchMemoriesModal()
        )

        if term is None:
            return

        memories = self.query_one("#memories", ListView)
        await memories.clear()

        if term == "":
            current_memories = get_memories(
                self.get_memory_query_options()
            )
        else:
            current_memories = search_memories(
                term,
                self.get_memory_query_options(),
            )

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

        memories.focus()


    @work
    async def action_relate_memory(self) -> None:
        """Open the memory relationship dialog."""
        selected = self.query_one(
            "#memories",
            ListView,
        ).highlighted_child

        if selected is None:
            return

        memory_id = int(
            selected.id.removeprefix("memory-")
        )

        related_id = await self.app.push_screen_wait(
            RelateMemoryModal(memory_id)
        )

        if related_id is None:
            return

        if not relate_memory(memory_id, related_id):
            return

        self.show_memory(str(memory_id))



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
        """Confirm a permanent deletion before performing it."""

        confirmed = await self.app.push_screen_wait(
            DeleteMemoryConfirm(memory_id)
        )

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

    async def on_button_pressed(self, event: Button.Pressed) -> None:
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

            memory_id = int(selected.id.removeprefix("memory-"))
            memory = get_memory(memory_id)

            if memory is None:
                return

            if memory["status"] == "archived":
                restore_memory(memory_id)
            else:
                archive_memory(memory_id)

            await self.refresh_memory_list()

        elif event.button.id == "memory-delete":
            selected = self.query_one("#memories", ListView).highlighted_child

            if selected is None:
                return

            memory_id = int(selected.id.removeprefix("memory-"))
            self.confirm_and_delete_memory(memory_id)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id != "memories":
            return

        if event.item is None:
            return

        memory_id = event.item.id.removeprefix("memory-")
        self.show_memory(memory_id)

    async def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id != "memories-all":
            return

        await self.refresh_memory_list()
