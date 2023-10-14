from django.db import models
from django.utils.translation import gettext as _

# Default length values
DEFAULT_TITLE_LENGTH = 225
MAX_CHARACTER_LENGTH = 10
MAX_CHARACTER_APPROXIMATE_FORM_LENGTH = 20
CATEGORY_POS_MAX_TITLE_LENGTH = 75  # Title length for parts of speech and categories
MAX_FILEFIELD_LENGTH = 500
MAX_NOTE_LENGTH = 500
MAX_EMAIL_LENGTH = 254

# constants for the default widgets, subset of the complete list of widgets
WIDGET_ALPHABET = "WIDGET_ALPHABET"
WIDGET_STATS = "WIDGET_STATS"
WIDGET_WOTD = "WIDGET_WOTD"
WIDGET_TEXT = "WIDGET_TEXT"


class Visibility(models.IntegerChoices):
    # enum intentionally has gaps to allow future changes to keep sequential order
    TEAM = 0, _("Team")
    MEMBERS = 10, _("Members")
    PUBLIC = 20, _("Public")


class Role(models.IntegerChoices):
    # enum intentionally has gaps to allow future changes to keep sequential order
    MEMBER = 0, _("Member")
    ASSISTANT = 10, _("Assistant")
    EDITOR = 20, _("Editor")
    LANGUAGE_ADMIN = 30, _("Language Admin")


class AppRole(models.IntegerChoices):
    # enum intentionally has gaps to allow future changes to keep sequential order
    STAFF = 0, _("Staff")
    SUPERADMIN = 10, _("Superadmin")
