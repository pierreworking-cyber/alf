document.addEventListener("DOMContentLoaded", () => {
    const readErrorMessage = async (response) => {
        try {
            const data = await response.json();
            return data.error || "Operation failed";
        } catch {
            return "Operation failed";
        }
    };

    const closeMenus = () => {
        document
            .querySelectorAll(".memory-category-actions")
            .forEach((menu) => menu.remove());
    };

    const createCategory = async (parentId = null) => {
        const prompt = parentId === null
            ? "New category:"
            : "New child category:";

        const name = await alfPrompt(prompt);

        if (!name || !name.trim()) {
            return;
        }

        const response = await fetch("/memory-categories", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                name: name.trim(),
                parent_id: parentId,
            }),
        });

        if (!response.ok) {
            await alfAlert(await readErrorMessage(response));
            return;
        }

        window.location.reload();
    };

    document
        .getElementById("new-memory-category")
        ?.addEventListener("click", () => createCategory());

    document
        .querySelectorAll(".memory-category-menu")
        .forEach((button) => {
            button.addEventListener("click", (event) => {
                event.stopPropagation();

                closeMenus();

                const category = button.closest(
                    ".memory-taxonomy-category"
                );

                const categoryId = category.dataset.categoryId;
                const categoryName = category.querySelector(
                    ".memory-taxonomy-header a"
                ).textContent.trim();

                const actions = document.createElement("div");
                actions.className = "memory-category-actions";

                const addChild = document.createElement("button");
                addChild.type = "button";
                addChild.textContent = "Add child";

                const rename = document.createElement("button");
                rename.type = "button";
                rename.textContent = "Rename";

                const remove = document.createElement("button");
                remove.type = "button";
                remove.textContent = "Delete";

                actions.append(
                    addChild,
                    rename,
                    remove
                );

                category.appendChild(actions);

                addChild.addEventListener("click", async () => {
                    await createCategory(Number(categoryId));
                });

                rename.addEventListener("click", async () => {
                    const name = await alfPrompt(
                        "Rename category:",
                        categoryName
                    );

                    if (!name || !name.trim()) {
                        return;
                    }

                    const response = await fetch(
                        `/memory-categories/${categoryId}`,
                        {
                            method: "PATCH",
                            headers: {
                                "Content-Type": "application/json",
                            },
                            body: JSON.stringify({
                                name: name.trim(),
                            }),
                        }
                    );

                    if (!response.ok) {
                        await alfAlert(
                            await readErrorMessage(response)
                        );
                        return;
                    }

                    window.location.reload();
                });

                remove.addEventListener("click", async () => {
                    const confirmed = await alfConfirm(
                        `Delete "${categoryName}"?`
                    );

                    if (!confirmed) {
                        return;
                    }

                    const response = await fetch(
                        `/memory-categories/${categoryId}`,
                        {
                            method: "DELETE",
                        }
                    );

                    if (!response.ok) {
                        await alfAlert(
                            await readErrorMessage(response)
                        );
                        return;
                    }

                    window.location.reload();
                });
            });
        });

    document.addEventListener("click", closeMenus);
});
