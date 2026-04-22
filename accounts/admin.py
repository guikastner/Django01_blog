from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "is_comment_banned", "comment_banned_at", "comment_banned_by")
    list_filter = ("is_comment_banned", "comment_banned_at")
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name")
    readonly_fields = ("created_at", "updated_at", "comment_banned_at", "comment_banned_by")
