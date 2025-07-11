from .model import Task, session_scope


def add_task(name, details, category, priority) -> None:
    with session_scope() as session:
        task = Task(
            name=name,
            details=details,
            category=category,
            priority=priority,
            is_complete=False,
        )
        session.add(task)


def delete_task(task_id) -> None:
    with session_scope() as session:
        task = session.get(Task, task_id)
        if task:
            session.delete(task)


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


def edit_task(task_id, name, details, category, priority) -> None:
    with session_scope() as session:
        task = session.get(Task, task_id)
        if task:
            task.name = name
            task.details = details
            task.category = category
            task.priority = priority
