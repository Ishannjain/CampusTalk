from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator


# Role choices for user types
ROLE_CHOICES = [
    ('student', 'Student'),
    ('moderator', 'Moderator'),
    ('admin', 'Administrator'),
]


class User(AbstractUser):
    """Extended User model with role-based access control"""
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student',
        help_text='User role determining permissions and capabilities'
    )
    is_verified = models.BooleanField(
        default=False,
        help_text='Whether the user has verified their college email'
    )
    
    class Meta:
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_admin(self):
        """Check if user has admin role"""
        return self.role == 'admin'
    
    def is_moderator(self):
        """Check if user is moderator or admin"""
        return self.role in ['moderator', 'admin']
    
    def is_student(self):
        """Check if user has student role"""
        return self.role == 'student'


class CommonPost(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=140, blank=True)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author.username}: {self.body[:40]}"


class Comment(models.Model):
    post = models.ForeignKey(CommonPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.id}"


class ChatMessage(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_common = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        if self.is_common:
            return f"Common chat by {self.sender.username}: {self.message[:30]}"
        return f"Private chat {self.sender.username} -> {self.recipient.username if self.recipient else 'None'}"


# Content Moderation Models
REPORT_STATUS_CHOICES = [
    ('pending', 'Pending Review'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('resolved', 'Resolved'),
]

REPORT_REASON_CHOICES = [
    ('spam', 'Spam'),
    ('inappropriate', 'Inappropriate Content'),
    ('harassment', 'Harassment/Bullying'),
    ('misinformation', 'Misinformation'),
    ('plagiarism', 'Plagiarism'),
    ('off_topic', 'Off Topic'),
    ('other', 'Other'),
]


class ContentReport(models.Model):
    """Model for reporting inappropriate content"""
    post = models.ForeignKey(
        CommonPost,
        on_delete=models.CASCADE,
        related_name='reports',
        help_text='The post being reported'
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_reports',
        help_text='User who submitted the report'
    )
    reason = models.CharField(
        max_length=50,
        choices=REPORT_REASON_CHOICES,
        help_text='Reason for reporting'
    )
    description = models.TextField(
        blank=True,
        help_text='Additional details about the report'
    )
    status = models.CharField(
        max_length=20,
        choices=REPORT_STATUS_CHOICES,
        default='pending',
        help_text='Current status of the report'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_reports',
        help_text='Moderator/Admin who reviewed this report'
    )
    review_notes = models.TextField(
        blank=True,
        help_text='Notes from the moderator/admin'
    )

    class Meta:
        ordering = ['-created_at']
        unique_together = ('post', 'reporter')  # One report per user per post

    def __str__(self):
        return f"Report of '{self.post.id}' by {self.reporter.username} - {self.get_status_display()}"