from dataclasses import dataclass


@dataclass
class JobRunResponseContent(object):
    __slots__ = ('job_id', 'queue')

    job_id: str
    queue: str

    def __str__(self):
        return f"job_id: {self.job_id}, queue: {self.queue}"
