# Campus Connect - Ranking System Implementation Guide

## Quick Start

### 1. Installation & Setup

The ranking system has been fully integrated into Campus Connect. Follow these steps to get started:

#### Step 1: Apply Database Migrations
```bash
cd c:\Users\G\Desktop\3rd Year\Sem-6\SE lab\campusconnect
python manage.py migrate accounts
```

#### Step 2: Create an Admin User (if not exists)
```bash
python manage.py createsuperuser
```

#### Step 3: Run Development Server
```bash
python manage.py runserver
```

Access the application at: `http://127.0.0.1:8000/`

### 2. Initial Configuration

#### Promote Users to Roles

1. Go to Django Admin: `http://127.0.0.1:8000/admin/`
2. Login with your superuser credentials
3. Navigate to **Users**
4. Select users and use bulk actions:
   - "Promote selected users to Moderator"
   - "Promote selected users to Administrator"
5. Or use the Admin Panel (if already promoted):
   - Go to `/admin-panel/` and manage roles there

#### Verify Users

In Django Admin or Admin Panel:
- Select users
- Click "Verify selected users"
- Now they can create posts

### 3. Key Components

#### Models Added/Extended

**User Model Extensions:**
- `role` - User role (student, moderator, admin)
- `points` - Achievement points
- `reputation_score` - Reputation percentage (0-100)
- `is_verified` - Email verification status

**New Models:**
- `ContentReport` - Post reports for moderation
- `UserRanking` - User statistics and rankings

#### Views Added

| Route | Purpose | Access |
|-------|---------|--------|
| `/leaderboard/` | Global rankings | All authenticated |
| `/user/<username>/` | User profile | All authenticated |
| `/report-post/<id>/` | Report a post | All authenticated |
| `/moderator/` | Moderation dashboard | Moderators+ |
| `/review-report/<id>/` | Review a report | Moderators+ |
| `/admin-panel/` | Admin dashboard | Admins only |
| `/promote-user/<id>/` | Change user role | Admins only |
| `/manage-user/<id>/` | Manage user account | Admins only |

---

## System Architecture

### Role Hierarchy

```
Student (Default)
  ↓ (Admin promotion)
Moderator
  ↓ (Admin promotion)
Administrator (Superuser)
```

### Points Flow

```
User Action → Points Awarded → Reputation Recalculated → Ranking Updated
```

### Content Moderation Flow

```
Post Created
  ↓
User Reports Post
  ↓
Report Pending Review
  ↓
Moderator Reviews (Approve/Reject/Resolve)
  ↓
Action Taken (if approved: Author penalized)
  ↓
Report Closed
```

---

## Files Added/Modified

### New Files Created:
- `accounts/decorators.py` - Role-based access control decorators
- `accounts/signals.py` - Auto-create ranking for new users
- `accounts/templates/accounts/leaderboard.html`
- `accounts/templates/accounts/user_profile.html`
- `accounts/templates/accounts/moderator_dashboard.html`
- `accounts/templates/accounts/admin_panel.html`
- `RANKING_SYSTEM_DOCS.md` - Full documentation
- `IMPLEMENTATION_GUIDE.md` - This file

### Modified Files:
- `accounts/models.py` - Extended User, added ContentReport & UserRanking
- `accounts/views.py` - Added role-based views and moderation endpoints
- `accounts/admin.py` - Enhanced admin interface with custom classes
- `accounts/forms.py` - Added ContentReportForm
- `accounts/urls.py` - Added new URL routes
- `accounts/apps.py` - Registered signals
- `accounts/templates/accounts/profile.html` - Updated with role/ranking info
- `accounts/templates/accounts/layout.html` - Added navigation for new features

---

## Features Overview

### 1. User Ranking System
- Global leaderboard sorted by points
- Reputation score calculation
- Role-based filtering
- User profile pages with stats

### 2. Role-Based Access Control
- Three distinct roles with different permissions
- Decorators for easy view protection
- Admin panel for role management
- Automatic role inheritance

### 3. Content Moderation
- Multi-category reporting system
- Moderator review dashboard
- Report history tracking
- Author penalty system

### 4. Points & Reputation
- Automatic point allocation for actions
- Reputation calculation algorithm
- Points visible in leaderboard
- Penalties for violations

### 5. Admin Controls
- System-wide statistics
- User account management
- Staff role assignment
- Comprehensive reporting views

---

## Django Admin Interface

The enhanced admin interface provides:

### UserAdmin
- Role display with color-coded badges
- Points and reputation filtering
- Batch actions for role management
- Quick access to verification status

### ContentReportAdmin
- Status-based filtering
- Reason categorization
- Read-only fields for data integrity
- Review workflow support

### UserRankingAdmin
- Auto-calculated rankings
- Contribution metrics
- Real-time metrics updates
- Sortable statistics

