import logging
import os

import tablib
from django.core.management import BaseCommand

from backend.resources.gallery import GalleryResource


class Command(BaseCommand):
    help = "Import CSV files of galleries into the fv-be database."

    # add argument to specify upload file directory
    def add_arguments(self, parser):
        parser.add_argument(
            "--filepath",
            dest="filepath",
            help="Directory where the import files are stored",
            default=None,
            required=True,
        )

    def handle(self, *args, **options):
        """
        Script to import CSV files of galleries into the fv-be database.

        Retrieves csv files from a local directory, then imports them with the gallery resource.

        Run with:
        python manage.py import_gallery_data --filepath /path/to/csv/files

        """

        logger = logging.getLogger(__name__)
        filepath = options["filepath"]

        if not os.path.exists(filepath):
            raise ValueError(f"Filepath {filepath} does not exist.")

        gallery_files = [f for f in os.listdir(filepath) if f.endswith(".csv")]

        if not gallery_files:
            raise ValueError("No CSV files found in the specified directory.")

        logger.info(f"Found {len(gallery_files)} gallery CSV files to process.")

        for file_name in gallery_files:
            full_path = os.path.join(filepath, file_name)
            logger.info(f"Processing file: {full_path}")

            try:
                with open(full_path, encoding="utf-8") as file:
                    table = tablib.import_set(file, format="csv")
                    resource = GalleryResource()

                    # Import the dataset
                    result = resource.import_data(table, dry_run=False)

                    # Log results
                    self.log_results(result, file_name)
            except Exception as e:
                logger.error(f"Error processing file {file_name}: {e}")
                continue

        logger.info("Gallery import completed.")

    def log_results(self, result, file_name):
        """
        Log the results of the import process.
        """
        if result.has_errors():
            self.stdout.write(f"Errors encountered while importing {file_name}:")
            for error in result.row_errors():
                self.stdout.write(f"Row {error[0]}: {error[1]}")
        else:
            self.stdout.write(f"File {file_name} imported successfully.")
