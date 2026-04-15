#!/usr/bin/env python
"""
Final verification script to ensure everything is properly configured
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail
from users.models import User
from email_communication.email_utils import is_valid_email

print("\n" + "=" * 80)
print("COMPLETE EMAIL SYSTEM VERIFICATION")
print("=" * 80 + "\n")

# Check 1: Environment Variables
print("1️⃣  EMAIL CONFIGURATION")
print("-" * 80)
print(f"   Backend: {settings.EMAIL_BACKEND}")
print(f"   Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
print(f"   User: {settings.EMAIL_HOST_USER}")
password_masked = '*' * (len(settings.EMAIL_HOST_PASSWORD) - 3) + settings.EMAIL_HOST_PASSWORD[-3:] if settings.EMAIL_HOST_PASSWORD else 'NOT SET'
print(f"   Password: {password_masked}")
print(f"   TLS: {settings.EMAIL_USE_TLS}")

# Check 2: Users and Email Validity
print("\n2️⃣  USER EMAIL VALIDATION")
print("-" * 80)
users = User.objects.filter(is_active=True)
valid_count = 0
invalid_count = 0
invalid_emails = []

for user in users:
    if is_valid_email(user.email):
        valid_count += 1
    else:
        invalid_count += 1
        invalid_emails.append(f"{user.email} ({user.get_role_display()})")

print(f"   Total active users: {users.count()}")
print(f"   Valid emails: {valid_count}")
print(f"   Invalid emails: {invalid_count}")

if invalid_emails:
    print(f"\n   Invalid emails found (will be skipped):")
    for email in invalid_emails:
        print(f"      ❌ {email}")

# Check 3: Test Email
print("\n3️⃣  TEST EMAIL SENDING")
print("-" * 80)
try:
    send_mail(
        subject='✓ Email Configuration Test',
        message='If you received this email, your configuration is working correctly!',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.EMAIL_HOST_USER],
        fail_silently=False
    )
    print("   ✅ Test email sent successfully!")
except Exception as e:
    error_msg = str(e)
    if "Username and Password not accepted" in error_msg:
        print("   ❌ AUTHENTICATION FAILED")
        print("      Your .env password may be outdated or incorrect")
        print("      → Restart Django server to reload .env variables")
        print("      → Or regenerate Gmail app password at https://myaccount.google.com/apppasswords")
    else:
        print(f"   ❌ Error: {error_msg[:100]}")

# Check 4: Ready Status
print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)

if settings.EMAIL_HOST_PASSWORD and valid_count > 0:
    print("\n✅ System appears properly configured!")
    print("\nYou can now safely send promotional and course announcement emails.")
    print(f"   - {valid_count} valid recipient(s) will receive emails")
    if invalid_count > 0:
        print(f"   - {invalid_count} invalid email(s) will be skipped")
else:
    print("\n⚠️  Configuration issues detected. Please review above.")

print("\n" + "=" * 80 + "\n")
