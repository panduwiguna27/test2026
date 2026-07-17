from django.contrib import admin

from .models import ManagedUser, Task, TaskExecutionLog


@admin.register(ManagedUser)
class ManagedUserAdmin(admin.ModelAdmin):
	list_display = ('id', 'username', 'quota_per_day', 'is_active', 'created_at')
	search_fields = ('username',)
	list_filter = ('is_active',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
	list_display = ('id', 'name', 'user', 'action', 'scheduled_for', 'status', 'created_at')
	search_fields = ('name', 'action', 'user__username')
	list_filter = ('status', 'action')


@admin.register(TaskExecutionLog)
class TaskExecutionLogAdmin(admin.ModelAdmin):
	list_display = ('id', 'task', 'user', 'status', 'executed_at')
	search_fields = ('task__name', 'user__username', 'message')
	list_filter = ('status',)

# Register your models here.
