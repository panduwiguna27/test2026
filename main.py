import datetime
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("task_scheduler")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)


class UserManager:
    """Manage users and enforce quota per-day."""

    def __init__(self) -> None:
        self._users: Dict[str, Dict[str, Any]] = {}
        self._today = datetime.date.today()

    def add_user(self, username: str, quota: int) -> None:
        self._users[username] = {"quota": quota, "executed": 0}
        logger.debug("Added user %s with quota=%d", username, quota)

    def can_execute(self, username: str) -> bool:
        self._reset_if_new_day()
        u = self._users.get(username)
        if not u:
            raise KeyError(f"Unknown user: {username}")
        return u["executed"] < u["quota"]

    def record_execution(self, username: str) -> None:
        self._reset_if_new_day()
        if username not in self._users:
            raise KeyError(f"Unknown user: {username}")
        self._users[username]["executed"] += 1
        logger.info("Recorded execution for %s (now %d/%d)", username, self._users[username]["executed"], self._users[username]["quota"])

    def get_remaining(self, username: str) -> int:
        self._reset_if_new_day()
        u = self._users.get(username)
        if not u:
            raise KeyError(f"Unknown user: {username}")
        return max(0, u["quota"] - u["executed"])

    def _reset_if_new_day(self) -> None:
        today = datetime.date.today()
        if today != self._today:
            logger.info("New day detected, resetting execution counters")
            for u in self._users.values():
                u["executed"] = 0
            self._today = today


@dataclass
class Task:
    user: str
    time_str: str  # "HH:MM"
    action: str
    params: Dict[str, Any] = field(default_factory=dict)

    def scheduled_datetime(self, reference: Optional[datetime.datetime] = None) -> datetime.datetime:
        """Return a datetime for today with the Task's time."""
        ref = reference or datetime.datetime.now()
        h, m = map(int, self.time_str.split(":"))
        return ref.replace(hour=h, minute=m, second=0, microsecond=0)


class TaskExecutor:
    """Base class for executors. Subclass and register executors for actions."""

    def execute(self, task: Task) -> None:
        raise NotImplementedError()


class SyncExecutor(TaskExecutor):
    def execute(self, task: Task) -> None:
        target = task.params.get("target")
        logger.info("[sync] User=%s syncing %s", task.user, target)


class BackupExecutor(TaskExecutor):
    def execute(self, task: Task) -> None:
        target = task.params.get("target")
        logger.info("[backup] User=%s backing up %s", task.user, target)


class DeleteExecutor(TaskExecutor):
    def execute(self, task: Task) -> None:
        target = task.params.get("target")
        logger.info("[delete] User=%s deleting %s", task.user, target)


class ExecutorRegistry:
    def __init__(self) -> None:
        self._registry: Dict[str, TaskExecutor] = {}

    def register(self, action: str, executor: TaskExecutor) -> None:
        self._registry[action] = executor
        logger.debug("Registered executor for action '%s'", action)

    def get(self, action: str) -> TaskExecutor:
        if action not in self._registry:
            raise KeyError(f"No executor registered for action '{action}'")
        return self._registry[action]


class Scheduler:
    """Simple scheduler that runs due tasks once per check interval."""

    def __init__(self, user_manager: UserManager, executors: ExecutorRegistry, check_interval: float = 30.0) -> None:
        self.user_manager = user_manager
        self.executors = executors
        self.tasks: List[Task] = []
        self.check_interval = check_interval

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)
        logger.debug("Scheduled task: %s", task)

    def run_pending(self) -> None:
        now = datetime.datetime.now()
        due = [t for t in self.tasks if t.scheduled_datetime() <= now]
        for task in due:
            try:
                if not self.user_manager.can_execute(task.user):
                    logger.warning("User %s exceeded quota, skipping task %s", task.user, task)
                    continue
                executor = self.executors.get(task.action)
                logger.info("Starting task %s for user %s", task.action, task.user)
                executor.execute(task)
                self.user_manager.record_execution(task.user)
            except Exception as e:
                logger.exception("Error executing task %s: %s", task, e)
            finally:
                # Remove the task after attempting execution so it won't run again
                try:
                    self.tasks.remove(task)
                except ValueError:
                    pass

    def run_forever(self) -> None:
        logger.info("Scheduler started (check interval=%s seconds)", self.check_interval)
        try:
            while True:
                self.run_pending()
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")


def bootstrap_example() -> None:
    user_mgr = UserManager()
    user_mgr.add_user("alice", quota=3)
    user_mgr.add_user("bob", quota=5)

    registry = ExecutorRegistry()
    registry.register("sync", SyncExecutor())
    registry.register("backup", BackupExecutor())
    registry.register("delete", DeleteExecutor())

    scheduler = Scheduler(user_mgr, registry, check_interval=5.0)

    # Example tasks (converted from the original lightweight format)
    scheduler.add_task(Task(user="alice", time_str=datetime.datetime.now().strftime("%H:%M"), action="sync", params={"target": "/data/x"}))
    scheduler.add_task(Task(user="bob", time_str=datetime.datetime.now().strftime("%H:%M"), action="backup", params={"target": "/srv/y"}))
    scheduler.add_task(Task(user="alice", time_str=datetime.datetime.now().strftime("%H:%M"), action="delete", params={"target": "/tmp/z"}))

    # Run once to process immediate tasks, then exit. Replace with run_forever() for continuous scheduling.
    scheduler.run_pending()


if __name__ == "__main__":
    bootstrap_example()
