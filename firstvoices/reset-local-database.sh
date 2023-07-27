#!/bin/bash

# Get the path to this script
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Using the input arguments, set the environment variables for a super-admin account username, password, and optional email.
# Arguments are as follows:
# -p <password> or --password <password>
# -e <email> or --email <email>
while test $# -gt 0; do
  case "$1" in
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
    printf 'Removing existing fv_be database.\n'
    dropdb -f fv_be --if-exists
    retval=$?
    if [ $retval -ne 0 ]; then
      printf "Database removal failed: exit code $retval\n"
      exit $retval
    fi

    # Create the empty database
    printf '\n\n'
    printf 'Recreating empty fv_be database.\n'
    createdb --username=postgres fv_be
    retval=$?
    if [ $retval -ne 0 ]; then
      printf "Database creation failed: exit code $retval\n"
      exit $retval
    fi

    # Make new backend migrations
    printf '\n\n'
    printf 'Generating backend migrations.\n'
    python $SCRIPT_DIR/manage.py makemigrations backend
    retval=$?
    if [ $retval -ne 0 ]; then
      printf "Backend migration generation failed: exit code $retval\n"
      exit $retval
    fi

    # Run the new migrations
    printf '\n\n'
    printf 'Running migrations.\n'
    python $SCRIPT_DIR/manage.py migrate
    retval=$?
    if [ $retval -ne 0 ]; then
      printf "Migration execution failed: exit code $retval\n"
      exit $retval
    fi

    # Create a superuser using the DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_PASSWORD, and DJANGO_SUPERUSER_EMAIL environment variables.
    printf '\n\n'
    printf 'Creating a superuser account using the DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_PASSWORD, and DJANGO_SUPERUSER_EMAIL environment variables.\n'
    python $SCRIPT_DIR/manage.py createsuperuser --noinput
    retval=$?
    if [ $retval -ne 0 ]; then
      printf "Superuser creation failed: exit code $retval\n"
      exit $retval
    fi

    # Create an app level superuser membership model for the admin user.
    printf '\n\n'
    printf 'Adding app Superadmin membership to superuser account.\n'
    python $SCRIPT_DIR/manage.py shell < $SCRIPT_DIR/scripts/create_local_superadmin_membership.py
    retval=$?
    if [ $retval -ne 0 ]; then
      printf "Superuser membership creation failed: exit code $retval\n"
      exit $retval
    fi

    # Reset the test database
    printf '\n'
    printf 'Flushing test database.\n'
    dropdb test_fv_be --if-exists
    retval=$?
    if [ $retval -ne 0 ]; then
      printf "Test database cleanup failed: exit code $retval\n"
      exit $retval
    fi

    # Check if Elasticsearch is running
    ELASTICSEARCH_HOST="localhost"
    ELASTICSEARCH_PORT="9200"
    response=$(curl -s -o /dev/null -w "%{http_code}" http://${ELASTICSEARCH_HOST}:${ELASTICSEARCH_PORT}/_cluster/health)
    if [ "$response" -eq 200 ]; then
      # Rebuild Elasticsearch index
      printf '\n'
      printf 'Rebuilding Elasticsearch index.\n'
      python $SCRIPT_DIR/manage.py rebuild_index
      retval=$?
      if [ $retval -ne 0 ]; then
        printf "Elasticsearch index rebuild failed: exit code $retval\n"
        exit $retval
      fi
    else
      printf '\n'
      printf 'Elasticsearch is not running. Skipping index rebuild.\n'
    fi

    printf '\n'
    printf 'Local reset completed successfully.\n'
    ;;

  [Nn]* )
    printf '\n'
    printf 'Cancelled. No changes made.\n';;
  * )
    printf '\n'
    printf 'Please enter yes or no.\n';;
esac
