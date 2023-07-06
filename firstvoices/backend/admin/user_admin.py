from django.contrib import admin

from backend.models import User

from . import MembershipInline


class UserMembershipInline(MembershipInline):
    fk_name = "user"


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "is_staff")
    fields = ("id", "email", "is_staff", "is_superuser", "date_joined", "last_login")
    search_fields = ("email", "id")

    # setting first_name and last_name to readonly because they are deprecated
    readonly_fields = (
        "id",
        "password",
        "first_name",
        "last_name",
        "date_joined",
        "last_login",
    )

    inlines = [UserMembershipInline]
