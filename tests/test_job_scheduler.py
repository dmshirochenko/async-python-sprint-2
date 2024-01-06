import pytest
from unittest.mock import patch
from src.job import Job, JobStatus
from src.scheduler import Scheduler

# Fixtures for reusable objects
@pytest.fixture
def mock_job(mocker):
    mock_function = mocker.MagicMock()
    return Job(func=mock_function, job_id='123')

@pytest.fixture
def scheduler():
    return Scheduler(pool_size=2)

# Tests for Job class
def test_job_initialization(mock_job):
    assert mock_job.job_id == '123'
    assert mock_job.status == JobStatus.PENDING

def test_update_status(mock_job):
    mock_job.update_status(JobStatus.RUNNING, result="Success", error=None)
    assert mock_job.status == JobStatus.RUNNING
    assert mock_job.result == "Success"
    assert mock_job.error is None

def test_can_retry(mock_job):
    mock_job.max_tries = 2
    assert mock_job.can_retry() == True
    mock_job.current_tries = 2
    assert mock_job.can_retry() == False

# Mock time dependency in is_runnable
@patch('time.time', return_value=100)
def test_is_runnable(mock_time, mock_job):
    mock_job.start_at = 50
    assert mock_job.is_runnable() == True
    mock_job.start_at = 150
    assert mock_job.is_runnable() == False

# Tests for Scheduler class
def test_scheduler_initialization(scheduler):
    assert scheduler._pool_size == 2
    assert len(scheduler.job_queue) == 0

def test_schedule_job(scheduler, mock_job):
    scheduler.schedule(mock_job)
    assert len(scheduler.job_queue) == 1

if __name__ == "__main__":
    pytest.main()
