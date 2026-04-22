from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, reverse

from .media import save_editor_image, validate_editor_image
from .models import Category, Post


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "status", "published_at", "created_at")
    list_filter = ("status", "categories", "created_at", "published_at")
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
        if obj is None or not obj.is_public():
            return None
        return super().get_view_on_site_url(obj)

    def upload_content_image(self, request):
        if request.method != "POST":
            return JsonResponse({"error": "Only POST requests are allowed."}, status=405)

        image = request.FILES.get("image")
        if image is None:
            return JsonResponse({"error": "No image file was uploaded."}, status=400)

        error = validate_editor_image(image)
        if error:
            return JsonResponse({"error": error}, status=400)

        return JsonResponse({"url": save_editor_image(image)})

    class Media:
        css = {"all": ("blog/admin_wysiwyg.css",)}
        js = ("blog/admin_wysiwyg.js",)
