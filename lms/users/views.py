from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.core.exceptions import PermissionDenied
from functools import wraps
from django.contrib.auth import logout
from django.contrib.auth import login, authenticate, get_backends
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserUpdateForm, ProfileUpdateForm
from django.contrib.auth import get_user_model
from .models import SubscribedUser, EmailVerification
from .forms import NewsLetterForm 
from django.contrib import messages
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
import logging
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

User = get_user_model()
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────
# DECORATOR: Check if email is verified
# ─────────────────────────────────────────────────────────────────
def email_verification_required(view_func):
    """Redirect to verify email page if email is not verified"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_email_verified:
            messages.warning(request, 'Please verify your email to continue.')
            return redirect('verify_email_pending')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# Register View
def register(request):
    if request.user.is_authenticated:
        if not getattr(request.user, 'is_email_verified', False):
            return redirect('verify_email_pending')
        return redirect('home')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'student'
            user.is_active = True  # User is active but not verified via email
            user.save()

            # Create email verification record
            email_verification, created = EmailVerification.objects.get_or_create(user=user)
            
            # Send verification email with OTP
            send_verification_email(request, user, email_verification)
            
            messages.success(request, f"Registration successful! A verification code has been sent to {user.email}. Please check your email.")
            return redirect('verify_email_pending')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

# Login View
def custom_login(request):
    if request.user.is_authenticated:
        if not getattr(request.user, 'is_email_verified', False):
            messages.warning(request, "Please verify your email first.")
            return redirect('verify_email_pending')
        return redirect('home')
        
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')  # email used as username
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                # Check if email is verified
                if not user.is_email_verified:
                    messages.warning(request, f"Please verify your email first. Check {user.email} for the verification code.")
                    return redirect('verify_email_pending')
                
                login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])
                messages.success(request, "Login successful. Welcome back!")
                return redirect('home')
            else:
                messages.error(request, "Invalid credentials. Please try again.")
    else:
        form = CustomAuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

def custom_logout(request):
    logout(request)  # Log out the user
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')  # Redirect to the logged_out page

# ─────────────────────────────────────────────────────────────────
# EMAIL VERIFICATION VIEWS
# ─────────────────────────────────────────────────────────────────

def send_verification_email(request, user, email_verification):
    try:
        otp = email_verification.generate_otp()
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        confirm_path = reverse('verify_email_confirm', kwargs={'uidb64': uidb64, 'token': otp})

        # Build absolute URIs, forcing HTTPS for proxied environments like Render
        # SITE_URL env var is the most reliable source; fallback to request object.
        site_url = getattr(settings, 'SITE_URL', '').rstrip('/')
        if site_url:
            direct_verify_url = f"{site_url}{confirm_path}"
            verify_url = f"{site_url}/verify-email/"
        else:
            direct_verify_url = request.build_absolute_uri(confirm_path)
            verify_url = request.build_absolute_uri('/verify-email/')

        # Ensure https:// is used — Render terminates SSL at the load balancer
        direct_verify_url = direct_verify_url.replace('http://', 'https://', 1)
        verify_url = verify_url.replace('http://', 'https://', 1)

        subject = 'Verify Your Email Address - Kuza Ndoto Academy'
        message = f"""
        Hello {user.first_name or user.email},

        Welcome to Kuza Ndoto Academy! Please verify your email address to activate your account.

        Your 6-digit verification code is: {otp}

        To verify your email instantly, click the link below:
        {direct_verify_url}

        Alternatively, you can enter the code manually at our verification page: {verify_url}

        This code will expire in 10 minutes.

        Do not share this code with anyone. If you did not create this account, please ignore this email.

        Best regards,
        Kuza Ndoto Academy Team
        """

        html_message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
            <h2 style="color: #4f46e5;">Welcome to Kuza Ndoto Academy!</h2>
            <p>Hello {user.first_name or user.email},</p>
            <p>Please verify your email address to activate your account.</p>
            
            <p style="font-size: 28px; font-weight: bold; color: #333; letter-spacing: 8px; text-align: center; padding: 20px; background-color: #f8fafc; border-radius: 8px; margin: 30px 0; border: 1px solid #e2e8f0;">
                {otp}
            </p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{direct_verify_url}" style="background-color: #4f46e5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Verify Email Instantly</a>
            </div>

            <p style="text-align: center; font-size: 0.9em; color: #666;">
                Or enter this code manually at our <a href="{verify_url}" style="color: #4f46e5;">verification page</a>.
            </p>

            <p><strong>This code will expire in 10 minutes.</strong></p>
            <p style="color: #dc2626; font-size: 0.9em;"><em>Do not share this code with anyone.</em></p>
            <p style="font-size: 0.8em; color: #999; margin-top: 40px; border-top: 1px solid #eee; padding-top: 20px;">
                If you did not create this account, please ignore this email.
            </p>
        </div>
        """
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [user.email]
        
        email = EmailMultiAlternatives(subject, message, from_email, to_email)
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)
        
        logger.info(f"Verification email sent successfully to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending verification email to {user.email}: {str(e)}", exc_info=True)
        return False

