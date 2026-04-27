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
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
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


# ============================================================================
# NEW GENERIC REPORT SYSTEM MODELS
# ============================================================================

GENERIC_REPORT_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('under_review', 'Under Review'),
    ('resolved', 'Resolved'),
    ('rejected', 'Rejected'),
]

GENERIC_REPORT_REASON_CHOICES = [
    ('spam', 'Spam'),
    ('harassment', 'Harassment / Abuse'),
    ('hate_speech', 'Hate Speech'),
    ('misinformation', 'Misinformation'),
    ('inappropriate', 'Inappropriate Content'),
    ('other', 'Other'),
]

TARGET_TYPE_CHOICES = [
    ('post', 'Post'),
    ('comment', 'Comment'),
    ('user', 'User Profile'),
]

class Report(models.Model):
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_made')
    target_type = models.CharField(max_length=20, choices=TARGET_TYPE_CHOICES)
    target_id = models.IntegerField()
    reason = models.CharField(max_length=50, choices=GENERIC_REPORT_REASON_CHOICES)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=GENERIC_REPORT_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report ({self.reason}) by {self.reporter.username} on {self.target_type}:{self.target_id}"

class ModerationAction(models.Model):
    ACTION_CHOICES = [
        ('warn', 'Warn User'),
        ('delete_content', 'Delete Content'),
        ('ban_user', 'Ban User'),
        ('ignore', 'Ignore / Reject Report'),
    ]
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='actions')
    moderator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='moderation_actions')
    action_taken = models.CharField(max_length=30, choices=ACTION_CHOICES)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        mod_name = self.moderator.username if self.moderator else 'Unknown'
        return f"{self.get_action_taken_display()} by {mod_name} for Report {self.report.id}"

class SystemNotification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient.username} (Read: {self.is_read})"


# ============================================================================
# COMMUNITY MODULE MODELS
# ============================================================================

class Community(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_communities')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Communities"

    def __str__(self):
        return self.name

class CommunityPost(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='community_posts')
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    image = models.ImageField(upload_to='community_posts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_anonymous = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Post by {self.user.username} in {self.community.name} (Anonymous: {self.is_anonymous})"

class CommunityPostLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f"{self.user.username} liked Post {self.post.id}"

class PostLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(CommonPost, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')

class CommentLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'comment')