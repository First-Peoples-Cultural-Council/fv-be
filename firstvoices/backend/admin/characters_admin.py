from django.contrib import admin
from django.urls import NoReverseMatch, reverse
from django.utils.html import format_html

from backend.models.characters import (
    Alphabet,
    Character,
    CharacterVariant,
    IgnoredCharacter,
)
from backend.models.dictionary import DictionaryEntry

from .base_admin import (
    BaseInlineAdmin,
    BaseInlineSiteContentAdmin,
    BaseSiteContentAdmin,
)


class CharacterInline(BaseInlineSiteContentAdmin):
    model = Character
    fields = (
        "title",
        "sort_order",
    ) + BaseInlineAdmin.fields
    ordering = ("sort_order",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("site", "created_by", "last_modified_by")


class CharacterVariantInline(BaseInlineSiteContentAdmin):
    model = CharacterVariant
    fields = (
        "title",
        "base_character",
    ) + BaseInlineAdmin.fields
    ordering = ("base_character__sort_order", "title")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("site", "created_by", "last_modified_by")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "base_character":
            kwargs["queryset"] = Character.objects.select_related("site").filter(
                site=self.get_site_from_object(request)
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class IgnoredCharacterInline(BaseInlineSiteContentAdmin):
    model = IgnoredCharacter
    fields = ("title",) + BaseInlineAdmin.fields


class CharacterRelatedDictionaryEntryInline(BaseInlineAdmin):
    model = DictionaryEntry.related_characters.through
    fields = ("character", "dictionary_entry")
    readonly_fields = BaseInlineAdmin.readonly_fields
    can_delete = True
    autocomplete_fields = ("dictionary_entry",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("dictionary_entry", "character", "character__site")


@admin.register(Character)
class CharacterAdmin(BaseSiteContentAdmin):
    list_display = (
        "title",
        "sort_order",
        "approximate_form",
    ) + BaseSiteContentAdmin.list_display
    search_fields = ("title", "approximate_form")
    inlines = (CharacterVariantInline, CharacterRelatedDictionaryEntryInline)
    autocomplete_fields = ("related_audio", "related_images", "related_videos")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("site", "created_by", "last_modified_by")


@admin.register(CharacterVariant)
class CharacterVariantAdmin(BaseSiteContentAdmin):
    fields = ("title", "base_character")
    list_display = (
        "title",
        "base_character",
    ) + BaseSiteContentAdmin.list_display
    search_fields = ("title", "base_character")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "base_character":
            kwargs["queryset"] = Character.objects.select_related("site").filter(
                site=self.get_site_from_object(request)
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "base_character",
            "base_character__site",
            "site",
            "created_by",
            "last_modified_by",
        )


@admin.register(IgnoredCharacter)
class IgnoredCharacterAdmin(BaseSiteContentAdmin):
    fields = ("title", "site")
    list_display = ("title", "site") + BaseSiteContentAdmin.list_display
    search_fields = ("title",)


@admin.register(Alphabet)
class AlphabetAdmin(BaseSiteContentAdmin):
    fields = ("id", "site", "input_to_canonical_map")
    list_display = (
        ("input_to_canonical_map",)
        + BaseSiteContentAdmin.list_display
        + ("admin_link",)
    )
    list_filter = ()

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
