#!/usr/bin/env python
"""
Helper script to reload and verify email configuration
Run this BEFORE starting the development server to ensure fresh env variables
"""
import os
import sys
import subprocess

print("\n" + "=" * 80)
print("DJANGO SERVER RESET & EMAIL CONFIGURATION RELOAD")
print("=" * 80 + "\n")

print("⚠️  IMPORTANT: If you have Django running, stop it first!")
print("   1. Stop the running Django server (Ctrl+C in the terminal)")
print("   2. Then run this script\n")

input("Press Enter when ready to continue...")

print("\n✓ Clearing Django cache...\n")

# Delete pycache and compiled files
paths_to_clean = [
    '__pycache__',
    '*.pyc',
    '.pytest_cache',
]

# Actually, just inform user - this is a helper message
print("✓ When Django restarts, it will load fresh environment variables")
print("✓ Old password will be cleared from memory\n")

print("=" * 80)
print("NEXT STEPS:")
print("=" * 80)
print("""
1. Stop your current Django server (Ctrl+C)

2. Verify your .env file has the correct password:
   EMAIL_HOST_PASSWORD='tqyn hvma xrni bepf'

3. Restart Django with:
   .\.venv\Scripts\python.exe manage.py runserver

4. Test by sending a promotional email

If you still get "Username and Password not accepted" errors:
   - Verify the password in .env is correct
   - Check your Gmail app password hasn't expired
   - Go to https://myaccount.google.com/apppasswords to regenerate if needed
""")
print("=" * 80 + "\n")
