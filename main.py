import time
import uuid
import os
from typing import Generator

from job import Job, coroutine
from scheduler import Scheduler
from utils import FileSystemOperations, NetworkOperationsPipe


@coroutine
def print_x(num: int, name: str) -> Generator[None, None, None]:
    for i in range(num):
        yield
        time.sleep(0.1)
        print(f"Вызов функции print_x с именем {name}")


if __name__ == "__main__":
    dir_name = "output_news_folder"
    file_name = "yahoo_news.txt"
    link = (
        "https://news.yahoo.com/trump-legal-news-brief-supreme-court-agrees-to-"
        "quickly-decide-whether-trump-can-be-kept-off-ballots-223044557.html"
    )
    path = os.path.join(dir_name, file_name)

    job1 = Job(func=FileSystemOperations().create_directory, job_id=uuid.uuid4(), args=[dir_name])
    job2 = Job(func=FileSystemOperations().create_file, job_id=uuid.uuid4(), args=[path])
    job3 = Job(
        func=NetworkOperationsPipe().html_to_txt_pipeline, job_id=uuid.uuid4(), args=[link, path]
    )  # dependencies=[job1, job2])

    loop = Scheduler()
    loop.schedule(job1)
    loop.schedule(job2)
    loop.schedule(job3)
    loop.run()
