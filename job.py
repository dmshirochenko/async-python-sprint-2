import time
import logging.config
from functools import wraps
from enum import Enum, auto
from typing import Optional

from config.logger import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


def coroutine(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        gen = f(*args, **kwargs)
        gen.send(None)
        return gen

    return wrap


class JobStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()


class Job:
    def __init__(
        self, func, job_id, args=None, kwargs=None, start_at=None, max_working_time=-1, max_tries=1, dependencies=[]
    ):
        self.func = func
        self.job_id = job_id
        self.__args = args or ()
        self.__kwargs = kwargs or {}
        self.coroutine_factory = lambda: func(*self.__args, **self.__kwargs)
        self.start_at = start_at if start_at else time.time()
        self.max_working_time = max_working_time
        self.start_time = time.time()
        self.max_tries = max_tries
        self.current_tries = 0
        self.dependencies = dependencies
        self.status: JobStatus = JobStatus.PENDING
        self.result = None
        self.error = None
        self.__coroutine = None

    def update_status(self, new_status: JobStatus, result: Optional[str] = None, error: Optional[str] = None):
        self.status = new_status
        self.result = result
        self.error = error

    def can_retry(self) -> bool:
        return self.current_tries < self.max_tries

    def run(self) -> None:
        logger.info("Job %s: Starts", self.job_id)

        if not self.is_runnable():
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

    def restart_coroutine(self):
        logger.info("Job %s re-start", self.job_id)
        self.__coroutine = None

    def close_coroutine(self):
        if self.__coroutine:
            logger.info("Closing coroutine for Job %s", self.job_id)
            self.__coroutine.close()
            self.__coroutine = None

    def is_runnable(self):
        if time.time() < self.start_at:
            return False
        return all(job.status == JobStatus.COMPLETED for job in self.dependencies)

    def has_failed_dependency(self) -> bool:
        return any(job.status == JobStatus.FAILED for job in self.dependencies)
