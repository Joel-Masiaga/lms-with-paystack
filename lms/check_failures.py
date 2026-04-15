#!/usr/bin/env python
"""
Check email failure details
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms.settings')
django.setup()

from email_communication.models import EmailLog, EmailRecipient

print("\n" + "=" * 80)
print("EMAIL FAILURE ANALYSIS")
print("=" * 80 + "\n")

# Get all failed emails with their error messages
failed_recipients = EmailRecipient.objects.filter(status='failed').select_related('email_log')[:10]

if failed_recipients.exists():
    print(f"Found {failed_recipients.count()} failed email records:\n")
    
    for recipient in failed_recipients:
        print(f"Email: {recipient.email_log.subject}")
        print(f"  Recipient: {recipient.recipient.email}")
        print(f"  Error: {recipient.error_message}")
        print()
else:
    print("No failed email records found.")

print("=" * 80 + "\n")
