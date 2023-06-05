def get_site_from_context(serializer):
    if "site" in serializer.context:
        return serializer.context["site"]
    else:
        return None
