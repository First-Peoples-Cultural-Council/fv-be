from elasticsearch.exceptions import NotFoundError


def rebuild_index(index, index_document):
    # Delete index
    delete_index(index)

    # Initialize new index
    index_document.init()


def delete_index(index):
    try:
        index.delete()
    except NotFoundError:
        print("Current index not found for deletion. Creating a new index.")
