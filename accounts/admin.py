from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "nickname", "is_active", "is_staff")
    search_fields = ("email", "nickname")
    ordering = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("정보", {"fields": ("nickname",)}),
        ("권한", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )
    add_fieldsets = (
        None,
        {"classes": ("wide",), "fields": ("email", "nickname", "password1", "password2")},
    )
