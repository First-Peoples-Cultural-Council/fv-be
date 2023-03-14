import uuid

# this will be replaced by our custom User class when we create the site models
from django.contrib.auth.models import User
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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_trashed = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, default=None
    )
    created_by_date = models.DateTimeField(auto_now_add=True)
    last_modified_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, default=None
    )
    last_modified_date = models.DateTimeField(auto_now=True)

    @property
    def created_by(self):
        return self.created_by.get_full_name()

    @property
    def last_modified_by(self):
        return self.last_modified_by.get_full_name()
