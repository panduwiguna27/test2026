# Django Task Scheduler Project

This project is a runnable Django implementation of:
- User management with quota control
- Task data model with configurable parameters (JSON/dict)
- Extensible task executor system
- Simple scheduling system
- Execution logging using Python logging module + DB logs

## Stack
- Django 4.2
- PostgreSQL

## Database Credentials (configured)
- Host: `localhost`
- Database: `test2026`
- User: `panduwiguna`
- Password: `Mahalestine1995!`
- Port: `5432`

Credentials are loaded from `.env`.

## Setup
```bash
cd /Users/panduwiguna/Documents/KERJAAN/PYTHON/TEST
/Users/panduwiguna/Documents/KERJAAN/.venv/bin/python -m pip install -r requirements.txt
```

## Migrations
```bash
cd /Users/panduwiguna/Documents/KERJAAN/PYTHON/TEST
/Users/panduwiguna/Documents/KERJAAN/.venv/bin/python manage.py migrate
```

## Run Server
```bash
cd /Users/panduwiguna/Documents/KERJAAN/PYTHON/TEST
/Users/panduwiguna/Documents/KERJAAN/.venv/bin/python manage.py runserver
```

## Run Scheduler
One-time:
```bash
cd /Users/panduwiguna/Documents/KERJAAN/PYTHON/TEST
/Users/panduwiguna/Documents/KERJAAN/.venv/bin/python manage.py run_scheduler
```

Continuous loop:
```bash
cd /Users/panduwiguna/Documents/KERJAAN/PYTHON/TEST
/Users/panduwiguna/Documents/KERJAAN/.venv/bin/python manage.py run_scheduler --loop --interval 10
```

## API Endpoints
- `GET /api/health/`
- `POST /api/tasks/create/`
- `POST /api/tasks/run-pending/`

### Create Task Example
```bash
curl -X POST http://127.0.0.1:8000/api/tasks/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "quota_per_day": 3,
    "name": "Nightly Backup",
    "action": "backup",
    "scheduled_for": "2026-07-17T23:00:00+07:00",
    "params": {
      "target": "/srv/data",
      "destination": "/srv/backup"
    }
  }'
```

## Extending Executors
Add new executors in `scheduler_app/services/executors.py`:
1. Create class implementing `TaskExecutor.execute(self, task)`.
2. Register action in `DEFAULT_EXECUTORS` mapping.
