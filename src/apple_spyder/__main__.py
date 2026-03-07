from __future__ import annotations

import errno
import logging
import signal
import threading
from wsgiref.simple_server import WSGIRequestHandler, make_server

from apple_spyder.api import app
from apple_spyder.logging_config import configure_logging
from apple_spyder.scheduler import CronTaskRunner
from apple_spyder.services import software_releases
from apple_spyder.settings import CONFIG_PATH, DATABASE_PATH, ConfigError, get_app_config

configure_logging()
logger = logging.getLogger("main")
access_logger = logging.getLogger("access")


class LoggingWSGIRequestHandler(WSGIRequestHandler):
    def log_message(self, format: str, *args) -> None:
        access_logger.info('%s - "%s" %s %s', self.address_string(), self.requestline, args[1], args[2])


def main() -> None:
    try:
        config = get_app_config()
    except ConfigError as exc:
        raise SystemExit(f"Config error: {exc}") from exc

    scheduler = CronTaskRunner(software_releases.main, job_name="software_release_check")
    _log_startup_summary(config=config, scheduler=scheduler)

    if not config.web.enabled:
        scheduler.start()
        logger.info("Runtime mode: scheduler-only")
        _wait_forever(scheduler)
        return

    logger.info("Starting web API: url=http://%s:%s", config.web.host, config.web.port)
    try:
        server = make_server(config.web.host, config.web.port, app, handler_class=LoggingWSGIRequestHandler)
    except OSError as exc:
        if exc.errno == errno.EADDRINUSE:
            logger.error("Web API failed to start: address already in use at %s:%s", config.web.host, config.web.port)
            raise SystemExit(1) from exc
        logger.exception("Web API failed to start")
        raise SystemExit(1) from exc

    server.timeout = 0.5
    scheduler.start()
    stop_event = threading.Event()

    def _shutdown(*_args) -> None:
        if stop_event.is_set():
            return
        stop_event.set()
        logger.info("Shutting down apple-spyder...")
        scheduler.stop()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        while not stop_event.is_set():
            server.handle_request()
    finally:
        scheduler.stop()
        server.server_close()


def _log_startup_summary(*, config, scheduler: CronTaskRunner) -> None:
    next_run = scheduler.get_next_run_time() if config.scheduler.enabled else None
    logger.info("Apple Spyder starting...")
    logger.info("Config loaded: path=%s", CONFIG_PATH)
    logger.info("Database path: %s", DATABASE_PATH)
    logger.info(
        "Telegram: enabled=%s bot_name=%s target_count=%s targets=%s",
        config.telegram.enabled,
        config.telegram.bot_name,
        len(config.telegram.chat_ids),
        ",".join(config.telegram.chat_ids),
    )
    logger.info("Weibo: enabled=%s", config.weibo.enabled)
    logger.info("RSS source: %s", config.urls.apple_developer_rss)
    logger.info(
        "Scheduler: enabled=%s cron_expr=%s run_on_startup=%s next_run=%s",
        config.scheduler.enabled,
        config.scheduler.cron_expr,
        config.scheduler.run_on_startup,
        scheduler._format_time(next_run),
    )
    logger.info(
        "Web API: enabled=%s host=%s port=%s",
        config.web.enabled,
        config.web.host,
        config.web.port,
    )


def _wait_forever(scheduler: CronTaskRunner) -> None:
    stop_event = threading.Event()

    def _stop(*_args) -> None:
        if stop_event.is_set():
            return
        logger.info("Shutting down apple-spyder...")
        scheduler.stop()
        stop_event.set()

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)
    stop_event.wait()


if __name__ == "__main__":
    main()
