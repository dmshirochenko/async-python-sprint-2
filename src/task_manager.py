import yaml
import time
import uuid
from typing import Dict, Any, List, Callable, Optional

from src.job import Job
from src.scheduler import Scheduler
from src.utils import func_resolver
import logging

logger = logging.getLogger(__name__)


class TaskManager:
    def __init__(self, yaml_file: str) -> None:
        self.yaml_file: str = yaml_file
        self.jobs: Dict[str, Job] = {}
        self.scheduler: Scheduler = Scheduler()
        try:
            self.load_yaml()
        except Exception as e:
            logger.error("Failed to load YAML file %s: %s", self.yaml_file, e)
            raise RuntimeError(f"Failed to load YAML file: {self.yaml_file}") from e

    def load_yaml(self) -> None:
        try:
            with open(self.yaml_file, "r") as file:
                config: Dict[str, Any] = yaml.safe_load(file)
                for job_conf in config["jobs"]:
                    job: Job = self.create_job_from_config(job_conf)
                    self.jobs[job_conf["id"]] = job
                    self.scheduler.schedule(job)
                    logger.info("Scheduled job with ID %s from YAML configuration", job_conf["id"])
        except yaml.YAMLError as e:
            logger.error("Error parsing YAML file %s: %s", self.yaml_file, e)
            raise RuntimeError(f"Error parsing YAML file: {self.yaml_file}") from e
        except IOError as e:
            logger.error("Error opening file %s: %s", self.yaml_file, e)
            raise RuntimeError(f"Error opening file: {self.yaml_file}") from e

    def create_job_from_config(self, config: Dict[str, Any]) -> Job:
        job_id: str = str(uuid.uuid4())
        func: Callable = func_resolver(config["function"])
        args: Any = config["args"]
        start_at: float = time.time() + int(config.get("start_at", 0))
        dependency_ids: Optional[List[str]] = config.get("dependencies", [])
        dependencies: List[Job] = [self.jobs[dep_id] for dep_id in dependency_ids if dep_id in self.jobs]
        job = Job(
            func=func,
            job_id=job_id,
            args=args,
            start_at=start_at,
            max_working_time=-1,
            max_tries=1,
            dependencies=dependencies,
        )
        logger.info("Creating job with ID %s from config", job_id)
        return job

    def run(self) -> None:
        logger.info("Starting TaskManager scheduler")
        self.scheduler.run()
