from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from .models import Language, Word, Phrase


class WordInline(admin.TabularInline):
    model = Word
    classes = ['collapse']
    extra = 0

    def admin_link(self, instance):
        url = reverse('admin:%s_%s_change' % (instance._meta.app_label,
                                              instance._meta.model_name),
                      args=(instance.id,))
        return format_html(u'<a href="{}">Edit: {}</a>', url, instance.title)

    def uuid(self, instance):
        return instance.id

    uuid.short_description = 'Id'
    readonly_fields = ('admin_link', 'uuid')


class PhraseInline(admin.TabularInline):
    model = Phrase
    classes = ['collapse']
    extra = 0

    def admin_link(self, instance):
        url = reverse('admin:%s_%s_change' % (instance._meta.app_label,
                                              instance._meta.model_name),
                      args=(instance.id,))
        return format_html(u'<a href="{}">Edit: {}</a>', url, instance.title)

    def uuid(self, instance):
        return instance.id

    uuid.short_description = 'Id'
    readonly_fields = ('admin_link', 'uuid')


class LanguageAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    inlines = [
        WordInline,
        PhraseInline,
    ]

    def get_queryset(self, request):
        qs = super(LanguageAdmin, self).get_queryset(request)
        return qs.annotate(word_count=Count('word', distinct=True)).annotate(
            phrase_count=Count('phrase', distinct=True))

    def word_count(self, inst):
        return inst.word_count

    def phrase_count(self, inst):
        return inst.phrase_count

    list_display = ('title', 'id', 'state', 'description', 'word_count', 'phrase_count')


class WordAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('title', 'id', 'state', 'language')


class PhraseAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('title', 'id', 'state', 'language')


admin.site.register(Language, LanguageAdmin)
admin.site.register(Word, WordAdmin)
admin.site.register(Phrase, PhraseAdmin)
# admin.site.register(Permission)
