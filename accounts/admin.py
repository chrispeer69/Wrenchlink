from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ModerationAction, User


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


@admin.register(ModerationAction)
class ModerationActionAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "target_user", "actor", "subject")
    list_filter = ("action", "object_type", "created_at")
    search_fields = (
        "target_user__email",
        "target_user__username",
        "actor__username",
        "subject",
        "message",
    )
    readonly_fields = (
        "actor",
        "target_user",
        "action",
        "subject",
        "message",
        "object_type",
        "object_id",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
