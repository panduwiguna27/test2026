import logging
from django.db import transaction
from django.utils import timezone

from scheduler_app.models import Task, TaskExecutionLog
from scheduler_app.services.executors import ExecutorRegistry, build_default_registry

logger = logging.getLogger('scheduler_app.scheduler')


class TaskScheduler:
    def __init__(self, registry: ExecutorRegistry | None = None) -> None:
        self.registry = registry or build_default_registry()

    def run_pending(self) -> int:
        now = timezone.now()
        pending_tasks = Task.objects.select_related('user').filter(
            status=Task.Status.PENDING,
            scheduled_for__lte=now,
            user__is_active=True,
        )

        processed_count = 0
        for task in pending_tasks:
            processed_count += 1
            self._execute_task(task)

        return processed_count

    @transaction.atomic
    def _execute_task(self, task: Task) -> None:
        task.status = Task.Status.RUNNING
        task.save(update_fields=['status', 'updated_at'])

        if not task.user.can_execute_task():
            message = f'User {task.user.username} exceeded daily quota={task.user.quota_per_day}'
            logger.warning(message)
            task.status = Task.Status.FAILED
            task.save(update_fields=['status', 'updated_at'])
            TaskExecutionLog.objects.create(
                task=task,
                user=task.user,
                status=TaskExecutionLog.Status.SKIPPED,
                message=message,
            )
            return

        try:
            executor = self.registry.get(task.action)
            message = executor.execute(task)
            task.status = Task.Status.SUCCESS
            task.save(update_fields=['status', 'updated_at'])
            TaskExecutionLog.objects.create(
                task=task,
                user=task.user,
                status=TaskExecutionLog.Status.SUCCESS,
                message=message,
            )
            logger.info('Task id=%s action=%s completed', task.id, task.action)
        except Exception as exc:
            logger.exception('Task id=%s failed', task.id)
            task.status = Task.Status.FAILED
            task.save(update_fields=['status', 'updated_at'])
            TaskExecutionLog.objects.create(
                task=task,
                user=task.user,
                status=TaskExecutionLog.Status.FAILED,
                message=str(exc),
            )
