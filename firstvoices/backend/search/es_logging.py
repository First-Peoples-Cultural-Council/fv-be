import logging

from backend.search.utils.constants import ES_CONNECTION_ERROR, ES_NOT_FOUND_ERROR

ES_NOT_FOUND_INFO = (
    "Tried to find a document that doesn't exist in the index. [%s] id [%s]"
)

logger = logging.getLogger(__name__)


def log_connection_error(e, instance):
    log_connection_error_details(e, type(instance).__name__, instance.id)


def log_connection_error_details(e, type_name, instance_id):
    logger.error(
        ES_CONNECTION_ERROR + "Error: [%s]", type_name, type_name, instance_id, e
    )


def log_not_found_warning(e, instance):
    logger.warning(
        ES_NOT_FOUND_ERROR + "Error: [%s]",
        "get",
        type(instance).__name__,
        instance.id,
        e,
    )


def log_not_found_info(instance):
    log_not_found_info_details(type(instance).__name__, instance.id)


def log_not_found_info_details(type_name, instance_id):
    logger.info(ES_NOT_FOUND_INFO, type_name, instance_id)


def log_fallback_exception(e, instance):
    log_fallback_exception_details(e, type(instance).__name__, instance.id)


def log_fallback_exception_details(e, type_name, instance_id):
    logger.error(
        "Unhandled elasticsearch error, with [%s] id [%s]. Error: [%s]",
        type_name,
        instance_id,
        e,
    )
