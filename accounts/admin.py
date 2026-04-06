from django.contrib import admin
from .models import User, CommonPost, Comment, ChatMessage

# Register your models here.
admin.site.register(User)
admin.site.register(CommonPost)
admin.site.register(Comment)
admin.site.register(ChatMessage)