from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Q
from .models import User, CommonPost, Comment, ChatMessage, ContentReport, ROLE_CHOICES


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Admin interface for user management with role-based access control"""
    list_display = ['username', 'get_role_badge', 'is_verified', 'date_joined']
    list_filter = ['role', 'is_verified', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        ('Account Information', {
            'fields': ('username', 'email', 'first_name', 'last_name')
        }),
        ('Role & Status', {
            'fields': ('role', 'is_verified'),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': ('is_staff', 'is_superuser', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['make_moderator', 'make_admin', 'make_student', 'verify_user', 'unverify_user']
    
    def get_role_badge(self, obj):
        """Display role with color-coded badge"""
        colors = {
            'admin': '#dc3545',      # red
            'moderator': '#ffc107',  # yellow
            'student': '#28a745',    # green
        }
        color = colors.get(obj.role, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_role_display()
        )
    get_role_badge.short_description = 'Role'
    
    def make_moderator(self, request, queryset):
        """Batch action to promote users to moderator"""
        updated = queryset.update(role='moderator')
        self.message_user(request, f'{updated} user(s) promoted to Moderator.')
    make_moderator.short_description = 'Promote selected users to Moderator'
    
    def make_admin(self, request, queryset):
        """Batch action to promote users to admin"""
        updated = queryset.update(role='admin')
        self.message_user(request, f'{updated} user(s) promoted to Administrator.')
    make_admin.short_description = 'Promote selected users to Administrator'
    
    def make_student(self, request, queryset):
        """Batch action to demote users to student"""
        updated = queryset.update(role='student')
        self.message_user(request, f'{updated} user(s) downgraded to Student.')
    make_student.short_description = 'Downgrade selected users to Student'
    
    def verify_user(self, request, queryset):
        """Batch action to verify users"""
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} user(s) verified.')
    verify_user.short_description = 'Verify selected users'
    
    def unverify_user(self, request, queryset):
        """Batch action to unverify users"""
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} user(s) unverified.')
    unverify_user.short_description = 'Unverify selected users'


@admin.register(ContentReport)
class ContentReportAdmin(admin.ModelAdmin):
    """Admin interface for content moderation and reporting"""
    list_display = ['id', 'post', 'reporter', 'reason', 'get_status_badge', 'created_at', 'reviewed_by']
    list_filter = ['status', 'reason', 'created_at']
    search_fields = ['reporter__username', 'reason', 'description']
    ordering = ['-created_at']
    readonly_fields = ['post', 'reporter', 'reason', 'description', 'created_at']
    
    fieldsets = (
        ('Report Information', {
            'fields': ('post', 'reporter', 'reason', 'description', 'created_at')
        }),
        ('Review Status', {
            'fields': ('status', 'reviewed_by', 'review_notes')
        }),
    )
    
    actions = ['approve_report', 'reject_report', 'mark_resolved']
    
    def get_status_badge(self, obj):
        """Display status with color-coded badge"""
        colors = {
            'pending': '#ffc107',    # yellow
            'approved': '#dc3545',   # red
            'rejected': '#28a745',   # green
            'resolved': '#007bff',   # blue
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    get_status_badge.short_description = 'Status'
    
    def approve_report(self, request, queryset):
        """Action to approve reports and flag posts"""
        updated = queryset.update(status='approved', reviewed_by=request.user)
        self.message_user(request, f'{updated} report(s) approved.')
    approve_report.short_description = 'Approve selected reports'
    
    def reject_report(self, request, queryset):
        """Action to reject reports"""
        updated = queryset.update(status='rejected', reviewed_by=request.user)
        self.message_user(request, f'{updated} report(s) rejected.')
    reject_report.short_description = 'Reject selected reports'
    
    def mark_resolved(self, request, queryset):
        """Action to mark reports as resolved"""
        updated = queryset.update(status='resolved', reviewed_by=request.user)
        self.message_user(request, f'{updated} report(s) marked as resolved.')
    mark_resolved.short_description = 'Mark selected reports as resolved'


# @admin.register(UserRanking)
class UserRankingAdmin(admin.ModelAdmin):
    """Admin interface for viewing user rankings and statistics"""
    list_display = ['get_rank', 'user', 'get_user_role', 'total_posts', 'total_comments', 'helpful_comments', 'violations', 'last_activity']
    list_filter = ['user__role', 'violations', 'last_activity']
    search_fields = ['user__username', 'user__email']
    ordering = ['user__points', 'user__reputation_score']
    readonly_fields = ['user', 'total_posts', 'total_comments', 'helpful_comments', 'reports_submitted', 'violations', 'last_activity', 'created_at']
    
    actions = ['update_rankings']
    
    def get_rank(self, obj):
        """Display user's rank"""
        rank = obj.get_rank()
        return format_html(
            '<span style="font-weight: bold; color: #007bff; font-size: 14px;">#{}</span>',
            rank
        )
    get_rank.short_description = 'Rank'
    
    def get_user_role(self, obj):
        """Display user's role with badge"""
        colors = {
            'admin': '#dc3545',
            'moderator': '#ffc107',
            'student': '#28a745',
        }
        color = colors.get(obj.user.role, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.user.get_role_display()
        )
    get_user_role.short_description = 'Role'
    
    def update_rankings(self, request, queryset):
        """Batch action to update ranking metrics"""
        for ranking in queryset:
            ranking.update_metrics()
        self.message_user(request, f'{queryset.count()} ranking(s) updated.')
    update_rankings.short_description = 'Update metrics for selected rankings'


@admin.register(CommonPost)
class CommonPostAdmin(admin.ModelAdmin):
    """Admin interface for managing posts"""
    list_display = ['id', 'author', 'get_author_role', 'get_excerpt', 'created_at', 'get_report_count']
    list_filter = ['created_at', 'author__role']
    search_fields = ['author__username', 'body', 'title']
    ordering = ['-created_at']
    readonly_fields = ['author', 'created_at', 'get_report_info']
    
    def get_author_role(self, obj):
        """Display author's role"""
        colors = {
            'admin': '#dc3545',
            'moderator': '#ffc107',
            'student': '#28a745',
        }
        color = colors.get(obj.author.role, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.author.get_role_display()
        )
    get_author_role.short_description = 'Author Role'
    
    def get_excerpt(self, obj):
        """Display excerpt of post"""
        return obj.body[:100] + '...' if len(obj.body) > 100 else obj.body
    get_excerpt.short_description = 'Excerpt'
    
    def get_report_count(self, obj):
        """Display number of reports for this post"""
        count = obj.reports.filter(status='pending').count()
        if count > 0:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{} pending</span>',
                count
            )
        return 'Clear'
    get_report_count.short_description = 'Reports'
    
    def get_report_info(self, obj):
        """Display detailed report information"""
        reports = obj.reports.all()
        if not reports:
            return 'No reports'
        html = '<ul>'
        for report in reports:
            html += f'<li>{report.reason} - {report.get_status_display()} by {report.reporter.username}</li>'
        html += '</ul>'
        return format_html(html)
    get_report_info.short_description = 'Report Information'


admin.site.register(Comment)
admin.site.register(ChatMessage)