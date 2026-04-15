from django.db import models
from django.utils import timezone
from users.models import User
from courses.models import Course


class EmailLog(models.Model):
    """Log of all sent emails for auditing purposes."""
    EMAIL_TYPE_CHOICES = [
        ('course_announcement', 'Course Announcement'),
        ('promotional', 'Promotional'),
        ('other', 'Other'),
    ]
    
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_emails')
    email_type = models.CharField(max_length=20, choices=EMAIL_TYPE_CHOICES)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='announcement_emails')
    recipients_count = models.IntegerField(default=0, help_text='Number of recipients')
    sent_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['sender', '-sent_at']),
            models.Index(fields=['email_type']),
        ]
    
    def __str__(self):
        return f"{self.get_email_type_display()} from {self.sender.email} - {self.subject}"


class EmailRecipient(models.Model):
    """Track individual email delivery."""
    DELIVERY_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]
    
    email_log = models.ForeignKey(EmailLog, on_delete=models.CASCADE, related_name='recipients')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_emails')
    status = models.CharField(max_length=10, choices=DELIVERY_STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True, default=None)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('email_log', 'recipient')
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['recipient', '-sent_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.email_log.subject} → {self.recipient.email}"
