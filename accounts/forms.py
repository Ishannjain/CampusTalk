from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, CommonPost, Comment, ChatMessage, ContentReport, REPORT_REASON_CHOICES

class CustomUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
        ]

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'class': 'form-control',
            'placeholder': 'Enter your username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )

class PostForm(forms.ModelForm):
    class Meta:
        model = CommonPost
        fields = ['title', 'body', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Post title (optional)'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Share something with the campus community...'}),
            'image': forms.FileInput(attrs={'class': 'form-control-file'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Write a comment...'}),
        }

class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Type your message...'}),
        }

class ContentReportForm(forms.ModelForm):
    class Meta:
        model = ContentReport
        fields = ['reason', 'description']
        widgets = {
            'reason': forms.Select(
                choices=REPORT_REASON_CHOICES,
                attrs={'class': 'form-control', 'required': True}
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Provide additional details about why this content is inappropriate...'
                }
            ),
        }

from .models import Community, CommunityPost

class CommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Community Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'What is this community about?'}),
        }

class CommunityPostForm(forms.ModelForm):
    class Meta:
        model = CommunityPost
        fields = ['content', 'image', 'is_anonymous']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Share something with this community...'}),
            'image': forms.FileInput(attrs={'class': 'form-control-file'}),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
