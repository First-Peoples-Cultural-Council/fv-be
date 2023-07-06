from django.core.validators import validate_slug
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext as _

from backend.models import Image
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
                name="SitePage_banner_image_or_video_only_one",
                check=(
                    Q(
                        Q(banner_image=None, banner_video=None)
                        | Q(Q(banner_image=None) & ~Q(banner_video=None))
                        | Q(~Q(banner_image=None) & Q(banner_video=None))
                    )
                ),
            )
        ]

    title = models.CharField(max_length=225)
    slug = models.SlugField(
        max_length=200,
        blank=False,
        validators=[validate_slug],
        db_index=True,
        unique=True,
    )
    subtitle = models.TextField(blank=True)
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
