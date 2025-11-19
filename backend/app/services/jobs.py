import threading
import time
import uuid
from typing import Any, Callable, Dict, Optional


class JobRecord:
    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        self.status: str = "pending"
        self.progress: float = 0.0
        self.details: Dict[str, Any] = {}
        self.error: Optional[str] = None


class JobManager:
    def __init__(self) -> None:
        self._jobs: Dict[str, JobRecord] = {}
        self._lock = threading.Lock()

    def create(self, target_fn: Callable[[JobRecord], None]) -> str:
        job_id = str(uuid.uuid4())
        rec = JobRecord(job_id)
        with self._lock:
            self._jobs[job_id] = rec
        t = threading.Thread(target=self._run_wrapper, args=(rec, target_fn), daemon=True)
        t.start()
        return job_id

    def _run_wrapper(self, rec: JobRecord, fn: Callable[[JobRecord], None]) -> None:
        try:
            rec.status = "running"
            fn(rec)
            if rec.status != "failed":
                rec.status = "completed"
                rec.progress = 1.0
        except Exception as e:
            rec.status = "failed"
            rec.error = str(e)

    def get(self, job_id: str) -> Optional[JobRecord]:
        with self._lock:
            return self._jobs.get(job_id)


job_manager = JobManager()



