# Email Verification System - Implementation Guide

## Overview
A comprehensive email verification system has been implemented for user registration. New users must verify their email address before they can log in or access platform features.

## Features Implemented

### 1. **Email Verification on Signup**
- Users receive a verification email after registration
- Email contains a unique verification link with token
- Token expires after 7 days
- Unverified users cannot log in

### 2. **Database Models**
- **User Model Update**: Added `is_email_verified` boolean field (default: False)
- **EmailVerification Model**: Stores verification tokens and status
  - `user`: OneToOne relationship to User
  - `token`: Unique verification token (UUID-based)
  - `is_verified`: Boolean flag for verification status
  - `created_at`: Timestamp when token was created
  - `expires_at`: Timestamp when token expires (7 days)

### 3. **Views & Logic**

#### Registration Flow:
1. User submits registration form
2. New User account created with `is_email_verified = False`
3. EmailVerification record created with unique token
4. Verification email sent to user's email address
5. User redirected to "Check Email" page
6. User clicks link in email to verify

#### Login Flow:
1. User enters email and password
2. If credentials valid AND email is verified → Login successful
3. If credentials valid BUT email NOT verified → Redirect to verification page with message

#### Email Verification:
1. User clicks verification link
2. Token validated (exists and not expired)
3. User marked as verified
4. User can now log in

### 4. **Views Created**

```python
register()                      # Updated to create verification tokens
custom_login()                  # Updated to check email verification
custom_logout()                 # Unchanged
verify_email_pending()          # Shows "Check your email" page
verify_email(token)             # Processes verification token
resend_verification_email()     # Allows users to request new token
send_verification_email()       # Helper function to send emails
```

### 5. **Decorator for Protected Views**
```python
@email_verification_required    # Ensures user email is verified
```

Use this decorator on views that should only be accessible to verified users:
```python
@login_required
@email_verification_required
def protected_view(request):
    # Only verified logged-in users can access
    pass
```

### 6. **URL Routes**
```
/register/                          - User registration form
/login/                             - User login
/verify-email/                      - Pending verification page
/verify-email/<token>/              - Email verification endpoint
/resend-verification/               - Resend verification email form
```

### 7. **Email Templates**
- **verify_email_pending.html**: Shows "Verification sent" page
- **resend_verification.html**: Form to request new verification email

## How to Use

### For Users:

#### 1. Sign Up:
```
1. Go to /register/
2. Enter email and password
3. Click "Register"
4. See "Check your email" message
5. Check inbox for verification email
6. Click verification link
7. Email is now verified
8. Log in with credentials
```

#### 2. Resend Verification (if email lost):
```
1. Go to /resend-verification/
2. Enter email address
3. New verification email sent
4. Click link in new email
```

### For Developers:

#### Protect Views (require verified email):
```python
from users.views import email_verification_required
from django.contrib.auth.decorators import login_required

@login_required
@email_verification_required
def my_view(request):
    # User must be logged in AND email verified
    return render(request, 'template.html')
```

#### Check Verification Status:
```python
user = request.user

if user.is_email_verified:
    # User email is verified
    pass
else:
    # User email not yet verified
    pass
```

#### Manual Verification (admin override):
```python
user = User.objects.get(email='user@example.com')
user.is_email_verified = True
user.save()

# Also update EmailVerification record
verification = user.email_verification
verification.is_verified = True
verification.save()
```

## Admin Panel Features

### User List:
- New column: "Is Email Verified" (shows checkmark for verified)
- New filter: Filter by email verification status
- New field: Email verification status in user details

### Email Verification Panel:
- View all verification tokens
- See verification status (Verified, Pending, Expired)
- Token expiration dates
- Resend or manually verify users

### Direct Management:
```python
# Via Django admin
1. Go to Users → User list
2. Click on user
3. Check "Is Email Verified" to mark as verified
4. Save
```

## Testing the System

### Test Scenario 1: New User Registration
```bash
1. Start Django server: python manage.py runserver
2. Go to http://localhost:8000/register/
3. Fill form with test email
4. Submit
5. Check email verification logs
6. Use test_send_email.py to verify emails work
7. Try to login (should fail with "verify email" message)
```

### Test Scenario 2: Email Verification
```bash
1. From previous test, get verification link
2. Click or paste link in browser
3. Should see "Email verified successfully"
4. Now login should work
```

### Test Scenario 3: Resend Link
```bash
1. Register with test email
2. Click "Resend Verification" link
3. Enter email address
4. Should receive new email with new link
5. Old link should not work
```

## Database Queries

### Check unverified users:
```python
from users.models import User

unverified = User.objects.filter(is_email_verified=False)
for user in unverified:
    print(f"{user.email} - Verified: {user.is_email_verified}")
```

### Check expired tokens:
```python
from users.models import EmailVerification
from django.utils import timezone

expired = EmailVerification.objects.filter(
    is_verified=False,
    expires_at__lt=timezone.now()
)
```

### Manually verify user:
```python
from users.models import User

user = User.objects.get(email='user@example.com')
user.email_verification.verify()
```

## Email Configuration

The system uses settings from `.env`:
- `EMAIL_BACKEND` = 'django.core.mail.backends.smtp.EmailBackend'
- `EMAIL_HOST` = 'smtp.gmail.com'
- `EMAIL_PORT` = 587
- `EMAIL_HOST_USER` = Gmail address
- `EMAIL_HOST_PASSWORD` = Gmail app password
- `EMAIL_USE_TLS` = True
- `DEFAULT_FROM_EMAIL` = Sender email

**Verification emails will only send if email configuration is correct!**

## Troubleshooting

### Issue: Token seems invalid/expired immediately
**Solution**: Check `INSTALLED_APPS` has `'users'` app registered

### Issue: Users can't receive verification emails
**Solution**: 
1. Run `.\..\\.venv\Scripts\python.exe test_send_email.py` to test SMTP
2. Check email configuration in settings.py and .env
3. Verify PASSWORD is app-specific password (not regular Gmail password)

### Issue: "Verification link has expired"
**Solution**: Tokens are valid for 7 days. Use "Resend Verification" to get new token.

### Issue: User cannot log in even after verifying
**Solution**: Restart Django server to reload data. Check admin to confirm `is_email_verified = True`

## Security Notes

- Tokens are UUID-based, cryptographically secure
- Tokens are unique per user (OneToOne relationship)
- Tokens expire after 7 days
- Users can resend unlimited times
- Old tokens are invalidated on resend
- Verification emails include timestamp and expiration info

## Future Enhancements

Potential improvements:
1. Add rate limiting to prevent email spam attacks
2. Add CAPTCHA to registration/resend forms
3. Send reminder emails before token expiration
4. Log verification attempts for audit trail
5. Add SMS verification as alternative
6. Implement two-factor authentication
7. Add email change confirmation

## Migration Info

Migration File: `users/migrations/0011_email_verification.py`

To view migration:
```bash
python manage.py showmigrations users
python manage.py sqlmigrate users 0011_email_verification
```

To rollback (if needed):
```bash
python manage.py migrate users 0008_notification
```

---

**System Status**: ✅ **FULLY IMPLEMENTED AND TESTED**
