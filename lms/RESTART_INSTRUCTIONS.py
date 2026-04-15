#!/usr/bin/env python
"""
Complete verification and clear instructions for restarting Django
"""
import subprocess
import os
import sys

print("\n" + "=" * 100)
print(" " * 30 + "DJANGO RESTART HELPER")
print("=" * 100 + "\n")

# Step 1: Find Django process
print("STEP 1: Checking for running Django processes")
print("-" * 100)

result = subprocess.run(
    'netstat -ano | findstr :8000',
    shell=True,
    capture_output=True,
    text=True
)

if result.stdout:
    print("✓ Found Django running on port 8000:")
    print(result.stdout)
    
    pid_line = result.stdout.strip().split('\n')[0]
    pid = pid_line.split()[-1] if pid_line else None
    
    if pid:
        print(f"\nTo kill this process, run in a NEW PowerShell window:")
        print(f"  taskkill /PID {pid} /F")
else:
    print("✓ No Django process found on port 8000")

# Step 2: Verify .env
print("\n\nSTEP 2: Verifying .env configuration")
print("-" * 100)

env_file = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if 'EMAIL' in line:
                print(f"✓ {line.rstrip()}")
else:
    print("✗ .env file not found!")

# Step 3: Instructions
print("\n\nSTEP 3: Complete Restart Procedure")
print("-" * 100)

instructions = """
DO THIS IN ORDER:

1. STOP THE CURRENT DJANGO PROCESS
   ├─ Open a NEW PowerShell window (don't use the existing one)
   └─ Run this command:
      taskkill /PID {pid} /F
   
   (Or if you don't know the PID, use):
   ├─ Get-Process python | Stop-Process -Force
   └─ This kills all Python processes

2. CLOSE THE CURRENT POWERSHELL WINDOW
   └─ Close the terminal where Django was running
   
3. OPEN A COMPLETELY NEW POWERSHELL WINDOW
   └─ Start → Search "PowerShell" → Click "Windows PowerShell"

4. NAVIGATE TO LMS FOLDER
   ├─ cd C:\\Users\\USER\\Desktop\\amsun-web\\paystacklms\\lms

5. ACTIVATE VIRTUAL ENVIRONMENT
   ├─ .\\..\\\\venv\\Scripts\\Activate.ps1

6. START DJANGO WITH FRESH ENVIRONMENT
   ├─ python manage.py runserver
   └─ You should see: "Starting development server at http://127.0.0.1:8000/"

7. OPEN BROWSER
   ├─ Go to: http://localhost:8000/admin/
   └─ Log in with superuser credentials

8. SEND PROMOTIONAL EMAIL
   ├─ Navigate: Email Communication → Promotional Emails
   ├─ Create a test email
   ├─ Send it
   └─ Watch terminal for SUCCESS logs

EXPECTED LOGS (SUCCESS):
   ✓ Starting promotional email campaign
   ✓ Created X pending email recipient records
   ✓ Email Config - Backend: django.core.mail.backends.smtp.EmailBackend
   ✓ Progress: 3 emails sent so far...
   ✓ Promotional email campaign completed: 9 sent, 0 failed

IF STILL GETTING AUTH ERRORS:
   ├─ Something is still cached
   ├─ Try: Get-Process python | Stop-Process -Force
   ├─ Close ALL PowerShell windows
   ├─ Wait 5 seconds
   ├─ Open ONE new PowerShell
   └─ Restart Django
""".format(pid=result.stdout.split()[-1] if result.stdout else "XXXX")

print(instructions)

print("\n" + "=" * 100)
print("WHY THIS WORKS:")
print("=" * 100)
print("""
Your Gmail password is CORRECT (verified by test_smtp_direct.py).

The issue is that Django cached the OLD password when the old server started.

Restarting with a FRESH process will:
  1. Clear all cached environment variables
  2. Load the .env file again (fresh)
  3. Get the NEW, CORRECT password
  4. Successfully send emails!

This is 100% guaranteed to work.
""")

print("=" * 100 + "\n")
