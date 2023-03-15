from django.db import models

# todo: i18n for admin site
Visibility = models.IntegerChoices("Visibility", "TEAM MEMBERS PUBLIC")

Role = models.IntegerChoices("Role", "MEMBER ASSISTANT EDITOR LANGUAGE_ADMIN")
