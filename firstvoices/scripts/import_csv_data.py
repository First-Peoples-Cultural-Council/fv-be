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

testpath = "/Your/Path/to/Import/File/sites_2023-05-18-15:36:23.104063.csv"

with open(testpath) as f:
    table = tablib.import_set(f, format="csv")
print(table)

resource = SiteResource()
result = resource.import_data(dataset=table, dry_run=False, raise_errors=True)

for type, total in result.totals.items():
    print(f"{type}: {total}")
