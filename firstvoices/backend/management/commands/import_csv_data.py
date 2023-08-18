import logging
import os

import tablib
from django.core.management import BaseCommand
from scripts.utils.aws_download_utils import (
    EXPORT_STORAGE_DIRECTORY,
    download_latest_exports,
)

from backend.models.app import AppImportStatus
from backend.resources.app import AppMembershipResource
from backend.resources.categories import CategoryMigrationResource
from backend.resources.characters import (
    CharacterResource,
    CharacterVariantResource,
    IgnoredCharacterResource,
)
from backend.resources.media import (
    AudioResource,
    AudioSpeakerMigrationResource,
    ImageResource,
    PersonResource,
    VideoResource,
)
from backend.resources.sites import (
    MembershipResource,
    SiteMigrationResource,
    SiteResource,
)
from backend.resources.users import UserResource
from backend.resources.widgets import SiteWidgetResource, WidgetSettingsResource


class Command(BaseCommand):
    def handle(self, **options):
        run_import()


def run_import():
    """Script to import CSV files of site content into the fv-be database.

    Locally downloads import files from AWS, then matches them with the right
    backend model resource to import with. Deletes the database, then imports
    model-by-model in a specified order into the clean space.
    Halts the process when encountering any data/validation error.

    Run with:
        python manage.py import_csv_data

    To add a new import:
        - Create or re-use a "Resource" mapping to the desired django model
        - Ensure all complex model properties (e.g. foreign keys) are correctly
            mapped to Python objects using a django-import-export "Widget"
        - https://django-import-export.readthedocs.io/en/latest/getting_started.html
    """

    logger = logging.getLogger(__name__)

    # Check that export data exists, if not then download it from AWS
    if not os.path.exists(EXPORT_STORAGE_DIRECTORY):
        download_latest_exports()

    available_exports = os.listdir(EXPORT_STORAGE_DIRECTORY)
    if not available_exports:
        download_latest_exports()
        available_exports = os.listdir(EXPORT_STORAGE_DIRECTORY)
    elif len(available_exports) > 1:
        raise ValueError("Multiple potential nuxeo exports found, aborting.")

    current_export_dir = os.path.join(EXPORT_STORAGE_DIRECTORY, available_exports[0])

    status = AppImportStatus.objects.create(
        label=f"nuxeo_import_{available_exports[0]}"
    )

    # List model resources in the correct order to import them
    import_resources = [
        ("users", UserResource()),
        ("app-memberships", AppMembershipResource()),
        ("sites", SiteMigrationResource()),
        ("site-memberships", MembershipResource()),
        ("categories", CategoryMigrationResource()),
        ("contributors", PersonResource()),
        ("audio-data", AudioResource()),
        ("audio-speakers", AudioSpeakerMigrationResource()),
        ("image-data", ImageResource()),
        ("video-data", VideoResource()),
        ("site_media", SiteResource()),
        ("base-characters", CharacterResource()),
        ("variant-characters", CharacterVariantResource()),
        ("ignored-characters", IgnoredCharacterResource()),
        ("site-widgets", SiteWidgetResource()),
        ("widget-settings", WidgetSettingsResource()),
        # more to be added
    ]

    # Match export files with the correct model resource and import them
    unmatched_files = os.listdir(current_export_dir)

    for key, resource in import_resources:
        logger.info(f"Importing {key} models...")

        # Parse files to import with this resource
        matched_files = [f for f in unmatched_files if f.startswith(key)]
        unmatched_files = [f for f in unmatched_files if f not in matched_files]

        if not matched_files:
            logger.warn(f"No '{key}' files found to import")
            status.no_warnings = False
            status.save()

        # Perform import
        for file in matched_files:
            logger.info(f"Importing file: {file}")
            with open(os.path.join(current_export_dir, file)) as f:
                table = tablib.import_set(f, format="csv")

            # raise errors to halt the import if an issue occurs
            try:
                result = resource.import_data(dataset=table, raise_errors=True)
                logger.info(
                    " ".join(
                        [f"{type}: {total}" for type, total in result.totals.items()]
                    )
                )
            except Exception as e:
                status.no_warnings = False
                status.save()
                raise e

    for file in unmatched_files:
        logger.warn(f"\n{file} not imported (no resource defined)")
        status.no_warnings = False

    # Clean up artifacts and update import status
    status.successful = True
    status.save()

    for file in os.listdir(current_export_dir):
        os.remove(os.path.join(current_export_dir, file))
    os.rmdir(current_export_dir)