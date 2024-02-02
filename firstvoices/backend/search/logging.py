import logging

from backend.search.utils.constants import ES_CONNECTION_ERROR, ES_NOT_FOUND_ERROR
from firstvoices.settings import ELASTICSEARCH_LOGGER

ES_NOT_FOUND_INFO = (
    "Tried to remove a document that doesn't exist in the index. [%s] id [%s]"
)

logger = logging.getLogger(ELASTICSEARCH_LOGGER)


def log_connection_error(e, instance):
    logger.error(
        ES_CONNECTION_ERROR
        % (type(instance).__name__, type(instance).__name__, instance.id)
    )
    logger.error(e)


def log_not_found_warning(e, instance):
    logger.warning(
        ES_NOT_FOUND_ERROR,
        "get",
        type(instance).__name__,
        instance.id,
    )
    logger.warning(e)


def log_not_found_info(instance):
    logger.info(
        ES_NOT_FOUND_INFO,
        type(instance).__name__,
        instance.id,
    )


def log_fallback_exception(e, instance):
    logger.error(type(e).__name__, type(instance).__name__, instance.id)
    logger.error(e)
