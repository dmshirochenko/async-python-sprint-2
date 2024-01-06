import time
import json
from unittest.mock import Mock, MagicMock, patch, mock_open, create_autospec

import pytest

from src.job import Job, JobStatus
from src.scheduler import Scheduler

# Job class tests
def test_job_initialization():
    mock_func = Mock()
    job = Job(func=mock_func, job_id="123", args=[1, 2], kwargs={"a": 3}, start_at=1000)
    assert job.job_id == "123"
    assert job.args == [1, 2]
    assert job.kwargs == {"a": 3}
    assert job.start_at == 1000
    assert job.status == JobStatus.PENDING


def test_update_status():
    job = Job(Mock(), "123")
    job.update_status(JobStatus.RUNNING, result="result", error="error")
    assert job.status == JobStatus.RUNNING
    assert job.result == "result"
    assert job.error == "error"


@pytest.mark.parametrize("current_tries, max_tries, expected", [(0, 1, True), (1, 1, False)])
def test_can_retry(current_tries, max_tries, expected):
    job = Job(Mock(), "123", max_tries=max_tries)
    job.current_tries = current_tries
    assert job.can_retry() is expected


@patch("time.time")
def test_has_exceeded_max_time(mock_time):
    initial_time = 1000
    mock_time.return_value = initial_time
    max_working_time = 50
    job = Job(Mock(), "123", start_at=initial_time, max_working_time=max_working_time)
    mock_time.return_value = initial_time + 30
    assert not job.has_exceeded_max_time()
    mock_time.return_value = initial_time + max_working_time + 1
    assert job.has_exceeded_max_time()


@patch("time.time", Mock(return_value=1000))
def test_is_start_time_reached():
    job = Job(Mock(), "123", start_at=950)
    assert job.is_start_time_reached() is True


def test_are_dependencies_completed():
    dependency_job = Job(Mock(), "dep", start_at=900)
    dependency_job.status = JobStatus.COMPLETED
    job = Job(Mock(), "123", start_at=950, dependencies=[dependency_job])
    assert job.are_dependencies_completed() is True


def test_has_failed_dependency():
    dependency_job = Job(Mock(), "dep", start_at=900)
    dependency_job.status = JobStatus.FAILED
    job = Job(Mock(), "123", start_at=950, dependencies=[dependency_job])
    assert job.has_failed_dependency() is True


def test_serialize_deserialize():
    mock_func = Mock()
    mock_func.__name__ = "mock_func"

    job = Job(mock_func, "123", args=[1, 2], kwargs={"a": 3}, start_at=950, max_working_time=50)
    serialized = job.serialize()

    func_resolver = Mock(return_value=mock_func)

    job_registry = MagicMock()
    job_registry.get_job.return_value = None

    deserialized_job = Job.deserialize(serialized, func_resolver, job_registry)

    assert deserialized_job.job_id == "123"
    assert deserialized_job.args == job.args
    assert deserialized_job.kwargs == job.kwargs
    assert deserialized_job.func.__name__ == "mock_func"


# Scheduler class tests
def test_scheduler_initialization():
    scheduler = Scheduler(pool_size=5)
    assert scheduler._pool_size == 5


def test_scheduling_jobs():
    scheduler = Scheduler()
    job = Mock()
    scheduler.schedule(job)
    assert len(scheduler.job_queue) == 1
    scheduler.add_job(job)
    assert len(scheduler.job_queue) == 2


@patch("src.job.Job", autospec=True)
def test_run_logic(mock_job_class):
    scheduler = Scheduler()

    # Create a mock job instance with behavior
    mock_job = create_autospec(Job)
    mock_job.has_exceeded_max_time.return_value = False
    mock_job.has_failed_dependency.return_value = False
    mock_job.status = JobStatus.PENDING

    # Set side effect to update job status to COMPLETED after being run
    def side_effect_run():
        mock_job.status = JobStatus.COMPLETED

    mock_job.run.side_effect = side_effect_run

    scheduler.schedule(mock_job)
    scheduler.run()

    mock_job.run.assert_called()


@patch("builtins.open", mock_open())
@patch("os.path.exists", return_value=True)
def test_load_save_jobs(mock_exists):
    scheduler = Scheduler()
    mock_job = Mock()
    mock_job.serialize.return_value = '{"job_id": "123"}'
    scheduler.add_job(mock_job)
    scheduler.save_jobs()
    open.assert_called_with(scheduler.state_file, "w")
    written_content = open().write.call_args_list
    serialized_data = "".join(call_args[0][0] for call_args in written_content)
    written_data = [json.loads(job) for job in json.loads(serialized_data)]
    expected_data = [json.loads(mock_job.serialize.return_value)]

    assert written_data == expected_data


@patch("src.scheduler.Scheduler.stop")
@patch("src.scheduler.Scheduler.load_jobs")
def test_restart_and_stop(mock_load_jobs, mock_stop):
    scheduler = Scheduler()
    scheduler.restart()
    mock_stop.assert_called()
    mock_load_jobs.assert_called()
