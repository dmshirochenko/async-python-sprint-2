import yaml
import time
import uuid

from src.job import Job
from src.scheduler import Scheduler
from src.utils import func_resolver


class TaskManager:
    def __init__(self, yaml_file):
        self.yaml_file = yaml_file
        self.jobs = {}
        self.scheduler = Scheduler()
        self.load_yaml()

    def load_yaml(self):
        with open(self.yaml_file, "r") as file:
            config = yaml.safe_load(file)
            for job_conf in config["jobs"]:
                job = self.create_job_from_config(job_conf)
                self.jobs[job_conf["id"]] = job
                self.scheduler.schedule(job)

    def create_job_from_config(self, config):
        job_id = uuid.uuid4()
        func = func_resolver(config["function"])
        args = config["args"]
        start_at = time.time() + int(config.get("start_at", 0))
        dependency_ids = config.get("dependencies", [])
        dependencies = [self.jobs[dep_id] for dep_id in dependency_ids if dep_id in self.jobs]
        return Job(
            func=func,
            job_id=job_id,
            args=args,
            start_at=start_at,
            max_working_time=-1,
            max_tries=1,
            dependencies=dependencies,
        )

    def run(self):
        self.scheduler.run()
