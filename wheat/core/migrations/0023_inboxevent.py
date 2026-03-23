from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0022_entry_web"),
    ]

    operations = [
        migrations.CreateModel(
            name="InboxItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("item_type", models.CharField(max_length=20)),
                ("item_id", models.URLField()),
                ("payload", models.JSONField(default=dict)),
                ("received_at", models.DateTimeField(auto_now_add=True)),
                (
                    "owner",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="inbox_items", to="core.author"),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="inboxitem",
            constraint=models.UniqueConstraint(fields=("owner", "item_id"), name="unique_inbox_item_per_owner"),
        ),
    ]
