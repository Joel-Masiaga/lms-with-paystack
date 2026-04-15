"""
URL configuration for lms project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from django.conf import settings
from users import views as user_views
from chatboat import views
 
from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path("api/", views.chatAPI, name="chatAPI"),
    path("chatbot/", views.chatAPI, name="chatAPI"),
      
    path('instructor/', include('instructor.urls')),
    path('management/', include('management.urls')),
    path('email_communication/', include('email_communication.urls')),
    path('community/', include('community.urls')),
    path('register/', user_views.register, name='register'),
    path('login/', user_views.custom_login, name='login'),
    path('logout/', user_views.custom_logout, name='logout'),
    
    # Email Verification URLs
    path('verify-email/', user_views.verify_email_pending, name='verify_email_pending'),
    path('verify-email/<uidb64>/<token>/', user_views.verify_email_confirm, name='verify_email_confirm'),
    path('resend-verification/', user_views.resend_verification_email, name='resend_verification'),
    
    path('profile/', user_views.profile, name='profile'),     # Profile view for users
    path('profile/create/', user_views.profile_create, name='profile_create'),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('tinymce/', include('tinymce.urls')),
    path('accounts/signup/', RedirectView.as_view(pattern_name='register', permanent=True), name='account_signup'),
    path('accounts/login/', RedirectView.as_view(pattern_name='login', permanent=True), name='account_login'),
    path('accounts/logout/', RedirectView.as_view(pattern_name='logout', permanent=True), name='account_logout'),
    path('accounts/', include('allauth.urls')),

    path('subscribe/', user_views.subscribe, name='subscribe'),
    path('unsubscribe/', user_views.unsubscribe, name='unsubscribe'),
    path('newsletter/', user_views.newsletter, name='newsletter'),
    path('tour/done/', user_views.mark_tour_seen, name='mark_tour_seen'),
    path('notifications/<int:notification_id>/read/', user_views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', user_views.mark_all_notifications_read, name='mark_all_notifications_read'),

    path("__reload__/", include("django_browser_reload.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)