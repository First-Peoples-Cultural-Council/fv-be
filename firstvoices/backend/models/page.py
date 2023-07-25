from django.core.validators import validate_slug
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext as _

from backend.models import Image, constants, validators
from backend.models.base import BaseControlledSiteContentModel
from backend.models.media import Video
from backend.models.widget import SiteWidgetList
from backend.permissions import predicates


class SitePage(BaseControlledSiteContentModel):
    class Meta:
        verbose_name = _("site page")
        verbose_name_plural = _("site pages")
        rules_permissions = {
            "view": predicates.is_visible_object,
            "add": predicates.is_superadmin,  # permissions will change when we add a write API
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }
        constraints = [
            # Constraint to ensure a SitePage has either a banner image or video or none but not both.
            models.CheckConstraint(
                check=(Q(banner_image__isnull=True) | Q(banner_video__isnull=True)),
                name="sitepage_only_one_banner",
            )
        ]
        # Ensures a page slug is unique across a single site
        unique_together = ["site", "slug"]

    title = models.CharField(max_length=constants.DEFAULT_TITLE_LENGTH)
    slug = models.SlugField(
        max_length=200,
        blank=False,
        validators=[validate_slug, validators.reserved_site_page_slug_validator],
        db_index=True,
        unique=False,
    )
    subtitle = models.CharField(blank=True, max_length=constants.DEFAULT_TITLE_LENGTH)
    widgets = models.ForeignKey(
        SiteWidgetList, on_delete=models.CASCADE, related_name="sitepage_set"
    )
    banner_image = models.ForeignKey(
        Image,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sitepage_set",
    )
    banner_video = models.ForeignKey(
        Video,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sitepage_set",
    )

    def __str__(self):
        return self.title
