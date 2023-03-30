from django.db import models
from django.utils.translation import gettext as _

# Character length values
MAX_CHARACTER_LENGTH = 10


class Visibility(models.IntegerChoices):
    TEAM = 0, _("Team")
    MEMBERS = 1, _("Members")
    PUBLIC = 2, _("Public")


class Role(models.IntegerChoices):
    MEMBER = 0, _("Member")
    ASSISTANT = 1, _("Assistant")
    EDITOR = 2, _("Editor")
    LANGUAGE_ADMIN = 3, _("Language Admin")
