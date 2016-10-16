"""
src/scheduler/job_runners/_base.py

Base job runner from which all other job runners should inherit from. There should be one job
runner per job type.
"""

from abc import ABC, abstractmethod

from ..job import Job


class AbstractJobRunner(ABC):
    """Abstract class for all other job runners in implement. For type hinting, yo."""

    @classmethod
    @abstractmethod
    def load_class(cls, *args, **kwargs):
        """Prepare any resources to be shared among all instances of this job runner."""
        pass

    @abstractmethod
    def load(self, *args, **kwargs):
        """Prepare any resources for this instance of the job runner."""
        pass

    @abstractmethod
    def run(self, job: Job, delay: float):
        """Run a given job."""
        pass
