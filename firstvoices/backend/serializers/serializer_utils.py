def get_site_from_context(serializer):
    return serializer.context["view"].kwargs["site_slug"]
