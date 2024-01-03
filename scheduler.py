from queue import Queue

from job import Job

class Scheduler:
    def __init__(self) -> None:
        self.__queue: Queue[Job] = Queue()

    def add_job(self, task: Job) -> None:
        self.__queue.put(task)

    def run(self) -> None:
        while not self.__queue.empty():
            job = self.__queue.get()
            try:
                job.run()
            except StopIteration:
                continue
            self.add_job(job)