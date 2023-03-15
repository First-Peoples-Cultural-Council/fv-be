import uuid

from django.conf import settings
from django.db import models
from rules.contrib.models import RulesModel


class BaseModel(RulesModel):
    """
    Base model for all FirstVoices Backend models, with standard fields and support for rules-based permissions.

    Date fields values are generated automatically, but user fields (created_by and last_modified_by) are required when
    creating new data.

    Access rules can be configured using a declaration in the Meta class, like this example:
    class Meta:
        rules_permissions = {
            "add": rules.is_staff,
            "view": rules.is_authenticated,
        }
    See the django-rules docs [https://github.com/dfunckt/django-rules#permissions-in-models] for more details.
    """

    class Meta:
        abstract = True

    # from uid (and seemingly not uid:uid)
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_index=True
    )

    # from isTrashed
    is_trashed = models.BooleanField(default=False)

    # from dc:creator
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="created_%(app_label)s_%(class)s",
        db_index=True,
    )

    # from dc:created
    created = models.DateTimeField(auto_now_add=True)

    # from dc:modified
    last_modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="modified_%(app_label)s_%(class)s",
        db_index=True,
    )

    # from dc:lastContributor
    last_modified = models.DateTimeField(auto_now=True)
