from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("comments", "0001_initial"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="comment",
            new_name="comments_co_post_id_cf2c9b_idx",
            old_name="comments_co_post_id_8eccef_idx",
        ),
    ]
