from django.core.validators import MinLengthValidator
from django.db import models
from django.utils.translation import gettext as _
from django_better_admin_arrayfield.models.fields import ArrayField

from backend.models.base import BaseSiteContentModel
from backend.models.constants import (
    DEFAULT_TITLE_LENGTH,
    EXTENDED_TITLE_LENGTH,
    MAX_EMAIL_LENGTH,
)
from backend.permissions import predicates


class OrganizationStatus(models.TextChoices):
    ACTIVE = "active", _("Active")
    INACTIVE = "inactive", _("Inactive")


class ContactInfo(BaseSiteContentModel):
    """
    Model for site contact us information
    """

    organization_name = models.CharField(
        max_length=DEFAULT_TITLE_LENGTH, null=False, blank=False
    )
    organization_status = models.CharField(
        max_length=8,
        choices=OrganizationStatus.choices,
        default=OrganizationStatus.ACTIVE,
        blank=False,
        null=False,
    )
    has_contact_information = models.BooleanField(default=True, null=False, blank=False)
    order = models.PositiveIntegerField(default=0, null=False, blank=False)

    # Active sites with contact information
    emails = ArrayField(
        models.EmailField(max_length=MAX_EMAIL_LENGTH),
        default=list,
        blank=False,
        null=False,
        validators=[MinLengthValidator(1)],
    )
    # JSON to store "label" : "number"
    phone_numbers = models.JSONField(default=list, blank=True, null=False)
    address = models.TextField(default="", null=False, blank=True)
    contact_message = models.TextField(default="", null=False, blank=True)
    # JSON to store "label" : "url"
    url_list = models.JSONField(default=list, blank=True, null=False)

    # historical site ownership data
    is_active_site_owner = models.BooleanField(default=True, null=False, blank=False)
    ownership_start_date = models.DateField(null=True, blank=True)
    ownership_end_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = _("Contact Us")
        verbose_name_plural = _("Contact Us")
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.is_language_admin_or_super,
            "change": predicates.is_language_admin_or_super,
            "delete": predicates.is_language_admin_or_super,
        }

    def __str__(self):
        return self.organization_name

    def save(self, *args, **kwargs):
        # set defaults for organizations without contact information
        if not self.has_contact_information:
            self.emails = ["ltp@fpcc.ca"]
            self.url_list = ["https://www.firstvoices.com/support"]
            self.contact_message = (
                "Please contact the FirstVoices team if you have any suggestions or "
                "feedback regarding our language content."
            )

        # set defaults for inactive organizations
        if not self.organization_status == OrganizationStatus.ACTIVE:
            self.emails = ["ltp@fpcc.ca"]
            self.url_list = ["https://www.firstvoices.com/support"]
            self.contact_message = (
                f"The project for the {self.site.title} language is currently inactive. "
                f"If this is your language or community and you are interested in working on this "
                f"project, please contact ltp@fpcc.ca for more information."
            )

        return super().save(*args, **kwargs)


class TeamMember(BaseSiteContentModel):
    class Meta:
        verbose_name = _("Team Member")
        verbose_name_plural = _("Team Members")
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.is_language_admin_or_super,
            "change": predicates.is_language_admin_or_super,
            "delete": predicates.is_language_admin_or_super,
        }

    # From Person model, no need to inherit as the Person model is used for entirely separate functions
    name = models.CharField(max_length=DEFAULT_TITLE_LENGTH, null=False, blank=False)
    bio = models.TextField(
        max_length=EXTENDED_TITLE_LENGTH, default="", null=False, blank=True
    )

    position = models.CharField(
        max_length=DEFAULT_TITLE_LENGTH, default="", blank=True, null=False
    )
    email = models.EmailField(
        max_length=MAX_EMAIL_LENGTH, default="", blank=True, null=False
    )
    # JSON to store "label" : "number"
    phone_numbers = models.JSONField(default=list, blank=True, null=False)
    organization_info = models.ForeignKey(
        ContactInfo, on_delete=models.CASCADE, related_name="team_members"
    )

    def __str__(self):
        return f"{self.name} ({self.site} - {self.organization_info.organization_name})"
