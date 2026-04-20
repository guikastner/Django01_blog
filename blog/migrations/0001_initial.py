# Generated manually for the initial blog schema.

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import blog.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Post",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=220, unique=True)),
                ("excerpt", models.TextField(blank=True)),
                ("content", models.TextField()),
                (
                    "cover_image",
                    models.ImageField(
                        blank=True,
                        upload_to="posts/covers/%Y/%m/",
                        validators=[
                            django.core.validators.FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
                            blog.models.validate_cover_image,
                        ],
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("draft", "Draft"), ("published", "Published")],
                        default="draft",
                        max_length=20,
                    ),
                ),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="posts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-published_at", "-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="post",
            index=models.Index(fields=["status", "published_at"], name="blog_post_status_7e22a7_idx"),
        ),
        migrations.AddIndex(
            model_name="post",
            index=models.Index(fields=["slug"], name="blog_post_slug_1aa868_idx"),
        ),
    ]
