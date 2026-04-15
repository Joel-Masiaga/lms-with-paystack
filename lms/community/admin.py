from django.contrib import admin
from .models import UserOnlineStatus, DirectMessage, Conversation, CommunityGroup, GroupMember, GroupMessage, CourseBroadcast, GroupInvitation


@admin.register(UserOnlineStatus)
class UserOnlineStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_online', 'last_seen')
    list_filter = ('is_online', 'last_seen')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('last_seen',)


@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('sender__username', 'recipient__username', 'content')
    ordering = ('-created_at',)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'last_message_at')
    list_filter = ('created_at', 'last_message_at')
    filter_horizontal = ('participants',)


@admin.register(CommunityGroup)
class CommunityGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'is_public', 'created_at')
    list_filter = ('is_public', 'created_at')
    search_fields = ('name', 'description')
    filter_horizontal = ('members',)


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'role', 'joined_at')
    list_filter = ('role', 'joined_at')
    search_fields = ('user__username', 'group__name')


@admin.register(GroupMessage)
class GroupMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'group', 'created_at')
    list_filter = ('group', 'created_at')
    search_fields = ('sender__username', 'group__name', 'content')
    ordering = ('-created_at',)


@admin.register(CourseBroadcast)
class CourseBroadcastAdmin(admin.ModelAdmin):
    list_display = ('course', 'instructor', 'subject', 'created_at')
    list_filter = ('course', 'created_at')
    search_fields = ('course__title', 'instructor__username', 'subject', 'content')
    ordering = ('-created_at',)


@admin.register(GroupInvitation)
class GroupInvitationAdmin(admin.ModelAdmin):
    list_display = ('group', 'created_by', 'invitee', 'status', 'created_at', 'expires_at')
    list_filter = ('status', 'created_at', 'expires_at')
    search_fields = ('group__name', 'created_by__username', 'invitee__username', 'invite_code')
    readonly_fields = ('invite_code', 'created_at', 'accepted_at')
    ordering = ('-created_at',)
