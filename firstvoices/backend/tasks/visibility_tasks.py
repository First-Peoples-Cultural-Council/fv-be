from celery import shared_task
from django.db import transaction

from backend.models import DictionaryEntry, SitePage, Song, Story, StoryPage
from backend.models.jobs import BulkVisibilityJob, JobStatus
from backend.models.widget import SiteWidget
from backend.search.signals.utils.pausing import pause_indexing, unpause_indexing
from backend.search.tasks.site_content_indexing_tasks import (
    sync_all_site_content_in_indexes,
)


@shared_task
def bulk_change_visibility(job_instance_id):
    """
    Changes the visibility of all site content from one visibility to another.
    """
    job = BulkVisibilityJob.objects.get(id=job_instance_id)
    site = job.site

    if BulkVisibilityJob.objects.filter(status=JobStatus.STARTED, site=site).exists():
        job.status = JobStatus.CANCELLED
        job.message = "Job cancelled as another bulk visibility job is already in progress for the same site."
        job.save()
        return

    job.status = JobStatus.STARTED
    job.save()

    pause_indexing(site)

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
            entries.update(visibility=job.to_visibility)
            songs.update(visibility=job.to_visibility)
            stories.update(visibility=job.to_visibility)
            story_pages.update(visibility=job.to_visibility)
            pages.update(visibility=job.to_visibility)
            widgets.update(visibility=job.to_visibility)
            # Change Site visibility
            site.visibility = job.to_visibility
            site.save()

    except Exception as e:
        # if there’s an error during the updates:
        # add the message to the batch visibility job instance and set the status to failed
        job.status = JobStatus.FAILED
        job.message = str(e)
        job.save()

        unpause_indexing(site)
        return

    # Resume search indexing for site, + reindex entire site
    unpause_indexing(site)
    sync_all_site_content_in_indexes(site)

    # update status of job at each step
    job.status = JobStatus.COMPLETE
    job.save()
