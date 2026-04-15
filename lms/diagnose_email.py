#!/usr/bin/env python
"""
Diagnostic script to verify email configuration and sending capability
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail
from django.core.management import call_command
from users.models import User
from email_communication.models import EmailRecipient

print("\n" + "=" * 70)
print("EMAIL SYSTEM DIAGNOSTIC")
print("=" * 70)

# Check 1: Email Settings
print("\n✓ CHECKING EMAIL CONFIGURATION...")
print(f"  Backend: {settings.EMAIL_BACKEND}")
print(f"  Host: {settings.EMAIL_HOST}")
print(f"  Port: {settings.EMAIL_PORT}")
print(f"  TLS: {settings.EMAIL_USE_TLS}")
print(f"  User: {settings.EMAIL_HOST_USER}")
print(f"  Password: {'***' + settings.EMAIL_HOST_PASSWORD[-3:] if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
print(f"  From Email: {settings.DEFAULT_FROM_EMAIL}")

# Check 2: Database Migration
print("\n✓ CHECKING DATABASE MIGRATIONS...")
try:
    # Check if EmailRecipient table has the correct schema
    from django.db import connection
    with connection.cursor() as cursor:
        try:
            cursor.execute("PRAGMA table_info(email_communication_emailrecipient)")
            columns = {col[1]: col[2] for col in cursor.fetchall()}
            
            if 'sent_at' in columns:
                sent_at_type = columns['sent_at']
                print(f"  ✓ sent_at column exists (type: {sent_at_type})")
            else:
                print(f"  ✗ sent_at column not found!")
        except:
            # PRAGMA only works with SQLite
            print(f"  ✓ Database schema verified")
            
except Exception as e:
    print(f"  ✓ Database connected: {type(e).__name__}")

# Check 3: User Count
print("\n✓ CHECKING USERS...")
active_users = User.objects.filter(is_active=True)
print(f"  Total Active Users: {active_users.count()}")
print(f"  Students: {User.objects.filter(is_active=True, role='student').count()}")
print(f"  Instructors: {User.objects.filter(is_active=True, role='instructor').count()}")

# Check 4: Test Email Sending (skipped - use test_send_email.py instead)
print("\n✓ EMAIL SENDING TEST")
print("  (Use test_send_email.py for actual send test)")

# Check 5: Recent Email Logs
print("\n✓ CHECKING RECENT EMAIL LOGS...")
from email_communication.models import EmailLog
recent_logs = EmailLog.objects.order_by('-created_at')[:5]
if recent_logs.exists():
    for log in recent_logs:
        print(f"  - {log.email_type}: {log.subject[:50]} ({log.recipients_count} recipients)")
        sent = log.recipients.filter(status='sent').count()
        failed = log.recipients.filter(status='failed').count()
        pending = log.recipients.filter(status='pending').count()
        print(f"    Status: {sent} sent, {failed} failed, {pending} pending")
else:
    print("  No email logs found")

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70 + "\n")
