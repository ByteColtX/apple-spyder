from __future__ import annotations

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Callable

from croniter import croniter

from apple_spyder.settings import get_scheduler_config


logger = logging.getLogger("scheduler")


class CronTaskRunner:
    def __init__(self, job: Callable[[], None], *, job_name: str = "job") -> None:
        self._job = job
        self._job_name = job_name
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix=f"scheduler-{job_name}")

    def start(self) -> None:
        config = get_scheduler_config()
        if not config.enabled:
            logger.info("Scheduler disabled: job=%s", self._job_name)
            return
        if self._thread and self._thread.is_alive():
            logger.info("Scheduler already running: job=%s", self._job_name)
            return

        next_run = self.get_next_run_time()
        self._thread = threading.Thread(target=self._run_loop, name=f"cron-{self._job_name}", daemon=True)
        self._thread.start()
        logger.info(
            "Scheduler started: job=%s cron_expr=%s run_on_startup=%s next_run=%s",
            self._job_name,
            config.cron_expr,
            config.run_on_startup,
            self._format_time(next_run),
        )

    def stop(self) -> None:
        self._stop_event.set()
        self._executor.shutdown(wait=False, cancel_futures=True)
        logger.info("Scheduler stopped: job=%s", self._job_name)

    def get_next_run_time(self, base_time: datetime | None = None) -> datetime:
        config = get_scheduler_config()
        base = base_time or datetime.now()
        return croniter(config.cron_expr, base).get_next(datetime)

    def _run_loop(self) -> None:
        config = get_scheduler_config()
        cron = croniter(config.cron_expr, datetime.now())

        if config.run_on_startup:
            self._submit_job(trigger="startup")

        while not self._stop_event.is_set():
            now = datetime.now()
            next_run = cron.get_next(datetime)
            sleep_seconds = max(0.0, (next_run - now).total_seconds())
            logger.info(
                "Scheduler waiting: job=%s next_run=%s sleep_seconds=%.3f",
                self._job_name,
                self._format_time(next_run),
                sleep_seconds,
            )
            if self._stop_event.wait(sleep_seconds):
                break
            self._submit_job(trigger="cron")

    def _submit_job(self, *, trigger: str) -> None:
        logger.info("Submitting scheduled job: job=%s trigger=%s", self._job_name, trigger)
        future = self._executor.submit(self._safe_run_job, trigger)
        future.add_done_callback(self._log_future_exception)

    def _safe_run_job(self, trigger: str) -> None:
        started_at = datetime.now()
        logger.info(
            "Scheduled job started: job=%s trigger=%s started_at=%s",
            self._job_name,
            trigger,
            self._format_time(started_at),
        )
        try:
            self._job()
            finished_at = datetime.now()
            elapsed_seconds = (finished_at - started_at).total_seconds()
            logger.info(
                "Scheduled job finished: job=%s trigger=%s finished_at=%s elapsed_seconds=%.3f",
                self._job_name,
                trigger,
                self._format_time(finished_at),
                elapsed_seconds,
            )
        except Exception:
            logger.exception("Scheduled job failed: job=%s trigger=%s", self._job_name, trigger)

    @staticmethod
    def _log_future_exception(future) -> None:
        exception = future.exception()
        if exception is not None:
            logger.exception("Scheduler future failed", exc_info=exception)

    @staticmethod
    def _format_time(value: datetime | None) -> str:
        if value is None:
            return "-"
        return value.isoformat(sep=" ", timespec="seconds")
