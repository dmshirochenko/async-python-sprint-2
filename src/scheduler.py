import os
import json

from collections import deque
from typing import Deque

import logging.config

from config.logger import LOGGING
from src.job import Job, JobStatus, JobRegistry
from src.utils import func_resolver

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, pool_size: int = 10, state_file="scheduler_state.json") -> None:
        self._pool_size: int = pool_size
        self.job_queue: Deque[Job] = deque()
        self.state_file = state_file
        self.running = False

    def schedule(self, job: Job) -> None:
        logger.info("Job scheduling ...")
        if len(self.job_queue) < self._pool_size:
            self.job_queue.append(job)
            logger.info("Job has been added successfully ...")
        else:
            logger.info("Scheduler task list exceeds the limit %s", self._pool_size)

    def add_job(self, job: Job) -> None:
        logger.info("Adding new job %s", job.job_id)
        self.job_queue.append(job)

    def run(self) -> None:
        while self.job_queue:
            job = self.job_queue.popleft()

            if job.has_exceeded_max_time():
                job.update_status(JobStatus.FAILED, error="Max working time exceeded")
                logger.error("Job %s: Max working time exceeded", job.job_id)
                job.close_coroutine()
                continue

            if job.has_failed_dependency():
                logger.error("Cannot run job %s: Dependency failed", job.job_id)
                job.update_status(JobStatus.FAILED, error="Dependency failed")
                job.close_coroutine()
                continue

            try:
                job.run()
            except StopIteration:
                job.update_status(JobStatus.COMPLETED)
                logger.info("Job %s: Completed", job.job_id)
            except Exception as e:
                logger.error("Error running job %s: %s", job.job_id, str(e))
                job.close_coroutine()
                if job.can_retry():
                    job.restart_coroutine()  # Restart the coroutine
                    job.current_tries += 1
                    self.add_job(job)  # Re-add the job to the queue for a retry
                else:
                    logger.error("Job %s: Max retry exceeded", job.job_id)
                    job.update_status(JobStatus.FAILED, error=str(e))
            else:
                if job.status != JobStatus.FAILED and job.status != JobStatus.COMPLETED:
                    self.add_job(job)

    def load_jobs(self):
        job_registry = JobRegistry()
        if os.path.exists(self.state_file):
            with open(self.state_file, "r") as file:
                serialized_jobs = json.load(file)
                for sj in serialized_jobs:
                    self.add_job(Job.deserialize(sj, func_resolver, job_registry))

    def save_jobs(self):
        with open(self.state_file, "w") as file:
            serialized_jobs = [job.serialize() for job in self.job_queue]
            json.dump(serialized_jobs, file)

    def restart(self):
        self.stop()
        self.job_queue.clear()
        self.load_jobs()
        self.run()

    def stop(self):
        logger.info("Stopping event loop and saving not finished jobs")
        self.save_jobs()
