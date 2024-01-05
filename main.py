import time
import uuid
from typing import Generator

from job import Job, coroutine
from scheduler import Scheduler


@coroutine
def print_x(num: int, name: str) -> Generator[None, None, None]:
    for i in range(num):
        yield
        time.sleep(1)
        print(f"Вызов функции print_x с именем {name}")


if __name__ == "__main__":
    job1 = Job(func=print_x, job_id=uuid.uuid4(), args=(1, "Один"))
    job2 = Job(func=print_x, job_id=uuid.uuid4(), args=(2, "Два"))
    job3 = Job(func=print_x, job_id=uuid.uuid4(), args=(3, "Три"), dependencies=[job1, job2])

    loop = Scheduler()
    loop.schedule(job1)
    loop.schedule(job2)
    loop.schedule(job3)
    loop.run()
