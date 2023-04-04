# FirstVoices Backend

Backend for the FirstVoices application

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

License: Apache Software License 2.0

---

## Developer setup

1. Clone the repo: https://github.com/First-Peoples-Cultural-Council/fv-be
1. Install prereqs:
   2. Python 3.10+
   3. PostgreSQL
1. Activate the virtual environment in the root of the project
   2. `source venv/bin/activate`
1. Install requirements
   2. `pip install -r requirements/local.txt`
3. Install pre-commit hooks
   4. `pre-commit install`
1. Create a database in postgres, and note the name
   2. `createdb --username=postgres <db name>`
1. Configure environment settings. Required settings are:
   2. DB_DATABASE
   3. DB_USERNAME
   4. DB_PASSWORD
   5. DB_HOST
   6. DB_PORT
1. Apply migration
   2. `python manage.py migrate`
1. Run the server and set it to automatically refresh on changes
   2. `npm install`
   3. `npm run dev`
1. (Optional) To load data from fixtures, use the following command (from inside the src directory) and replace the fixture_name with fixtures available.
   1. `python manage.py loaddata fixture_name`
   2. Fixtures available:
      3.  `partsOfSpeech_initial.json`


---

## IDE Linting and Formatting (Optional)
These instruction include the steps needed to setup your local IDE so that you will get warnings if any changes are not up to the linting and formatting standards.
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
Flake8 is a Python wrapper which combines several linting tools into one. More details about Flake8 can be found on [the official Flake8 GitHub page](https://github.com/PyCQA/flake8).

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

## Settings

Moved to [settings](http://cookiecutter-django.readthedocs.io/en/latest/settings.html).

## Basic Commands

### Setting Up Your Users

-   To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

-   To create a **superuser account**, use this command:

        $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

### Local Database Cleanup Script
For local development, a script has been created which will do the following:
- Drops any existing databases named `fv_be`
- Creates a fresh `fv_be` database
- Deletes any migrations in the fv_be/*/migrations folders
- Makes fresh migrations
- Runs the migrations
- Creates a superuser using the following arguments:
  - `-u <username> or --username <username>` to specify the username
  - `-p <password> or --password <password>` to specify the password
  - `-e <email> or --email <email>` to specify an optional email (a default will be used if not supplied)
- If no arguments are supplied the script will create a superuser using the following environment variables if they are set:
  - `DJANGO_SUPERUSER_USERNAME` to specify the username
  - `DJANGO_SUPERUSER_PASSWORD` to specify the password
  - `DJANGO_SUPERUSER_EMAIL` to specify an optional email
- If no environment variables are set and no arguments are found then the script will fail to create a superuser.

You may need to give the script executable permission for your machine by running the following command:
```
chmod +x src/reset-local-database.sh
```
An example command to run the script might look like the following:
```
./src/reset-local-database.sh -u admin -p admin -e admin@example.com
```
or if you have already set the environment variables locally:
```
./src/reset-local-database.sh
```

### Type checks

Running type checks with mypy:

    $ mypy firstvoices

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

#### Running tests with pytest

    $ pytest

### Live reloading and Sass CSS compilation

Moved to [Live reloading and SASS compilation](https://cookiecutter-django.readthedocs.io/en/latest/developing-locally.html#sass-compilation-live-reloading).

## Deployment

The following details how to deploy this application.

### Custom Bootstrap Compilation

The generated CSS is set up with automatic Bootstrap recompilation with variables of your choice.
Bootstrap v5 is installed using npm and customised by tweaking your variables in `static/sass/custom_bootstrap_vars`.

You can find a list of available variables [in the bootstrap source](https://github.com/twbs/bootstrap/blob/v5.1.3/scss/_variables.scss), or get explanations on them in the [Bootstrap docs](https://getbootstrap.com/docs/5.1/customize/sass/).

Bootstrap's javascript as well as its dependencies are concatenated into a single file: `static/js/vendors.js`.
