from django.db import models

# FirstVoices
from .base import BaseModel


class Category(BaseModel):
    """Model for Categories."""

    # Fields
    title = models.CharField(max_length=200)
    description = models.TextField()
    # todo: Add a nesting check for maximum one level of nesting
    # i.e. Parent Categories can have children but those children cannot have more children
    parent = models.ForeignKey("self", blank=True, null=True, on_delete=models.PROTECT)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.title
