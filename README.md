# FirstVoices Backend

Backend for the FirstVoices application

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

License: Apache Software License 2.0

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
1. (Optional) To load data from fixtures, use the following command and replace the fixture_name with fixtures available.
   1. `python manage.py loaddata fixture_name`
   2. Fixtures available:
      3.  `partsOfSpeech_initial.json`


## Settings

Moved to [settings](http://cookiecutter-django.readthedocs.io/en/latest/settings.html).

## Basic Commands

### Setting Up Your Users

-   To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

-   To create a **superuser account**, use this command:

        $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

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
