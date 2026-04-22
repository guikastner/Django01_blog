from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone
from PIL import Image, UnidentifiedImageError


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
EXTENSION_BY_CONTENT_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
CONTENT_TYPE_BY_IMAGE_FORMAT = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}
EXTENSION_BY_IMAGE_FORMAT = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
}


def _reset_uploaded_file(image):
    if hasattr(image, "seek"):
        image.seek(0)


def _detect_image_format(image):
    try:
        with Image.open(image) as detected_image:
            detected_image.verify()
            return detected_image.format
    except (OSError, UnidentifiedImageError, ValueError):
        return ""
    finally:
        _reset_uploaded_file(image)


def validate_editor_image(image):
    content_type = getattr(image, "content_type", "")
    if content_type not in settings.ALLOWED_COVER_IMAGE_TYPES:
        max_types = ", ".join(sorted(settings.ALLOWED_COVER_IMAGE_TYPES))
        return f"Only these image types are allowed: {max_types}."

    if image.size > settings.MAX_COVER_IMAGE_SIZE:
        max_mb = settings.MAX_COVER_IMAGE_SIZE // (1024 * 1024)
        return f"Images must be smaller than {max_mb} MB."

    image_format = _detect_image_format(image)
    real_content_type = CONTENT_TYPE_BY_IMAGE_FORMAT.get(image_format)
    if real_content_type is None:
        return "Uploaded file is not a valid JPEG, PNG, or WebP image."

    if real_content_type != content_type:
        return "Uploaded image content does not match its declared type."

    image.validated_image_extension = EXTENSION_BY_IMAGE_FORMAT[image_format]
    return ""


def save_editor_image(image):
    extension = getattr(image, "validated_image_extension", "")
    if not extension:
        extension = EXTENSION_BY_IMAGE_FORMAT.get(_detect_image_format(image), "")
    if not extension:
        extension = Path(image.name).suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        extension = EXTENSION_BY_CONTENT_TYPE[getattr(image, "content_type", "")]

    now = timezone.now()
    path_name = f"posts/content/{now:%Y/%m}/{uuid4().hex}{extension}"
    saved_path = default_storage.save(path_name, image)
    return default_storage.url(saved_path)
