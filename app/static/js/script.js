
document.addEventListener("DOMContentLoaded", function () {

    const yearElement = document.getElementById("current-year");

    if (yearElement) {
        yearElement.textContent = new Date().getFullYear();
    }

    /* Task form validation */

    const taskForms = document.querySelectorAll(
        'form[action*="/tasks/create"], form[action*="/tasks/edit/"]'
    );

    taskForms.forEach(function (form) {

        form.addEventListener("submit", function (event) {

            const title = form.querySelector('[name="title"]');
            const startDate = form.querySelector('[name="start_date"]');
            const dueDate = form.querySelector('[name="due_date"]');
            const imageInput = form.querySelector('[name="image"]');

            if (title && title.value.trim() === "") {
                event.preventDefault();
                alert("Task title is required.");
                title.focus();
                return;
            }

            if (
                startDate &&
                dueDate &&
                startDate.value &&
                dueDate.value &&
                dueDate.value < startDate.value
            ) {
                event.preventDefault();
                alert("Due date cannot be earlier than start date.");
                dueDate.focus();
                return;
            }

            if (imageInput && imageInput.files.length > 0) {

                const image = imageInput.files[0];

                const allowedTypes = [
                    "image/png",
                    "image/jpeg"
                ];

                const maxSize = 5 * 1024 * 1024;

                if (!allowedTypes.includes(image.type)) {
                    event.preventDefault();
                    alert("Only PNG, JPG and JPEG images are allowed.");
                    imageInput.value = "";
                    return;
                }

                if (image.size > maxSize) {
                    event.preventDefault();
                    alert("Image size must be less than 5 MB.");
                    imageInput.value = "";
                    return;
                }
            }
        });
    });

    /* Search, Filter, Sorting and Results Count */

    const searchInput = document.getElementById("task-search");
    const statusFilter = document.getElementById("status-filter");
    const priorityFilter = document.getElementById("priority-filter");
    const sortFilter = document.getElementById("sort-filter");

    const taskList = document.getElementById("pending-task-list");

    const filterTaskCards = Array.from(
        document.querySelectorAll("[data-filter-task]")
    );

    const noFilterResults = document.getElementById("no-filter-results");
    const filterResultsCount = document.getElementById("filter-results-count");

    function sortTasks() {

        if (!taskList || !sortFilter) {
            return;
        }

        const sortType = sortFilter.value;

        const sortedCards = [...filterTaskCards];

        const priorityOrder = {
            High: 1,
            Medium: 2,
            Low: 3
        };

        sortedCards.sort(function (a, b) {

            const createdA = Date.parse(a.dataset.createdAt || "") || 0;
            const createdB = Date.parse(b.dataset.createdAt || "") || 0;

            const dueA = a.dataset.sortDueDate || "";
            const dueB = b.dataset.sortDueDate || "";

            if (sortType === "newest") {
                return createdB - createdA;
            }

            if (sortType === "oldest") {
                return createdA - createdB;
            }

            if (sortType === "due-early") {

                if (!dueA && !dueB) return 0;
                if (!dueA) return 1;
                if (!dueB) return -1;

                return dueA.localeCompare(dueB);
            }

            if (sortType === "due-late") {

                if (!dueA && !dueB) return 0;
                if (!dueA) return 1;
                if (!dueB) return -1;

                return dueB.localeCompare(dueA);
            }

            if (sortType === "priority") {

                const priorityA = priorityOrder[a.dataset.priority] || 4;
                const priorityB = priorityOrder[b.dataset.priority] || 4;

                return priorityA - priorityB;
            }

            return 0;
        });

        sortedCards.forEach(function (taskCard) {
            taskList.appendChild(taskCard);
        });
    }

    function applyTaskFilters() {

        if (!searchInput || !statusFilter || !priorityFilter) {
            return;
        }

        const searchText = searchInput.value.trim().toLowerCase();
        const selectedStatus = statusFilter.value;
        const selectedPriority = priorityFilter.value;

        let visibleTaskCount = 0;

        const totalTaskCount = filterTaskCards.length;

        filterTaskCards.forEach(function (taskCard) {

            const title = (taskCard.dataset.title || "").toLowerCase();
            const status = taskCard.dataset.status || "";
            const priority = taskCard.dataset.priority || "";

            const matchesSearch = title.includes(searchText);

            const matchesStatus =
                selectedStatus === "All" ||
                status === selectedStatus;

            const matchesPriority =
                selectedPriority === "All" ||
                priority === selectedPriority;

            const shouldDisplay =
                matchesSearch &&
                matchesStatus &&
                matchesPriority;

            taskCard.style.display = shouldDisplay ? "" : "none";

            if (shouldDisplay) {
                visibleTaskCount++;
            }
        });

        if (filterResultsCount) {
            filterResultsCount.textContent =
                "Showing " + visibleTaskCount +
                " of " + totalTaskCount + " tasks";
        }

        if (noFilterResults) {
            noFilterResults.style.display =
                visibleTaskCount === 0 && totalTaskCount > 0
                    ? "block"
                    : "none";
        }
    }

    function updateTaskDisplay() {
        sortTasks();
        applyTaskFilters();
    }

    if (searchInput) {
        searchInput.addEventListener("input", applyTaskFilters);
    }

    if (statusFilter) {
        statusFilter.addEventListener("change", applyTaskFilters);
    }

    if (priorityFilter) {
        priorityFilter.addEventListener("change", applyTaskFilters);
    }

    if (sortFilter) {
        sortFilter.addEventListener("change", updateTaskDisplay);
    }

    updateTaskDisplay();

    /* Completed history drawer */

    const openHistoryButton = document.getElementById("open-history-btn");
    const closeHistoryButton = document.getElementById("close-history-btn");

    const historyDrawer = document.getElementById("history-drawer");
    const drawerOverlay = document.getElementById("drawer-overlay");

    /* Task details modal elements */

    const taskModalOverlay = document.getElementById("task-modal-overlay");
    const closeTaskModalButton = document.getElementById("close-task-modal");

    const modalTitle = document.getElementById("modal-task-title");
    const modalDescription = document.getElementById("modal-task-description");
    const modalStatus = document.getElementById("modal-task-status");
    const modalPriority = document.getElementById("modal-task-priority");

    const modalStartDate = document.getElementById("modal-start-date");
    const modalDueDate = document.getElementById("modal-due-date");
    const modalCompletedDate = document.getElementById("modal-completed-date");

    const completedDateContainer = document.getElementById(
        "completed-date-container"
    );

    const modalImage = document.getElementById("modal-task-image");

    const modalImagePlaceholder = document.getElementById(
        "modal-image-placeholder"
    );

    const modalEditButton = document.getElementById("modal-edit-btn");
    const modalCompleteForm = document.getElementById("modal-complete-form");
    const modalDeleteForm = document.getElementById("modal-delete-form");

    /* Open history drawer */

    function openHistoryDrawer() {

        if (!historyDrawer || !drawerOverlay) {
            return;
        }

        historyDrawer.classList.add("active");
        drawerOverlay.classList.add("active");

        document.body.style.overflow = "hidden";
    }

    /* Close history drawer */

    function closeHistoryDrawer() {

        if (!historyDrawer || !drawerOverlay) {
            return;
        }

        historyDrawer.classList.remove("active");
        drawerOverlay.classList.remove("active");

        if (
            !taskModalOverlay ||
            !taskModalOverlay.classList.contains("active")
        ) {
            document.body.style.overflow = "";
        }
    }

    if (openHistoryButton) {
        openHistoryButton.addEventListener("click", openHistoryDrawer);
    }

    if (closeHistoryButton) {
        closeHistoryButton.addEventListener("click", closeHistoryDrawer);
    }

    if (drawerOverlay) {
        drawerOverlay.addEventListener("click", closeHistoryDrawer);
    }

    /* Open task details modal */

    function openTaskModal(taskCard) {

        if (!taskModalOverlay) {
            return;
        }

        const title = taskCard.dataset.title || "";
        const description = taskCard.dataset.description || "";
        const priority = taskCard.dataset.priority || "";
        const status = taskCard.dataset.status || "";

        const startDate = taskCard.dataset.startDate || "Not specified";
        const dueDate = taskCard.dataset.dueDate || "Not specified";

        const completedAt = taskCard.dataset.completedAt || "";
        const image = taskCard.dataset.image || "";

        modalTitle.textContent = title;

        modalDescription.textContent =
            description || "No description provided.";

        modalStatus.textContent = status;
        modalStatus.className = "task-status";

        if (status === "Completed") {
            modalStatus.classList.add("completed-status");
        } else {
            modalStatus.classList.add("pending-status");
        }

        modalPriority.textContent = "Priority: " + priority;

        modalStartDate.textContent = startDate;
        modalDueDate.textContent = dueDate;

        if (status === "Completed") {

            completedDateContainer.style.display = "block";

            modalCompletedDate.textContent =
                completedAt || "Not available";

        } else {

            completedDateContainer.style.display = "none";
        }

        if (image) {

            modalImage.src = image;
            modalImage.alt = title;

            modalImage.classList.add("visible");
            modalImagePlaceholder.classList.add("hidden");

        } else {

            modalImage.removeAttribute("src");

            modalImage.classList.remove("visible");
            modalImagePlaceholder.classList.remove("hidden");
        }

        modalEditButton.href = taskCard.dataset.editUrl || "#";

        if (status === "Pending") {

            modalCompleteForm.action = taskCard.dataset.completeUrl;
            modalCompleteForm.style.display = "block";

        } else {

            modalCompleteForm.style.display = "none";
        }

        modalDeleteForm.action = taskCard.dataset.deleteUrl;

        taskModalOverlay.classList.add("active");

        document.body.style.overflow = "hidden";
    }

    /* Close task details modal */

    function closeTaskModal() {

        if (!taskModalOverlay) {
            return;
        }

        taskModalOverlay.classList.remove("active");

        if (
            historyDrawer &&
            historyDrawer.classList.contains("active")
        ) {
            document.body.style.overflow = "hidden";
        } else {
            document.body.style.overflow = "";
        }
    }

    /* Task card click events */

    const taskCards = document.querySelectorAll("[data-task-card]");

    taskCards.forEach(function (taskCard) {

        taskCard.addEventListener("click", function () {
            openTaskModal(taskCard);
        });
    });

    if (closeTaskModalButton) {
        closeTaskModalButton.addEventListener("click", closeTaskModal);
    }

    if (taskModalOverlay) {

        taskModalOverlay.addEventListener("click", function (event) {

            if (event.target === taskModalOverlay) {
                closeTaskModal();
            }
        });
    }

    /* Delete confirmation */

    if (modalDeleteForm) {

        modalDeleteForm.addEventListener("submit", function (event) {

            const confirmed = confirm(
                "Are you sure you want to delete this task?"
            );

            if (!confirmed) {
                event.preventDefault();
            }
        });
    }

    /* Keyboard controls */

    document.addEventListener("keydown", function (event) {

        if (event.key === "Escape") {

            if (
                taskModalOverlay &&
                taskModalOverlay.classList.contains("active")
            ) {

                closeTaskModal();

            } else if (
                historyDrawer &&
                historyDrawer.classList.contains("active")
            ) {

                closeHistoryDrawer();
            }
        }
    });

});
