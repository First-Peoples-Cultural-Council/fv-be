import logging

from elasticsearch import Elasticsearch
from elasticsearch_dsl import connections

from firstvoices.settings import ELASTICSEARCH_HOST, ELASTICSEARCH_LOGGER


def elasticsearch_running():
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)

    try:
        es = Elasticsearch([ELASTICSEARCH_HOST], verify_certs=True)
        if not es.ping():
            raise ValueError("Connection Refused")
        connections.configure(default={"hosts": ELASTICSEARCH_HOST})
        logger.info(f"{logger.name} - Elasticsearch connection successful.")
        return True
    except (ConnectionError, ValueError):
        logger.warning(
            "Elasticsearch server down. Documents will not be indexed or returned from search."
        )
        return False
