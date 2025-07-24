from nicegui import ui
from datetime import datetime
from sqlalchemy import nulls_last

from src.model import Task, session_scope
from src.actions import (
    add_task,
    delete_task,
    edit_task,
    mark_task_complete,
    mark_task_incomplete,
    get_unique_categories,
)

ui.add_body_html('<style>.ag-row-hover .ag-cell  { background-color: inherit}</style>')

# Title
ui.label("📝 Todooey").classes("text-2xl font-bold")
selected_row = {"id": None}
details_column_visible = {"state": True}
all_active_categories = {}
all_categories = get_unique_categories(active_only=False)

with ui.row().classes("items-center gap-4 q-mt-md q-mb-sm"):
    def colored_box(label, color):
        with ui.row().classes("items-center gap-2"):
            ui.element("div").style(f"width: 16px; height: 16px; background-color: {color}; border-radius: 3px;")
            ui.label(label).classes("text-sm")

    colored_box("Overdue", "#d96550")
    colored_box("Today", "#f2aa4b")
    colored_box("This week", "#f7ecb5")
    colored_box("The rest", "#eae9e9")  # grey or white for everything else


def update_task_list() -> None:
    new_data = []
    with session_scope() as session:
        for _i, task in enumerate(session.query(Task).filter_by(archived=False).order_by(Task.is_complete, nulls_last(Task.complete_by), Task.priority, Task.effort).all()):
            new_data.append(
                {
                    "id": task.id,
                    "name": task.name,
                    "details": task.details,
                    "category": task.category,
                    "priority": task.priority,
                    "effort": task.effort,
                    "complete_by": task.complete_by.strftime('%d-%m-%Y') if task.complete_by else None,
                    "is_complete": "✅" if task.is_complete else "⬜",
                },
            )
        task_table.options["rowData"] = new_data
        task_table.update()
    update_all_categories()


