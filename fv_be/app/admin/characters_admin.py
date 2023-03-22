from django.contrib import admin

from fv_be.app.models.characters import Character, CharacterVariant, IgnoredCharacter

from .base_admin import BaseInlineAdmin, BaseSiteContentAdmin


@admin.register(Character)
class CharacterAdmin(BaseSiteContentAdmin):
    fields = (
        "title",
        "sort_order",
        "approximate_form",
        "site",
        "notes",
    )
    list_display = (
        "title",
        "sort_order",
        "approximate_form",
    ) + BaseSiteContentAdmin.list_display
    search_fields = ("title", "approximate_form")


@admin.register(CharacterVariant)
class CharacterVariantAdmin(BaseSiteContentAdmin):
    fields = ("title", "base_character", "site")
    list_display = (
        "title",
        "base_character",
    ) + BaseSiteContentAdmin.list_display
    search_fields = ("title", "base_character")


@admin.register(IgnoredCharacter)
class IgnoredCharacterAdmin(BaseSiteContentAdmin):
    fields = ("title", "site")
    list_display = ("title", "site") + BaseSiteContentAdmin.list_display
    search_fields = ("title",)


class CharacterInline(BaseInlineAdmin):
    model = Character
    fields = (
        "title",
        "sort_order",
        "approximate_form",
        "notes",
    ) + BaseInlineAdmin.fields
    readonly_fields = BaseInlineAdmin.readonly_fields + CharacterAdmin.readonly_fields


class CharacterVariantInline(BaseInlineAdmin):
    model = CharacterVariant
    fields = (
        "title",
        "base_character",
    ) + BaseInlineAdmin.fields
    readonly_fields = (
        BaseInlineAdmin.readonly_fields + CharacterVariantAdmin.readonly_fields
    )


class IgnoredCharacterInline(BaseInlineAdmin):
    model = IgnoredCharacter
    fields = ("title",) + BaseInlineAdmin.fields
    readonly_fields = (
        BaseInlineAdmin.readonly_fields + IgnoredCharacterAdmin.readonly_fields
    )
