def get_select_related_media_fields(media_field_name):
    """
    Args:
        media_field_name: the name of an Image or Video model field

    Returns:
        a list of field name strings including the provided media field and its associated file models

    """
    f = media_field_name
    return [f, f"{f}__original", f"{f}__thumbnail", f"{f}__small", f"{f}__medium"]
