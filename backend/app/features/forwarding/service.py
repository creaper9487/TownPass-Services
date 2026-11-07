"""送件佇列：把含個資的預約送到中心。送達即刪；24 小時內送不出去就刪除並發警報。"""

from datetime import timedelta

from app.features.forwarding import repository as repo
from app.tools.crawlers import forward_reservation
from app.tools.crawlers.runner import run_crawler
from app.tools.crawlers.schemas import ForwardReceipt
from app.tools.logger import get_logger
from app.tools.timeutil import now

logger = get_logger(__name__)

JOB_TTL = timedelta(hours=24)
RETRY_BACKOFF = [30, 60, 300, 900, 1800, 3600]  # 秒


def enqueue(reservation_id: str, payload: dict) -> None:
    t = now()
    repo.jobs[reservation_id] = repo.ForwardJob(
        reservation_id, payload, 0, "pending", t, t + JOB_TTL
    )


def cancel(reservation_id: str) -> None:
    repo.jobs.pop(reservation_id, None)


async def process_due() -> None:
    """背景工作：送出到期的工作。回呼 reservation 更新 forward_state。"""
    from app.features.reservation import service as reservation_service

    t = now()
    for job in list(repo.jobs.values()):
        if t >= job.expires_at:
            # 不 log 個資，只記 id
            logger.error("forward job expired, needs manual handling: %s", job.reservation_id)
            repo.jobs.pop(job.reservation_id, None)
            reservation_service.set_forward_state(job.reservation_id, "failed")
            continue
        if t < job.next_try_at:
            continue
        try:
            receipt = await run_crawler(forward_reservation, ForwardReceipt, job.payload)
        except NotImplementedError:
            job.next_try_at = t + timedelta(seconds=RETRY_BACKOFF[0])
            continue
        except Exception as exc:  # noqa: BLE001  暫時性失敗 → 重試
            job.attempts += 1
            delay = RETRY_BACKOFF[min(job.attempts - 1, len(RETRY_BACKOFF) - 1)]
            job.next_try_at = t + timedelta(seconds=delay)
            logger.warning("forward %s failed (%s), retry in %ss", job.reservation_id, type(exc).__name__, delay)
            continue

        repo.jobs.pop(job.reservation_id, None)  # 送達（或永久失敗）即刪個資
        reservation_service.set_forward_state(job.reservation_id, "sent" if receipt.accepted else "failed")
