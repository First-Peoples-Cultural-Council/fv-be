from rules import predicate


@predicate
def is_site_published(user, site):
    return site.state == "published"


@predicate
def is_site_enabled(user, site):
    return site.state == "enabled"


@predicate
def is_site_disabled(user, site):
    return site.state == "disabled"


@predicate
def is_site_new(user, site):
    return site.state == "new"


@predicate
def is_site_republish(user, site):
    return site.state == "republish"


@predicate
def is_object_site_published(user, object):
    return object.site.state == "published"


# for use in controlling read access for models
@predicate
def is_visible_object(user, object):
    return True


@predicate
def is_visible_site(user, object):
    return True


# for use in controlling create/update/delete access for models
@predicate
def is_at_least_member(user, object):
    return True


@predicate
def is_at_least_recorder(user, object):
    return True


@predicate
def is_at_least_editor(user, object):
    return True


@predicate
def is_at_least_language_admin(user, object):
    return True


@predicate
def is_at_least_staff_admin(user, object):
    return True


@predicate
def is_superadmin(user, object):
    return True
