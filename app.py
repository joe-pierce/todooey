from nicegui import ui

from src.actions import (
    add_task,
    delete_task,
    edit_task,
    mark_task_complete,
    mark_task_incomplete,
)
from src.model import Task, session_scope


def update_task_list() -> None:
    new_data = []
    with session_scope() as session:
        for _i, task in enumerate(session.query(Task).all()):
            new_data.append(
                {
                    "id": task.id,
                    "name": task.name,
                    "details": task.details,
                    "category": task.category,
                    "priority": task.priority,
                    "is_complete": "✅" if task.is_complete else "⬜",
                },
            )
        task_table.options["rowData"] = new_data
        task_table.update()


def refresh_task_list() -> None:
    """Refresh the task table with current tasks from the database."""
    new_data = []
    with session_scope() as session:
        for i, task in enumerate(session.query(Task).all()):
            new_data.append(
                {
                    "id": task.id,
                    "name": task.name,
                    "details": task.details,
                    "category": task.category,
                    "priority": task.priority,
                    "is_complete": "✅" if task.is_complete else "⬜",
                },
            )
        task_table.run_grid_method("setGridOption", "rowData", new_data)

    # task_table.run_grid_method("setColumnsVisible", ["details"], details_column_visible["state"])

    # 🧠 Re-select row if still present
    if selected_row["id"] is not None:
        # Find the row index with matching ID
        for i, row in enumerate(new_data):
            if row["id"] == selected_row["id"]:
                task_table.run_row_method(i, "setSelected", True)

                break


# Title
ui.label("📝 Task Manager").classes("text-2xl font-bold m-4")
selected_row = {"id": None}
details_column_visible = {"state": True}


def handle_row_select(e) -> None:
    selected_row["id"] = e.args["data"]["id"]


def double_click_toggle_completed(e) -> None:
    selected_row["id"] = e.args["data"]["id"]
    if e.args["colId"] != "is_complete":
        return
    if e.args["data"]["is_complete"] == "⬜":
        do_mark_complete()
    else:
        do_mark_not_complete()


class ToggleDetailsButton(ui.button):
    def __init__(self, *args, **kwargs) -> None:
        self.label_show = "🙉 Show details"
        self.label_hide = "🙈 Hide details"
        self.details_visible = True  # assume visible initially
        self.current_label = self.label_hide
        super().__init__(*args, **kwargs)
        self.on("click", self.toggle)

    def toggle(self) -> None:
        self.details_visible = not self.details_visible
        self.current_label = self.label_hide if self.details_visible else self.label_show
        details_column_visible["state"] = self.details_visible
        task_table.run_grid_method(
            "setColumnsVisible",
            ["details"],
            self.details_visible,
        )
        self.update()

    def update(self) -> None:
        self.set_text(self.current_label)

        super().update()


# Task Table

task_table = (
    ui.aggrid(
        {
            "defaultColDef": {"flex": 1},
            "columnDefs": [
                {"headerName": "ID", "field": "id", "width": 50, "hide": True},
                {
                    "headerName": "Name",
                    "field": "name",
                    "filter": "agTextColumnFilter",
                    "floatingFilter": True,
                    "width": 200,
                },
                {
                    "headerName": "Details",
                    "field": "details",
                    "filter": "agTextColumnFilter",
                    "floatingFilter": True,
                    "width": 300,
                },
                {
                    "headerName": "Category",
                    "field": "category",
                    "filter": "agTextColumnFilter",
                    "floatingFilter": True,
                    "width": 150,
                },
                {
                    "headerName": "Priority",
                    "field": "priority",
                    "filter": "agNumberColumnFilter",
                    "floatingFilter": True,
                    "width": 50,
                    "sortable": True,
                },
                {"headerName": "Completed", "field": "is_complete", "width": 50},
            ],
            "rowData": [],
            "rowSelection": "single",
        },
    )
    .on("cellDoubleClicked", double_click_toggle_completed)
    .on("cellClicked", handle_row_select)
)

