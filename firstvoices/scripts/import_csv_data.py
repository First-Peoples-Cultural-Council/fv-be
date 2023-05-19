import tablib
from import_export import resources

from backend.models.sites import Site

"""Script to import CSV files of site content into the fv-be database.

Designate the list of import tasks/models and their order
Connect to the import inbox directory
For each model, grab files from import todo area
    parse the filenames to know what kinds of imports they are
Start with general-FV level content (e.g. sites) -- for each file:
    Open the file
    Convert to tablib format
    (Somehow validate to make sure content doesn't violate model?)
    import data (dry run for now)
    if there's an error, exit the entire task bc we can't be sure??
    but if successful, save the data into the db
Then do site-wise content
    Parse the file name to determine the site id to upload to
    Make sure that site id exists in the db

Run with:
    python manage.py shell < scripts/import_csv_data.py
"""

testpath = "/Your/Path/to/Import/File/sites_2023-05-18-15:36:23.104063.csv"

with open(testpath) as f:
    table = tablib.import_set(f, format="csv")
print(table)

site_resource = resources.modelresource_factory(model=Site)()
result = site_resource.import_data(dataset=table, dry_run=True, raise_errors=True)
# TODO: currently only works if the user already exists
# TODO: convert nuxeo state to visibility

print(result.has_errors())
print(result.has_validation_errors())
print(result.totals)
# OrderedDict([('new', 0), ('update', 0), ('delete', 0), ('skip', 0), ('error', 1), ('invalid', 9)])
# TODO: this result can be parsed in tests to make sure things are smooth
