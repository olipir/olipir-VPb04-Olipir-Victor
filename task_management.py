"""Система управления задачами (Todo-лист) на основе ООП."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


PRIORITY_MAP: dict[str, int] = {
    "low": 1,
    "medium": 2,
    "high": 3,
}


def _normalize_priority(priority: str | int) -> int:
    """Приводит приоритет к числовому значению 1–3."""
    if isinstance(priority, int):
        if priority not in (1, 2, 3):
            raise ValueError("Приоритет должен быть 1, 2 или 3")
        return priority
    if priority not in PRIORITY_MAP:
        raise ValueError('Приоритет должен быть "low", "medium" или "high"')
    return PRIORITY_MAP[priority]


class Task:
    """Описывает отдельную задачу."""

    def __init__(
        self,
        id: int,
        title: str,
        description: str = "",
        project_id: int | None = None,
        is_done: bool = False,
        due_date: datetime | None = None,
        priority: str | int = "medium",
        created_at: datetime | None = None,
    ) -> None:
        self.id = id
        self.title = title
        self.description = description
        self.project_id = project_id
        self.is_done = is_done
        self.due_date = due_date
        self.priority = priority
        self.created_at = created_at or datetime.now()

    def mark_as_done(self) -> None:
        """Помечает задачу как выполненную."""
        self.is_done = True

    def mark_as_undone(self) -> None:
        """Снимает отметку о выполнении."""
        self.is_done = False

    def update_description(self, new_text: str) -> None:
        """Обновляет описание задачи."""
        self.description = new_text

    def set_due_date(self, date: datetime) -> None:
        """Устанавливает или обновляет дедлайн."""
        self.due_date = date

    def set_priority(self, priority: str | int) -> None:
        """Устанавливает приоритет задачи."""
        _normalize_priority(priority)
        self.priority = priority

    def is_overdue(self) -> bool:
        """Проверяет, просрочена ли невыполненная задача."""
        if self.is_done or self.due_date is None:
            return False
        return self.due_date < datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """Возвращает представление задачи в виде словаря."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "project_id": self.project_id,
            "is_done": self.is_done,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
        }


class Project:
    """Группирует задачи по смысловым блокам."""

    def __init__(
        self,
        id: int,
        name: str,
        owner_id: int,
        created_at: datetime | None = None,
    ) -> None:
        self.id = id
        self.name = name
        self.owner_id = owner_id
        self.tasks: list[Task] = []
        self.created_at = created_at or datetime.now()

    def add_task(self, task: Task) -> None:
        """Добавляет задачу в проект и связывает её по project_id."""
        task.project_id = self.id
        if task not in self.tasks:
            self.tasks.append(task)

    def remove_task(self, task_id: int) -> Task | None:
        """Удаляет задачу из проекта и очищает project_id."""
        for index, task in enumerate(self.tasks):
            if task.id == task_id:
                task.project_id = None
                return self.tasks.pop(index)
        return None

    def get_tasks(
        self,
        filter_done: bool | None = None,
        filter_priority: str | None = None,
    ) -> list[Task]:
        """Возвращает список задач с фильтрацией по статусу и приоритету."""
        result = self.tasks

        if filter_done is not None:
            result = [task for task in result if task.is_done == filter_done]

        if filter_priority is not None:
            target = _normalize_priority(filter_priority)
            result = [
                task
                for task in result
                if _normalize_priority(task.priority) == target
            ]

        return result

    def get_overdue_tasks(self) -> list[Task]:
        """Возвращает список просроченных задач."""
        return [task for task in self.tasks if task.is_overdue()]

    def rename(self, new_name: str) -> None:
        """Изменяет название проекта."""
        self.name = new_name

    def to_dict(self, include_tasks: bool = False) -> dict[str, Any]:
        """Сериализует проект в словарь."""
        data: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat(),
            "task_count": len(self.tasks),
        }
        if include_tasks:
            data["tasks"] = [task.to_dict() for task in self.tasks]
        return data


class User:
    """Представляет пользователя системы, владеет проектами и задачами."""

    _next_project_id: int = 1

    def __init__(self, id: int, username: str, email: str) -> None:
        self.id = id
        self.username = username
        self.email = email
        self.projects: list[Project] = []

    def create_project(self, name: str) -> Project:
        """Создаёт новый проект и добавляет его в список projects."""
        project = Project(id=User._next_project_id, name=name, owner_id=self.id)
        User._next_project_id += 1
        self.projects.append(project)
        return project

    def get_projects(self) -> list[Project]:
        """Возвращает все проекты пользователя."""
        return list(self.projects)

    def get_all_tasks(self) -> list[Task]:
        """Собирает все задачи пользователя из всех его проектов."""
        tasks: list[Task] = []
        for project in self.projects:
            tasks.extend(project.tasks)
        return tasks

    def to_dict(self, include_projects: bool = False) -> dict[str, Any]:
        """Представление пользователя в виде словаря."""
        data: dict[str, Any] = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "project_count": len(self.projects),
        }
        if include_projects:
            data["projects"] = [
                project.to_dict(include_tasks=True) for project in self.projects
            ]
        return data


