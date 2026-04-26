from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('user/<str:username>/', views.user_profile, name='user_profile'),
    path('create-post/', views.create_post, name='create_post'),
    path('comment/<int:post_id>/', views.add_comment, name='add_comment'),
    path('common-chat/', views.common_chat, name='common_chat'),
    path('chat/<str:username>/', views.personal_chat, name='personal_chat'),
    
    # Reporting and Moderation
    path('report-post/<int:post_id>/', views.report_post, name='report_post'),
    path('moderator/', views.moderator_dashboard, name='moderator_dashboard'),
    path('review-report/<int:report_id>/', views.review_report, name='review_report'),
    
    # Admin Panel
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('promote-user/<int:user_id>/', views.promote_user, name='promote_user'),
    path('manage-user/<int:user_id>/', views.manage_user, name='manage_user'),
]