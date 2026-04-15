from django.db import models
from django.utils import timezone
from django_resized import ResizedImageField
from users.models import User
from courses.models import Course


class UserOnlineStatus(models.Model):
    """Track user online status for real-time features."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='online_status')
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "User Online Statuses"
    
    def __str__(self):
        return f"{self.user.email} - {'Online' if self.is_online else 'Offline'}"
    
    def set_online(self):
        """Mark user as online."""
        self.is_online = True
        self.last_seen = timezone.now()
        self.save()
    
    def set_offline(self):
        """Mark user as offline."""
        self.is_online = False
        self.save()


class DirectMessage(models.Model):
    """One-on-one direct messages between users."""
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField(blank=True, default='')
    attachment = models.FileField(upload_to='message_attachments/%Y/%m/%d/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender', 'recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.sender.username} → {self.recipient.username}"


class Conversation(models.Model):
    """Track direct message conversations between two users."""
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_message_at']
    
    def __str__(self):
        participants_str = ', '.join([u.username for u in self.participants.all()])
        return f"Conversation: {participants_str}"


class CommunityGroup(models.Model):
    """Community groups for discussion."""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    icon = ResizedImageField(size=[400,400], quality=85, upload_to='group_icons/%Y/%m/%d/', null=True, blank=True)
    creator = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_groups')
    members = models.ManyToManyField(User, related_name='joined_groups', through='GroupMember')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class GroupMember(models.Model):
    """Track membership in community groups."""
    ROLE_CHOICES = [
        ('admin', 'Group Admin'),
        ('member', 'Member'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(CommunityGroup, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'group']
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.group.name}"


class GroupMessage(models.Model):
    """Messages posted in community groups."""
    group = models.ForeignKey(CommunityGroup, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.PROTECT, related_name='group_messages')
    content = models.TextField(blank=True, default='')
    attachment = models.FileField(upload_to='message_attachments/%Y/%m/%d/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['group', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.sender.username} @ {self.group.name}"


class CourseBroadcast(models.Model):
    """Instructors can broadcast messages to their course participants."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='broadcasts')
    instructor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='course_broadcasts')
    subject = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.course.title} - {self.subject}"


class GroupInvitation(models.Model):
    """Shareable invitations for groups - members can invite others."""
    import uuid
    
    group = models.ForeignKey(CommunityGroup, on_delete=models.CASCADE, related_name='invitations')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_invitations_sent')
    invitee = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='group_invitations_received')
    
    # Shareable link code (for public sharing)
    invite_code = models.CharField(max_length=20, unique=True, db_index=True)
    
    # Status tracking
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Tracking dates
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # Invitations expire after 30 days
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    message = models.TextField(blank=True, help_text="Optional message with the invitation")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['group', 'status']),
            models.Index(fields=['invite_code']),
            models.Index(fields=['invitee', 'status']),
        ]
    
    def __str__(self):
        return f"Invite to {self.group.name} by {self.created_by.username}"
    
    def is_valid(self):
        """Check if invitation is still valid (not expired and not declined/accepted)."""
        from django.utils import timezone
        if self.status != 'pending':
            return False
        if timezone.now() > self.expires_at:
            return False
        return True