class TaskManager:
    """Глобальное хранилище задач для поиска и отчётов."""

    _next_task_id: int = 1

    def __init__(self) -> None:
        self._tasks: dict[int, Task] = {}

    def create_task(
        self,
        title: str,
        description: str = "",
        due_date: datetime | None = None,
        priority: str | int = "medium",
    ) -> Task:
        """Создаёт задачу с автоматическим id и регистрирует её."""
        task = Task(
            id=TaskManager._next_task_id,
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
        )
        TaskManager._next_task_id += 1
        self.register_task(task)
        return task

    def register_task(self, task: Task) -> None:
        """Регистрирует задачу в глобальном хранилище."""
        self._tasks[task.id] = task

    def get_task(self, task_id: int) -> Task | None:
        """Возвращает задачу по id."""
        return self._tasks.get(task_id)

    def get_all_overdue(self) -> list[Task]:
        """Собирает просроченные задачи для отчёта."""
        return [task for task in self._tasks.values() if task.is_overdue()]


if __name__ == "__main__":
    print("=== Демонстрация системы управления задачами ===\n")

    user = User(id=1, username="victor", email="victor@example.com")
    print(f"Пользователь: {user.username} ({user.email})")

    work_project = user.create_project("Работа")
    home_project = user.create_project("Дом")
    print(f"Проекты: {[p.name for p in user.get_projects()]}")

    task_manager = TaskManager()

    task1 = task_manager.create_task(
        title="Подготовить отчёт",
        description="Квартальный отчёт для руководства",
        due_date=datetime.now() + timedelta(days=3),
        priority="high",
    )
    task2 = task_manager.create_task(
        title="Созвон с командой",
        due_date=datetime.now() + timedelta(days=1),
        priority="medium",
    )
    task3 = task_manager.create_task(
        title="Купить продукты",
        description="Молоко, хлеб, яйца",
        due_date=datetime.now() - timedelta(days=1),
        priority="low",
    )
    task4 = task_manager.create_task(
        title="Прочитать документацию",
        priority=2,
    )

    work_project.add_task(task1)
    work_project.add_task(task2)
    work_project.add_task(task4)
    home_project.add_task(task3)

    print(f"\nЗадачи в проекте «{work_project.name}»:")
    for task in work_project.get_tasks():
        status = "выполнена" if task.is_done else "активна"
        print(f"  [{status}] {task.title} (приоритет: {task.priority})")

    task1.mark_as_done()
    print(f"\nЗадача «{task1.title}» выполнена: is_done={task1.is_done}")

    task4.update_description("Изучить раздел по ООП")
    task4.set_priority("high")
    print(
        f"Обновлена задача «{task4.title}»: {task4.description}, "
        f"приоритет: {task4.priority}"
    )

    undone_high = work_project.get_tasks(filter_done=False, filter_priority="high")
    print(f"\nНевыполненные задачи с высоким приоритетом в «{work_project.name}»:")
    for task in undone_high:
        print(f"  - {task.title}")

    overdue_in_home = home_project.get_overdue_tasks()
    print(f"\nПросроченные задачи в «{home_project.name}»:")
    for task in overdue_in_home:
        print(f"  - {task.title} (дедлайн: {task.due_date})")

    all_overdue = task_manager.get_all_overdue()
    print(f"\nВсе просроченные задачи: {[t.title for t in all_overdue]}")

    print(f"\nВсе задачи пользователя ({len(user.get_all_tasks())}):")
    for task in user.get_all_tasks():
        print(f"  - [{task.id}] {task.title}")

    home_project.rename("Быт и покупки")
    print(f"\nПроект переименован: «{home_project.name}»")

    removed = home_project.remove_task(task3.id)
    if removed:
        print(
            f"Задача «{removed.title}» удалена из проекта "
            f"(project_id={removed.project_id})"
        )
        print(f"Задача остаётся в TaskManager: {task_manager.get_task(task3.id) is not None}")

    print("\n--- Сериализация пользователя ---")
    print(user.to_dict(include_projects=True))
