from django.contrib import admin

from .models import Comment


@admin.action(description="Approve selected comments")
def approve_comments(modeladmin, request, queryset):
    queryset.update(is_approved=True)


@admin.action(description="Reject selected comments")
def reject_comments(modeladmin, request, queryset):
    queryset.update(is_approved=False)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "post", "is_approved", "created_at")
    list_filter = ("is_approved", "post", "created_at")
    search_fields = ("name", "email", "user__username", "user__email", "body", "post__title")
    readonly_fields = ("created_at", "updated_at")
    actions = [approve_comments, reject_comments]
