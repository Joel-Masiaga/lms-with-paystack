"""
Migration to add 'pending' status and make sent_at nullable.
Handles existing records by setting sent_at to the email_log created_at time.
"""

from django.db import migrations, models
from django.utils import timezone


def set_default_sent_at(apps, schema_editor):
    """Set sent_at to created_at for existing records."""
    EmailRecipient = apps.get_model('email_communication', 'EmailRecipient')
    
    # For all records without sent_at, set it to their email_log's created_at
    for recipient in EmailRecipient.objects.filter(sent_at__isnull=True):
        if recipient.email_log:
            recipient.sent_at = recipient.email_log.created_at
            recipient.save(update_fields=['sent_at'])


class Migration(migrations.Migration):

    dependencies = [
        ('email_communication', '0001_initial'),
    ]

    operations = [
        # First, update the status field to include 'pending' choice
        migrations.AlterField(
            model_name='emailrecipient',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('sent', 'Sent'),
                    ('failed', 'Failed'),
                    ('bounced', 'Bounced')
                ],
                default='pending',
                max_length=10
            ),
        ),
        
        # Then, set default sent_at for existing records
        migrations.RunPython(set_default_sent_at),
        
        # Finally, make sent_at nullable for new pending records
        migrations.AlterField(
            model_name='emailrecipient',
            name='sent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
