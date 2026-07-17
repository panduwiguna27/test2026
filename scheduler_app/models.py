from django.db import models
from django.utils import timezone


class ManagedUser(models.Model):
	username = models.CharField(max_length=100, unique=True)
	quota_per_day = models.PositiveIntegerField(default=3)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return self.username

	def can_execute_task(self) -> bool:
		start_of_day = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
		execution_count = self.execution_logs.filter(status=TaskExecutionLog.Status.SUCCESS, executed_at__gte=start_of_day).count()
		return execution_count < self.quota_per_day


class Task(models.Model):
	class Status(models.TextChoices):
		PENDING = 'pending', 'Pending'
		RUNNING = 'running', 'Running'
		SUCCESS = 'success', 'Success'
		FAILED = 'failed', 'Failed'

	user = models.ForeignKey(ManagedUser, on_delete=models.CASCADE, related_name='tasks')
	name = models.CharField(max_length=255)
	action = models.CharField(max_length=100)
	scheduled_for = models.DateTimeField()
	params = models.JSONField(default=dict, blank=True)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['scheduled_for']
		indexes = [
			models.Index(fields=['status', 'scheduled_for']),
			models.Index(fields=['user', 'scheduled_for']),
		]

	def __str__(self) -> str:
		return f'{self.name} ({self.action}) for {self.user.username}'


class TaskExecutionLog(models.Model):
	class Status(models.TextChoices):
		SUCCESS = 'success', 'Success'
		FAILED = 'failed', 'Failed'
		SKIPPED = 'skipped', 'Skipped'

	task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='execution_logs')
	user = models.ForeignKey(ManagedUser, on_delete=models.CASCADE, related_name='execution_logs')
	status = models.CharField(max_length=20, choices=Status.choices)
	message = models.TextField(blank=True)
	executed_at = models.DateTimeField(default=timezone.now)

	class Meta:
		ordering = ['-executed_at']

	def __str__(self) -> str:
		return f'{self.task_id}:{self.status}@{self.executed_at.isoformat()}'
