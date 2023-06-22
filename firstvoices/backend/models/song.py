from django.db import models

from backend.permissions import predicates
from .base import AudienceMixin, BaseControlledSiteContentModel
from .media import RelatedMediaMixin
from .mixins import AuthouredMixin, dynamic_translated_field_mixin_factory


class Song(
    AuthouredMixin,
    AudienceMixin,
    RelatedMediaMixin,
    dynamic_translated_field_mixin_factory("Song",
                                           "title",
                                           unique=False,
                                           blank=False,
                                           nullable=False
                                           ),
    dynamic_translated_field_mixin_factory("Song", "introduction"),
    dynamic_translated_field_mixin_factory("Song", "lyrics"),
    BaseControlledSiteContentModel,
):
    """
    Representing a song associated with a site, including unique title, lyrics, introduction, and media links

    Notes for data migration:
    authours from fvbook:author (which should be dereferenced)
    introduction from fvbook:introduction
    introduction_translanation from fvbook:introduction_literal_translation

    lyrics_translation from fvbook:lyrics_translation
    lyrics from fvbook:lyrics

    title from dc:title
    title_translation from fvbook:title_literal_translation

    cover_image should be a duplicate of the first entry in fv:related_pictures for migration, can vary after that
    """

    class Meta:
        unique_together = ("site", "title")
        rules_permissions = {
            "view": predicates.is_visible_object,
            "add": predicates.is_superadmin,
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    cover_image = models.OneToOneField(
        to="Image", on_delete=models.RESTRICT, related_name="+", null=True
    )

    def __str__(self):
        return self.title
