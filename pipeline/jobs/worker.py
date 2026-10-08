"""Worker process: runs scheduled jobs with APScheduler.

Phase 1 only schedules a heartbeat. Phase 10 adds the ingest and detection jobs.
"""

import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from pipeline.config import get_settings

log = logging.getLogger("worker")


def heartbeat() -> None:
    s = get_settings()
    log.info("worker alive (mode=%s, basin=%s)", s.data_mode.value, s.basin_id)


def build_scheduler() -> BlockingScheduler:
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(heartbeat, "interval", minutes=5, id="heartbeat")
    return scheduler


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    heartbeat()
    build_scheduler().start()


if __name__ == "__main__":
    main()
