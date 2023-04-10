from django.db import models

State = models.IntegerChoices("State", "PUBLISHED ENABLED NEW")
