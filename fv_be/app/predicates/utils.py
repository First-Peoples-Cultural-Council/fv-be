def get_site_id(obj):
    """
    Returns the site id for the object, with handling for Site objects as well as site content models
    """
    return obj.id if obj.__class__.__name__ == "Site" else obj.site.id


def get_role(user, obj):
    """
    Returns an integer corresponding to a user's role on the site matching
    the given obj, or -1 if they are not a member of that site.
    """

    if user.is_anonymous:
        return -1

    membership = user.memberships.filter(site__id=get_site_id(obj))
    return membership[0].role if len(membership) > 0 else -1
