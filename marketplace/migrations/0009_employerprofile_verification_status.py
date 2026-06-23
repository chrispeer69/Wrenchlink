from django.db import migrations, models


def copy_employer_verification_status(apps, schema_editor):
    EmployerProfile = apps.get_model("marketplace", "EmployerProfile")
    EmployerProfile.objects.filter(is_verified=True).update(
        verification_status="verified"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("marketplace", "0008_alter_notification_event"),
    ]

    operations = [
        migrations.AddField(
            model_name="employerprofile",
            name="rejection_reason",
            field=models.CharField(blank=True, max_length=600),
        ),
        migrations.AddField(
            model_name="employerprofile",
            name="verification_status",
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
        migrations.RunPython(
            copy_employer_verification_status, migrations.RunPython.noop
        ),
    ]
