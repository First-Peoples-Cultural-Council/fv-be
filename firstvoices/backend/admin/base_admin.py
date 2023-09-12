import logging

from django.contrib import admin
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils.html import format_html
from django.utils.translation import gettext as _

from backend.models.media import Audio, Image, Video
from backend.models.sites import Site


class SiteListFilter(admin.SimpleListFilter):
    # Allow any model to be filtered by language site
    title = "site"
    parameter_name = "site"

    def lookups(self, request, model_admin):
        list_of_sites = [(site.id, site.title) for site in Site.objects.all()]
        return sorted(list_of_sites, key=lambda tp: tp[1].lower())

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(site__id=self.value())
        return queryset


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
    list_filter = (SiteListFilter,)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # prefetch the media models' site info (it is used for their display name)
        if db_field.name == "related_audio":
            kwargs["queryset"] = Audio.objects.filter(
                site=self.get_site_from_object(request)
            ).select_related("site")
        if db_field.name == "related_images":
            kwargs["queryset"] = Image.objects.filter(
                site=self.get_site_from_object(request)
            ).select_related("site")
        if db_field.name == "related_videos":
            kwargs["queryset"] = Video.objects.filter(
                site=self.get_site_from_object(request)
            ).select_related("site")
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_site_from_object(self, request):
        if not hasattr(self, "parent_site"):
            self.parent_site = None
            object_id = request.resolver_match.kwargs.get("object_id")
            instance = self.get_object(request, object_id)
            if instance:
                self.parent_site = instance.site
        return self.parent_site


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
    # Should appear only on Site admin or other BaseSiteContent admin objects
    list_select_related = ("site",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("site")

    def get_site_from_object(self, request):
        if not hasattr(self, "parent_site"):
            self.parent_site = None
            object_id = request.resolver_match.kwargs.get("object_id")
            instance = self.parent_model.objects.filter(id=object_id).first()
            if instance and isinstance(instance, Site):
                self.parent_site = instance
            elif instance and hasattr(instance, "site"):
                self.parent_site = instance.site
        return self.parent_site


class HiddenBaseAdmin(BaseAdmin):
    """
    This utility class controls if a model will be displayed on the admin index page. This does not restrict
    access to the view, add, change, or delete views.

    Ref: https://docs.djangoproject.com/en/4.1/ref/contrib/admin/#django.contrib.admin.ModelAdmin.has_add_permission
    """

    def has_module_permission(self, request):
        return {}
