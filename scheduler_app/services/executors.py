import logging
from abc import ABC, abstractmethod
from typing import Dict, Type

from scheduler_app.models import Task

logger = logging.getLogger('scheduler_app.executors')


class TaskExecutor(ABC):
    @abstractmethod
    def execute(self, task: Task) -> str:
        """Execute a task and return execution message."""


class SyncExecutor(TaskExecutor):
    def execute(self, task: Task) -> str:
        target = task.params.get('target', 'unknown-target')
        message = f"[sync] synced target={target}"
        logger.info(message)
        return message


class BackupExecutor(TaskExecutor):
    def execute(self, task: Task) -> str:
        target = task.params.get('target', 'unknown-target')
        destination = task.params.get('destination', 'default-backup-location')
        message = f"[backup] backed up target={target} destination={destination}"
        logger.info(message)
        return message


class DeleteExecutor(TaskExecutor):
    def execute(self, task: Task) -> str:
        target = task.params.get('target', 'unknown-target')
        force = bool(task.params.get('force', False))
        message = f"[delete] delete requested target={target} force={force}"
        logger.info(message)
        return message


class ExecutorRegistry:
    def __init__(self) -> None:
        self._registry: Dict[str, TaskExecutor] = {}

    def register(self, action: str, executor: TaskExecutor) -> None:
        self._registry[action] = executor

    def get(self, action: str) -> TaskExecutor:
        if action not in self._registry:
            raise KeyError(f"No executor registered for action '{action}'")
        return self._registry[action]


DEFAULT_EXECUTORS: Dict[str, Type[TaskExecutor]] = {
    'sync': SyncExecutor,
    'backup': BackupExecutor,
    'delete': DeleteExecutor,
}


def build_default_registry() -> ExecutorRegistry:
    registry = ExecutorRegistry()
    for action, executor_cls in DEFAULT_EXECUTORS.items():
        registry.register(action, executor_cls())
    return registry
