import rules


@rules.predicate
def is_site_published(user, site):
    return site.state == "published"


@rules.predicate
def is_site_enabled(user, site):
    return site.state == "enabled"


@rules.predicate
def is_site_disabled(user, site):
    return site.state == "disabled"


@rules.predicate
def is_site_new(user, site):
    return site.state == "new"


@rules.predicate
def is_site_republish(user, site):
    return site.state == "republish"


@rules.predicate
def is_object_site_published(user, object):
    return object.site.state == "published"
