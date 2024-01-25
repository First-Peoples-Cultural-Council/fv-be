from elasticsearch_dsl import Q

BASE_BOOST = 1.0  # neutral default


def exact_match(q, field, boost=BASE_BOOST):
    return Q(
        {
            "term": {
                field: {
                    "value": q,
                    "boost": boost,
                }
            }
        }
    )


def fuzzy_match(q, field, boost=BASE_BOOST):
    return Q(
        {
            "match": {
                field: {
                    "query": q,
                    "boost": boost,
                    "fuzziness": "AUTO",
                }
            }
        }
    )
