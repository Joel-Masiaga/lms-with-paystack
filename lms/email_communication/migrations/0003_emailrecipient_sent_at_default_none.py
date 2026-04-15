# Generated migration to set default=None for sent_at field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email_communication', '0002_emailrecipient_status_pending'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailrecipient',
            name='sent_at',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
    ]
