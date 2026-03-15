import uuid

from django.db import migrations, models


def populate_like_serials_and_remove_duplicates(apps, schema_editor):
    EntryLike = apps.get_model("core", "EntryLike")
    CommentLike = apps.get_model("core", "CommentLike")

    seen_entry_likes = set()
    for like in EntryLike.objects.order_by("id"):
        key = (like.author_id, like.entry_id)
        if key in seen_entry_likes:
            like.delete()
            continue

        seen_entry_likes.add(key)
        if like.serial is None:
            like.serial = uuid.uuid4()
            like.save(update_fields=["serial"])

    seen_comment_likes = set()
    for like in CommentLike.objects.order_by("id"):
        key = (like.author_id, like.comment_id)
        if key in seen_comment_likes:
            like.delete()
            continue

        seen_comment_likes.add(key)
        if like.serial is None:
            like.serial = uuid.uuid4()
            like.save(update_fields=["serial"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0014_alter_entry_title"),
    ]

    operations = [
        migrations.AddField(
            model_name="entrylike",
            name="serial",
            field=models.UUIDField(default=uuid.uuid4, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="commentlike",
            name="serial",
            field=models.UUIDField(default=uuid.uuid4, editable=False, null=True),
        ),
        migrations.RunPython(
            populate_like_serials_and_remove_duplicates,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="entrylike",
            name="serial",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name="commentlike",
            name="serial",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddConstraint(
            model_name="entrylike",
            constraint=models.UniqueConstraint(
                fields=("author", "entry"),
                name="unique_entry_like",
            ),
        ),
        migrations.AddConstraint(
            model_name="commentlike",
            constraint=models.UniqueConstraint(
                fields=("author", "comment"),
                name="unique_comment_like",
            ),
        ),
    ]
