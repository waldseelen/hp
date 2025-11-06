"""
Mock implementation of Celery for testing

Provides a mock Celery app that executes tasks synchronously
without requiring a running broker or worker.
"""

from typing import Any, Callable, Dict, Optional
from unittest.mock import MagicMock


class MockAsyncResult:
    """Mock Celery AsyncResult"""

    def __init__(self, task_id: str, result: Any = None, state: str = "SUCCESS"):
        self.id = task_id
        self.result = result
        self.state = state

    def get(self, timeout: Optional[float] = None) -> Any:
        """Get task result"""
        return self.result

    def ready(self) -> bool:
        """Check if task is ready"""
        return self.state in ("SUCCESS", "FAILURE")

    def successful(self) -> bool:
        """Check if task completed successfully"""
        return self.state == "SUCCESS"

    def failed(self) -> bool:
        """Check if task failed"""
        return self.state == "FAILURE"


class MockTask:
    """Mock Celery task"""

    def __init__(self, func: Callable, app: "MockCeleryApp"):
        self.func = func
        self.app = app
        self.name = f"{func.__module__}.{func.__name__}"
        self._call_count = 0
        self._last_args = None
        self._last_kwargs = None

    def __call__(self, *args, **kwargs):
        """Execute task synchronously"""
        self._call_count += 1
        self._last_args = args
        self._last_kwargs = kwargs
        return self.func(*args, **kwargs)

    def delay(self, *args, **kwargs) -> MockAsyncResult:
        """
        Execute task asynchronously (actually synchronous in mock)

        Usage:
            result = my_task.delay(arg1, arg2)
            value = result.get()
        """
        self._call_count += 1
        self._last_args = args
        self._last_kwargs = kwargs

        try:
            result = self.func(*args, **kwargs)
            return MockAsyncResult(
                task_id=f"mock-task-{self._call_count}", result=result
            )
        except Exception as e:
            return MockAsyncResult(
                task_id=f"mock-task-{self._call_count}", result=e, state="FAILURE"
            )

    def apply_async(
        self,
        args: tuple = (),
        kwargs: Optional[Dict] = None,
        countdown: Optional[int] = None,
        eta: Optional[Any] = None,
        **options,
    ) -> MockAsyncResult:
        """
        Execute task asynchronously with options

        In mock, countdown and eta are ignored, task executes immediately.
        """
        kwargs = kwargs or {}
        return self.delay(*args, **kwargs)

    def apply(self, args: tuple = (), kwargs: Optional[Dict] = None) -> Any:
        """Execute task synchronously and return result directly"""
        kwargs = kwargs or {}
        return self(*args, **kwargs)

    @property
    def called(self) -> bool:
        """Check if task was called"""
        return self._call_count > 0

    @property
    def call_count(self) -> int:
        """Get number of times task was called"""
        return self._call_count

    def reset_mock(self):
        """Reset call tracking"""
        self._call_count = 0
        self._last_args = None
        self._last_kwargs = None


class MockCeleryApp:
    """
    Mock Celery application for testing

    Executes tasks synchronously without a broker.

    Usage in tests:
        from tests.mocks import MockCeleryApp

        @pytest.fixture
        def mock_celery(monkeypatch):
            mock_app = MockCeleryApp("test_app")
            monkeypatch.setattr("celery.Celery", lambda *args, **kwargs: mock_app)
            return mock_app

        def test_task(mock_celery):
            @mock_celery.task
            def add(x, y):
                return x + y

            result = add.delay(2, 3)
            assert result.get() == 5
    """

    def __init__(self, name: str = "test_app", broker: Optional[str] = None, **kwargs):
        self.name = name
        self.broker = broker or "memory://"
        self.tasks: Dict[str, MockTask] = {}
        self.conf = MagicMock()
        self.control = MagicMock()

    def task(
        self,
        func: Optional[Callable] = None,
        *,
        name: Optional[str] = None,
        bind: bool = False,
        **options,
    ):
        """
        Decorator to register a task

        Usage:
            @app.task
            def my_task(x, y):
                return x + y

            @app.task(name="custom.task.name")
            def another_task():
                pass
        """

        def decorator(f: Callable) -> MockTask:
            task = MockTask(f, self)
            task_name = name or task.name
            self.tasks[task_name] = task
            return task

        if func is None:
            # Called with arguments: @app.task(name="...")
            return decorator
        else:
            # Called without arguments: @app.task
            return decorator(func)

    def send_task(
        self,
        name: str,
        args: tuple = (),
        kwargs: Optional[Dict] = None,
        **options,
    ) -> MockAsyncResult:
        """Send task by name"""
        kwargs = kwargs or {}
        if name in self.tasks:
            return self.tasks[name].delay(*args, **kwargs)
        else:
            # Task not registered, return mock result
            return MockAsyncResult(task_id=f"mock-unknown-{name}")

    def on_after_configure(self):
        """Hook for after configuration (no-op in mock)"""
        return MagicMock()

    def config_from_object(self, obj: Any):
        """Load config from object (no-op in mock)"""
        pass

    def autodiscover_tasks(self, packages: Optional[list] = None):
        """Auto-discover tasks (no-op in mock)"""
        pass

    def get_task(self, name: str) -> Optional[MockTask]:
        """Get registered task by name"""
        return self.tasks.get(name)

    def reset_all_tasks(self):
        """Reset all task call counters"""
        for task in self.tasks.values():
            task.reset_mock()


# Convenience function for creating shared_task decorator
def mock_shared_task(func: Optional[Callable] = None, **options):
    """
    Mock shared_task decorator

    Usage in tests:
        from tests.mocks.celery_mock import mock_shared_task

        @pytest.fixture
        def mock_tasks(monkeypatch):
            monkeypatch.setattr(
                "celery.shared_task",
                mock_shared_task
            )

        def test_shared_task(mock_tasks):
            @shared_task
            def my_task():
                return "done"

            assert my_task() == "done"
    """
    app = MockCeleryApp("shared_tasks")

    def decorator(f: Callable) -> MockTask:
        return app.task(f)

    if func is None:
        return decorator
    else:
        return decorator(func)
