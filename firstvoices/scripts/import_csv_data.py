import os

import tablib

from backend.resources.sites import SiteResource

"""Script to import CSV files of site content into the fv-be database.

Designate the list of import tasks/models and their order
For each model, grab files from import todo area
    parse the filenames to know what kinds of imports they are
Delete the existing database
Start with general-FV level content (e.g. sites) -- for each file:
    If there's an error, halt the entire import (for now)
    if successful, save the data into the db
Then do site-wise content (tbd)

Run with:
    python manage.py shell < scripts/import_csv_data.py
"""


# Get Nuxeo data from AWS
# FIX: add download_latest here

data_dir = os.path.join(os.getcwd(), "scripts", "utils", "export_data")
# FIX: need a function to generate the same dir that aws saves to
data_export_list = os.listdir(data_dir)

if len(data_export_list) == 0:
    raise ValueError("No nuxeo export data found in AWS bucket.")
if len(data_export_list) > 1:
    raise ValueError("Multiple potential nuxeo exports found.")

current_export_dir = os.path.join(data_dir, data_export_list[-1])
unmatched_files = os.listdir(current_export_dir)
# if not unmatched_files:
#     raise ValueError("Nuxeo export contains no files to be imported.")
# FIX: is this necessary


# Match export files with model resources for import, in import order
import_resources = [
    ("sites", SiteResource()),
    # more to be added
]
# ??? should we import by model or by site? currently by model b/c easier

files_to_import = {}
for prefix, _ in import_resources:
    # Parse files to import with this resource
    matched_files = [f for f in unmatched_files if f.startswith(prefix)]
    if not matched_files:
        pass  # ??? raise some kind of warning?

    files_to_import[prefix] = matched_files

    for f in matched_files:
        unmatched_files.remove(f)

# TODO: Delete the database so it is clean
print("Deleting existing data...")

# Perform the import
for prefix, resource in import_resources:
    print(f"\nImporting {prefix} models...")

    for file in files_to_import[prefix]:
        print(f"Importing file: {file}")
        with open(os.path.join(current_export_dir, file)) as f:
            table = tablib.import_set(f, format="csv")
        result = resource.import_data(dataset=table, dry_run=True, raise_errors=False)
        # FIX: fix settings -- we should raise errors for now, currently off

        for type, total in result.totals.items():
            print(f"{type}: {total}")

if unmatched_files:
    print(f"\n{len(unmatched_files)} files could not be imported (no resource defined)")
    print(unmatched_files)

# if import is successful, delete the export from local, and move to "DONE" in aws
# if import failed, retain local and don't move in AWS