def verify_email_pending(request):
    """Show email verification page to enter OTP"""
    if request.user.is_authenticated and request.user.is_email_verified:
        return redirect('home')
    
    # Handle OTP submission
    if request.method == 'POST':
        otp = request.POST.get('otp', '').strip()
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'Please provide your email address.')
            return render(request, 'users/verify_email_pending.html')
        
        try:
            user = User.objects.get(email=email)
            email_verification = user.otp
            
            if email_verification.is_attempt_limit_exceeded():
                messages.error(request, 'Too many failed attempts. Please request a new verification code.')
                return redirect('resend_verification')
            
            if not email_verification.is_otp_valid():
                messages.error(request, 'Verification code has expired. Please request a new one.')
                return redirect('resend_verification')
            
            if email_verification.verify_otp(otp):
                if request.user.is_authenticated and request.user.email == user.email:
                    messages.success(request, 'Email verified successfully! Welcome.')
                    return redirect('home')
                messages.success(request, 'Email verified successfully! You can now log in to your account.')
                return redirect('login')
            else:
                remaining = 5 - email_verification.attempts
                messages.error(request, f'Invalid verification code. {remaining} attempts remaining.')
                return render(request, 'users/verify_email_pending.html', {'email': email})
        
        except User.DoesNotExist:
            messages.error(request, 'No account found with that email address.')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
    
    return render(request, 'users/verify_email_pending.html')

def verify_email(request, token=None):
    """Legacy route - redirect to OTP verification"""
    messages.info(request, 'Please enter the verification code sent to your email.')
    return redirect('verify_email_pending')

