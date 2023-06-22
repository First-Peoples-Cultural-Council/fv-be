from django.contrib import admin

from backend.admin import BaseSiteContentAdmin, BaseInlineAdmin
from backend.models import Song, TranslatedText


class TranslatedTextAdmin(BaseInlineAdmin):
    """
    Base class for inline translations (you'll get an FK error and a useless verbose_name if you use it directly)
    """
    model = TranslatedText
    fields = ("text", "language")
    list_display = ("text", "language")


class InlineLyricsTranslations(TranslatedTextAdmin):
    fk_name = 'song_lyrics'
    verbose_name = 'Lyrics Translation'
    verbose_name_plural = 'Lyrics Translations'


class InlineTitleTranslactions(TranslatedTextAdmin):
    fk_name = 'song_title'
    verbose_name = 'Title Translation'
    verbose_name_plural = 'Title Translations'


class InlineIntroductionTranslactions(TranslatedTextAdmin):
    fk_name = 'song_introduction'
    verbose_name = 'Introduction Translation'
    verbose_name_plural = 'Introduction Translations'


@admin.register(Song)
class SongAdmin(BaseSiteContentAdmin):
    list_display = ("title",) + BaseSiteContentAdmin.list_display
    inlines = [InlineIntroductionTranslactions,
               InlineTitleTranslactions,
               InlineLyricsTranslations]

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super(SongAdmin, self).get_form(request, obj, change, **kwargs)
        form.base_fields['cover_image'].required = False
        form.base_fields['authours'].required = False
        return form
