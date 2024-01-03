import time
from typing import Generator

from job import Job, coroutine
from scheduler import Scheduler
from utils import file_system_operations, file_operations, network_operations

@coroutine
def print_x(num: int, name: str) -> Generator[None, None, None]:
    for i in range(num):
        yield
        print(f'Вызов функции print_x с именем {name}')

if __name__ == '__main__':
    job1 = Job(target=print_x, args=(2, 'Два'))
    job2 = Job(target=print_x, args=(3, 'Три'))
    job3 = Job(target=print_x, args=(4, 'Четыре'))

    loop = Scheduler()
    loop.add_job(job1)
    loop.add_job(job2)
    loop.add_job(job3)
    loop.run()


