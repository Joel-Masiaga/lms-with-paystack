#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms.settings')
django.setup()

from django.core.mail import send_mail

try:
    # Test sending an email
    send_mail(
        subject='Test Email from Paystack LMS',
        message='This is a test email to verify Gmail SMTP configuration is working correctly.',
        from_email='masiagajoel001@gmail.com',
        recipient_list=['masiagajoel001@gmail.com'],
        fail_silently=False
    )
    print("✓ Test email sent successfully!")
except Exception as e:
    print(f"✗ Error sending test email: {e}")
    sys.exit(1)
