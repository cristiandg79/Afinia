from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0003_plan_country'),
    ]

    operations = [
        migrations.AlterField(
            model_name='planattendance',
            name='status',
            field=models.CharField(
                choices=[
                    ('requested', 'Solicitado'),
                    ('approved', 'Miembro'),
                    ('moderator', 'Moderador'),
                    ('declined', 'Rechazado'),
                ],
                default='requested',
                max_length=20,
            ),
        ),
    ]
