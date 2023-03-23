from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext as _
from django.urls.exceptions import NoReverseMatch


class BaseAdmin(admin.ModelAdmin):
    readonly_fields = (
        "id",
        "created",
        "created_by",
        "last_modified_by",
        "last_modified",
    )
    list_display = (
        "id",
        "is_trashed",
        "created_by",
        "created",
        "last_modified_by",
        "last_modified",
    )

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


class BaseSiteContentAdmin(BaseAdmin):
    list_display = ("site",) + BaseAdmin.list_display


class BaseControlledSiteContentAdmin(BaseSiteContentAdmin):
    list_display = ("visibility",) + BaseSiteContentAdmin.list_display


class BaseInlineAdmin(admin.TabularInline):
    classes = ["collapse"]
    extra = 0
    readonly_fields = (
        "admin_link",
        "item_id",
    )
    can_delete = False
    fields = (
        "admin_link",
        "id",
        "created",
        "created_by",
        "last_modified",
        "last_modified_by",
        "is_trashed",
    )

    def item_id(self, instance):
        return instance.id

    item_id.short_description = _("Id")

    def admin_link(self, instance):
        # todo: Add reverse links for all models
        try:
            url = reverse(
                f"admin:{instance._meta.app_label}_{instance._meta.model_name}_change",
                args=(instance.id,),
            )
            # todo: i18n for 'Edit' not working here for some reason
            return format_html('<a href="{}">{}: {}</a>', url, "Edit", str(instance))
        except NoReverseMatch as e:
            return None

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user

        obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)


# todo: better name for following class
class AdminHideUtility(BaseAdmin):
    """
    This utility class lets the admin classes to be registered on the top level of admin interface, to get the reverse
    links working for inline admin classes and also prevents the classes that inherit this to be shown at the top level.
    """
    def get_model_perms(self, request):
        return {}
