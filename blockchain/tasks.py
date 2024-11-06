import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def process_events(logs: dict[str, any]):
    logger.info("Begin task... ")

    logger.info("Task processed task... ")

    return "DONE"




