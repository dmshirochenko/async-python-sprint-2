from src.task_manager import TaskManager


def main():
    task_manager = TaskManager("job_schedule_example.yaml")
    task_manager.run()


if __name__ == "__main__":
    main()
