# Campus Connect - Ranking-Based Role System Documentation

## System Overview

Campus Connect now includes a comprehensive ranking-based role system with role-based access control (RBAC), content moderation, and user reputation tracking. This system enables admins to manage the platform effectively with different user roles and levels of responsibility.

## User Roles

### 1. **Student** (Default Role)
The standard user role for college students and faculty.

**Capabilities:**
- Create academic posts and doubts
- Comment on posts
- Like/interact with content
- Report inappropriate content
- View leaderboard and rankings
- Participate in common chat

**Points & Rewards:**
- +5 points for creating a post
- +2 points for reporting content
- Reputation score based on contributions

**Restrictions:**
- Must verify email to create posts
- Can be temporarily restricted for violations

---

### 2. **Moderator**
Trusted users/staff responsible for content review and community management.

**Capabilities:**
- All Student capabilities
- Access moderation dashboard
- Review reported content
- Approve or reject reports
- Add review notes to reports
- Mark reports as resolved
- Search and filter reports

**Responsibilities:**
- Review content complaints
- Enforce community guidelines
- Document violations
- Maintain community standards

---

### 3. **Administrator**
System administrators with full control over the platform.

**Capabilities:**
- All Moderator capabilities
- Access admin panel
- Promote/demote users between roles
- View system statistics
- Manage staff members
- Suspend/unsuspend accounts
- Verify users
- Warn users with point penalties
- View comprehensive system reports

**Dashboard Includes:**
- User distribution statistics
- Report status overview
- Recent moderation activity
- Staff management tools

---

## Ranking & Points System

### Points Calculation

Users earn points for various contributions:

| Action | Points |
|--------|--------|
| Create a post | +5 |
| Submit a valid report | +2 |
| Community guideline violation | -10 |
| Warning from admin | -5 |

### Reputation Score

Reputation is calculated as a percentage (0-100) based on:

```
Base Score = min(points / 10, 100)
Post Bonus = min(posts_count * 5, 50)
Comment Bonus = min(comments_count * 2, 30)

Total Reputation = min(base_score + post_bonus + comment_bonus, 100)
```

### Leaderboard

Users are ranked globally based on:
1. Points (primary)
2. Reputation Score (secondary)

Top rankings display with medals:
- 🥇 #1 (Gold)
- 🥈 #2 (Silver)
- 🥉 #3 (Bronze)

---

## Content Reporting & Moderation

### Report Reasons

Users can report content for:
- **Spam** - Repetitive or unsolicited content
- **Inappropriate Content** - Offensive or indecent material
- **Harassment/Bullying** - Targeted attacks on users
- **Misinformation** - False or misleading information
- **Plagiarism** - Copied content without attribution
- **Off-Topic** - Content not related to campus/academics
- **Other** - Additional reasons (with description)

### Report Workflow

1. **User submits report** with reason and optional description
2. **Moderator reviews** in moderation dashboard
3. **Action Taken:**
   - **Approve**: Post flagged, author penalized (-10 points, violation recorded)
   - **Reject**: Report dismissed
   - **Resolve**: Issue handled, report closed

### Report Statistics

Track reports by status:
- **Pending** - Awaiting review
- **Approved** - Content violation confirmed
- **Rejected** - Found to be compliant
- **Resolved** - Action taken and closed

---

## Admin Panel Features

### System Statistics
- Total users count
- Verified vs unverified users
- Role distribution
- Pending reports count

### Staff Management
- View all moderators and admins
- Promote users to moderator or admin
- Demote users to student
- Verify unverified users
- Suspend/unsuspend accounts
- Warn users (automatic -5 point penalty)

### Report Dashboard
- View recent content reports
- Filter by status or reason
- Access moderator dashboard from admin panel
- Quick statistics on all report types

---

## Key Features

### Role-Based Access Control (RBAC)

Decorators ensure only authorized users can access specific views:

```python
@admin_required       # Admin only
@moderator_required   # Moderator & Admin
@can_post            # Verified users only
@can_moderate        # Moderator & Admin with extra checks
```

### User Profile Pages

Each user has a detailed profile showing:
- Current role and verification status
- Global ranking position
- Points and reputation score
- Contribution statistics (posts, comments, reports)
- Recent activity
- Last active timestamp

