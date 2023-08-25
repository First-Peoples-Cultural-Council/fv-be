def get_select_related_media_fields(media_field_name):
    """
    Args:
        media_field_name: the name of an Image or Video model field. To get the fields for an Image or Video model,
            set media_field_name as None

    Returns:
        a list of field name strings including the provided media field and its associated file models

    """
    f = f"{media_field_name}__" if media_field_name else ""
    fields = [f"{f}original", f"{f}thumbnail", f"{f}small", f"{f}medium"]
    if media_field_name:
        fields = fields + [media_field_name]

    return fields
