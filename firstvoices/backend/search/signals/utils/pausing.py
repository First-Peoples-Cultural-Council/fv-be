from backend.models.sites import SiteFeature

INDEXING_PAUSED_FEATURE = "indexing_paused"


def pause_indexing(site):
    feature = SiteFeature.objects.get_or_create(site=site, key=INDEXING_PAUSED_FEATURE)
    feature.is_enabled = True
    feature.save()


def unpause_indexing(site):
    feature = SiteFeature.objects.get_or_create(site=site, key=INDEXING_PAUSED_FEATURE)
    feature.is_enabled = False
    feature.save()


def is_indexing_paused(site):
    if not site.sitefeature_set.filter(key=INDEXING_PAUSED_FEATURE).exists():
        return False
    return site.sitefeature_set.get(key=INDEXING_PAUSED_FEATURE).is_enabled
