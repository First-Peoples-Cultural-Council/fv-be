from celery import shared_task
from celery.utils.log import get_task_logger
from django.db import transaction
from django.utils import timezone

from backend.models import DictionaryEntry, SitePage, Song, Story, StoryPage
from backend.models.jobs import BulkVisibilityJob, JobStatus
from backend.models.sites import SiteFeature
from backend.models.widget import SiteWidget
from backend.search.tasks.site_content_indexing_tasks import (
    request_sync_all_site_content_in_indexes,
)
from backend.tasks.constants import ASYNC_TASK_END_TEMPLATE, ASYNC_TASK_START_TEMPLATE


@shared_task
def bulk_change_visibility(job_instance_id: str):
    """
    Changes the visibility of all site content from one visibility to another.
    """

    logger = get_task_logger(__name__)
    logger.info(ASYNC_TASK_START_TEMPLATE, f"job_instance_id: {job_instance_id}")

    job = BulkVisibilityJob.objects.get(id=job_instance_id)
    site = job.site
    indexing_paused_feature = SiteFeature.objects.get_or_create(
        site=site, key="indexing_paused"
    )

    if BulkVisibilityJob.objects.filter(status=JobStatus.STARTED, site=site).exists():
        cancelled_message = "Job cancelled as another bulk visibility job is already in progress for the same site."
        job.status = JobStatus.CANCELLED
        job.message = cancelled_message
        job.save()
        logger.info(cancelled_message)
        logger.info(ASYNC_TASK_END_TEMPLATE)
        return

    job.status = JobStatus.STARTED
    job.save()

    # Pause search indexing for the site the job is for
    indexing_paused_feature[0].is_enabled = True
    indexing_paused_feature[0].save()

    # Update all visibility for dictionary entries, songs, stories, story, pages, pages and widgets
    # Must be done as a single transaction
    entries = DictionaryEntry.objects.filter(site=site, visibility=job.from_visibility)
    songs = Song.objects.filter(site=site, visibility=job.from_visibility)
    stories = Story.objects.filter(site=site, visibility=job.from_visibility)
    story_pages = StoryPage.objects.filter(site=site, visibility=job.from_visibility)
    pages = SitePage.objects.filter(site=site, visibility=job.from_visibility)
    widgets = SiteWidget.objects.filter(site=site, visibility=job.from_visibility)

    try:
        with transaction.atomic():
            entries.update(
                system_last_modified=timezone.now(),
                system_last_modified_by=job.created_by,
                visibility=job.to_visibility,
            )
            songs.update(
                system_last_modified=timezone.now(),
                system_last_modified_by=job.created_by,
                visibility=job.to_visibility,
            )
            stories.update(
                system_last_modified=timezone.now(),
                system_last_modified_by=job.created_by,
                visibility=job.to_visibility,
            )
            story_pages.update(
                system_last_modified=timezone.now(),
                system_last_modified_by=job.created_by,
                visibility=job.to_visibility,
            )
            pages.update(
                system_last_modified=timezone.now(),
                system_last_modified_by=job.created_by,
                visibility=job.to_visibility,
            )
            widgets.update(
                system_last_modified=timezone.now(),
                system_last_modified_by=job.created_by,
                visibility=job.to_visibility,
            )
            # Change Site visibility
            site.visibility = job.to_visibility
            site.save()

    except Exception as e:
        # if there’s an error during the updates:
        # add the message to the batch visibility job instance and set the status to failed
        job.status = JobStatus.FAILED
        error_message = str(e)
        job.message = error_message
        job.save()

        indexing_paused_feature[0].is_enabled = False
        indexing_paused_feature[0].save()

        logger.error(error_message)
        logger.info(ASYNC_TASK_END_TEMPLATE)
        return

    # Resume search indexing for site, + reindex entire site
    indexing_paused_feature[0].is_enabled = False
    indexing_paused_feature[0].save()
    request_sync_all_site_content_in_indexes(site)

    # update status of job at each step
    job.status = JobStatus.COMPLETE
    job.save()

    logger.info(ASYNC_TASK_END_TEMPLATE)
