from django.db import migrations, models


def copy_document_review_status(apps, schema_editor):
    TechnicianDocument = apps.get_model("marketplace", "TechnicianDocument")
    TechnicianDocument.objects.filter(is_verified=True).update(status="verified")


class Migration(migrations.Migration):
    dependencies = [
        ("marketplace", "0006_notification_event_notificationpreference"),
    ]

    operations = [
        migrations.AddField(
            model_name="techniciandocument",
            name="rejection_reason",
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AddField(
            model_name="techniciandocument",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending review"),
                    ("verified", "Verified"),
                    ("rejected", "Rejected"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.RunPython(copy_document_review_status, migrations.RunPython.noop),
    ]
