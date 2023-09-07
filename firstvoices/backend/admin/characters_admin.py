from django.contrib import admin

from backend.models.characters import (
    Alphabet,
    Character,
    CharacterVariant,
    IgnoredCharacter,
)
from backend.models.dictionary import DictionaryEntry

from .base_admin import (
    BaseAdmin,
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


class CharacterVariantInline(BaseInlineSiteContentAdmin):
    model = CharacterVariant
    fields = (
        "title",
        "base_character",
    ) + BaseInlineAdmin.fields
    ordering = ("base_character__sort_order", "title")

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

    # see fw-4234 about filtering the dictionary entries by site here
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "dictionary_entry":
            # Get the Character from the request and filter dictionary entries by its site_id
            character_id = request.resolver_match.kwargs.get("object_id")
            if character_id:
                queryset = DictionaryEntry.objects.filter(
                    site_id=self.model.character.field.related_model.objects.get(
                        pk=character_id
                    ).site_id
                )
                kwargs["queryset"] = queryset
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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
        return qs.select_related("base_character")


@admin.register(IgnoredCharacter)
class IgnoredCharacterAdmin(BaseSiteContentAdmin):
    fields = ("title", "site")
    list_display = ("title", "site") + BaseSiteContentAdmin.list_display
    search_fields = ("title",)


@admin.register(Alphabet)
class AlphabetAdmin(BaseAdmin):
    fields = ("site", "input_to_canonical_map")
    list_display = (
        "site",
        "input_to_canonical_map",
    ) + BaseAdmin.list_display
