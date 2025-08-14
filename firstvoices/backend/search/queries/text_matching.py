from elasticsearch.dsl import Q

BASE_BOOST = 1.0  # neutral default


def exact_term_match(q, field, boost=BASE_BOOST):
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


def match_phrase(q, field, boost=BASE_BOOST, slop=0):
    """
    Returns: An elasticsearch dsl query clause for matching phrases.

    Parameters:
        field: The field to match
        q: search query
        boost: boost for matching phrase
        slop: How far apart the terms can be in order to match
    """
    return Q({"match_phrase": {field: {"query": q, "boost": boost, "slop": slop}}})


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
