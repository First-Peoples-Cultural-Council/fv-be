from django.contrib.auth import get_user_model
from import_export import fields, widgets

from backend.models.app import AppMembership
from backend.models.constants import AppRole
from backend.resources.base import BaseResource
from backend.resources.utils.import_export_widgets import ChoicesWidget


class AppMembershipResource(BaseResource):
    role = fields.Field(
        column_name="role",
        widget=ChoicesWidget(AppRole.choices),
        attribute="role",
    )
    user = fields.Field(
        column_name="user",
        attribute="user",
        widget=widgets.ForeignKeyWidget(get_user_model(), field="email"),
    )

    class Meta:
        model = AppMembership

    def skip_row(self, instance, original, row, import_validation_errors=None):
        """Don't create/overwrite app-level roles for users that already have one."""
        user_has_role = AppMembership.objects.filter(user=instance.user).exists()
        if user_has_role:
            return True
        return super().skip_row(instance, original, row, import_validation_errors)
