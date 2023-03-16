from django.core.validators import validate_slug
from django.db import models

from fv_be.app.models import BaseModel
from fv_be.users.models import User

from .constants import Role, Visibility


class LanguageFamily(BaseModel):
    """
    Represents a Language Family.
    """

    # from FVLanguageFamily type

    class Meta:
        # todo: i18n
        verbose_name = "language family"
        verbose_name_plural = "language families"

    # from parent_languages.csv OR from fvdialect:language_family on one of the
    # linked sites (via one of the linked languages)
    title = models.CharField(max_length=200)

    # from dc:title
    alternate_names = models.TextField(max_length=200, blank=True)

    def __str__(self):
        return self.title


class Language(BaseModel):
    """
    Represents a Language.
    """

    # from fvlanguage type

    # from parent_languages.csv OR from fvdialect:parent_language on one of the linked sites
    title = models.CharField(max_length=200)

    # from dc:title
    alternate_names = models.TextField(max_length=200, blank=True)

    # from fva:family
    language_family = models.ForeignKey(
        LanguageFamily, null=True, on_delete=models.SET_NULL
    )

    # from fvdialect:bcp_47
    # BCP 47 Spec: https://www.ietf.org/rfc/bcp/bcp47.txt
    language_code = models.TextField(max_length=100)

    # from parent_languages.csv converted from RGB value to a hex number
    # todo: consider something like django-colorfield to get nice admin ui for this
    colour = models.IntegerField()

    def __str__(self):
        return self.title


class Site(BaseModel):
    """
    Represents Language Site and contains the basic public information about the site. For site information that should
    be access-controlled, see the SiteInformation model.
    """

    # from fvdialect type

    # from dc:title
    title = models.CharField(max_length=200)

    # from fvdialect:short_url
    slug = models.SlugField(
        max_length=200, blank=False, validators=[validate_slug], db_index=True
    )

    # from fva:language
    language = models.ForeignKey(Language, null=True, on_delete=models.SET_NULL)

    # from state (will have to be translated from existing states to new visibilities)
    visibility = models.IntegerField(
        choices=Visibility.choices, default=Visibility.TEAM, db_index=True
    )

    # todo: add logo field when media is ready / from fvdialect:logo
    # todo: contact_email vs link to a contact user /  from fvdialect:contact_email

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

    site = models.ForeignKey(Site, on_delete=models.CASCADE)


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

    # site_id from group memberships

    # from user
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # from group memberships
    role = models.IntegerField(choices=Role.choices, unique=True, default=Role.MEMBER)

    class Meta:
        unique_together = ("site", "user")

    def __str__(self):
        # todo: i18n
        return f"User [{self.user}] has role [{Role.labels[self.role]}] on site [{self.site}]"
