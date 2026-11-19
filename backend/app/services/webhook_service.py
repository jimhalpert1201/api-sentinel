import asyncio
import logging

import httpx

from app.schemas.webhook import WebhookPayload

logger = logging.getLogger(__name__)

# Keep strong references to background tasks to prevent premature garbage collection (RUF006)
_background_tasks: set[asyncio.Task] = set()


async def _perform_webhook_post(webhook_url: str, payload_data: dict) -> httpx.Response:
    """Send single HTTP POST request to webhook destination."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        return await client.post(webhook_url, json=payload_data)


async def send_incident_webhook(webhook_url: str, payload: WebhookPayload) -> bool:
    """
    Send an incident webhook notification with resilience against transient failures.
    - Times out after 5.0 seconds.
    - Retries once on 5xx server errors or network disconnects with 2.0s backoff.
    - Never raises exceptions to the caller; failures are safely logged.
    """
    payload_data = payload.model_dump(mode="json")
    max_attempts = 2

    for attempt in range(1, max_attempts + 1):
        try:
            response = await _perform_webhook_post(webhook_url, payload_data)
            if response.status_code < 400:
                logger.info(
                    "Webhook successfully delivered to %s for incident %s",
                    webhook_url,
                    payload.incident_id,
                )
                return True

            if 400 <= response.status_code < 500:
                logger.warning(
                    "Webhook target %s returned client error %d. Not retrying.",
                    webhook_url,
                    response.status_code,
                )
                return False

            # Status code >= 500
            logger.warning(
                "Webhook target %s returned server error %d (attempt %d/%d).",
                webhook_url,
                response.status_code,
                attempt,
                max_attempts,
            )

        except (httpx.TimeoutException, httpx.NetworkError, Exception) as exc:
            logger.warning(
                "Webhook delivery attempt %d/%d to %s failed: %s",
                attempt,
                max_attempts,
                webhook_url,
                str(exc),
            )

        # Retry once after delay if attempt < max_attempts
        if attempt < max_attempts:
            await asyncio.sleep(2.0)

    logger.error(
        "Failed to deliver webhook to %s after %d attempts for incident %s",
        webhook_url,
        max_attempts,
        payload.incident_id,
    )
    return False


def dispatch_incident_webhook_safely(
    webhook_url: str | None,
    payload: WebhookPayload,
) -> None:
    """
    Safely schedule an asynchronous webhook dispatch task.
    Gracefully handles environments without an active event loop (e.g. sync unit tests).
    """
    if not webhook_url:
        return

    try:
        loop = asyncio.get_running_loop()
        task = loop.create_task(send_incident_webhook(webhook_url, payload))
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)
    except RuntimeError:
        # No running event loop in current thread
        logger.debug("No active event loop to schedule webhook dispatch.")
