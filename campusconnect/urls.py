"""
URL configuration for campusconnect project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

handler404 = 'accounts.views.handler404'
handler500 = 'accounts.views.handler500'
handler403 = 'accounts.views.handler403'
handler400 = 'accounts.views.handler400'

# Custom URL pattern for users subdomain
# In production, configure your web server (nginx/Apache) to route users.* to this Django app

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("accounts.urls")),
    # Users subdomain route - maps users.domain.com/register to registration
    path('register/', RedirectView.as_view(url='/', permanent=False), name='users_register_redirect'),
]
