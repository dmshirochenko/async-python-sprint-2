import time
import json
import logging.config
from enum import Enum, auto
from typing import Callable, Any, Sequence, Optional, Dict

from config.logger import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


class JobStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()


SERIALIZABLE_FIELDS = {
    "job_id",
    "status",
    "args",
    "kwargs",
    "start_at",
    "max_working_time",
    "max_tries",
    "current_tries",
}


class Job:
    def __init__(
        self,
        func: Callable,
        job_id: str,
        args: Optional[Sequence[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        start_at: Optional[float] = None,
        max_working_time: int = -1,
        max_tries: int = 1,
        dependencies: Optional[Sequence["Job"]] = None,
    ):
        self.func = func
        self.job_id = job_id
        self.args = args if args is not None else ()
        self.kwargs = kwargs if kwargs is not None else {}
        self.coroutine_factory = lambda: func(*self.args, **self.kwargs)
        self.start_at = start_at if start_at is not None else time.time()
        self.max_working_time = max_working_time
        self.start_time = time.time()
        self.max_tries = max_tries
        self.current_tries = 0
        self.dependencies = dependencies if dependencies is not None else []
        self.status = JobStatus.PENDING
        self.result = None
        self.error = None
        self.__coroutine = None

    def update_status(self, new_status: JobStatus, result: Optional[str] = None, error: Optional[str] = None) -> None:
        self.status = new_status
        self.result = result
        self.error = error

    def can_retry(self) -> bool:
        return self.current_tries < self.max_tries

    def run(self) -> None:
        logger.info("Job %s: Starts", self.job_id)

        if not self.is_runnable():
            logger.info("Job is not runnable will be back to queue func name %s", self.func.__name__)
            return

        self.update_status(JobStatus.RUNNING)

        if self.__coroutine is None:
            self.__coroutine = self.coroutine_factory()

        try:
            self.__coroutine.send(None)
        except StopIteration:
            raise
        except Exception as e:
            raise e

    def has_exceeded_max_time(self) -> bool:
        if self.max_working_time == -1:
            return False
        return (time.time() - self.start_time) > self.max_working_time

    def restart_coroutine(self) -> None:
        logger.info("Job %s re-start", self.job_id)
        self.__coroutine = None

    def close_coroutine(self) -> None:
        if self.__coroutine:
            logger.info("Closing coroutine for Job %s", self.job_id)
            self.__coroutine.close()
            self.__coroutine = None

    def is_start_time_reached(self) -> bool:
        return time.time() >= self.start_at

    def are_dependencies_completed(self) -> bool:
        return all(job.status == JobStatus.COMPLETED for job in self.dependencies)

    def is_runnable(self) -> bool:
        return self.is_start_time_reached() and self.are_dependencies_completed()

    def has_failed_dependency(self) -> bool:
        return any(job.status == JobStatus.FAILED for job in self.dependencies)

    def serialize(self) -> str:
        data = {}
        for field in SERIALIZABLE_FIELDS:
            if hasattr(self, field):
                if field == "status":
                    data[field] = self.status.name
                elif field == "job_id":
                    data[field] = str(getattr(self, field))
                else:
                    data[field] = getattr(self, field)

        if hasattr(self, "func") and callable(self.func):
            data["func_name"] = self.func.__name__

        if self.dependencies:
            data["dependencies"] = [dep.serialize() for dep in self.dependencies]

        return json.dumps(data)

    @staticmethod
    def create_from_data(
        data: Dict[str, Any], func_resolver: Callable[[str], Callable], job_registry: "JobRegistry"
    ) -> "Job":
        job_id = data["job_id"]
        existing_job = job_registry.get_job(job_id)
        if existing_job:
            return existing_job

        func = func_resolver(data["func_name"])
        dependencies_data = data.get("dependencies", [])
        dependencies = []
        for dep_data in dependencies_data:
            if isinstance(dep_data, str):
                dep_data = json.loads(dep_data)
            dependencies.append(Job.create_from_data(dep_data, func_resolver, job_registry))

        job = Job(
            func=func,
            job_id=data["job_id"],
            args=data["args"],
            kwargs=data["kwargs"],
            start_at=data["start_at"],
            max_working_time=data["max_working_time"],
            max_tries=data["max_tries"],
            dependencies=dependencies,
        )
        job.status = JobStatus[data["status"]]
        job.current_tries = data["current_tries"]

        # Register the new job
        job_registry.register_job(job)

        return job

    @staticmethod
    def deserialize(
        serialized_str: str, func_resolver: Callable[[str], Callable], job_registry: "JobRegistry"
    ) -> "Job":
        data = json.loads(serialized_str)
        return Job.create_from_data(data, func_resolver, job_registry)


class JobRegistry:
    def __init__(self) -> None:
        self.jobs: Dict[str, Job] = {}

    def get_job(self, job_id: str) -> Optional[Job]:
        return self.jobs.get(job_id)

    def register_job(self, job: Job) -> None:
        self.jobs[job.job_id] = job
