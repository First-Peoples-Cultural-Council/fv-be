from django.contrib import admin

from backend.models import User, UserProfile

from . import MembershipInline
from .base_admin import BaseInlineAdmin, HiddenBaseAdmin


@admin.register(UserProfile)
class UserProfileAdmin(HiddenBaseAdmin):
    list_display = ("user",) + HiddenBaseAdmin.list_display
    search_fields = (
        "user",
        "traditional_name",
    )


class UserProfileInline(BaseInlineAdmin):
    model = UserProfile
    fk_name = "user"
    fields = ("character", "dictionary_entry")
    fk_name = "user"


class UserMembershipInline(MembershipInline):
    fk_name = "user"


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "is_staff")
    fields = ("id", "email", "first_name", "last_name", "date_joined", "last_login")
    search_fields = ("email", "first_name", "last_name", "id")

    # setting first_name and last_name to readonly because they are deprecated
    readonly_fields = (
        "id",
        "password",
        "first_name",
        "last_name",
        "date_joined",
        "last_login",
    )

    inlines = [UserProfileInline, UserMembershipInline]
