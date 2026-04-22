from django.conf import settings
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comment_profile")
    is_comment_banned = models.BooleanField(default=False)
    comment_ban_reason = models.CharField(max_length=255, blank=True)
    comment_banned_at = models.DateTimeField(blank=True, null=True)
    comment_banned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="issued_comment_bans",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__username"]

    def __str__(self):
        return f"Comment profile for {self.user}"

    @classmethod
    def for_user(cls, user):
        profile, _created = cls.objects.get_or_create(user=user)
        return profile

    def ban_from_comments(self, banned_by, reason=""):
        self.is_comment_banned = True
        self.comment_ban_reason = reason.strip()
        self.comment_banned_at = timezone.now()
        self.comment_banned_by = banned_by
        self.save(
            update_fields=[
                "is_comment_banned",
                "comment_ban_reason",
                "comment_banned_at",
                "comment_banned_by",
                "updated_at",
            ]
        )

    def allow_comments(self):
        self.is_comment_banned = False
        self.comment_ban_reason = ""
        self.comment_banned_at = None
        self.comment_banned_by = None
        self.save(
            update_fields=[
                "is_comment_banned",
                "comment_ban_reason",
                "comment_banned_at",
                "comment_banned_by",
                "updated_at",
            ]
        )
