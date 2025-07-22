from .model import Task, session_scope


def add_task(name, details, category, priority, effort,complete_by) -> None:
    with session_scope() as session:
        task = Task(
            name=name,
            details=details,
            category=category.lower(),
            priority=priority,
            is_complete=False,
            archived=False,
            effort=effort,
            complete_by=complete_by
        )
        session.add(task)


def delete_task(task_id) -> None:
    with session_scope() as session:
        task = session.get(Task, task_id)
        if task:
            task.archived = True


def mark_task_complete(task_id) -> None:
    with session_scope() as session:
        task = session.get(Task, task_id)
        if task:
            task.is_complete = True


def mark_task_incomplete(task_id) -> None:
    with session_scope() as session:
        task = session.get(Task, task_id)
        if task:
            task.is_complete = False


def edit_task(task_id, name, details, category, priority, effort, complete_by) -> None:
    with session_scope() as session:
        task = session.get(Task, task_id)
        if task:
            task.name = name
            task.details = details
            task.category = category
            task.priority = priority
            task.effort = effort
            task.complete_by = complete_by

def get_unique_categories(active_only: bool) -> list[str]:
    with session_scope() as session:
        result = session.query(Task.category)
        if active_only:
            return [row[0] for row in result.filter_by(archived=False).distinct().all()]
        return [row[0] for row in result.distinct().all()]