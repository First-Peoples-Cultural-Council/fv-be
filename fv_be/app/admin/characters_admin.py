from django.contrib import admin

from fv_be.app.models.characters import Character, CharacterVariant, IgnoredCharacter
from fv_be.app.models.dictionary import DictionaryEntry

# FirstVoices
from .base_admin import BaseInlineAdmin, BaseSiteContentAdmin


class CharacterRelatedDictionaryEntryInline(BaseInlineAdmin):
    model = Character.related_dictionary_entries.through
    fields = ("character", "dictionary_entry")
    readonly_fields = BaseInlineAdmin.readonly_fields
    can_delete = True

    # TODO: When adding a character, all related dictionary entries are shown. This should be filtered by site.
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
    filter_horizontal = ("related_dictionary_entries",)
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


class CharacterInline(BaseInlineAdmin):
    filter_horizontal = ("related_dictionary_entries",)
    model = Character
    fields = (
        "title",
        "sort_order",
        "approximate_form",
        "notes",
    ) + BaseInlineAdmin.fields
    readonly_fields = BaseInlineAdmin.readonly_fields + CharacterAdmin.readonly_fields
    inlines = (CharacterRelatedDictionaryEntryInline,)


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
