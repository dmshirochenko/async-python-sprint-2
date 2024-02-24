# Task Scheduler Project

## Project Overview

The project involves designing and implementing a task scheduler capable of executing incoming tasks with various specifications and requirements. This scheduler is intended to manage tasks efficiently, ensuring high throughput and reliability even after system restarts.

The service is schematically represented in the diagram below:
![image](schema.png)


## Project Structure

Here is the overall structure of the project:

- config/ # Configuration files for the project
    -  config.py # General configurations
    -  logger.py # Logger configurations
- src/ # Source code for the main application
    -  job.py # Defines the Job class
    -  scheduler.py # Defines the Scheduler class
    -  task_manager.py # Task manager for handling jobs
    -  utils.py # Utility functions used across the project
- tests/ # Automated tests for the project
    -  conftest.py # Test configuration and fixtures
    -  test_job_scheduler.py # Test suite for the Job and Scheduler classes
- .env_example # Example environment configuration
- main.py # Main executable script for the project
- README.md # README file with project details
- requirements.txt # List of dependencies to install


## Running the Application

To run the application, follow these steps:

1. Ensure you have Python 3.x installed on your system.
2. Set up a virtual environment and activate it:
    python3 -m venv .venv
    source .venv/bin/activate # On Windows use .venv\Scripts\activate
3. Install the required dependencies:
    pip install -r requirements.txt
4. Update 'job_schedule_example.yaml' with jobs needed
5. Run the `main.py` script:
    python main.py


## Short Description

**Objective:** To create a `Scheduler` class and a `Job` class that together facilitate the scheduling and execution of tasks based on defined constraints and settings.


### Scheduler Class

- **Concurrency Limit:** Can run up to 10 tasks simultaneously by default, adjustable as needed.
- **Functionality:** Supports adding tasks and executing them within the scheduler's constraints and the task's specific settings.
- **State Persistence:** Maintains the status of running and waiting tasks, ensuring that this state can be restored after a restart to continue task execution seamlessly.


### Job Class

- **Execution Duration:** Optional parameter to specify the maximum allowed duration for task execution.
- **Start Time:** Optional parameter to schedule a task to start at a specific time.
- **Restart Count:** Optional parameter defining how many times a task should be restarted if it fails or if its dependencies are not met, with a default of 0 restarts if unspecified.
- **Dependencies:** Optional parameter to specify other tasks that must be completed before this task can start.

### Testing the Scheduler

- **File System Operations:** Includes creating, deleting, and modifying directories and files.
- **File Operations:** Encompasses creating, reading, and writing files.
- **Network Operations:** Involves handling URLs (GET requests) and analyzing the results.
- **Task Pipeline:** Describes a sequence of at least three interdependent tasks executed in order.
