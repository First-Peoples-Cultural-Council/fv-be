import logging

from django.contrib import admin
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils.html import format_html
from django.utils.translation import gettext as _

from backend.models.media import Audio, Image, Video


class BaseAdmin(admin.ModelAdmin):
    readonly_fields = (
        "id",
        "created",
        "created_by",
        "last_modified_by",
        "last_modified",
    )
    fields = (
        "id",
        "created",
        "created_by",
        "last_modified_by",
        "last_modified",
    )
    list_display = (
        "id",
        "created_by",
        "created",
        "last_modified_by",
        "last_modified",
    )
    list_select_related = ["created_by", "last_modified_by"]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user

        obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        for f in formset.forms:
            if not f.instance.created:
                f.instance.created_by = request.user

            f.instance.last_modified_by = request.user

        super().save_formset(request, form, formset, change)


class BaseSiteContentAdmin(BaseAdmin):
    list_display = ("site",) + BaseAdmin.list_display
    list_select_related = BaseAdmin.list_select_related + ["site"]

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # prefetch the media models' site info (it is used for their display name)
        if db_field.name == "related_audio":
            kwargs["queryset"] = Audio.objects.select_related("site")
        if db_field.name == "related_images":
            kwargs["queryset"] = Image.objects.select_related("site")
        if db_field.name == "related_videos":
            kwargs["queryset"] = Video.objects.select_related("site")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class BaseControlledSiteContentAdmin(BaseSiteContentAdmin):
    list_display = ("visibility",) + BaseSiteContentAdmin.list_display


class BaseInlineAdmin(admin.TabularInline):
    logger = logging.getLogger(__name__)
    classes = ["collapse"]
    extra = 0
    readonly_fields = (
        "admin_link",
        "item_id",
        "id",
        "created",
        "created_by",
        "last_modified_by",
        "last_modified",
    )
    can_delete = False
    fields = (
        "admin_link",
        "id",
    )

    def item_id(self, instance):
        return instance.id

    item_id.short_description = _("Id")

    def admin_link(self, instance):
        try:
            url = reverse(
                f"admin:{instance._meta.app_label}_{instance._meta.model_name}_change",
                args=(instance.id,),
            )
            # see fw-4179, i18n for 'Edit' not working here for some reason
            return format_html('<a href="{}">{}: {}</a>', url, "Edit", str(instance))
        except NoReverseMatch as e:
            self.logger.warning(
                self,
                f"{instance._meta.app_label}_{instance._meta.model_name} model has no _change url configured",
                e,
            )
            return None

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user

        obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)


class BaseInlineSiteContentAdmin(BaseInlineAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("site")


class HiddenBaseAdmin(BaseAdmin):
    """
    This utility class controls if a model will be displayed on the admin index page. This does not restrict
    access to the view, add, change, or delete views.

    Ref: https://docs.djangoproject.com/en/4.1/ref/contrib/admin/#django.contrib.admin.ModelAdmin.has_add_permission
    """

    def has_module_permission(self, request):
        return {}