### CommonPostAdmin
- Author role display
- Report count with status badges
- Direct access to report information

---

## Usage Scenarios

### Scenario 1: Promoting a Moderator

1. Admin goes to `/admin-panel/`
2. Under Staff Management tab
3. Finds the user in the list
4. Uses the dropdown to change role
5. User gets moderator permissions immediately

### Scenario 2: Handling a Content Report

1. User reports a post as spam
2. Report appears in moderator dashboard
3. Moderator reviews the post
4. Moderator decides to approve the report
5. Post author loses 10 points
6. Report marked as approved
7. System notifies admin

### Scenario 3: Viewing Leaderboard

1. User navigates to `/leaderboard/`
2. Can filter by role (Students, Moderators, Admins)
3. Sees their rank displayed
4. Can click profile to view any user's stats
5. Sees reputation progress bars

---

## Common Tasks

### Create New Admin
```python
# Via Django shell
from accounts.models import User
user = User.objects.get(username='alice')
user.role = 'admin'
user.save()
```

### Verify a User
```python
user.is_verified = True
user.save()
```

### Award Points
```python
user.add_points(50)  # Adds points and recalculates reputation
```

### Get User Ranking
```python
ranking = user.ranking  # One-to-one relationship
rank_position = ranking.get_rank()
```

### Check User Permissions
```python
user.is_admin()      # True if admin
user.is_moderator()  # True if moderator or admin
user.is_student()    # True if student
```

---

## Troubleshooting

### Issue: Users can't post
**Solution:** Verify users have `is_verified = True`

### Issue: Ranking not showing
**Solution:** Ensure UserRanking record exists (auto-created via signals)

### Issue: Report dashboard empty
**Solution:** Ensure reports have been submitted (status = 'pending')

### Issue: Permission denied on admin panel
**Solution:** User must have role = 'admin', not just is_staff = True

### Issue: Migrations failing
**Solution:** Ensure database is clean or run `python manage.py migrate --fake-initial`

---

## Performance Considerations

### Database Optimization
- UserRanking uses `select_related('user')` for efficiency
- Reports use `select_related` for author/reporter
- Leaderboard limits to top 100 users
- Indexes on role, status, created_at

### Caching Opportunities
- Cache leaderboard rankings (refresh hourly)
- Cache user profile statistics
- Cache pending report count for moderators

### Scalability
- UserRanking one-to-one relationship avoids N+1 queries
- Points calculation is O(1)
- Reputation calculation cached on user save
- Report queries optimized with filtering

---

## Security Considerations

### Access Control
- Decorators enforce role requirements
- Views check `is_authenticated` and role
- Admin panel restricted to admins only
- Forms validate user permissions

### Data Protection
- Points and reputation immutable except through defined methods
- Report review notes can't be modified after submission
- User roles can only be changed by admins
- Suspension prevents posting but preserves data

### Audit Trail
- Report status and reviewer tracked
- Review notes document decisions
- User modification timestamps available
- Admin actions could be logged (future enhancement)

---

## Testing

### Test Scenarios

1. **User Creation**
   - New user auto-gets ranking record
   - Default role is student
   - Email unverified by default

2. **Posting**
   - Unverified users can't post
   - Post creation awards 5 points
   - Reputation updates automatically

3. **Reporting**
   - User can report once per post
   - Report appears in moderator dashboard
   - Approving penalizes author

4. **Role Management**
   - Admin can promote/demote users
   - Moderators see moderation dashboard
   - Students can't access admin panel

5. **Leaderboard**
   - Users ranked by points
   - Filters work correctly
   - Pagination works for 100+ users

### Manual Testing Checklist
```
□ Create new user
□ Login as student
□ Verify email (via admin)
□ Create post (should award 5 points)
□ Report a post
□ Login as admin
□ Promote user to moderator
□ Review report as moderator
□ Access admin panel
□ View leaderboard
□ Check user profile
□ Verify reputation calculation
```

---

## Future Enhancements

Planned features:

1. **Badges System**
   - Award badges for milestones
   - Display on user profile
   - Different categories

2. **Notifications**
   - Notify user on report decision
   - Alert admins of repeated violations
   - Notify on role changes

3. **Advanced Moderation**
   - Automated content filtering
   - Appeal system for users
   - Logging of all admin actions

4. **Analytics Dashboard**
   - Platform statistics
   - User growth charts
   - Report trends analysis

5. **Gamification**
   - Achievements system
   - Daily challenges
   - Season-based rankings

---

## Support

For issues or questions:
1. Check [RANKING_SYSTEM_DOCS.md](RANKING_SYSTEM_DOCS.md) for detailed documentation
2. Review [admin interface](#django-admin-interface) section
3. Check logs for error messages
4. Run Django tests to verify setup

---

*Campus Connect Ranking System - v1.0*
*Last Updated: April 2024*
