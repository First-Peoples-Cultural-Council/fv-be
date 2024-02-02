from django.db.models import Prefetch
from django.db.models.functions import Upper
from rest_framework import serializers

from backend.models import Language
from backend.models.sites import Site, SiteFeature
from backend.serializers.site_serializers import SiteSummarySerializer
from backend.views.utils import get_select_related_media_fields


class LanguageSerializer(serializers.Serializer):
    """
    Serializes basic details about a Language, including a list of visible (Public or Members) Sites for that Language.
    """

    id = serializers.UUIDField(read_only=True)
    language = serializers.CharField(source="title", read_only=True)
    language_code = serializers.CharField(read_only=True)
    sites = SiteSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Language
        fields = ("id", "language", "language_code", "sites")

    @classmethod
    def make_queryset_eager(cls, queryset, visible_sites):
        """Add prefetching as required by this serializer"""
        return queryset.order_by(Upper("title")).prefetch_related(
            Prefetch(
                "sites",
                queryset=visible_sites.order_by(Upper("title")).select_related(
                    *get_select_related_media_fields("logo")
                ),
            ),
            Prefetch(
                "sites__sitefeature_set",
                queryset=SiteFeature.objects.filter(is_enabled=True),
            ),
        )


class LanguagePlaceholderSerializer(serializers.Serializer):
    """
    Serializes a single site that doesn't have a language.
    """

    class Meta:
        model = Site

    def to_representation(self, instance):
        return {
            "language": "",
            "languageCode": "",
            "no_language_assigned": True,
            "id": f"{str(instance.id)}-placeholder",
            "sites": [SiteSummarySerializer(instance, context=self.context).data],
        }

    @classmethod
    def make_queryset_eager(cls, queryset):
        """Add prefetching as required by this serializer"""
        return (
            queryset.order_by(Upper("title"))
            .select_related(*get_select_related_media_fields("logo"))
            .prefetch_related(
                Prefetch(
                    "sitefeature_set",
                    queryset=SiteFeature.objects.filter(is_enabled=True),
                ),
            )
        )
