from django.urls import path
from . import views

urlpatterns = [
    # Admin Dashboard
    path('', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    
    # User Management
    path('users/', views.UserManagementView.as_view(), name='user_management'),
    path('users/<int:user_id>/', views.UserDetailAdminView.as_view(), name='user_detail_admin'),
    path('users/<int:user_id>/edit/', views.UpdateUserRightsView.as_view(), name='update_user_rights'),
    
    # User Rights Management
    path('rights/', views.UserRightsManagementView.as_view(), name='user_rights_management'),
    
    # AJAX Endpoints
    path('ajax/user/<int:user_id>/role/', views.AjaxUpdateUserRoleView.as_view(), name='ajax_update_user_role'),
    path('ajax/user/<int:user_id>/admin/', views.AjaxToggleAdminView.as_view(), name='ajax_toggle_admin'),
    path('ajax/user/<int:user_id>/superuser/', views.AjaxToggleSuperuserView.as_view(), name='ajax_toggle_superuser'),
]
