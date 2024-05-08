import logging
import uuid

import tablib

from backend.models.import_jobs import ImportJobReport
from backend.resources.dictionary import DictionaryEntryResource


def get_uuid(row):
    return str(uuid.uuid4())


def toggle_boolean_column(table, old_column_name, new_column_name):
    # This utility function reverses the boolean values and renames
    # the column, as required for Audience flags

    # If the old column does not exist,
    # do nothing
    if old_column_name not in table.headers:
        return table

    column_index = table.headers.index(old_column_name)
    for row in table:
        old_value = row[column_index]
        new_value = not old_value

        new_row = list(row)
        new_row.append(new_value)
        del row[column_index]
    table.headers.append(new_column_name)
    del table.headers[column_index]
    return table


def execute_dry_run_import(import_job_instance):
    # This function will be modified later with a flag
    # to reuse the same code
    logger = logging.getLogger(__name__)
    site_id = str(import_job_instance.site.id)

    # Disconnecting search indexing signals
    # disconnect_signals()
    # logger.info("Disconnected all search index related signals")

    resource = DictionaryEntryResource()

    table = tablib.Dataset().load(
        import_job_instance.data.content.open().read().decode("utf-8-sig"), format="csv"
    )

    # Adjusting dataset
    # lower casing headers
    table.headers = [header.lower() for header in table.headers]
    # Adding site and id to each row
    # table.append_col([site_id]*table.height, header="site")
    table.append_col(get_uuid, header="id")
    table.append_col([str(site_id)] * table.height, header="site")
    table = toggle_boolean_column(table, "include_in_games", "exclude_from_games")
    table = toggle_boolean_column(table, "include_on_kids_site", "exclude_from_kids")

    try:
        result = resource.import_data(dataset=table, dry_run=True)
    except Exception as e:
        logger.error(e)

    # check for errors
    if result.has_errors():
        # Add ImportJobReportRow(s) for the respective errors
        pass

    # Create an ImportJobReport for the run
    report = ImportJobReport(
        # site=import_job_instance.site,
        site=import_job_instance.site,
        importjob=import_job_instance,
        new_rows=result.totals["new"],
        skipped_rows=result.totals["skip"],
        error_rows=result.totals["error"],
    )
    report.save()

    # Connecting back search indexing signals
    # connect_signals()
    # logger.info("Re-connected all search index related signals")

    # Confirm created/last_modified
    # Confirm if I can now modify the resource ?
