import json

from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from scheduler_app.models import ManagedUser, Task, TaskExecutionLog
from scheduler_app.services.scheduler import TaskScheduler


@require_GET
def health(request: HttpRequest) -> JsonResponse:
	return JsonResponse({'status': 'ok', 'timestamp': timezone.now().isoformat()})


@csrf_exempt
@require_POST
def create_task(request: HttpRequest) -> JsonResponse:
	try:
		payload = json.loads(request.body.decode('utf-8'))
		username = payload['username']
		task_name = payload['name']
		action = payload['action']
		scheduled_for = payload.get('scheduled_for')
		params = payload.get('params', {})
	except (json.JSONDecodeError, KeyError) as exc:
		return JsonResponse({'error': f'invalid payload: {exc}'}, status=400)

	user, _ = ManagedUser.objects.get_or_create(
		username=username,
		defaults={'quota_per_day': int(payload.get('quota_per_day', 3))},
	)
	when = timezone.now() if not scheduled_for else timezone.datetime.fromisoformat(scheduled_for)
	if timezone.is_naive(when):
		when = timezone.make_aware(when, timezone.get_current_timezone())

	task = Task.objects.create(
		user=user,
		name=task_name,
		action=action,
		scheduled_for=when,
		params=params,
	)
	return JsonResponse({'task_id': task.id, 'status': task.status})


@csrf_exempt
@require_POST
def run_pending_tasks(request: HttpRequest) -> JsonResponse:
	scheduler = TaskScheduler()
	processed = scheduler.run_pending()
	return JsonResponse({'processed': processed})


@require_GET
def quota_summary(request: HttpRequest, username: str) -> JsonResponse:
	try:
		user = ManagedUser.objects.get(username=username)
	except ManagedUser.DoesNotExist:
		return JsonResponse({'error': 'user not found'}, status=404)

	start_of_day = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
	success_today = TaskExecutionLog.objects.filter(
		user=user,
		status=TaskExecutionLog.Status.SUCCESS,
		executed_at__gte=start_of_day,
	).count()

	pending_count = Task.objects.filter(user=user, status=Task.Status.PENDING).count()
	running_count = Task.objects.filter(user=user, status=Task.Status.RUNNING).count()
	failed_count = Task.objects.filter(user=user, status=Task.Status.FAILED).count()
	success_count = Task.objects.filter(user=user, status=Task.Status.SUCCESS).count()

	remaining_quota = max(0, user.quota_per_day - success_today)

	return JsonResponse(
		{
			'username': user.username,
			'quota_per_day': user.quota_per_day,
			'success_today': success_today,
			'remaining_quota': remaining_quota,
			'tasks': {
				'pending': pending_count,
				'running': running_count,
				'success': success_count,
				'failed': failed_count,
			},
		}
	)
