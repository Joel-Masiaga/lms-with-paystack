from django.urls import path
from . import views
from . import async_utils

urlpatterns = [
    # Community Hub
    path('', views.CommunityHubView.as_view(), name='community_hub'),
    
    # User Discovery
    path('users/', views.UserDirectoryView.as_view(), name='user_directory'),
    
    # Direct Messages (Legacy - kept for backward compatibility)
    path('messages/', views.ConversationListView.as_view(), name='conversation_list'),
    path('messages/<int:user_id>/', views.ConversationDetailView.as_view(), name='conversation_detail'),
    
    # Unified Messages (New - handles both DM and group chats)
    path('chat/', views.UnifiedConversationDetailView.as_view(), name='unified_conversation'),
    
    # Community Groups
    path('groups/', views.GroupListView.as_view(), name='group_list'),
    path('groups/discover/', views.GroupDiscoveryView.as_view(), name='group_discovery'),
    path('groups/create/', views.CreateGroupView.as_view(), name='create_group'),
    path('groups/<int:group_id>/', views.GroupDetailView.as_view(), name='group_detail'),
    path('groups/<int:group_id>/join/', views.JoinGroupView.as_view(), name='join_group'),
    path('groups/<int:group_id>/leave/', views.LeaveGroupView.as_view(), name='leave_group'),
    path('groups/<int:group_id>/invite/', views.SendGroupInviteView.as_view(), name='send_group_invite'),
    path('groups/<int:group_id>/edit/', views.GroupEditView.as_view(), name='edit_group'),
    path('groups/<int:group_id>/members/', views.GroupMembersView.as_view(), name='group_members'),
    path('groups/<int:group_id>/members/<int:member_id>/remove/', views.RemoveGroupMemberView.as_view(), name='remove_group_member'),
    
    # Group Invitations
    path('invitations/', views.GroupInvitationsView.as_view(), name='group_invitations'),
    
    # Course Broadcasts
    path('broadcast/', views.CourseBroadcastView.as_view(), name='course_broadcast'),
    path('broadcast/<int:course_id>/', views.CourseBroadcastListView.as_view(), name='course_broadcasts'),
    path('announcements/', views.StudentAnnouncementsView.as_view(), name='student_announcements'),
    
    # Async Utilities (HTMX endpoints)
    path('upload/attachment/', async_utils.upload_message_attachment, name='upload_attachment'),
    path('upload/group-attachment/', async_utils.upload_group_message_attachment, name='upload_group_attachment'),
    path('history/<int:user_id>/', async_utils.load_message_history, name='load_message_history'),
    path('group/<int:group_id>/history/', async_utils.load_group_message_history, name='load_group_message_history'),
]
