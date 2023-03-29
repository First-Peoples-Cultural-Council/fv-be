import rules
from django.contrib.auth import get_user_model
from django.core.validators import validate_slug
from django.db import models
from django.utils.translation import gettext as _

from firstvoices.backend import predicates
from firstvoices.backend.models import BaseModel

from .constants import Role, Visibility


class LanguageFamily(BaseModel):
    """
    Represents a Language Family.
    """

    # from FVLanguageFamily type

    class Meta:
        verbose_name = _("language family")
        verbose_name_plural = _("language families")
        rules_permissions = {
            "view": rules.always_allow,
            "add": predicates.is_superadmin,
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    # from parent_languages.csv OR from fvdialect:language_family on one of the
    # linked sites (via one of the linked languages)
    title = models.CharField(max_length=200, unique=True)

    # from dc:title
    alternate_names = models.TextField(max_length=200, blank=True)

    def __str__(self):
        return self.title


class Language(BaseModel):
    """
    Represents a Language.
    """

    # from fvlanguage type

    class Meta:
        verbose_name = _("language")
        verbose_name_plural = _("languages")
        rules_permissions = {
            "view": rules.always_allow,
            "add": predicates.is_superadmin,
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    # from parent_languages.csv OR from fvdialect:parent_language on one of the linked sites
    title = models.CharField(max_length=200, unique=True)

    # from dc:title
    alternate_names = models.CharField(max_length=200, blank=True)

    # from fva:family
    language_family = models.ForeignKey(LanguageFamily, on_delete=models.PROTECT)

    # from fvdialect:bcp_47
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

    class Meta:
        verbose_name = _("site")
        verbose_name_plural = _("sites")
        rules_permissions = {
            "view": predicates.can_view_site_model,
            "add": predicates.is_superadmin,  # todo
            "change": predicates.is_superadmin,  # todo
            "delete": predicates.is_superadmin,  # todo
        }

    # from dc:title
    title = models.CharField(max_length=200, unique=True)

    # from fvdialect:short_url
    slug = models.SlugField(
        max_length=200,
        blank=False,
        validators=[validate_slug],
        db_index=True,
        unique=True,
    )

    # from fva:language
    language = models.ForeignKey(
        Language, null=True, blank=True, on_delete=models.SET_NULL
    )

    # from state (will have to be translated from existing states to new visibilities)
    visibility = models.IntegerField(
        choices=Visibility.choices, default=Visibility.TEAM, db_index=True
    )

    # from fvdialect:contact_email
    contact_email = models.EmailField(null=True, blank=True)

    # see fw-4130, add logo field when media is ready / from fvdialect:logo

    @property
    def language_family(self):
        if self.language is not None:
            return self.language.language_family
        else:
            return None

    def __str__(self):
        return self.title


class BaseSiteContentModel(BaseModel):
    """
    Base model for non-access-controlled site content data such as categories, that do not have their own
    visibility levels. Can also be used as a base for more specific types of site content base models.
    """

    class Meta:
        abstract = True

    site = models.ForeignKey(
        Site, on_delete=models.CASCADE, related_name="%(app_label)s_%(class)s"
    )


class BaseControlledSiteContentModel(BaseSiteContentModel):
    """
    Base model for access-controlled site content models such as words, phrases, songs, and stories, that have their own
    visibility level setting.
    """

    class Meta:
        abstract = True

    visibility = models.IntegerField(
        choices=Visibility.choices, default=Visibility.TEAM
    )


class Membership(BaseSiteContentModel):
    """Represents a user's membership to a language site"""

    # site from group memberships

    # from user
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="memberships"
    )

    # from group memberships
    role = models.IntegerField(choices=Role.choices, default=Role.MEMBER)

    class Meta:
        verbose_name = _("membership")
        verbose_name_plural = _("memberships")
        unique_together = ("site", "user")
        rules_permissions = {
            "view": predicates.can_view_membership_model,
            "add": predicates.is_superadmin,  # todo
            "change": predicates.is_superadmin,  # todo
            "delete": predicates.is_superadmin,  # todo
        }

    def __str__(self):
        return f"{self.user} ({self.site} {Role.labels[self.role]})"


class SiteFeature(BaseSiteContentModel):
    """Represents a feature flag for a site"""

    # from fv-features:features json array

    key = models.CharField(max_length=100)
    is_enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("site feature")
        verbose_name_plural = _("site features")
        unique_together = ("site", "key")
        rules_permissions = {
            "view": rules.always_allow,
            "add": predicates.is_superadmin,  # todo
            "change": predicates.is_superadmin,  # todo
            "delete": predicates.is_superadmin,  # todo
        }

    def __str__(self):
        return f"{self.key}: {self.is_enabled} ({self.site})"


class SiteMenu(BaseModel):
    """
    Represents the configuration for a site menu.
    """

    json = models.JSONField()
    site = models.OneToOneField(
        Site, on_delete=models.CASCADE, related_name="site_menu"
    )

    class Meta:
        verbose_name = _("site menu")
        verbose_name_plural = _("site menus")

    def __str__(self):
        return f"Menu JSON for {self.site.title}"
