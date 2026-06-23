from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("marketplace", "0007_techniciandocument_review_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="notification",
            name="event",
            field=models.CharField(
                choices=[
                    ("message", "Messages"),
                    ("application", "Application activity"),
                    ("offer", "Invitations and offers"),
                    ("credential", "Credential requests"),
                    ("job_match", "Matching jobs"),
                    ("system", "Account and moderation notices"),
                ],
                default="application",
                max_length=20,
            ),
        ),
    ]
