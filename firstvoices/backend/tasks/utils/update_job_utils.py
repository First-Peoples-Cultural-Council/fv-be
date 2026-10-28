from datetime import datetime
from uuid import UUID

import tablib
from rest_framework.exceptions import ValidationError

from backend.models import DictionaryEntry
from backend.models.import_jobs import ImportJobStatus
from backend.tasks.constants import MAXIMUM_ENTRIES_PER_UPDATE_JOB
from backend.utils.uuid_utils import is_valid_uuid

SNAPSHOT_RELATIONS = (
    "categories",
    "related_dictionary_entries",
    "related_characters",
    "related_audio",
    "related_documents",
    "related_images",
    "related_videos",
)


def snapshot_entry(entry):
    """Save entry fields and relationship IDs in a JSON-compatible format."""
    field_values = {}

    for field in entry._meta.concrete_fields:
        # Skip the primary key field as it is already used as the snapshot key.
        if field.primary_key:
            continue
        value = field.value_from_object(entry)

        # JSON cannot store datetime or UUID objects directly, so convert them to strings.
        if isinstance(value, datetime):
            value = value.isoformat()
        elif isinstance(value, UUID):
            value = str(value)
        field_values[field.attname] = value

    # Capture the IDs of related objects for each relationship defined in SNAPSHOT_RELATIONS.
    relations = {}
    for relation_name in SNAPSHOT_RELATIONS:
        related_objects = getattr(entry, relation_name).all()
        related_ids = []
        for related_object in related_objects:
            related_ids.append(str(related_object.id))

        # Sort the related IDs to ensure consistent ordering for comparison during rollback.
        relations[relation_name] = sorted(related_ids)

    return {
        "fields": field_values,
        "relations": relations,
    }


def snapshot_update_entries(data, update_job):
    """Capture existing same-site entries before the update runs."""
    entry_ids = []

    # Collect valid entry IDs from the CSV data for snapshotting.
    for row in data.dict:
        entry_id = row.get("id")
        # Invalid CSV rows are handled by the update process, not snapshot capture.
        if entry_id and is_valid_uuid(entry_id):
            entry_ids.append(entry_id)

    entries = DictionaryEntry.objects.filter(
        site=update_job.site, id__in=entry_ids
    ).prefetch_related(*SNAPSHOT_RELATIONS)

    snapshots = {}
    for entry in entries:
        snapshots[str(entry.id)] = snapshot_entry(entry)
    return snapshots


def validate_snapshot_references(snapshot):
    """Check that all old references exist before restoring any entries."""
    for entry_id, change in snapshot.items():
        before_state = change["before_state"]

        # Check that all foreign key references in the before state exist in the database.
        for field in DictionaryEntry._meta.concrete_fields:
            if not field.is_relation:
                continue

            related_id = before_state["fields"].get(field.attname)
            if related_id is None:
                continue

            related_model = field.related_model
            if not related_model.objects.filter(id=related_id).exists():
                raise ValidationError(
                    f"Cannot restore entry {entry_id}: missing {field.name} {related_id}."
                )

        # Check collection relationships without loading each related object separately.
        for relation_name, related_ids in before_state["relations"].items():
            relation_field = DictionaryEntry._meta.get_field(relation_name)
            related_model = relation_field.related_model
            existing_ids = related_model.objects.filter(id__in=related_ids).values_list(
                "id", flat=True
            )
            existing_ids = [str(related_id) for related_id in existing_ids]

            missing_ids = []
            for related_id in related_ids:
                if related_id not in existing_ids:
                    missing_ids.append(related_id)

            if missing_ids:
                raise ValidationError(
                    f"Cannot restore entry {entry_id}: missing {relation_name} {sorted(missing_ids)}."
                )


def verify_update_job_size_limit(current_job):
    """Reject update jobs whose CSV exceeds the allowed number of rows."""
    csv_content = current_job.data.content.open().read().decode("utf-8-sig")
    data = tablib.Dataset().load(csv_content, format="csv")
    entry_count = len(data)

    if entry_count > MAXIMUM_ENTRIES_PER_UPDATE_JOB:
        current_job.status = ImportJobStatus.FAILED
        current_job.save()
        raise ValidationError(
            f"The update job contains {entry_count} entries, "
            f"which exceeds the maximum allowed limit of {MAXIMUM_ENTRIES_PER_UPDATE_JOB} entries."
        )
