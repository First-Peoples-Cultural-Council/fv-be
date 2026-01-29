from celery import current_task, shared_task
from celery.utils.log import get_task_logger

from backend.models import Alphabet, DictionaryCleanupJob, DictionaryEntry
from backend.models.jobs import JobStatus
from backend.tasks.constants import ASYNC_TASK_END_TEMPLATE, ASYNC_TASK_START_TEMPLATE


@shared_task
def cleanup_dictionary(job_instance_id: str):
    """
    Calculates and returns the results of a custom order recalculation,
    including the changes in custom order and title and the count of unknown characters.
    Jobs marked as preview will not update DictionaryEntries in the database.
    """

    logger = get_task_logger(__name__)
    logger.info(ASYNC_TASK_START_TEMPLATE, f"job_instance_id: {job_instance_id}")

    job = DictionaryCleanupJob.objects.get(id=job_instance_id)
    job.task_id = current_task.request.id

    if DictionaryCleanupJob.objects.filter(
        status=JobStatus.STARTED, site=job.site
    ).exists():
        cancelled_message = "Job cancelled as another dictionary cleanup job is already in progress for the same site."
        job.status = JobStatus.CANCELLED
        job.message = cancelled_message
        job.save()
        logger.info(cancelled_message)
        logger.info(ASYNC_TASK_END_TEMPLATE)
        return

    job.status = JobStatus.STARTED
    job.save()

    site = job.site
    alphabet = Alphabet.objects.get_or_create(site=site)[0]
    results = {}

    # First, get the changes in custom order and title for every entry, and store entries with unknown characters
    updated_entries = []
    unknown_character_count = {}

    # Return the results of the recalculation i.e. the changes in custom order and title for every entry
    for entry in DictionaryEntry.objects.filter(site=site):
        original_title = entry.title
        original_custom_order = entry.custom_order

        cleaned_title = alphabet.clean_confusables(entry.title)
        new_order = alphabet.get_custom_order(cleaned_title)

        # If job is not preview, save the entry to recalculate custom order and clean title
        if not job.is_preview:
            try:
                entry.system_last_modified_by = job.created_by
                entry.save(set_modified_date=False)
            except Exception as e:
                job.status = JobStatus.FAILED
                job.message = str(e)
                job.save()

                logger.error(e)
                logger.info(ASYNC_TASK_END_TEMPLATE)
                return

        append_updated_entry(
            updated_entries,
            original_title,
            original_custom_order,
            cleaned_title,
            new_order,
        )

        # Count unknown characters remaining in each entry, first split by character, then apply custom order
        chars = alphabet.get_character_list(cleaned_title)
        for char in chars:
            custom_order = alphabet.get_custom_order(char)
            if "⚑" in custom_order:
                unknown_character_count[custom_order] = (
                    unknown_character_count.get(custom_order, 0) + 1
                )

    results["unknown_character_count"] = unknown_character_count
    results["updated_entries"] = updated_entries

    # Save the result to the database
    job.cleanup_result = results
    job.status = JobStatus.COMPLETE
    job.save()

    logger.info(ASYNC_TASK_END_TEMPLATE)


def append_updated_entry(
    updated_entries, original_title, original_custom_order, cleaned_title, new_order
):
    result = {
        "title": original_title,
        "cleaned_title": "",
        "is_title_updated": False,
        "previous_custom_order": original_custom_order,
        "new_custom_order": "",
    }

    if result["previous_custom_order"] != new_order:
        result["new_custom_order"] = new_order
    if result["title"] != cleaned_title:
        result["cleaned_title"] = cleaned_title
        result["is_title_updated"] = True

    if result["new_custom_order"] or result["cleaned_title"]:
        updated_entries.append(result)
