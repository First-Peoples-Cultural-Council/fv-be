# FirstVoices Backend

Backend for the FirstVoices application

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=First-Peoples-Cultural-Council_fv-be&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=First-Peoples-Cultural-Council_fv-be)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=First-Peoples-Cultural-Council_fv-be&metric=coverage)](https://sonarcloud.io/summary/new_code?id=First-Peoples-Cultural-Council_fv-be)
[![Build](https://github.com/First-Peoples-Cultural-Council/fv-be/actions/workflows/build.yml/badge.svg)](https://github.com/First-Peoples-Cultural-Council/fv-be/actions/workflows/build.yml)

License: Apache Software License 2.0

---

## Developer setup

1. Clone the repo: `git clone https://github.com/First-Peoples-Cultural-Council/fv-be.git`
1. Install prereqs:
   - [Python 3.10+](https://www.python.org/)
     - (Recommended: [pyenv](https://github.com/pyenv/pyenv) to install and manage current Python versions)
   - [PostgreSQL](https://www.postgresql.org/)
     - Recommended Mac installation: Using Homebrew
       - `brew update`
       - `brew install libmagic`
       - `brew install postgresql`
       - `brew services start postgresql` to start the service and autostart on system startup.
       - `brew services stop postgresql` to stop the service.
     - For other operating systems see [the official installation docs](https://www.postgresql.org/docs/current/installation.html).
   - [FFmpeg](http://ffmpeg.org/)
     - Recommended Mac installation: Using Homebrew
       - `brew update`
       - `brew install ffmpeg`
     - For other operating systems see [the official downloads page](https://ffmpeg.org/download.html).
   - [libmagic library for python-magic wrapper](https://github.com/ahupp/python-magic)
     - Recommended Mac installation: Using Homebrew
       - `brew update`
       - `brew install libmagic`
     - For other operating systems see [the installation page in the README](https://github.com/ahupp/python-magic#installation).
1. (Recommended) Create and activate a virtual environment in the root of the project
   - (Recommended [venv](https://docs.python.org/3/library/venv.html) or [direnv](https://direnv.net/))
   - If using [venv](https://docs.python.org/3/library/venv.html)
     - python -m venv <name for your venv>
     - `source <name for your venv>/bin/activate`
   - If using [direnv](https://direnv.net/)
     - Install direnv as explained in the [official installation docs](https://direnv.net/docs/installation.html).
     - Create a .envrc file in the root project directory
     - Add environment variables to the .envrc file and they will be loaded into your environment whenever you navigate your terminal to the root directory and any child directories.
1. Install requirements
   - `pip install -r requirements.debug.txt`
1. Install pre-commit hooks
   - `pre-commit install`
1. Create a database in postgres, and note the name
   - `createdb --username=postgres <db name>` - use the name `fv_be` for local development (see Local Database Cleanup Script instructions below)
1. Configure required environment variables for the database:
   - `DB_DATABASE`: `<db name>` when you created the database
   - `DB_USERNAME`: the database admin username (usually `postgres`)
   - `DB_PASSWORD`: the password for your database (can be blank if you have not set a password)
   - `DB_HOST`: the host address your database is running on (usually `127.0.0.1` if running locally)
   - `DB_PORT`: the port your database is running on (defaults to `5432` if you haven't changed it)
   - Recommended:
     - `DJANGO_SUPERUSER_EMAIL`: an email for the app superuser account (used to log in to the admin panel).
     - `DJANGO_SUPERUSER_USERNAME`: a username for the app superuser account.
     - `DJANGO_SUPERUSER_PASSWORD`: a password for the app superuser account.
1. Configure required environment variables for media file storage:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `MEDIA_UPLOAD_S3_BUCKET`
   - `MEDIA_UPLOAD_S3_REGION`
1. Configure optional environment variables as needed (used for the reset-local-database.sh script, Sentry and Elasticsearch):
   - `SENTRY_DSN`: the data source name that tells the Sentry SDK where to send events (to upload to the dashboard). If this is not set then events will not be sent to a dashboard.
   - `SENTRY_ENVIRONMENT`: a string specifying the name of the environment to tag Sentry events with (defaults to `production` if not set).
   - `SENTRY_RELEASE`: a custom release version to tag Sentry events with (defaults to the commit SHA if not set).
   - `SENTRY_TRACES_SAMPLE_RATE`: the sample rate for error events, in the range of 0.0 to 1.0 (defaults to 1.0 if not set, meaning 100% of the errors are sent).
   - `DJANGO_ADMIN_URL`: sets the URL of the admin panel for security purposes (defaults to `admin/` if not set).
   - `DATA_S3_BUCKET`: the name of the S3 Bucket that export data is stored in (if using the aws_download_utils.py script to download export data).
   - `DJANGO_SECRET_KEY`: required for non-debug (production) installations
   - `ENVIRONMENT_COLOR`: optional css-compatible color string, to highlight the environment name on the admin site
   - `ELASTICSEARCH_DEFAULT_SHARDS`: if you want to change the number of shards (used for elasticsearch purposes)
   - `ELASTICSEARCH_DEFAULT_REPLICAS`: if you want to change the number of replicas (used for elasticsearch purposes)
   - If using [venv](https://docs.python.org/3/library/venv.html)
     - You can add `export <variable name>=<variable value>` to the `<name for your venv>/bin/activate` file.
   - If using [direnv](https://direnv.net/)
     - You can add `export <variable name>=<variable value>` to the `.envrc` file in the root of you project.
1. Apply migration
   - Navigate to the `firstvoices` directory: `cd firstvoices`
   - From the `firstvoices` directory: `python manage.py migrate`
1. Start the server
   - Navigate to the `firstvoices` directory if you aren't already there: `cd firstvoices`
   - `python manage.py runserver`
1. (Optional) To load data from fixtures, use the following command (from inside the `firstvoices` directory) and replace `<fixture_name>` with fixtures available.
   - `python manage.py loaddata <fixture_name>`
   - Fixtures available:
     - Default fixtures which are automatically loaded in migrations:
       - `appjson-defaults.json`
       - `appjson-has_app.json`
       - `default_g2p_config.json`
       - `language_families.json`
       - `languages.json`
       - `partsOfSpeech_initial.json`
     - Other:
       - None
1. (Optional) To run ElasticSearch, RabbitMQ and redis, the following command needs to be run from the fv-be folder.
   `docker compose up -d` which will run all the mentioned docker services.
   To run a specific service for some testing purposes, use the following command:
   `docker compose up -d {service}` e.g.`docker compose up -d elastic`.
   1. For ElasticSearch, to confirm the service is up and running, visit
      http://localhost:9200/ and verify the status.
1. (Optional) By default, the App will send emails to console but an SMTP server can be used by setting the following environment variables:
   - `ENABLE_SMTP_BACKEND`: Set to `True` to enable the SMTP backend.
   - `EMAIL_SENDER_ADDRESS`: The email address that emails will be sent from.
   - `EMAIL_HOST`: The host address of the SMTP server.
   - `EMAIL_PORT`: The port of the SMTP server.

---

## IDE Linting and Formatting (Recommended)

These instructions include the steps needed to set up your local IDE so that you will get warnings if any changes are not up to the linting and formatting standards.
The pre-commit hooks will ensure that your code changes are up to these standards, but setting up the following in your IDE will help to catch any issues earlier.

**(Recommended before staging and committing files with git):** The entire suite of pre-commit hooks can be run manually by running the following commands from the root project directory:

On all files in the project, including any unstaged files:

```
pre-commit run -a
```

On all files that are staged with git:

```
pre-commit run
```

On individual files:

```
pre-commit run --files <filepath>
```

### Flake8

Flake8 is a Python wrapper that combines several linting tools into one. More details about Flake8 can be found on [the official Flake8 GitHub page](https://github.com/PyCQA/flake8).

The Flake8 pre-commit hook can be executed on all files with the following command:

```
pre-commit run flake8 -a
```

#### PyCharm Setup

The following steps will enable automatic Flake8 checks during editing. General PyCharm instructions can be found in the [File Watchers](https://www.jetbrains.com/help/pycharm/tutorial-file-watchers-in-product.html) and [Inspections](https://www.jetbrains.com/help/pycharm/inspections-settings.html) documentation.

1. Find the location of your Flake8 installation: `which flake8`
2. Install and enable the [File Watchers](https://plugins.jetbrains.com/plugin/7177-file-watchers) plugin in PyCharm if it isn't already.
3. Go to Settings -> Tools -> File Watchers and add a new custom file watcher with the following values:
   - File type: `Python`
   - Scope: `Project Files`
   - Program: The path to your Flake8 installation. You can set this to `$PyInterpreterDirectory$/flake8` if you are using a Python interpreter within a virtual environment.
   - Arguments: `$FileDir$/$FileName$`
   - Working directory: `$Projectpath$`
   - Check `Auto-save edited files to trigger the watcher` to run the checks any time a file is changed. If unchecked the linting will trigger on a `File -> Save All`.
   - Check `Trigger the watcher on external changes` to run the watcher on any changes made to the files outside of PyCharm.
   - Show console: `On error`
   - Output filters: `$FILE_PATH$:$LINE$:$COLUMN$:$MESSAGE$`
4. Go to Settings -> Editor -> Inspections, expand the `File Watchers` dropdown and ensure the box beside `File watcher problems` is checked.
   - Optionally, set the severity to a higher level such as `Warning` or `Error`.

#### VSCode Setup

The following steps will enable automatic Flake8 checks during editing. General VSCode linting instructions can be found in the [linting documentation](https://code.visualstudio.com/docs/python/linting).

1. Enable linting in VSCode:
   - Open the command palette `command-p on Mac or control-shift-p on Windows`
   - Select the `> Python: Select Linter` command and then select `flake8` to enable flake8 linting.
2. Install the flake8 linting extension if prompted by clicking the prompt that appears in the bottom right corner after step 1.
3. Set the linter to run on file save:
   - Open the command palette `command-p on Mac or control-shift-p on Windows`
   - Open the settings UI `> Preferences: Open settings (UI)`
   - Search for `lintOnSave` and check the box
   - (Optional): In the same settings UI search for `autoSave` and set it to `afterDelay` to automatically save files after a set delay (default is 1000ms).
4. Flake8 issues will now be highlighted in the code and displayed in the problems panel which can be opened with `shift-command-m on Mac or control-shift-m on Windows`

### Other Tools

The following tools are included in the pre-commit hooks and can be run individually if needed.

#### [Black](https://github.com/psf/black): A Python code formatter that will ensure a consistent style throughout the code base.

```
pre-commit run black -a
```

#### [pyupgrade](https://github.com/asottile/pyupgrade): A tool to automatically upgrade old Python syntax to newer versions.

```
pre-commit run pyupgrade -a
```

#### [isort](https://github.com/PyCQA/isort): A utility to automatically sort and organize Python imports.

```
pre-commit run trailing-whitespace -a
```

#### [Trailing Whitespace](https://github.com/pre-commit/pre-commit-hooks#trailing-whitespace): Trims trailing whitespace from the ends of lines.

```
pre-commit run trailing-whitespace -a
```

#### [end-of-file-fixer](https://github.com/pre-commit/pre-commit-hooks#end-of-file-fixer): Ensures files end with a newline character.

```
pre-commit run end-of-file-fixer -a
```

#### [check-yaml](https://github.com/pre-commit/pre-commit-hooks#check-yaml): Verifies YAML files for syntax correctness.

```
pre-commit run check-yaml -a
```

---

## Basic Commands

### Setting Up Your Users

- To create a **superuser account**, with the environment variables you may have set earlier, use this command:

  ```
  cd firstvoices
  python manage.py createsuperuser --noinput
  ```

  or if you want to supply the username and password manually:

  ```
  cd firstvoices
  python manage.py createsuperuser
  ```

- Normal users can be created using the admin panel, which can be accessed using the URL listed in the [Useful Local URLs on Startup](#useful-local-urls-on-startup) section. The admin panel can only be accessed when logged in as a superuser or staff user.

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

### Local Database Cleanup Script

For local development, a script has been created which will do the following:

- Drops any existing databases named `fv_be`
- Creates a fresh `fv_be` database
- Makes fresh migrations
- Runs the migrations (the migrations add the default fixtures)
- Creates a superuser using the following arguments:
  - `-u <username> or --username <username>` to specify the username
  - `-p <password> or --password <password>` to specify the password
  - `-e <email> or --email <email>` to specify an optional email (a default will be used, `admin@example.com`, if not supplied)
- If no arguments are supplied the script will create a superuser using the following environment variables if they are set (as specified in the [Developer Setup Section](#developer-setup)):
  - `DJANGO_SUPERUSER_USERNAME` to specify the username
  - `DJANGO_SUPERUSER_PASSWORD` to specify the password
  - `DJANGO_SUPERUSER_EMAIL` to specify an email
- If no environment variables are set and no arguments are found then the script will fail to create a superuser.

You may need to give the script executable permission on your machine by running the following command:

```
chmod +x firstvoices/reset-local-database.sh
```

An example command to run the script might look like the following:

```
./firstvoices/reset-local-database.sh -u admin -p admin -e admin@example.com
```

or if you have already set the environment variables locally:

```
./firstvoices/reset-local-database.sh
```

### Setting Up Custom Order/Confusable Cleaning for Dictionary Entries

To set up custom order/confusable cleaning locally, you will need to do the following:

- Load the `default_g2p_config.json` fixture if it isn't already (it should get loaded during migrations).
- Create `Character` models that correspond with the characters you will use in a site's alphabet.
  - Base characters are required, ignorables and variants are optional.
- Create an `Alphabet` class with an appropriate input to canonical mapping that defines confusables.
  - For example: `[{"in": "á", "out": "a"}, {"in": "ᐱ", "out": "A"}, {"in": "Á", "out": "A"}, {"in": "c̣", "out": "c"}, {"in": "C̣", "out": "C"}, {"in": "ȼh", "out": "ch"}, {"in": "Ȼh", "out": "Ch"}]`
  - Check [g2p documentation](https://github.com/roedoejet/g2p) for more detailed mapping options.

### Building Elasticsearch Index
To build/rebuild elasticsearch indices:
1. Make sure the elasticsearch server is running. The instructions can be found in this file
on how to start the server locally if required.
2. Also make sure a celery worker is running. The instructions can be found in this file under [Celery](#celery) section.
3. Run the following command from the `firstvoices/` folder:
`python manage.py rebuild_index`
4. A success message should be displayed if the process gets completed.
5. Optional arguments can be supplied using the `--index` flag which accepts name of indices as input.
Currently, the following indices are supported: `dictionary_entries, songs, stories, media, languages`


### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

- navigate to the `firstvoices` directory:

```
cd firstvoices
```

- Run the tests with coverage, generate an html results page, and open the results in a browser:

```
coverage run -m pytest
coverage html
open htmlcov/index.html
```

### Running tests with pytest

From the `firstvoices` project directory:

- Run all tests:

```
pytest
```

- Run a set of tests in a directory:

```
pytest <path to directory>
```

- Run a single file:

```
pytest <path to file>
```

- Run a single test:

```
pytest <path to file containing test> -k '<name of single test>'
```

- Run all tests marked with a marker:

```
pytest -m <marker>'
e.g. pytest -m integration (for running integration tests.)
```

- Reset the test database:

```
python manage.py reset_db -D test_fv_be
```

## Docker

The local docker-compose file sets up ancillary tools to support async task execution via celery, as well as a local
ElasticSearch instance for testing.

To run just `docker compose up`. The default values in `settings.py` will fall back to appropriate values.

If you prefer to run your own instances of `RabbitMQ`, `ElasticSearch`, or `Redis`, set the following environment vars (
docker-compatible defaults shown):

- `CELERY_BROKER_URL`=`"amqp://rabbitmq:rabbitmq@localhost:5672//fv"`
- `CELERY_RESULT_BACKEND`=`"redis://localhost/0"`
- `ELASTICSEARCH_HOST`=`"localhost"`
- `ELASTICSEARCH_PRIMARY_INDEX`=`"fv"`

## Celery

For async and periodic tasks to successfully execute, a worker process must be running. In another terminal, with the
virtual environment setup, execute `celery -A firstvoices worker -B` in the `./firstvoices` directory

## Management Commands
The following management commands are available to run from the `firstvoices` directory:
Note: use `python manage.py {command} -h` to list all the args and their use.
- `python manage.py copy_site` - Copies all content (except for widgets and pages) to a new site.
- `python manage.py rebuild_index` - Rebuilds the elasticsearch index.
- `python manage.py unicode_export` - Generates the csv files for the orthography-resources folder for the [unicode-resources repository.](https://github.com/First-Peoples-Cultural-Council/unicode-resources)

Management commands added for data cleanup purposes with niche use cases:
- `python manage.py convert_draftjs_to_html` - Converts all draftJS content to sanitized HTML for all models that have a draftJS field.
- `python manage.py convert_heic` - Converts existing HEIC files to JPEG or PNG format.
- `python manage.py merge_duplicate_speakers` - Merges duplicate speakers based on case-insensitive exact matches on the name, within the same site.


## Useful Local URLs On Startup

- Admin panel (login using a superuser account as explained in the [Setting Up Your Users](#setting-up-your-users) section): `localhost:8000/admin`
- Base API list: `localhost:8000/api/1.0/`
- API docs page: `localhost:8000/api/docs/`
- Sites Model API list view: `localhost:8000/api/1.0/sites` for example to get a list of sites models go to `localhost:8000/api/1.0/sites/`
- Sites Model API detail view: `localhost:8000/api/1.0/sites/<site-slug>/` for example to get a detail view for a test site that you have created go to `localhost:8000/api/1.0/sites/test-site/`
- Model API list view for a specific model type: `localhost:8000/api/1.0/sites/<site-slug>/<model type here>/` for example to get a list of dictionary models for a test site that you have created go to `localhost:8000/api/1.0/sites/test-site/dictionary/`
- Model API detail view for a specific model of a type: `localhost:8000/api/1.0/sites/<site-slug>/<model type here>/<id>/` for example to get a detail view for a dictionary entry under a test site you have created go to `localhost:8000/api/1.0/sites/test-site/dictionary/983dc8d7-0878-4b2f-8c74-f9e10ec2e6fc/`
