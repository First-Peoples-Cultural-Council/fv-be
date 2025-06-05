from elasticsearch.dsl import Q

BASE_BOOST = 1.0  # neutral default


def exact_match(q, field, boost=BASE_BOOST):
    """
    Returns: An elasticsearch dsl query clause for matching exact terms.
    """
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
    """
    Returns: An elasticsearch dsl query clause for matching full words, with fuzziness (typos and misspellings).
    """
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


def substring_match(q, field, boost=BASE_BOOST):
    """
    Returns: An elasticsearch dsl query clause for matching partial words (e.g., find "test" in "testing").
    """
    return Q(
        {
            "wildcard": {
                field: {
                    "value": f"*{q}*",
                    "boost": boost,
                }
            }
        }
    )
