from celery import current_task, shared_task
from celery.utils.log import get_task_logger
from django.db import transaction
from rest_framework.exceptions import ValidationError

from backend.models import DictionaryEntry
from backend.models.jobs import JobStatus
from backend.models.update_jobs import RollbackJob, UpdateJob, UpdateJobStatus
from backend.search.indexing.dictionary_index import DictionaryEntryDocumentManager
from backend.search.tasks.index_manager_tasks import request_sync_in_index
from backend.tasks.batch_utils import verify_no_other_jobs_running
from backend.tasks.utils.update_job_utils import (
    SNAPSHOT_RELATIONS,
    snapshot_entry,
    validate_snapshot_references,
)


@shared_task
def rollback_update_job(rollback_job_id):
    logger = get_task_logger(__name__)
    conflicts = []

    # Queue the rollback job if it is accepted and mark it as started.
    rollback_job = RollbackJob.objects.get(id=rollback_job_id)
    if rollback_job.status != JobStatus.ACCEPTED:
        logger.warning("Rollback job %s is not queued.", rollback_job_id)
        return
    rollback_job.status = JobStatus.STARTED
    rollback_job.task_id = current_task.request.id
    rollback_job.save()

    try:
        with transaction.atomic():
            update_job = UpdateJob.objects.get(
                id=rollback_job.update_job_id, site=rollback_job.site
            )
            if (
                update_job.status != UpdateJobStatus.COMPLETE
                or update_job.change_snapshot is None
            ):
                raise ValidationError(
                    "Only completed jobs with snapshots can be rolled back."
                )
            verify_no_other_jobs_running(rollback_job)

            snapshot = update_job.change_snapshot
            entries = {
                str(entry.id): entry
                for entry in DictionaryEntry.objects.filter(
                    site=update_job.site, id__in=snapshot
                ).prefetch_related(*SNAPSHOT_RELATIONS)
            }

            # Ensure all entries referenced in the snapshot exist in the database.
            missing = set(snapshot) - set(entries)
            if missing:
                raise ValidationError(
                    f"Cannot restore missing entries: {sorted(missing)}."
                )
            validate_snapshot_references(snapshot)

            for entry_id, change in snapshot.items():
                entry = entries[entry_id]
                current = snapshot_entry(entry)
                after = change["after_state"]

                # Identify fields that have changed between the current and after states.
                changed_fields = [
                    name
                    for section in ("fields", "relations")
                    for name, value in after[section].items()
                    if current[section][name] != value
                ]
                if changed_fields:
                    conflicts.append({"id": entry_id, "fields": changed_fields})

                # Restore the entry to its state before the update, bypassing save hooks.
                before = change["before_state"]
                DictionaryEntry.objects.filter(id=entry_id).update(**before["fields"])
                # Restore the many-to-many relations to their state before the update.
                for name, ids in before["relations"].items():
                    getattr(entry, name).set(ids)
                # Request sync in the search index for the restored entry.
                request_sync_in_index(DictionaryEntryDocumentManager, entry)

            if conflicts:
                logger.warning("Overriding rollback conflicts: %s", conflicts)
            update_job.status = UpdateJobStatus.ROLLED_BACK
            update_job.save()
            rollback_job.status = JobStatus.COMPLETE
            rollback_job.message = None
            rollback_job.conflicts = conflicts
            rollback_job.save()
            # TODO: Delete only orphaned job-created media/S3 files; support cleanup-only retries.
    except Exception as exc:
        logger.exception("Rollback job %s failed.", rollback_job_id)
        # Keep content changes atomic, but retain the failure report outside that transaction.
        RollbackJob.objects.filter(id=rollback_job_id).update(
            status=JobStatus.FAILED, message=str(exc), conflicts=conflicts
        )
