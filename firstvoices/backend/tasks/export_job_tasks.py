import logging

from celery import current_task, shared_task
from celery.utils.log import get_task_logger
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.utils import timezone

from backend import models
from backend.models.files import File
from backend.models.import_jobs import JobStatus
from backend.models.jobs import ExportJob
from backend.search.queries.query_builder import (
    get_base_entries_search_query,
    get_base_entries_sort_query,
)
from backend.search.utils import get_ids_by_type, get_search_response, queryset_as_map
from backend.serializers.export_serializers import DictionaryEntryExportSerializer
from backend.tasks.constants import ASYNC_TASK_END_TEMPLATE, ASYNC_TASK_START_TEMPLATE
from backend.utils.export_utils import convert_queryset_to_csv_content


@shared_task
def generate_export_csv(export_job_id):
    """
    Executes the search, then hydrates and serializes the search results.
    Converts the results into a csv, uploads the csv and attaches it to the export job.
    """

    logger = get_task_logger(__name__)
    task_id = current_task.request.id
    logger.info(
        ASYNC_TASK_START_TEMPLATE,
        f"ExportJob id: {export_job_id}",
    )

    export_job = ExportJob.objects.get(id=export_job_id)

    if export_job.status in [
        JobStatus.STARTED,
        JobStatus.COMPLETE,
    ]:
        logger.info(
            "This job could not be started as it is either already running or completed. "
            f"ExportJob id: {export_job_id}."
        )
        return

    export_job.task_id = task_id
    export_job.save()

    generate_export(export_job)

    logger.info(ASYNC_TASK_END_TEMPLATE)


def generate_export(export_job_instance):
    flatten_fields = {
        "categories": "category",
        "translations": "translation",
        "notes": "note",
        "acknowledgements": "acknowledgement",
        "alternate_spellings": "alternate_spelling",
        "pronunciations": "pronunciation",
        "related_dictionary_entries": "related_entry_id",
    }

    logger = get_task_logger(__name__)
    user = get_user_model().objects.filter(email=export_job_instance.created_by).first()

    export_job_instance.status = JobStatus.STARTED
    export_job_instance.save()

    search_params = export_job_instance.export_params.copy()
    search_params["user"] = user
    filename = f"export_{export_job_instance.site.slug}_{
        timezone.localtime(timezone.now()).strftime("%Y_%m_%d_%H_%M_%S")
    }.csv"

    results = None

    try:
        results = get_search_results(search_params)
    except Exception as e:
        logger.error(
            f"Unable to get search results for export_job: {str(export_job_instance.id)}. Error: {e}."
        )
        export_job_instance.status = JobStatus.FAILED

    csv_string = None

    if results:
        try:
            csv_string = convert_queryset_to_csv_content(results, flatten_fields)
        except Exception as e:
            logger.error(
                f"Unable to convert queryset to csv content for export_job: {str(export_job_instance.id)}. Error: {e}."
            )
            export_job_instance.status = JobStatus.FAILED
            export_job_instance.save()

    if csv_string:
        try:
            csv_file_content = ContentFile(csv_string, filename)
            export_csv_file = File(
                content=csv_file_content,
                site=export_job_instance.site,
                created_by=export_job_instance.last_modified_by,
                last_modified_by=export_job_instance.last_modified_by,
            )
            export_csv_file.save()
            export_job_instance.export_csv = export_csv_file
            export_job_instance.status = JobStatus.COMPLETE
        except Exception as e:
            logger.error(
                "Unable to either create, save, or attach csv for export_job: "
                f"{str(export_job_instance.id)}. Error: {e}."
            )
            export_job_instance.status = JobStatus.FAILED
        finally:
            export_job_instance.save()


def get_search_results(search_params):

    search_query = get_base_entries_search_query(**search_params)
    search_query = get_base_entries_sort_query(search_query, **search_params)

    response = get_search_response(search_query)
    search_results = response["hits"]["hits"]

    data = hydrate(search_results, search_params["user"])
    serialized_data = []

    for result in search_results:
        item = serialize_result(result, data)
        if item:
            serialized_data.append(item)
    serialized_data = [
        dictionary_entry["entry"] for dictionary_entry in serialized_data
    ]

    return serialized_data


def hydrate(search_results, user):
    """Retrieves data for each item in the search results, grouped by type. If a serializer is defined for the type,
    attempts to use the serializer to add eager fetching (prefetch, etc). Returns actual data not lazy querysets.

        Returns: a dictionary where the keys are model names and the values are maps of { model_id: model_instance}
            for that type.
    """
    ids = get_ids_by_type(search_results)
    data = {}

    for model_name, model_ids in ids.items():
        queryset = getattr(models, model_name).objects.filter(id__in=model_ids)
        queryset = make_queryset_eager(model_name, queryset, user)

        data[model_name] = queryset_as_map(queryset)

    return data


def make_queryset_eager(model_name, queryset, user):
    """Pass the user to serializers, to allow for permission-based prefetching.

    Returns: updated queryset
    """
    serializer = get_serializer_class_for_model_type(model_name)
    if hasattr(serializer, "make_queryset_eager"):
        return serializer.make_queryset_eager(queryset, user)
    else:
        return queryset


def serialize_result(result, data):
    """Serializes a single search_result, using the provided hydration data and the configured serializer classes.

    Params:
        search_result: an ElasticSearch hit
        data: a dictionary of data objects keyed by model, as returned by the hydrate method

    Returns: serializer data
    """

    data_to_serialize = get_data_to_serialize(result, data)

    if not data_to_serialize:
        return None

    result_type = result["_source"]["document_type"]
    serializer = get_serializer_class_for_model_type(result_type)

    return serializer(data_to_serialize).data


def get_data_to_serialize(result, data):
    entry_data = None
    result_type = result["_source"]["document_type"]
    result_id = result["_source"]["document_id"]
    try:
        entry_data = data[str(result_type)][str(result_id)]
    except KeyError:
        logger = logging.getLogger(__name__)
        logger.warning(
            "Search result was not found in database. [%s] id [%s]",
            result_type,
            result_id,
        )

    if entry_data is None:
        return None

    return {"search_result_id": result["_id"], "entry": entry_data}


def get_serializer_class_for_model_type(model_type):
    serializer_classes = {
        "DictionaryEntry": DictionaryEntryExportSerializer,
    }
    if model_type in serializer_classes:
        return serializer_classes[model_type]

    return None