def refresh_task_list() -> None:
    """Refresh the task table with current tasks from the database."""
    new_data = []
    with session_scope() as session:
        for i, task in enumerate(session.query(Task).filter_by(archived=False).order_by(Task.is_complete, nulls_last(Task.complete_by), Task.priority, Task.effort).all()):
            if all_active_categories.get(task.category, True):
                new_data.append(
                    {
                        "id": task.id,
                        "name": task.name,
                        "details": task.details,
                        "category": task.category,
                        "priority": task.priority,
                        "effort": task.effort,
                        "complete_by": task.complete_by.strftime('%d-%m-%Y') if task.complete_by else None,
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
    update_all_categories()


def update_all_categories():
    latest = get_unique_categories(active_only=True)
    for key in all_active_categories.copy():
        if key not in latest:
            del all_active_categories[key]

    for cat in latest:
        if cat not in all_active_categories:
            all_active_categories[cat] = True

    refresh_category_buttons()
    all_categories[:] = get_unique_categories(active_only=False)
    add_category.set_autocomplete(all_categories)
    edit_category.set_autocomplete(all_categories)


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


class HideCategoryButton(ui.button):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.label = args[0]
        self.data_visible = all_active_categories[self.label]
        self.on("click", self.toggle)

    def toggle(self) -> None:
        self.data_visible = not self.data_visible
        all_active_categories[self.label] = self.data_visible
        self.update()
        refresh_task_list()

    def update(self) -> None:
        self.props(f'color={"green" if self.data_visible else "grey"}')
        super().update()


# Task Table

task_table = (
    ui.aggrid(
        {
            "defaultColDef": {"flex": 1},
            "enableCellTextSelection": True,
            "columnDefs": [
                {"headerName": "ID", "field": "id", "width": 50, "hide": True},
                {
                    "headerName": "Name",
                    "field": "name",
                    "width": 200,
                },
                {
                    "headerName": "Details",
                    "field": "details",
                    "width": 300,
                    "wrapText": True,
                    "autoHeight": True,
                },
                {
                    "headerName": "Category",
                    "field": "category",
                    "width": 150,
                },
                {
                    "headerName": "Priority",
                    "field": "priority",
                    "width": 50,
                    "sortable": True,
                },
                {
                    "headerName": "Effort",
                    "field": "effort",
                    "width": 50,
                },
                {
                    "headerName": "Complete by",
                    "field": "complete_by",
                    "width": 100
                    
                },
                {
                    "headerName": "Completed",
                    "field": "is_complete",
                    "width": 50,
                    "cellStyle": {"fontSize": "20px", "textAlign": "center"},
                },
            ],
            "rowData": [],
            "rowSelection": "single",
            ":getRowStyle": """
                    function(params) {
                        const completeBy = params.data.complete_by;
                        const isComplete = params.data.is_complete === "✅";
                        if (!completeBy || isComplete) return null;
                        
                        const today = new Date();
                        const [day, month, year] = completeBy.split("-").map(Number);
                        const dueDate = new Date(year, month - 1, day);

                        // Remove time from today
                        today.setHours(0, 0, 0, 0);
                        dueDate.setHours(0, 0, 0, 0);

                        // Start of the week (Monday)
                        const startOfWeek = new Date(today);
                        startOfWeek.setDate(today.getDate() - today.getDay() + 1);

                        // End of the week (Sunday)
                        const endOfWeek = new Date(startOfWeek);
                        endOfWeek.setDate(startOfWeek.getDate() + 6);

                        if (dueDate < today) {
                            return { backgroundColor: '#d96550' }; //
                        } else if (dueDate.getTime() === today.getTime()) {
                            return { backgroundColor: '#f2aa4b' }; //
                        } else if (dueDate > today && dueDate <= endOfWeek) {
                            return { backgroundColor: '#f7ecb5' }; //
                        }
                        return null;
                    }
                """
            
            
        },
    )
    .style("height: 450px")
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
with ui.row().classes("gap-2"):

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
            edit_priority.value = int(task.priority)
            edit_effort.value = int(task.effort)
            edit_complete_by.value = task.complete_by.strftime('%Y-%m-%d') if task.complete_by else None
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


def validate_int(value):
    try:
        int(value)
        return True
    except: 
        return False
    

# Add dialog
with ui.dialog() as add_dialog, ui.card().style("width: 700px"):
    ui.label("Add Task")
    
        
    add_name = ui.input("Name").props("outlined").classes("w-full")
    add_details = ui.textarea("Details").props("outlined").classes("w-full")
    add_category = ui.input("Category", autocomplete=all_categories).props("outlined").classes("w-full")
    add_priority = ui.input("Priority", validation={'Must be an int': validate_int}).props("outlined type=number").classes("w-full")
    add_effort = ui.input("Effort", validation={'Must be an int': validate_int}).props("outlined type=number").classes("w-full")
    add_complete_by = ui.date("Complete by").props("outlined").classes("w-40 text-sm p-1")

    def handle_add() -> None:
        try:
            add_task(
            add_name.value,
            add_details.value,
            add_category.value,
            int(add_priority.value),
            int(add_effort.value),
            datetime.strptime(add_complete_by.value, '%Y-%m-%d')
            )
            refresh_task_list()
            ui.notify("Task added ✅")
        except Exception as e:
            print(e)
            ui.notify("Failed to add task ❌")
        else:
            add_dialog.close()
            add_name.set_value(None)
            add_details.set_value(None)
            add_category.set_value(None)
            add_priority.set_value(None)
            add_effort.set_value(None)
            add_complete_by.set_value(None)

            

    ui.button("Add Task", on_click=handle_add).bind_enabled_from(add_priority, "value").classes("bg-primary text-white")

# Edit Dialog
with ui.dialog() as edit_dialog, ui.card().style("width: 700px"):
    ui.label("Edit Task")

    edit_name = ui.input("Name").props("outlined").classes("w-full")
    edit_details = ui.textarea("Details").props("outlined").classes("w-full")
    edit_category = ui.input("Category", autocomplete=all_categories).props("outlined").classes("w-full")
    edit_priority = ui.input("Priority", validation={'Must be an int': validate_int}).props("outlined type=number").classes("w-full")
    edit_effort = ui.input("Effort", validation={'Must be an int': validate_int}).props("outlined type=number").classes("w-full")
    edit_complete_by = ui.date("Complete by").props("outlined").classes("w-50")

    def submit_edit() -> None:
        if selected_row["id"]:
            try:
                edit_task(
                    selected_row["id"],
                    edit_name.value,
                    edit_details.value,
                    edit_category.value,
                    int(edit_priority.value),
                    int(edit_effort.value),
                    datetime.strptime(edit_complete_by.value, '%Y-%m-%d') if edit_complete_by.value else None
                )
                refresh_task_list()
                ui.notify("Task updated ✅")
            except Exception as e:
                print(e)
                ui.notify("Failed to edit task ❌")
                
            else:
                edit_dialog.close()

    ui.button("Save Changes", on_click=submit_edit).classes(
        "mt-2 bg-primary text-white",
    )


def refresh_category_buttons():
    category_row.clear()
    with category_row:
        for category in all_active_categories:
            HideCategoryButton(category)


ui.separator()
category_row = ui.row().classes("gap-2")

# Initial load of tasks
update_task_list()



ui.run()
