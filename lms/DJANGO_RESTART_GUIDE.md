# DJANGO SERVER RESTART GUIDE - CRITICAL

## ⚠️ YOUR GMAIL PASSWORD IS CORRECT

The diagnostic testing confirms:
- ✅ Gmail SMTP credentials are VALID
- ✅ Email authentication WORKS
- ✅ Test emails SEND successfully

**The only issue:** Your running Django server has the OLD password cached in memory.

---

## 🔧 COMPLETE FIX PROCEDURE

### Step 1: Open PowerShell (NEW WINDOW)
Do NOT use the terminal where Django is running.

```powershell
# Open NEW PowerShell window
Start → Type "PowerShell" → Open
```

### Step 2: Kill Running Django Process
```powershell
# Find and kill Django on port 8000
netstat -ano | findstr :8000

# Kill the process (replace XXXX with the PID from above)
taskkill /PID XXXX /F
```

### Step 3: Verify .env File
```powershell
# Navigate to lms folder
cd c:\Users\USER\Desktop\amsun-web\paystacklms\lms

# Check .env content
cat .env | findstr EMAIL
```

Output should look like:
```
EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST='smtp.gmail.com'
EMAIL_PORT=587
EMAIL_HOST_USER='masiagajoel001@gmail.com'
EMAIL_HOST_PASSWORD='tqyn hvma xrni bepf'
EMAIL_USE_TLS=True
```

### Step 4: Start Fresh Django Server
```powershell
cd c:\Users\USER\Desktop\amsun-web\paystacklms\lms

# Activate venv
.\..\\.venv\Scripts\Activate.ps1

# Start Django server
python manage.py runserver
```

You should see:
```
Starting development server at http://127.0.0.1:8000/
```

### Step 5: Test Email Sending
1. Go to: http://localhost:8000/admin/
2. Navigate: Email Communication → Promotional Emails
3. Send a test email
4. Watch the terminal for logs:

**Expected Success Logs:**
```
Starting promotional email campaign
Created X pending email recipient records
Email Config - Backend: django.core.mail.backends.smtp.EmailBackend
Progress: 3 emails sent so far...
Promotional email campaign completed: 9 sent, 0 failed
HTTP POST /email_communication/promotional/preview/ 302
```

**Still Getting Auth Errors?**
```
Failed to send email: (535, b'5.7.8 Username and Password not accepted'
```

If this happens:
1. Check Task Manager → End ALL python.exe processes
2. Close PowerShell completely
3. Open NEW PowerShell
4. Start Django fresh
5. Try again

---

## 🧹 WHAT WAS FIXED

### ✅ .env File Cleaned
- Removed trailing spaces after password
- Fixed spacing in EMAIL_BACKEND line
- Removed trailing blank lines

### ✅ Email Validation Added
Your system now:
- Validates email format before sending
- Skips invalid emails gracefully
- Sends successfully to valid emails
- Logs details about failures

### ✅ Enhanced Logging
Comprehensive logs show:
- Campaign start and recipient count
- Configuration being used
- Progress every 10 emails
- Individual email failures with reasons
- Final summary (X sent, Y failed)

---

## ✅ VERIFICATION CHECKLIST

Before running promotional emails, verify:

- [ ] Ran `test_smtp_direct.py` - shows AUTHENTICATION SUCCESSFUL
- [ ] .env file has correct password (no extra spaces)
- [ ] OLD Django server fully killed (check Task Manager)
- [ ] Started NEW Django with `manage.py runserver`
- [ ] Can see "Starting development server" message
- [ ] Django shows NO auth errors in terminal

---

## 📋 QUICK COMMANDS REFERENCE

```powershell
# Kill Django and restart
netstat -ano | findstr :8000
taskkill /PID XXXX /F

# Navigate to lms folder
cd c:\Users\USER\Desktop\amsun-web\paystacklms\lms

# Activate virtual environment
.\..\\.venv\Scripts\Activate.ps1

# Start Django server (FRESH)
python manage.py runserver

# In ANOTHER terminal - Test SMTP directly
.\..\\.venv\Scripts\python.exe test_smtp_direct.py

# Verify email configuration
.\..\\.venv\Scripts\python.exe verify_email_system.py
```

---

## 🎯 THE FIX IS SIMPLE

**Your credentials are 100% correct.** You just need to:

1. **Kill the old Django process** (with cached old password)
2. **Start a new Django process** (will load fresh .env)
3. **Send your email** (will work!)

That's it! 🚀
