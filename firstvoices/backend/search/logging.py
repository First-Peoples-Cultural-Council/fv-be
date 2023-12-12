import logging

from backend.search.utils.constants import ES_CONNECTION_ERROR, ES_NOT_FOUND_ERROR
from firstvoices.settings import ELASTICSEARCH_LOGGER


def log_connection_error(e, instance):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)
    logger.error(
        ES_CONNECTION_ERROR
        % (type(instance).__name__, type(instance).__name__, instance.id)
    )
    logger.error(e)


def log_not_found_error(e, instance):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)
    logger.warning(
        ES_NOT_FOUND_ERROR,
        "get",
        type(instance).__name__,
        instance.id,
    )
    logger.warning(e)


def log_fallback_exception(e, instance):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)
    logger.error(type(e).__name__, type(instance).__name__, instance.id)
    logger.error(e)
