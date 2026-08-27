let currentMindmapId = null;

const options = {
    container: "jsmind-container",
    editable: true,
    theme: "primary",
    mode: "full",
    view: {
        draggable: true,
        hide_scrollbars_when_draggable: true
    }
};

const mindmap = new jsMind(options);

document
    .querySelector("#new-mindmap")
    .addEventListener("click", function () {
        currentMindmapId = null;

        document.querySelector("#mindmap-empty").style.display =
            "none";

        const mindmapName = "New Mindmap";

        const newMind = {
            meta: {
                name: mindmapName,
                author: "ALF",
                version: "0.1"
            },
            format: "node_array",
            data: [
                {
                    id: "root",
                    isroot: true,
                    topic: mindmapName,
                    expanded: true
                }
            ]
        };

        mindmap.show(newMind);
        mindmap.select_node("root");
        mindmap.view.e_panel.focus();
    });

document
    .querySelector("#save-mindmap")
    .addEventListener("click", async function () {
        const documentData = mindmap.get_data("node_array");

        const rootNode = documentData.data.find(
            function (node) {
                return node.isroot;
            }
        );

        const name = rootNode
            ? rootNode.topic.trim() || "New Mindmap"
            : "New Mindmap";

        const isNewMindmap = currentMindmapId === null;
        const response = await fetch("/mindmaps/save", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                id: currentMindmapId,
                category: "Uncategorised",
                name: name,
                content: JSON.stringify(documentData)
            })
        });

        if (!response.ok) {
            return;
        }

        const result = await response.json();

        currentMindmapId = result.id;

        if (isNewMindmap) {
            const mapItem = document.createElement("button");
            mapItem.type = "button";
            mapItem.className = "mindmap-item";
            mapItem.dataset.mindmapId = result.id;

            mapItem.draggable = true;

            mapItem.addEventListener("dragstart", function (event) {
                event.dataTransfer.setData(
                    "text/plain",
                    mapItem.dataset.mindmapId
                );
            });

            const mapName = document.createElement("span");
            mapName.textContent = name;

            mapItem.append(mapName);

            const uncategorisedCategory =
                Array.from(
                    document.querySelectorAll(".mindmap-category")
                ).find(
                    function (category) {
                        return (
                            category.querySelector("h3")?.textContent.trim() ===
                            "Uncategorised"
                        );
                    }
                );

            if (uncategorisedCategory) {
                uncategorisedCategory
                    .querySelector(".mindmap-list")
                    .append(mapItem);
            }
        }
    });

    document
        .querySelectorAll(".mindmap-item")
        .forEach(function (item) {
            item.draggable = true;

            item.addEventListener("dragstart", function (event) {
                event.dataTransfer.setData(
                    "text/plain",
                    item.dataset.mindmapId
                );
            });
        });

    document
        .querySelectorAll(".mindmap-category")
        .forEach(function (category) {
            const heading = category.querySelector("h3");

                if (
                    heading.textContent.trim() !==
                    "Uncategorised"
                ) {
                    heading.draggable = true;
                }

            heading.addEventListener("dragstart", function (event) {
                event.dataTransfer.setData(
                    "application/x-mindmap-category",
                    category.dataset.categoryId
                );
            });
        });

    document
        .querySelectorAll(".mindmap-category")
        .forEach(function (category) {
                category.addEventListener("dragover", function (event) {
                    if (
                        event.dataTransfer.types.includes(
                            "application/x-mindmap-category"
                        ) ||
                        event.dataTransfer.types.includes("text/plain")
                    ) {
                        event.preventDefault();
                    }
                });

            category.addEventListener("drop", async function (event) {
                event.preventDefault();

                const categoryId =
                    event.dataTransfer.getData(
                        "application/x-mindmap-category"
                    );

                if (categoryId) {
                    const draggedCategory =
                        document.querySelector(
                            `.mindmap-category[data-category-id="${categoryId}"]`
                        );

                    if (!draggedCategory || draggedCategory === category) {
                        return;
                    }

                    const categories = Array.from(
                        document.querySelectorAll(".mindmap-category")
                    );

                    const draggedIndex =
                        categories.indexOf(draggedCategory);
                    const targetIndex = categories.indexOf(category);

                    const rect = category.getBoundingClientRect();
                    const insertAfter =
                        event.clientY >= rect.top + rect.height / 2;

                        let position = targetIndex;

                        if (insertAfter) {
                            position += 1;
                        }

                        if (draggedIndex < position) {
                            position -= 1;
                        }

                        const uncategorisedCategory = categories.find(
                            function (item) {
                                return (
                                    item.querySelector("h3")?.textContent.trim() ===
                                    "Uncategorised"
                                );
                            }
                        );

                        if (uncategorisedCategory) {
                            const uncategorisedIndex =
                                categories.indexOf(uncategorisedCategory);

                            if (position <= uncategorisedIndex) {
                                position = uncategorisedIndex + 1;
                            }
                        }

                    const response = await fetch(
                        `/mindmap-categories/${categoryId}/move`,
                        {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json"
                            },
                            body: JSON.stringify({
                                position: position
                            })
                        }
                    );

                    if (!response.ok) {
                        return;
                    }

                        const orderedCategories = Array.from(
                            document.querySelectorAll(".mindmap-category")
                        );

                        const newIndex = position;

                        if (newIndex < orderedCategories.length) {
                            category.parentElement.insertBefore(
                                draggedCategory,
                                orderedCategories[newIndex]
                            );
                        } else {
                            category.parentElement.append(draggedCategory);
                        }

                    return;
                }

                const mindmapId =
                    event.dataTransfer.getData("text/plain");

                if (!mindmapId) {
                    return;
                }

                const categoryName = category
                    .querySelector("h3")
                    .textContent.trim();

                const response = await fetch(
                    `/mindmaps/${mindmapId}/move`,
                    {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            category: categoryName
                        })
                    }
                );

                if (!response.ok) {
                    return;
                }

                const mapItem = document.querySelector(
                    `.mindmap-item[data-mindmap-id="${mindmapId}"]`
                );

                if (!mapItem) {
                    return;
                }

                category
                    .querySelector(".mindmap-list")
                    .append(mapItem);
            });
        });

    document
        .querySelectorAll(".mindmap-category h3")
        .forEach(function (heading) {
            const category = heading.textContent.trim();
            const storageKey = `mindmap-category-collapsed:${category}`;

            if (localStorage.getItem(storageKey) === "true") {
                heading.parentElement.classList.add("collapsed");
            }

            heading.addEventListener("click", function () {
                const categoryElement = heading.parentElement;
                const collapsed =
                    categoryElement.classList.toggle("collapsed");

                localStorage.setItem(
                    storageKey,
                    collapsed ? "true" : "false"
                );
            });
        });


document
    .querySelectorAll(".mindmap-item")
    .forEach(function (item) {
        item.addEventListener("click", async function () {
            const mindmapId = item.dataset.mindmapId;

            const response = await fetch(
                `/mindmaps/${mindmapId}`
            );

            if (!response.ok) {
                return;
            }

            const savedMindmap = await response.json();
            const savedContent = JSON.parse(
                savedMindmap.content
            );

            currentMindmapId = savedMindmap.id;

            document.querySelector("#mindmap-empty").style.display =
                "none";

            mindmap.show(savedContent);
            mindmap.select_node("root");
            mindmap.view.e_panel.focus();
        });
    });
