from django.db import models

from backend.permissions import predicates

from .base import AudienceMixin, BaseControlledSiteContentModel
from .media import RelatedMediaMixin
from .mixins import AuthouredMixin, dynamic_translated_field_mixin_factory


class Song(
    AuthouredMixin,
    AudienceMixin,
    RelatedMediaMixin,
    dynamic_translated_field_mixin_factory(
        "title", unique=False, blank=False, nullable=False
    ),
    dynamic_translated_field_mixin_factory("introduction"),
    dynamic_translated_field_mixin_factory("lyrics"),
    BaseControlledSiteContentModel,
):
    """
    Representing a song associated with a site, including unique title, lyrics, introduction, and media links
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
        to="Image", on_delete=models.RESTRICT, related_name="+"
    )

    def __str__(self):
        return self.title
