from elasticsearch.exceptions import NotFoundError


def delete_index(index):
    try:
        delete_status = index.delete()
    except NotFoundError:
        print("Current index not found for deletion. Creating a new index.")
    return delete_status
