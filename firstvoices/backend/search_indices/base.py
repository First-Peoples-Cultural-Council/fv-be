import logging

from elasticsearch import Elasticsearch
from elasticsearch_dsl import connections

from firstvoices.settings import ELASTICSEARCH_HOST


def elasticsearch_running():
    try:
        es = Elasticsearch([ELASTICSEARCH_HOST], verify_certs=True)
        if not es.ping():
            raise ValueError("Connection Refused")
        connections.configure(default={"hosts": ELASTICSEARCH_HOST})
        return True
    except (ConnectionError, ValueError):
        logger = logging.getLogger(__name__)
        logger.warning(
            "Elasticsearch server down. Documents will not be indexed or returned from search."
        )
        return False
