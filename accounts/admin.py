from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class WrenchLinkUserAdmin(UserAdmin):
    list_display = ("email", "first_name", "last_name", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active", "email_verified")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    fieldsets = UserAdmin.fieldsets + (
        ("WrenchLink", {"fields": ("role", "email_verified")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("WrenchLink", {"fields": ("email", "role", "first_name", "last_name")}),
    )
