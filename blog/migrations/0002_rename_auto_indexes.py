from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("blog", "0001_initial"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="post",
            new_name="blog_post_status_5b2843_idx",
            old_name="blog_post_status_7e22a7_idx",
        ),
        migrations.RenameIndex(
            model_name="post",
            new_name="blog_post_slug_cdb902_idx",
            old_name="blog_post_slug_1aa868_idx",
        ),
    ]
