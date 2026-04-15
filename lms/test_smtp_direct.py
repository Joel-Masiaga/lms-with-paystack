#!/usr/bin/env python
"""
Deep SMTP connection diagnostic
Tests SMTP connection directly without Django abstractions
"""
import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load .env file directly
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

print("\n" + "=" * 80)
print("DEEP SMTP DIAGNOSTIC")
print("=" * 80 + "\n")

# Get credentials from .env
email_host = os.getenv('EMAIL_HOST', '').strip()
email_port = int(os.getenv('EMAIL_PORT', '587'))
email_user = os.getenv('EMAIL_HOST_USER', '').strip()
email_password = os.getenv('EMAIL_HOST_PASSWORD', '')
email_use_tls = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'

print("1️⃣  CONFIGURATION LOADED FROM .env")
print("-" * 80)
print(f"EMAIL_HOST: '{email_host}'")
print(f"EMAIL_PORT: {email_port}")
print(f"EMAIL_HOST_USER: '{email_user}'")
print(f"EMAIL_PASSWORD length: {len(email_password)} characters")
print(f"EMAIL_PASSWORD (hex): {email_password.encode().hex()}")
print(f"EMAIL_PASSWORD (repr): {repr(email_password)}")
print(f"EMAIL_USE_TLS: {email_use_tls}")

# Check for whitespace issues
if email_password != email_password.strip():
    print(f"\n⚠️  WARNING: Password has leading/trailing whitespace!")
    print(f"   Original length: {len(email_password)}")
    print(f"   Stripped length: {len(email_password.strip())}")
    email_password = email_password.strip()

# Test SMTP connection
print("\n2️⃣  TESTING SMTP CONNECTION")
print("-" * 80)

try:
    print(f"Connecting to {email_host}:{email_port}...")
    server = smtplib.SMTP(email_host, email_port, timeout=10)
    print("✓ TCP connection established\n")
    
    print("Starting TLS...")
    server.starttls()
    print("✓ TLS connection secured\n")
    
    print(f"Authenticating as: {email_user}")
    server.login(email_user, email_password)
    print("✓ AUTHENTICATION SUCCESSFUL!\n")
    
    print("Sending test email...")
    # Create message
    msg = MIMEText("Test email from SMTP diagnostic")
    msg['Subject'] = "[TEST] SMTP Configuration Verified"
    msg['From'] = email_user
    msg['To'] = email_user
    
    # Send
    server.send_message(msg)
    print("✓ Test email sent successfully!\n")
    
    server.quit()
    
    print("=" * 80)
    print("✅ SMTP CONFIGURATION IS CORRECT")
    print("=" * 80)
    print("""
Your Gmail credentials are working correctly!

If Django is still failing:
1. Restart Django server completely
2. Make sure .env file is saved properly
3. Check for any whitespace in passwords
""")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"\n❌ AUTHENTICATION FAILED: {e}\n")
    print("=" * 80)
    print("SOLUTIONS:")
    print("=" * 80)
    print("""
1. Your Gmail app password may be EXPIRED or INCORRECT
   → Go to https://myaccount.google.com/apppasswords
   → Generate a NEW app password
   → Copy the 16-character password (with spaces)
   → Update it in .env file

2. Check for hidden whitespace in .env
   → Open .env in a text editor
   → Check that EMAIL_HOST_PASSWORD line has no extra spaces
   → Format should be: EMAIL_HOST_PASSWORD='password'

3. Restart Django after updating
   → Stop the server (Ctrl+C)
   → Run: .\..\\.venv\Scripts\python.exe manage.py runserver
""")
    sys.exit(1)
    
except smtplib.SMTPException as e:
    print(f"\n❌ SMTP ERROR: {e}\n")
    print("""
Check your SMTP settings:
- EMAIL_HOST should be: smtp.gmail.com
- EMAIL_PORT should be: 587
- EMAIL_USE_TLS should be: True
""")
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n")
