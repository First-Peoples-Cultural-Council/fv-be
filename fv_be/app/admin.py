from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from .models import Category, Membership, Role, Site, Word


class WordInline(admin.TabularInline):
    model = Word
    classes = ["collapse"]
    extra = 0

    def admin_link(self, instance):
        url = reverse(
            "admin:{}_{}_change".format(
                instance._meta.app_label, instance._meta.model_name
            ),
            args=(instance.id,),
        )
        return format_html('<a href="{}">Edit: {}</a>', url, instance.title)

    def uuid(self, instance):
        return instance.id

    uuid.short_description = "Id"
    readonly_fields = ("admin_link", "uuid")


class CategoryInline(admin.TabularInline):
    model = Category
    classes = ["collapse"]
    extra = 0

    def admin_link(self, instance):
        url = reverse(
            "admin:{}_{}_change".format(
                instance._meta.app_label, instance._meta.model_name
            ),
            args=(instance.id,),
        )
        return format_html('<a href="{}">Edit: {}</a>', url, instance.title)

    def uuid(self, instance):
        return instance.id

    uuid.short_description = "Id"
    readonly_fields = ("admin_link", "uuid")
    filter_horizontal = ("words",)


class SiteAdmin(admin.ModelAdmin):
    readonly_fields = ("id",)
    inlines = [
        WordInline,
        CategoryInline,
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(word_count=Count("word", distinct=True)).annotate(
            category_count=Count("category", distinct=True)
        )

    def word_count(self, inst):
        return inst.word_count

    def category_count(self, inst):
        return inst.category_count

    list_display = ("title", "id", "state", "word_count", "category_count")


class WordAdmin(admin.ModelAdmin):
    readonly_fields = ("id",)
    list_display = ("title", "id", "state", "site")


class CategoryAdmin(admin.ModelAdmin):
    readonly_fields = ("id",)
    list_display = ("title", "id", "state", "site")
    filter_horizontal = ("words",)


admin.site.register(Membership)
admin.site.register(Role)
admin.site.register(Site, SiteAdmin)
admin.site.register(Word, WordAdmin)
admin.site.register(Category, CategoryAdmin)