# task_table.add_slot('header', r'''
#     <q-tr :props="props">
#         <q-th auto-width />
#         <q-th v-for="col in props.cols" :key="col.name" :props="props">
#             {{ col.label }}
#         </q-th>
#     </q-tr>
# ''')
# task_table.add_slot('body', r'''
#     <q-tr :props="props">
#         <q-td auto-width>
#             <q-btn size="sm" color="accent" round dense
#                 @click="props.expand = !props.expand"
#                 :icon="props.expand ? 'remove' : 'add'" />
#         </q-td>
#         <q-td v-for="col in props.cols" :key="col.name" :props="props">
#             {{ col.value }}
#         </q-td>
#     </q-tr>
#     <q-tr v-show="props.expand" :props="props">
#         <q-td colspan="100%">
#             <div class="text-left">{{ props.row.details }}</div>
#         </q-td>
#     </q-tr>
# ''')

# Action buttons
with ui.row().classes("m-4"):

    def do_add_task() -> None:
        add_dialog.open()

    def do_mark_complete() -> None:
        if selected_row["id"]:
            mark_task_complete(selected_row["id"])
            refresh_task_list()
            ui.notify("Task marked complete")

    def do_mark_not_complete() -> None:
        if selected_row["id"]:
            mark_task_incomplete(selected_row["id"])
            refresh_task_list()
            ui.notify("Task marked incomplete")

    def do_delete() -> None:
        if selected_row["id"]:
            delete_task(selected_row["id"])
            selected_row["id"] = None
            refresh_task_list()
            ui.notify("Task deleted")

    def open_edit_dialog() -> None:
        if not selected_row["id"]:
            return
        with session_scope() as session:
            task = session.query(Task).get(selected_row["id"])
            if not task:
                return

            edit_name.value = task.name
            edit_details.value = task.details
            edit_category.value = task.category
            edit_priority.value = str(task.priority)
            edit_dialog.open()

    def do_clear() -> None:
        if selected_row["id"] is not None:
            task_table.run_grid_method("deselectAll")

            selected_row["id"] = None

    ui.button("✏️ Add task", on_click=do_add_task).props("color=orange")
    ui.button("✅ Mark Complete", on_click=do_mark_complete).props(
        "color=green",
    ).bind_enabled_from(selected_row, "id")
    ui.button("📝 Edit", on_click=open_edit_dialog).props(
        "color=blue",
    ).bind_enabled_from(selected_row, "id")
    ui.button("🗑️ Delete", on_click=do_delete).props("color=red").bind_enabled_from(
        selected_row,
        "id",
    )
    ui.button("💥 Clear selection", on_click=do_clear).props(
        "color=grey",
    ).bind_enabled_from(selected_row, "id")
    ToggleDetailsButton().props("color=brown")

t = ...
# Add dialog
with ui.dialog() as add_dialog, ui.card():
    ui.label("Add Task")

    add_name = ui.input("Name").props("outlined")
    add_details = ui.input("Details").props("outlined")
    add_category = ui.input("Category").props("outlined")
    add_priority = ui.input("Priority").props("outlined type=number")

    def handle_add() -> None:
        add_task(
            add_name.value,
            add_details.value,
            add_category.value,
            int(add_priority.value),
        )
        refresh_task_list()
        ui.notify("Task added ✅")
        add_dialog.close()

    ui.button("Add Task", on_click=handle_add).classes("bg-primary text-white")

# Edit Dialog
with ui.dialog() as edit_dialog, ui.card():
    ui.label("Edit Task")

    edit_name = ui.input("Name").props("outlined")
    edit_details = ui.input("Details").props("outlined")
    edit_category = ui.input("Category").props("outlined")
    edit_priority = ui.input("Priority").props("outlined type=number")

    def submit_edit() -> None:
        if selected_row["id"]:
            edit_task(
                selected_row["id"],
                edit_name.value,
                edit_details.value,
                edit_category.value,
                int(edit_priority.value),
            )
            refresh_task_list()
            edit_dialog.close()
            ui.notify("Task updated")

    ui.button("Save Changes", on_click=submit_edit).classes(
        "mt-2 bg-primary text-white",
    )

# Initial load of tasks
update_task_list()

ui.run()
# if __name__=="__main__":
# ui.run(native=True, reload=False, window_size=(1300, 900))
