import json

from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from scheduler_app.models import ManagedUser, Task
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
