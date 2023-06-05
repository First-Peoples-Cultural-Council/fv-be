from django.http import Http404

from backend.models.sites import Site


def get_site_from_context(serializer):
    if "site" in serializer.context:
        return serializer.context["site"]
    elif "site_slug" in serializer.context:
        site = Site.objects.filter(slug=serializer.context["site_slug"])
        if len(site) == 0:
            return Http404
        return site.first()