def resend_verification_email(request):
    """Resend verification OTP to user"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        try:
            user = User.objects.get(email=email)
            
            if user.is_email_verified:
                messages.info(request, 'Your email is already verified. You can log in now.')
                return redirect('login')
            
            # Get or create email verification record
            email_verification, created = EmailVerification.objects.get_or_create(user=user)
            
            # Reset attempts and generate new OTP
            email_verification.generate_otp()
            
            # Send verification email with new OTP
            if send_verification_email(request, user, email_verification):
                messages.success(request, f'Verification code sent to {email}. Please check your inbox.')
            else:
                messages.error(request, 'Failed to send verification code. Please try again.')
            
            return redirect('verify_email_pending')
            
        except User.DoesNotExist:
            messages.error(request, 'No account found with that email address.')
    
    return render(request, 'users/resend_verification.html')
@login_required
def profile(request):
    # Check if the user has a profile
    if not hasattr(request.user, 'profile') or request.user.profile is None:
        # If not, redirect them to the profile creation page
        return redirect('profile_create')  # Make sure to create a 'profile_create' view
    
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            return redirect('profile')  # Redirect to the profile page after successful update
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'users/profile.html', context)

@login_required
def profile_create(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES)

        if u_form.is_valid() and p_form.is_valid():
            user = u_form.save()
            profile = p_form.save(commit=False)
            profile.user = user  # Assign the profile to the user
            profile.save()
            return redirect('profile')  # Redirect to the profile page after profile creation
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm()

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'users/profile_create.html', context)

# Subscription viewsfrom django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .models import SubscribedUser, User

@login_required
def subscribe(request):
    if request.method == 'POST':
        user = request.user
        
        # Ensure the user has an email
        if not user.email:
            messages.error(request, "Please update your profile with a valid email before subscribing.")
            return redirect('profile')

        # Validate email format
        try:
            validate_email(user.email)
        except ValidationError:
            messages.error(request, "Your email is invalid. Please update your profile with a valid email before subscribing.")
            return redirect('profile')

        # Check if the email is correctly associated with the logged-in user
        if not User.objects.filter(id=user.id, email=user.email).exists():
            messages.error(request, "Your email does not match our records. Please update your profile with the correct email.")
            return redirect('profile')

        # Avoid duplicate subscriptions
        subscription, created = SubscribedUser.objects.get_or_create(user=user, defaults={'subscribed': True})
        
        if created:
            messages.success(request, "You have successfully subscribed!")
        else:
            messages.info(request, "You are already subscribed.")

    return redirect('home')


@login_required
def unsubscribe(request):
    if request.method == 'POST':
        user = request.user
         
        # Ensure the user has an email
        if not user.email:
            messages.error(request, "Please update your profile with a valid email before unsubscribing.")
            return redirect('profile')

        # Validate email format
        try:
            validate_email(user.email)
        except ValidationError:
            messages.error(request, "Your email is invalid. Please update your profile with a valid email before unsubscribing.")
            return redirect('profile')

        # Check if the email is correctly associated with the logged-in user
        if not User.objects.filter(id=user.id, email=user.email).exists():
            messages.error(request, "Your email does not match our records. Please update your profile with the correct email before unsubscribing.")
            return redirect('profile')

        # Check if the user has a subscription
        subscription = SubscribedUser.objects.filter(user=user)
        if subscription.exists():
            subscription.delete()
            messages.success(request, "You have successfully unsubscribed.")
        else:
            messages.info(request, "You were not subscribed.")

    return redirect('home')


def superuser_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return redirect('home') 
        return view_func(request, *args, **kwargs)
    return wrapper

@superuser_required
def newsletter(request):
    if request.method == 'POST':
        form = NewsLetterForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data.get('subject')
            receivers = form.cleaned_data.get('receivers').split(',')
            message = form.cleaned_data.get('message')
           
           
            mail = EmailMessage(subject, message, f'Soma Online <{request.user.email}>', bcc=receivers)
            mail.content_subtype = 'html'

            if mail.send():
                messages.success(request, "Newsletter sent successfully.")
            else:
                messages.error(request, "Failed to send newsletter.")

        else: 
            for error in list(form.errors.values()):
                messages.error(request, error)
           
        return redirect('home')

    form = NewsLetterForm()
    form.fields['receivers'].initial = ','.join([active.user.email for active in SubscribedUser.objects.all()])
    return render(request=request, template_name='users/newsletter.html', context={'form': form})
        

from django.http import JsonResponse
from django.views.decorators.http import require_POST

@login_required
@require_POST
def mark_tour_seen(request):
    """Called via fetch() when user finishes or skips the onboarding tour."""
    try:
        profile = request.user.profile
        profile.has_seen_tour = True
        profile.save(update_fields=['has_seen_tour'])
        return JsonResponse({'status': 'ok'})
    except Exception:
        return JsonResponse({'status': 'error'}, status=400)


# -------------------------------------------
# Notification Views
# -------------------------------------------
from .models import Notification

@login_required
def mark_notification_read(request, notification_id):
    """Mark a single notification as read and redirect to its link."""
    from django.shortcuts import get_object_or_404
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    if notification.link:
        return redirect(notification.link)
    return redirect('home')


@login_required
@require_POST
def mark_all_notifications_read(request):
    """Mark all unread notifications as read — AJAX/HTMX endpoint."""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'ok'})
def verify_email_confirm(request, uidb64, token):
    """Verify email via one-click link sent in the email"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        email_verification = user.otp

        if hasattr(email_verification, 'is_attempt_limit_exceeded') and email_verification.is_attempt_limit_exceeded():
            messages.error(request, 'Too many failed attempts. Please request a new verification code.')
            return redirect('resend_verification')

        if not email_verification.is_valid():
            messages.error(request, 'Verification link has expired. Please request a new one.')
            return redirect('resend_verification')

        if email_verification.verify_otp(token):
            if request.user.is_authenticated and request.user.email == user.email:
                messages.success(request, 'Email verified successfully! Welcome.')
                return redirect('home')
            messages.success(request, 'Email verified successfully! You can now log in to your account.')
            return redirect('login')
        else:
            remaining = 5 - email_verification.attempts
            messages.error(request, f'Invalid verification link. {remaining} attempts remaining.')
            return redirect('verify_email_pending')

    except (TypeError, ValueError, OverflowError, User.DoesNotExist, AttributeError):
        messages.error(request, 'Invalid or broken verification link. Please check your URL or request a new code.')
        return redirect('verify_email_pending')
