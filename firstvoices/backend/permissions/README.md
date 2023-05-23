# FirstVoices Permissions

The FirstVoices Backend implements object-level permissions using programmatic rules,
rather than permission settings stored in the database. These rules are implemented
both as python rules that can be tested in python code (see predicates),
and as query filters that can be tested in the database when retrieving data
(see managers).

Both versions of each permission rule need to match; this is tested in test_permission_settings for all models.

## Predicates

The predicates allow checking permissions on a model instance at run time. See [Rules](https://github.com/dfunckt/django-rules) for full documentation.

## Managers

The PermissionsManager provides methods for querying the database for
objects a user has permission to view.
