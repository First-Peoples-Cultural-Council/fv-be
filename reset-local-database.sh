#!/bin/bash

# Using the input arguments, set the environment variables for a super-admin account username, password, and optional email.
# Arguments are as follows:
# -u <username> or --username <username>
# -p <password> or --password <password>
# -e <email> or --email <email>
while test $# -gt 0; do
  case "$1" in
    -u|--username)
      shift
      if [[ $1 != -* ]] && [[ -n $1 ]] && test $# -gt 0; then
        printf 'Found username argument.\n'
        export DJANGO_SUPERUSER_USERNAME=$1
        shift
      else
        printf 'No username specified after [-u|--username] flag.\n'
        exit 1
      fi
      ;;
    -p|--password)
      shift
      if [[ $1 != -* ]] && [[ -n $1 ]] && test $# -gt 0; then
        printf 'Found password argument.\n'
        export DJANGO_SUPERUSER_PASSWORD=$1
        shift
      else
        printf 'No password specified after [-p|--password] flag.\n'
        exit 1
      fi
      ;;
    -e|--email)
      shift
      if [[ $1 != -* ]] && [[ -n $1 ]] && test $# -gt 0; then
        printf 'Found email argument.\n'
        export DJANGO_SUPERUSER_EMAIL=$1
        shift
      else
        printf 'No email specified after [-e|--email] flag.\n'
        exit 1
      fi
      ;;
    *)
      break
      ;;
  esac
done

# If the username environment variable has not been set using the arguments then check for an environment variable.
if [[ -z "${DJANGO_SUPERUSER_USERNAME}" ]]; then
  printf 'Please set your DJANGO_SUPERUSER_USERNAME environment variable or supply one with the [-u <username>] argument and rerun this script.\n'
  exit 1
fi

# If the password environment variable has not been set using the arguments then check for an environment variable.
if [[ -z "${DJANGO_SUPERUSER_PASSWORD}" ]]; then
  printf 'Please set your DJANGO_SUPERUSER_PASSWORD environment variable or supply one with the [-p <password>] argument and rerun this script.\n'
  exit 1
fi

# If the email environment variable has not been set using the arguments then check for an environment variable or default to a set email address.
if [[ -z "${DJANGO_SUPERUSER_EMAIL}" ]]; then
  printf 'No DJANGO_SUPERUSER_EMAIL environment variable or [-e <email>] argument found. Using the default "admin@example.com".\n'
  export DJANGO_SUPERUSER_EMAIL=admin@example.com
fi

# Prompt user to confirm reset.
read -p $'Are you sure you want to wipe your local fv_be database? [Y/N] ' yn
case $yn in
  [Yy]* )
    # Drop the existing database
    printf '\n'
    printf 'Removing existing fv_be database.'
    dropdb -f fv_be

    # Create the empty database
    printf '\n\n'
    printf 'Recreating empty fv_be database.'
    createdb fv_be

    # Delete any existing migrations files
    printf '\n\n'
    printf 'Removing existing migrations.'
    find ./fv_be/*/migrations -type f -not -name '__init__.py' -delete

    # Make new migrations
    printf '\n\n'
    printf 'Generating migrations.\n'
    python manage.py makemigrations

    # Run the new migrations
    printf '\n\n'
    printf 'Running migrations.\n'
    python manage.py migrate

    # Create a superuser using the DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_PASSWORD, and DJANGO_SUPERUSER_EMAIL environment variables.
    printf '\n\n'
    printf 'Creating a superuser account using the DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_PASSWORD, and DJANGO_SUPERUSER_EMAIL environment variables.\n'
    python manage.py createsuperuser --noinput;;

  [Nn]* )
    printf '\n'
    printf 'Cancelled. No changes made.\n';;
  * )
    printf '\n'
    printf 'Please enter yes or no.\n';;
esac
