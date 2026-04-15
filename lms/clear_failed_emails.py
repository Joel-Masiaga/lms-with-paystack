#!/usr/bin/env python
"""
Clear failed email records to start fresh
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms.settings')
django.setup()

from email_communication.models import EmailRecipient, EmailLog

print("\nClearing failed email records...\n")

# Delete all failed recipient records
failed_count = EmailRecipient.objects.filter(status='failed').count()
EmailRecipient.objects.filter(status='failed').delete()
print(f"✓ Deleted {failed_count} failed email records")

# Delete email logs with no sent emails
empty_logs = EmailLog.objects.filter(recipients__isnull=True)
empty_logs_count = empty_logs.count()
empty_logs.delete()
print(f"✓ Deleted {empty_logs_count} empty email logs")

print("\nDatabase cleaned. Ready to send new emails.\n")
