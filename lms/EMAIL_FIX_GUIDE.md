# Email Configuration Troubleshooting & Fix Guide

## Problem
You're getting "Username and Password not accepted" errors when the test script works fine.

## Root Cause
**The Django development server running in your terminal has CACHED the old environment variables in memory.** 

When you:
1. Started Django (`python manage.py runserver`)
2. Django loaded environment variables from .env into memory
3. Changed the password in .env
4. The running Django process still uses the OLD password

The test script works because it runs in a **fresh Python process** that loads the current .env variables.

## Solution: RESTART THE DJANGO SERVER

### Step 1: Stop the Current Server
- Go to the terminal where Django is running
- Press **Ctrl+C** to stop it
- Wait for it to fully shut down (you'll see no more output)

### Step 2: Clear Any .env Caches (Optional)
```powershell
# This helps ensure clean reload
cd c:\Users\USER\Desktop\amsun-web\paystacklms\lms
```

### Step 3: Verify .env Password
Open `.env` and confirm the EMAIL_HOST_PASSWORD line is:
```
EMAIL_HOST_PASSWORD='tqyn hvma xrni bepf'
```

### Step 4: Restart Django with New Variables
```powershell
cd c:\Users\USER\Desktop\amsun-web\paystacklms\lms
.\..\\.venv\Scripts\python.exe manage.py runserver
```

### Step 5: Test Email Sending
- Go to Admin → Promotional Emails
- Send a test email
- Check the results - emails should now be sent successfully

## What Changed in the Code

### Email Validation Added
The system now:
1. **Validates all email addresses** before attempting to send
2. **Skips invalid emails** and logs them as warnings
3. **Continues sending to valid emails** even if some addresses are invalid
4. **Provides detailed logging** of what failed and why

### Benefits
- ✅ Invalid emails don't block the entire campaign
- ✅ Valid emails get delivered successfully
- ✅ Clear logs show which emails were invalid
- ✅ Better error handling and recovery

## Example: Promotional Email with Mixed Valid/Invalid Emails

**Before this fix:**
- All 9 recipients fail → 0 sent, 9 failed ❌

**After this fix:**
- Invalid emails skipped (logged as warnings)
- Valid emails processed and sent ✅
- Campaign continues despite some invalid addresses

## Logs Example
```
Starting promotional email campaign: "Test" to 9 all users
Created 7 pending email recipient records
Found 2 invalid email addresses: invalid@, bad@email
Progress: 3 emails sent so far...
Progress: 6 emails sent so far...
Promotional email campaign completed: 7 sent, 0 failed
```

## If You Still Get "Username and Password Not Accepted"

1. **Double-check the password in .env** - make sure it's the latest app password
2. **Generate a new Gmail app password:**
   - Go to https://myaccount.google.com/apppasswords
   - Select Mail and Windows Computer
   - Copy the 16-character password (with spaces)
   - Update .env and restart Django

3. **Verify Django environment variables:**
   - Run: `.\..\\.venv\Scripts\python.exe diagnose_email.py`
   - Check that EMAIL_HOST_PASSWORD shows the new password

## Quick Test Command
```powershell
# Test in a fresh Python process
cd c:\Users\USER\Desktop\amsun-web\paystacklms\lms
.\..\\.venv\Scripts\python.exe test_send_email.py
```

This test always works because it loads fresh env variables. If THIS fails, your .env password is wrong.

---

**Summary:** Restart Django, and your email system will work perfectly! ✅
