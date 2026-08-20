import asyncio

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Button,
    Checkbox,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Select,
    Static,
    TextArea,
)

from alf.command_catalogue import commands
from alf.memory import (
    archive_memory,
    delete_memory,
    find_related_memory_candidates,
    get_memories,
    get_memory,
    remember,
    update_memory,
)
from alf.question import answer_question


class ALFTUI(App):
    """Minimal Textual playground."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #main {
        height: 1fr;
    }

      #navigation {
          width: 12%;
          border: solid yellow;
      }

      #workspace {
          width: 88%;
          height: 1fr;
      }

      #workspace-left {
          width: 40%;
          border: solid green;
          padding: 1 2;
      }

      #remember-workspace #workspace-left {
          padding-top: 0;
      }

      #workspace-right {
          width: 60%;
          border: solid blue;
          padding: 1 2;
      }

      .workspace-title {
          height: 3;
          content-align: left middle;
      }

      #remember-workspace {
          height: 1fr;
      }

      #remember-category {
          height: 3;
      }

      #remember-input {
          width: 100%;
          height: 1fr;
      }

      #remember-related-title {
          height: 3;
          padding-top: 1;
      }

      #remember-related {
          height: 1fr;
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

      #remember-save {
          width: 100%;
          height: 3;
      }

    #remember-save {
        width: 100%;
        height: 3;
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

    #question-status {
        width: 1fr;
        padding: 1 2;
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
                    for command in ("question", "remember", "memories")
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
                        yield Checkbox(
                            "Detailed answer",
                            id="detailed-answer",
                        )
                        yield Button("Ask", id="ask")
                        yield Static(
                            "Ready",
                            id="question-status",
                        )

                    yield Static(
                        question_tui["guidance"],
                        id="guidance",
                    )

                    with VerticalScroll(id="answer"):
                        yield Static(
                            "Your answer will appear here.",
                        )

                    yield Static(
                        "Source: —",
                        id="answer-source",
                    )

                    yield Button("OK", id="answer-ok")

                with Horizontal(id="remember-workspace"):

                    with Vertical(id="workspace-left"):
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
                                ("Fact", "fact"),
                            ],
                            value="note",
                            id="remember-category",
                        )

                        yield TextArea(
                            id="remember-input",
                            placeholder=remember_tui["description"],
                        )

                        yield Button(
                            "Save",
                            id="remember-save",
                        )
                    with Vertical(id="workspace-right"):
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
        footer_guidance = self.query_one("#footer-guidance", Static)

        question_workspace.display = workspace_id == "question"
        remember_workspace.display = workspace_id == "remember"
        memories_workspace.display = workspace_id == "memories"

        footer_guidance.update(commands[workspace_id]["tui"]["guidance"])


    def show_question(self) -> None:
        self.show_workspace("question")


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
        answer = self.query_one("#answer Static", Static)
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
        self.query_one("#answer Static", Static).update(result.answer)

        source = result.source or "No reliable source"
        self.query_one("#answer-source", Static).update(
            f"Source: {source}"
        )

        self.query_one("#answer-ok", Button).display = True
        self.query_one("#ask", Button).disabled = False

    def show_question_error(self, error: str) -> None:
        self.query_one("#question-status", Static).update("Failed")
        self.query_one("#answer", Static).update(
            "I couldn't get an answer to the question."
        )
        self.query_one("#answer-source", Static).update(
            f"Error: {error}"
        )
        self.query_one("#answer-ok", Button).display = True
        self.query_one("#ask", Button).disabled = False



    def clear_question(self) -> None:
        self.query_one("#question-input", Input).value = ""
        self.query_one("#answer Static", Static).update(
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

        elif event.button.id == "answer-ok":
            self.clear_question()

        elif event.button.id == "remember-save":
            await self.save_remembered_memory()

        elif event.button.id == "memory-archive":
            selected = self.query_one("#memories", ListView).highlighted_child

            if selected is None:
                return

            memory_id = selected.id.removeprefix("memory-")
            archive_memory(int(memory_id))
            await self.refresh_memories()

        elif event.button.id == "memory-delete":
            selected = self.query_one("#memories", ListView).highlighted_child

            if selected is None:
                return

            memory_id = selected.id.removeprefix("memory-")
            delete_memory(int(memory_id))
            await self.refresh_memories()

    async def save_remembered_memory(self) -> None:
        category = self.query_one("#remember-category", Select).value
        content = self.query_one("#remember-input", TextArea).text.strip()

        guidance = self.query_one("#footer-guidance", Static)

        if category is Select.BLANK:
            guidance.update("Please choose a memory category.")
            return

        if not content:
            guidance.update("Please enter something to remember.")
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
            guidance.update("I couldn't save that memory.")
            return

        self.query_one("#remember-input", TextArea).text = ""
        self.clear_related_memories()
        guidance.update("Memory saved.")

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
        if event.list_view.id == "navigation":
            if event.item is None:
                return

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
