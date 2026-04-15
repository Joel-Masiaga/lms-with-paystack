from django.urls import path
from . import views

urlpatterns = [
    # Instructor email routes
    path('instructor/email/', views.InstructorEmailStudentsView.as_view(), name='instructor_email'),
    path('instructor/email/preview/', views.InstructorEmailPreviewView.as_view(), name='instructor_email_preview'),
    path('instructor/email/history/', views.InstructorEmailHistoryView.as_view(), name='instructor_email_history'),
    
    # Superuser promotional email routes
    path('promotional/', views.PromotionalEmailView.as_view(), name='promotional_email'),
    path('promotional/preview/', views.PromotionalEmailPreviewView.as_view(), name='promotional_email_preview'),
    path('promotional/history/', views.PromotionalEmailHistoryView.as_view(), name='promotional_email_history'),
]
