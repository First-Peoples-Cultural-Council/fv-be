from django.contrib import admin

from firstvoices.backend.models.characters import (
    AlphabetMapper,
    Character,
    CharacterVariant,
    IgnoredCharacter,
)
from firstvoices.backend.models.dictionary import DictionaryEntry

from .base_admin import BaseInlineAdmin, BaseSiteContentAdmin


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
    inlines = (CharacterRelatedDictionaryEntryInline,)


@admin.register(CharacterVariant)
class CharacterVariantAdmin(BaseSiteContentAdmin):
    fields = ("title", "base_character")
    list_display = (
        "title",
        "base_character",
        "site",
    ) + BaseSiteContentAdmin.list_display
    search_fields = ("title", "base_character")


@admin.register(IgnoredCharacter)
class IgnoredCharacterAdmin(BaseSiteContentAdmin):
    fields = ("title", "site")
    list_display = ("title", "site") + BaseSiteContentAdmin.list_display
    search_fields = ("title",)


@admin.register(AlphabetMapper)
class AlphabetMapperAdmin(BaseSiteContentAdmin):
    fields = ("site", "input_to_canonical_map")
    list_display = (
        "site",
        "input_to_canonical_map",
    ) + BaseSiteContentAdmin.list_display


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
