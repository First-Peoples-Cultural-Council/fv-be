from django.core.validators import validate_slug
from django.db import models

from fv_be.app.models import BaseModel
from fv_be.users.models import User

from .constants import Role, Visibility


class LanguageFamily(BaseModel):
    """
    Represents a Language Family.
    """

    # from fvlanguage type

    class Meta:
        # todo: i18n
        verbose_name = "language family"
        verbose_name_plural = "language families"

    # from dc:title
    title = models.CharField(max_length=200)

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
    language_family = models.ForeignKey(LanguageFamily, on_delete=models.DO_NOTHING)

    # from state (will have to be translated from existing states to new visibilities)
    visibility = models.IntegerField(
        choices=Visibility.choices, default=Visibility.TEAM, db_index=True
    )

    # todo: add logo field when media is ready / from fvdialect:logo
    # todo: add banner field when media is ready / from fvdialect:background_top_image

    def __str__(self):
        return self.title


class BaseSiteContentModel(BaseModel):
    """
    Base model for non-access-controlled site content data such as categories, that do not have their own
    visibility levels. Can also be used as a base for more specific types of site content base models.
    """

    class Meta:
        abstract = True

    site = models.ForeignKey(Site, on_delete=models.CASCADE, db_index=True)


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


class SiteInformation(BaseSiteContentModel):
    """Contains the access-controlled information about a language site."""

    # details come from fvdialect document

    # fvdialect:contact_information
    contact_information = models.TextField(blank=True)

    # fvdialect:site_menu
    site_menu = models.JSONField()

    # fvdialect:greeting
    greeting = models.TextField(blank=True)

    # fvdialect:about_our_language
    about_our_language = models.TextField(blank=True)

    # fvdialect:about_us
    about_us = models.TextField(blank=True)

    # dc:description
    description = models.TextField(blank=True)

    # todo: discuss how to handle existing contributors which are stored as usernames / from dc:contributors
    # todo: add featured words when words are available / from fvdialect:featured_words
    # todo: add featured audio when media is available / from fvdialect:featured_audio
    # todo: add keyboards when available / from fvdialect:keyboards
    # todo: decide whether to import fvl:import_id (from the fvlegacy schema)
    # todo: as part of pages and widgets epic / from widgets:active

    def __str__(self):
        # todo: i18n
        return f"Site information for {self.site.title}"


class Membership(BaseSiteContentModel):
    """Represents a user's membership to a language site"""

    # todo: mappings from nuxeo
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    role = models.IntegerField(choices=Role.choices, unique=True, default=Role.MEMBER)

    class Meta:
        unique_together = ("site", "user")

    def __str__(self):
        # todo: i18n
        return f"User [{self.user}] has role [{Role.labels[self.role]}] on site [{self.site}]"
