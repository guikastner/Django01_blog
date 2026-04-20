from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
EXTENSION_BY_CONTENT_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def validate_editor_image(image):
    content_type = getattr(image, "content_type", "")
    if content_type not in settings.ALLOWED_COVER_IMAGE_TYPES:
        max_types = ", ".join(sorted(settings.ALLOWED_COVER_IMAGE_TYPES))
        return f"Only these image types are allowed: {max_types}."

    if image.size > settings.MAX_COVER_IMAGE_SIZE:
        max_mb = settings.MAX_COVER_IMAGE_SIZE // (1024 * 1024)
        return f"Images must be smaller than {max_mb} MB."

    return ""


def save_editor_image(image):
    extension = Path(image.name).suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        extension = EXTENSION_BY_CONTENT_TYPE[getattr(image, "content_type", "")]

    now = timezone.now()
    path_name = f"posts/content/{now:%Y/%m}/{uuid4().hex}{extension}"
    saved_path = default_storage.save(path_name, image)
    return default_storage.url(saved_path)
