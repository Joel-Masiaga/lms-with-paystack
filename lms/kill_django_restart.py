#!/usr/bin/env python
"""
Kill any running Django processes and restart with clean environment
"""
import os
import subprocess
import sys
import time

print("\n" + "=" * 80)
print("DJANGO PROCESS RESET")
print("=" * 80 + "\n")

try:
    # Find and kill Django processes
    print("🔍 Looking for running Django processes...\n")
    
    # Windows command to find and kill python processes on port 8000
    result = subprocess.run(
        'netstat -ano | findstr :8000',
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        print("Found Django process on port 8000:")
        print(result.stdout)
        
        # Extract PID and kill it
        lines = result.stdout.strip().split('\n')
        for line in lines:
            parts = line.split()
            if len(parts) > 0:
                pid = parts[-1]
                print(f"\n🛑 Killing process {pid}...")
                subprocess.run(f'taskkill /PID {pid} /F', shell=True)
                print(f"✓ Process {pid} terminated")
        
        time.sleep(2)
    else:
        print("No Django process found on port 8000")
        print("The server may have already stopped.\n")

except Exception as e:
    print(f"Note: {e}\n")

print("\n" + "=" * 80)
print("NEXT STEPS")
print("=" * 80)
print("""
1. Run this command to start a FRESH Django server:

   .\..\\.venv\Scripts\python.exe manage.py runserver

2. Open your browser and go to: http://localhost:8000/admin/

3. Navigate to: Email Communication → Promotional Emails

4. Send a test promotional email

5. Check the logs - it should show:
   ✅ "X emails sent successfully"

If you still see authentication errors:
   - Your .env password is not being loaded
   - Check .env trailing spaces
   - Try manually restarting Windows PowerShell as well
""")
print("=" * 80 + "\n")
