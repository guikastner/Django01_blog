from pathlib import Path
from uuid import uuid4

from django.contrib import admin
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.urls import path, reverse
from django.utils import timezone

from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "status", "published_at", "created_at")
    list_filter = ("status", "created_at", "published_at")
    search_fields = ("title", "excerpt", "content")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "published_at"
    ordering = ("-published_at", "-created_at")

    def get_urls(self):
        custom_urls = [
            path(
                "upload-content-image/",
                self.admin_site.admin_view(self.upload_content_image),
                name="blog_post_upload_content_image",
            ),
        ]
        return custom_urls + super().get_urls()

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "content":
            formfield.widget.attrs["data-upload-url"] = reverse("admin:blog_post_upload_content_image")
        return formfield

    def get_view_on_site_url(self, obj=None):
        if (
            obj is None
            or obj.status != Post.Status.PUBLISHED
            or obj.published_at is None
            or obj.published_at > timezone.now()
        ):
            return None
        return super().get_view_on_site_url(obj)

    def upload_content_image(self, request):
        if request.method != "POST":
            return JsonResponse({"error": "Only POST requests are allowed."}, status=405)

        image = request.FILES.get("image")
        if image is None:
            return JsonResponse({"error": "No image file was uploaded."}, status=400)

        content_type = getattr(image, "content_type", "")
        if content_type not in settings.ALLOWED_COVER_IMAGE_TYPES:
            return JsonResponse({"error": "Only JPEG, PNG, and WebP images are allowed."}, status=400)

        if image.size > settings.MAX_COVER_IMAGE_SIZE:
            max_mb = settings.MAX_COVER_IMAGE_SIZE // (1024 * 1024)
            return JsonResponse({"error": f"Images must be smaller than {max_mb} MB."}, status=400)

        extension = Path(image.name).suffix.lower()
        if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
            extension = {
                "image/jpeg": ".jpg",
                "image/png": ".png",
                "image/webp": ".webp",
            }[content_type]

        now = timezone.now()
        path_name = f"posts/content/{now:%Y/%m}/{uuid4().hex}{extension}"
        saved_path = default_storage.save(path_name, image)
        return JsonResponse({"url": default_storage.url(saved_path)})

    class Media:
        css = {"all": ("blog/admin_wysiwyg.css",)}
        js = ("blog/admin_wysiwyg.js",)
