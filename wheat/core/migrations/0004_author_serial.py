from django.db import migrations, models
import uuid


def populate_author_serials(apps, schema_editor):
    Author = apps.get_model("core", "Author")
    for a in Author.objects.all():
        if not a.serial:
            a.serial = uuid.uuid4()
            a.save(update_fields=["serial"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_author_description_alter_author_displayname_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="author",
            name="serial",
            field=models.UUIDField(null=True, editable=False),
        ),

        migrations.RunPython(populate_author_serials, migrations.RunPython.noop),

        migrations.AlterField(
            model_name="author",
            name="serial",
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
    ]