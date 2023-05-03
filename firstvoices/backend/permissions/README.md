# FirstVoices Permissions

The FirstVoices Backend implements object-level permissions using programmatic rules,
rather than permission settings stored in the database. These rules are implemented
both as python rules that can be tested in python code (see predicates),
and as query filters that can be tested in the database when retrieving data
(see managers).

Both versions of each permission rule need to match; this is tested in test_permission_consistency.

## Predicates

@Todo: include info from https://firstvoices.atlassian.net/wiki/spaces/FIR/pages/238321669/Permissions+and+Role+Design+Implementation

## Managers

The ViewPermissionManager provides an interface for querying the database for
objects a user has permission to view for a specific site or for all sites.

Each subclass of the generic ViewPermissionManager implements a specific permission
rule
