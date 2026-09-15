from django.db import models
from django.utils.translation import gettext as _

from backend.models.base import BaseSiteContentModel
from backend.models.constants import DEFAULT_TITLE_LENGTH
from backend.permissions import predicates


class Organization(BaseSiteContentModel):
    """
    Model for site contact us information
    """

    name = models.CharField(max_length=DEFAULT_TITLE_LENGTH, null=False, blank=False)
    order = models.PositiveIntegerField(default=0, null=False, blank=False)

    # JSON to store "label" : "email"
    emails = models.JSONField(default=list, blank=True, null=False)
    # JSON to store "label" : "number"
    phone_numbers = models.JSONField(default=list, blank=True, null=False)
    address = models.TextField(default="", null=False, blank=True)
    contact_message = models.TextField(
        default="Please contact us if you have any suggestions or feedback regarding our language content.",
        null=False,
        blank=True,
    )
    # JSON to store "label" : "url"
    url_list = models.JSONField(default=list, blank=True, null=False)

    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.is_language_admin_or_super,
            "change": predicates.is_language_admin_or_super,
            "delete": predicates.is_language_admin_or_super,
        }

    def __str__(self):
        return self.name