### Leaderboard

Comprehensive rankings with:
- Role-based filtering
- Current user rank display
- Reputation progress bars
- Activity timestamps
- Clickable user profiles

---

## Database Models

### User Model (Extended)
```python
- role: CharField (student, moderator, admin)
- points: IntegerField
- reputation_score: FloatField
- is_verified: BooleanField
```

### ContentReport Model
```python
- post: ForeignKey(CommonPost)
- reporter: ForeignKey(User)
- reason: CharField (choice field)
- description: TextField
- status: CharField (pending, approved, rejected, resolved)
- reviewed_by: ForeignKey(User, null=True)
- review_notes: TextField
- created_at & updated_at: DateTime
```

### UserRanking Model
```python
- user: OneToOneField(User)
- total_posts: IntegerField
- total_comments: IntegerField
- helpful_comments: IntegerField
- reports_submitted: IntegerField
- violations: IntegerField
- last_activity: DateTime
```

---

## URL Routes

### Public Routes
- `/` - Home/feed
- `/leaderboard/` - View global rankings
- `/user/<username>/` - View user profile

### Moderation Routes
- `/report-post/<post_id>/` - Submit report (authenticated users)
- `/moderator/` - Moderation dashboard (moderators+)
- `/review-report/<report_id>/` - Review report (moderators+)

### Admin Routes
- `/admin-panel/` - Admin dashboard (admins only)
- `/promote-user/<user_id>/` - Change user role (admins only)
- `/manage-user/<user_id>/` - Manage user account (admins only)

---

## Best Practices

### For Administrators
1. Regularly review pending reports
2. Document violation reasons in review notes
3. Promote trusted community members to moderators
4. Monitor system statistics for trends
5. Take action on repeated violators

### For Moderators
1. Review reports promptly
2. Provide clear review notes for actions taken
3. Be fair and consistent in decisions
4. Escalate complex issues to admins
5. Document patterns of user behavior

### For Users
1. Read community guidelines before posting
2. Report genuinely inappropriate content
3. Be respectful in discussions
4. Participate to earn points and reputation
5. Aim to maintain high reputation scores

---

## Future Enhancements

Potential features for expansion:

1. **Badges & Achievements** - Award badges for milestones
2. **Reputation Decay** - Reduce old violation records over time
3. **Appeal System** - Users can appeal moderation decisions
4. **User Feedback** - Notifications on report outcomes
5. **Activity Logs** - Comprehensive audit trail
6. **Automated Moderation** - AI-powered content filtering
7. **Ban/Blacklist** - Permanent account restrictions
8. **Role-Based Permissions** - Fine-grained access control

---

## Setup Instructions

### Database Migration
```bash
python manage.py makemigrations accounts
python manage.py migrate accounts
```

### Creating Admin User
```bash
python manage.py createsuperuser
# Then use Django admin to assign roles
```

### Initial Setup
1. Create superuser account
2. Use Django admin interface to promote users to moderators/admins
3. Verify trusted users to allow posting
4. Configure moderation guidelines in admin panel

---

## Support & Troubleshooting

### User Visibility Issues
- Ensure `is_verified = True` for users to appear in leaderboard
- Check `is_active = True` for user accounts
- Verify user role is set correctly

### Report Not Showing
- Check report status
- Verify reporter user still exists (not deleted)
- Ensure post still exists

### Permission Denied Errors
- Verify user role matches required permission
- Check if user is authenticated
- Confirm is_verified flag for required views

---

## Admin Interface Enhancements

The Django admin interface includes custom admin classes for:

### UserAdmin
- Role-based filtering and display
- Batch actions: promote, demote, verify, award points
- Custom list display with badges

### ContentReportAdmin
- Status filtering with color-coded badges
- Batch actions: approve, reject, resolve
- Read-only fields for data integrity

### UserRankingAdmin
- Automatic ranking calculation
- Real-time metrics updates
- Sortable by rank

### CommonPostAdmin
- Display author role
- Show report count and status
- Quick access to report information

---

*Last Updated: April 2024*
*Campus Connect - Mini Campus Social Network*
