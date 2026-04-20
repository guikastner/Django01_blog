from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("blog", "0002_rename_auto_indexes"),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True)),
                ("slug", models.SlugField(max_length=100, unique=True)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name_plural": "categories",
                "ordering": ["name"],
            },
        ),
        migrations.AddIndex(
            model_name="category",
            index=models.Index(fields=["slug"], name="blog_catego_slug_fc0bb9_idx"),
        ),
        migrations.AddField(
            model_name="post",
            name="categories",
            field=models.ManyToManyField(blank=True, related_name="posts", to="blog.category"),
        ),
    ]
