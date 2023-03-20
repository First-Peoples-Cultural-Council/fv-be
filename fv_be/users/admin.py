from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from fv_be.app.admin.sites_admin import BaseInlineAdmin, MembershipAdmin
from fv_be.app.models.sites import Membership
from fv_be.users.forms import UserAdminChangeForm, UserAdminCreationForm

User = get_user_model()


class MembershipInline(BaseInlineAdmin):
    fk_name = "user"
    model = Membership
    fields = ("role", "site", "site_link") + BaseInlineAdmin.fields
    readonly_fields = (
        ("site_link",)
        + BaseInlineAdmin.readonly_fields
        + MembershipAdmin.readonly_fields
    )

    def site_link(self, instance):
        url = reverse(
            "admin:app_site_change",
            args=(instance.site.id,),
        )
        # todo: i18n for 'Edit site' not working here for some reason
        return format_html(
            '<a href="{}">{}: {}</a>', url, "Edit site", str(instance.site)
        )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user

        obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("display_name", "full_name", "year_born")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"fields": ("email", "password1", "password2")}),
        (_("Personal info"), {"fields": ("display_name", "full_name", "year_born")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = [
        "email",
        "display_name",
        "full_name",
        "year_born",
        "is_superuser",
        "id",
    ]
    search_fields = ["email", "display_name", "full_name", "id"]
    readonly_fields = [
        "last_login",
        "date_joined",
    ]
    inlines = [MembershipInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user

        obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        for form in formset.forms:
            if not form.instance.created:
                form.instance.created_by = request.user

            form.instance.last_modified_by = request.user

        super().save_formset(request, form, formset, change)
