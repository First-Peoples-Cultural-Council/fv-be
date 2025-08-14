import rules
from django.contrib.auth import get_user_model
from django.core.validators import validate_slug
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext as _
from django_better_admin_arrayfield.models.fields import ArrayField

from backend.permissions import predicates
from backend.permissions.managers import PermissionsManager

from . import Image
from .base import BaseModel, BaseSiteContentModel
from .constants import (
    DEFAULT_TITLE_LENGTH,
    EXTENDED_TITLE_LENGTH,
    MAX_EMAIL_LENGTH,
    Role,
    Visibility,
)
from .media import Video
from .utils import load_default_categories, load_default_widgets
from .widget import SiteWidgetList


class LanguageFamilyManager(PermissionsManager):
    """Manager allowing foreign key relationship to use natural key when loading fixtures"""

    use_in_migrations = True

    def get_by_natural_key(self, title):
        return self.get(title=title)


class SiteManager(PermissionsManager):
    def explorable(self):
        """Returns instances that are suitable for listing in a directory of Sites."""
        return (
            self.get_queryset()
            .filter(visibility__gte=Visibility.MEMBERS)
            .filter(is_hidden=False)
        )


class LanguageFamily(BaseModel):
    """
    Represents a Language Family.
    """

    objects = LanguageFamilyManager()

    class Meta:
        verbose_name = _("language family")
        verbose_name_plural = _("language families")
        rules_permissions = {
            "view": rules.always_allow,
            "add": predicates.is_superadmin,
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    title = models.CharField(max_length=DEFAULT_TITLE_LENGTH, unique=True)

    alternate_names = models.TextField(max_length=DEFAULT_TITLE_LENGTH, blank=True)

    def natural_key(self):
        return (self.title,)

    def __str__(self):
        return self.title


class Language(BaseModel):
    """
    Represents a Language.
    """

    class Meta:
        verbose_name = _("language")
        verbose_name_plural = _("languages")
        rules_permissions = {
            "view": rules.always_allow,
            "add": predicates.is_superadmin,
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    title = models.CharField(max_length=DEFAULT_TITLE_LENGTH, unique=True)

    alternate_names = models.CharField(max_length=DEFAULT_TITLE_LENGTH, blank=True)

    community_keywords = models.CharField(max_length=EXTENDED_TITLE_LENGTH, blank=True)

    language_family = models.ForeignKey(
        LanguageFamily, on_delete=models.PROTECT, related_name="languages"
    )

    # BCP 47 Spec: https://www.ietf.org/rfc/bcp/bcp47.txt
    language_code = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.title


class Site(BaseModel):
    """
    Represents Language Site and contains the basic public information about the site. For site information that should
    be access-controlled, see the SiteInformation model.
    """

    # from fvdialect type

    objects = SiteManager()

    class Meta:
        verbose_name = _("site")
        verbose_name_plural = _("sites")
        rules_permissions = {
            "view": predicates.can_view_site,
            "add": predicates.is_superadmin,
            "change": predicates.is_language_admin_or_super,
            "delete": predicates.is_superadmin,
        }

        constraints = [
            models.CheckConstraint(
                check=(Q(banner_image__isnull=True) | Q(banner_video__isnull=True)),
                name="site_only_one_banner",
            )
        ]

    # from dc:title
    title = models.CharField(max_length=DEFAULT_TITLE_LENGTH, unique=True)

    # from fvdialect:short_url
    slug = models.SlugField(
        max_length=DEFAULT_TITLE_LENGTH,
        blank=False,
        validators=[validate_slug],
        db_index=True,
        unique=True,
    )

    # from fvdialect:parent_language
    language = models.ForeignKey(
        Language, null=True, blank=True, on_delete=models.SET_NULL, related_name="sites"
    )

    # from state (will have to be translated from existing states to new visibilities)
    visibility = models.IntegerField(
        choices=Visibility.choices, default=Visibility.TEAM, db_index=True
    )

    # from fvdialect:contact_email
    contact_email_old = models.EmailField(null=True, blank=True)

    contact_emails = ArrayField(
        models.EmailField(max_length=MAX_EMAIL_LENGTH), blank=True, default=list
    )

    contact_users = models.ManyToManyField(get_user_model(), blank=True)

    homepage = models.OneToOneField(
        SiteWidgetList,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="homepage_site",
    )

    # from fvdialect:logo
    logo = models.OneToOneField(
        Image,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="site_logo_of",
    )

    # from fvdialect:background_top_image
    banner_image = models.OneToOneField(
        Image,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="site_banner_of",
    )

    # from fvdialect:background_top_video
    banner_video = models.OneToOneField(
        Video,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="site_banner_of",
    )

    is_hidden = models.BooleanField(default=False)

    @property
    def language_family(self):
        if self.language is not None:
            return self.language.language_family
        else:
            return None

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Check if saving a new model or updating an existing one.
        new_model = self._state.adding
        super().save(*args, **kwargs)

        if new_model:
            # Add default categories for all new sites.
            load_default_categories(self)
            # Add default no-settings widgets for new sites
            load_default_widgets(self)


class Membership(BaseSiteContentModel):
    """
    Represents a user's membership to a language site
    """

    # site from group name (userinfo:groups)

    # matched based on userinfo:email
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="memberships"
    )

    # from group name (userinfo:groups)
    role = models.IntegerField(choices=Role.choices, default=Role.MEMBER)

    class Meta:
        verbose_name = _("membership")
        verbose_name_plural = _("memberships")
        unique_together = ("site", "user")
        rules_permissions = {
            "view": predicates.can_view_user_info,
            "add": predicates.is_at_least_staff_admin,
            "change": predicates.is_at_least_language_admin,
            "delete": predicates.is_at_least_language_admin,
        }

    def __str__(self):
        return f"{self.user} ({self.site} {self.get_role_display()})"

    def __repr__(self):
        return str(self)


class SiteFeature(BaseSiteContentModel):
    """Represents a feature flag for a site"""

    # from fv-features:features json array

    key = models.SlugField(
        max_length=DEFAULT_TITLE_LENGTH,
        blank=False,
        validators=[validate_slug],
    )
    is_enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("site feature")
        verbose_name_plural = _("site features")
        unique_together = ("site", "key")
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.is_superadmin,
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

        indexes = [
            models.Index(fields=["key", "site"], name="sitefeature_key_idx"),
        ]

    def __str__(self):
        return f"{self.key}: {self.is_enabled} ({self.site})"


class SiteMenu(BaseModel):
    """
    Represents the configuration for a site menu.
    """

    json = models.JSONField()
    site = models.OneToOneField(Site, on_delete=models.CASCADE, related_name="menu")

    class Meta:
        verbose_name = _("site menu")
        verbose_name_plural = _("site menus")
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.is_superadmin,
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    def __str__(self):
        return f"Menu JSON for {self.site.title}"
