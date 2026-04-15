from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from django_resized import ResizedImageField


# -------------------------
# Custom manager for User model
# -------------------------
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


# -------------------------
# Custom User model with email-based authentication
# -------------------------
class User(AbstractUser):
    email = models.EmailField(unique=True, max_length=255)
    username = None  # We are not using the username field
    is_email_verified = models.BooleanField(default=False)

    ROLE_CHOICES = [
        ('student', 'Student'),
        ('instructor', 'Instructor'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Only email and password are required

    def __str__(self):
        return self.email

    def is_student(self):
        return self.role == 'student'

    def is_instructor(self):
        return self.role == 'instructor'


# -------------------------
# Profile model for storing additional user information
# -------------------------
class Profile(models.Model):
    image = ResizedImageField(size=[600,600], quality=85, default='default.jpg', upload_to='profiles/', blank=True, null=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='profile')

    points = models.PositiveIntegerField(default=0)
    earned_badges = models.ManyToManyField('courses.Course', blank=True, related_name='awarded_to')
    has_seen_tour = models.BooleanField(default=False)

    def __str__(self):
        return f"Profile of {self.first_name or ''} {self.last_name or ''} ({self.user.email})"

    def save(self, *args, **kwargs):
        """
        Handles image resizing safely for both Cloudinary and local storage.
        Avoids using .path, which is unsupported by remote storages.
        """
        super().save(*args, **kwargs)

        if self.image:
            try:
                # Open the image from storage (works for Cloudinary too)
                img_file = self.image.open()
                img = Image.open(img_file)

                # Resize if necessary
                if img.height > 300 or img.width > 300:
                    output_size = (300, 300)
                    img.thumbnail(output_size)

                    # Save resized image into memory
                    buffer = BytesIO()
                    img.save(buffer, format='JPEG')
                    buffer.seek(0)

                    # Replace old image with resized one
                    self.image.save(self.image.name, ContentFile(buffer.read()), save=False)
                    super().save(*args, **kwargs)
            except Exception as e:
                print(f"Image processing failed: {e}")

    @property
    def is_complete(self):
        return bool((self.first_name or "").strip() and (self.last_name or "").strip())


# -------------------------
# Subscription model for storing user subscriptions
# -------------------------
class SubscribedUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    created_at = models.DateTimeField(auto_now_add=True)
    subscribed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} - Subscribed: {self.subscribed}"

import random
from django.utils import timezone
from datetime import timedelta

class OTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='otp')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    attempts = models.PositiveIntegerField(default=0, help_text='Number of failed OTP attempts')
    is_verified = models.BooleanField(default=False)

    def generate_code(self):
        self.code = f"{random.randint(100000, 999999)}"
        self.created_at = timezone.now()
        self.attempts = 0
        self.save()
        return self.code

    def is_valid(self):
        # OTP is valid for 10 minutes
        return not self.is_verified and timezone.now() < (self.created_at + timedelta(minutes=10))

    def __str__(self):
        return f"OTP for {self.user.email}"
        
    # Wrappers for existing logic in views.py if any:
    def generate_otp(self):
        return self.generate_code()
        
    def is_otp_valid(self):
        return self.is_valid()
        
    def verify_otp(self, entered_otp):
        """Verify OTP and mark email as verified"""
        if not self.is_valid() or str(entered_otp) != str(self.code):
            self.attempts += 1
            self.save()
            return False
            
        # OTP is correct
        self.is_verified = True
        self.attempts = 0
        self.save()
        self.user.is_email_verified = True
        self.user.save()
        return True

    def is_attempt_limit_exceeded(self, limit=5):
        return self.attempts >= limit

# Alias for compatibility if still used anywhere
EmailVerification = OTP

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.URLField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recipient.email} - {self.title}"
