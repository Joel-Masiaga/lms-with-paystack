from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, ListView, DetailView, CreateView
from django.contrib import messages
from django.db.models import Q, Count, Prefetch
from django.http import JsonResponse

from users.models import User
from courses.models import Course, Enrollment
from .models import DirectMessage, Conversation, CommunityGroup, GroupMember, GroupMessage, CourseBroadcast, UserOnlineStatus, GroupInvitation
from .forms import DirectMessageForm, CreateGroupForm, EditGroupForm, GroupMessageForm, CourseBroadcastForm


# ─────────────────────────────────────────────────────────────────
# COMMUNITY HUB
# ─────────────────────────────────────────────────────────────────

class CommunityHubView(LoginRequiredMixin, TemplateView):
    """Main Community hub page with all connection options."""
    template_name = 'community/community_hub.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Count stats for dashboard
        pending_invitations = GroupInvitation.objects.filter(
            invitee=user,
            status='pending'
        ).count()
        
        user_groups = user.joined_groups.all().count()
        
        context.update({
            'pending_invitations_count': pending_invitations,
            'user_groups_count': user_groups,
        })
        
        return context


# ─────────────────────────────────────────────────────────────────
# USER DIRECTORY & DISCOVERY
# ─────────────────────────────────────────────────────────────────

class UserDirectoryView(LoginRequiredMixin, TemplateView):
    """Browse and discover other users to connect with."""
    template_name = 'community/user_directory.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        search_query = self.request.GET.get('q', '')
        role_filter = self.request.GET.get('role', '')
        
        # Get all users except current user
        users_list = User.objects.exclude(id=user.id).select_related('profile')
        
        # Get conversations to check who user is already chatting with
        user_conversations = Conversation.objects.filter(participants=user).prefetch_related('participants')
        chatting_with_ids = set()
        for conv in user_conversations:
            chatting_with_ids.update(conv.participants.values_list('id', flat=True))
        chatting_with_ids.discard(user.id)
        
        # Apply filters
        if search_query:
            users_list = users_list.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(profile__first_name__icontains=search_query) |
                Q(profile__last_name__icontains=search_query)
            )
        
        if role_filter:
            users_list = users_list.filter(role=role_filter)
        
        # Get user's own role for display
        user_role = 'Instructor' if user.role == 'instructor' else 'Student'
        
        context['users'] = users_list[:50]  # Limit to 50 for performance
        context['search_query'] = search_query
        context['role_filter'] = role_filter
        context['chatting_with_ids'] = chatting_with_ids
        context['user_role'] = user_role
        
        return context


# ─────────────────────────────────────────────────────────────────
# DIRECT MESSAGING VIEWS
# ─────────────────────────────────────────────────────────────────

class ConversationListView(LoginRequiredMixin, TemplateView):
    """List all conversations (both direct messages and group chats) for the logged-in user."""
    template_name = 'community/conversation_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # ─────────────────────────────────────────────────────────────
        # DIRECT MESSAGE CONVERSATIONS
        # ─────────────────────────────────────────────────────────────
        conversations = Conversation.objects.filter(
            participants=user
        ).prefetch_related('participants').order_by('-last_message_at')
        
        # Enhance with last message info and other user info
        direct_messages_data = []
        total_unread = 0
        
        for conversation in conversations:
            other_users = conversation.participants.exclude(id=user.id)
            if other_users.exists():
                other_user = other_users.first()
                
                # Get last message
                last_msg = DirectMessage.objects.filter(
                    Q(sender=user, recipient=other_user) |
                    Q(sender=other_user, recipient=user)
                ).order_by('-created_at').first()
                
                # Count unread messages from this specific user
                unread_count = DirectMessage.objects.filter(
                    sender=other_user,
                    recipient=user,
                    is_read=False
                ).count()
                
                total_unread += unread_count
                
                # Get user's online status
                try:
                    online_status = other_user.online_status
                except UserOnlineStatus.DoesNotExist:
                    online_status = UserOnlineStatus.objects.create(user=other_user)
                
                direct_messages_data.append({
                    'type': 'direct',
                    'conversation': conversation,
                    'other_user': other_user,
                    'last_message': last_msg,
                    'last_message_at': last_msg.created_at if last_msg else conversation.created_at,
                    'unread_count': unread_count,
                    'is_online': online_status.is_online,
                    'last_seen': online_status.last_seen,
                    'name': other_user.get_full_name() or other_user.username,
                    'image': other_user.profile.image if hasattr(other_user, 'profile') else None
                })
        
        # ─────────────────────────────────────────────────────────────
        # GROUP CONVERSATIONS
        # ─────────────────────────────────────────────────────────────
        user_groups = user.joined_groups.all()
        group_messages_data = []
        
        for group in user_groups:
            # Get last message in group
            last_group_msg = group.messages.order_by('-created_at').first()
            
            group_messages_data.append({
                'type': 'group',
                'group': group,
                'last_message': last_group_msg,
                'last_message_at': last_group_msg.created_at if last_group_msg else group.created_at,
                'unread_count': 0,  # Placeholder for future unread functionality
                'member_count': group.members.count(),
                'name': group.name,
                'image': None  # Groups don't have images yet, but placeholder for future use
            })
        
        # ─────────────────────────────────────────────────────────────
        # COMBINE AND SORT
        # ─────────────────────────────────────────────────────────────
        all_conversations = direct_messages_data + group_messages_data
        # Sort by most recent last message
        all_conversations.sort(key=lambda x: x['last_message_at'], reverse=True)
        
        context['conversations_data'] = all_conversations
        context['total_unread'] = total_unread
        return context


class ConversationDetailView(LoginRequiredMixin, TemplateView):
    """View messages with a specific user."""
    template_name = 'community/conversation_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = kwargs.get('user_id')
        current_user = self.request.user
        other_user = get_object_or_404(User, id=user_id)
        
        # Prevent self-messaging
        if current_user.id == other_user.id:
            messages.error(self.request, 'You cannot message yourself.')
            return redirect('conversation_list')
        
        # Get or create conversation
        conversation = get_or_create_conversation(current_user, other_user)
        
        # Get messages between users
        messages_list = DirectMessage.objects.filter(
            Q(sender=current_user, recipient=other_user) |
            Q(sender=other_user, recipient=current_user)
        ).order_by('created_at')
        
        # Mark messages as read
        DirectMessage.objects.filter(
            recipient=current_user, 
            sender=other_user, 
            is_read=False
        ).update(is_read=True)
        
        # Get user's online status
        try:
            online_status = other_user.online_status
        except UserOnlineStatus.DoesNotExist:
            online_status = UserOnlineStatus.objects.create(user=other_user)
        
        # Get all conversations for sidebar
        all_conversations = Conversation.objects.filter(
            participants=current_user
        ).prefetch_related('participants').order_by('-last_message_at')
        
        conversations_sidebar = []
        total_unread = 0
        
        for conv in all_conversations:
            other_users = conv.participants.exclude(id=current_user.id)
            if other_users.exists():
                sidebar_user = other_users.first()
                
                # Get last message
                last_msg = DirectMessage.objects.filter(
                    Q(sender=current_user, recipient=sidebar_user) |
                    Q(sender=sidebar_user, recipient=current_user)
                ).order_by('-created_at').first()
                
                # Count unread messages
                unread_count = DirectMessage.objects.filter(
                    sender=sidebar_user,
                    recipient=current_user,
                    is_read=False
                ).count()
                
                total_unread += unread_count
                
                # Get online status
                try:
                    sidebar_status = sidebar_user.online_status
                except UserOnlineStatus.DoesNotExist:
                    sidebar_status = UserOnlineStatus.objects.create(user=sidebar_user)
                
                conversations_sidebar.append({
                    'user': sidebar_user,
                    'last_message': last_msg,
                    'unread_count': unread_count,
                    'is_online': sidebar_status.is_online,
                    'is_active': sidebar_user.id == other_user.id
                })
        
        context['other_user'] = other_user
        context['messages'] = messages_list
        context['form'] = DirectMessageForm()
        context['conversation'] = conversation
        context['is_online'] = online_status.is_online
        context['last_seen'] = online_status.last_seen
        context['conversations_sidebar'] = conversations_sidebar
        context['total_unread'] = total_unread
        
        return context
    
    def post(self, request, **kwargs):
        user_id = kwargs.get('user_id')
        current_user = request.user
        other_user = get_object_or_404(User, id=user_id)
        user_id = kwargs.get('user_id')
        current_user = request.user
        other_user = get_object_or_404(User, id=user_id)
        
        # Prevent self-messaging
        if current_user.id == other_user.id:
            messages.error(self.request, 'You cannot message yourself.')
            return redirect('conversation_list')
        
        # Get or create conversation
        conversation = get_or_create_conversation(current_user, other_user)
        
        # Get messages between users
        messages_list = DirectMessage.objects.filter(
            Q(sender=current_user, recipient=other_user) |
            Q(sender=other_user, recipient=current_user)
        ).order_by('created_at')
        
        # Mark messages as read
        DirectMessage.objects.filter(
            recipient=current_user, 
            sender=other_user, 
            is_read=False
        ).update(is_read=True)
        
        # Get user's online status
        try:
            online_status = other_user.online_status
        except UserOnlineStatus.DoesNotExist:
            online_status = UserOnlineStatus.objects.create(user=other_user)
        
        # Get all conversations for sidebar
        all_conversations = Conversation.objects.filter(
            participants=current_user
        ).prefetch_related('participants').order_by('-last_message_at')
        
        conversations_sidebar = []
        total_unread = 0
        
        for conv in all_conversations:
            other_users = conv.participants.exclude(id=current_user.id)
            if other_users.exists():
                sidebar_user = other_users.first()
                
                # Get last message
                last_msg = DirectMessage.objects.filter(
                    Q(sender=current_user, recipient=sidebar_user) |
                    Q(sender=sidebar_user, recipient=current_user)
                ).order_by('-created_at').first()
                
                # Count unread messages
                unread_count = DirectMessage.objects.filter(
                    sender=sidebar_user,
                    recipient=current_user,
                    is_read=False
                ).count()
                
                total_unread += unread_count
                
                # Get online status
                try:
                    sidebar_status = sidebar_user.online_status
                except UserOnlineStatus.DoesNotExist:
                    sidebar_status = UserOnlineStatus.objects.create(user=sidebar_user)
                
                conversations_sidebar.append({
                    'user': sidebar_user,
                    'last_message': last_msg,
                    'unread_count': unread_count,
                    'is_online': sidebar_status.is_online,
                    'is_active': sidebar_user.id == other_user.id
                })
        
        context['other_user'] = other_user
        context['messages'] = messages_list
        context['form'] = DirectMessageForm()
        context['conversation'] = conversation
        context['is_online'] = online_status.is_online
        context['last_seen'] = online_status.last_seen
        context['conversations_sidebar'] = conversations_sidebar
        context['total_unread'] = total_unread
        
        return context
    
    def post(self, request, **kwargs):
        user_id = kwargs.get('user_id')
        current_user = request.user
        other_user = get_object_or_404(User, id=user_id)
        
        form = DirectMessageForm(request.POST, request.FILES)


class UnifiedConversationDetailView(LoginRequiredMixin, TemplateView):
    """Unified view for both direct messages and group conversations.
    
    This allows seamless switching between DM and group chats from a single interface.
    Query params: conversation_type=direct|group, user_id or group_id depending on type
    """
    template_name = 'community/unified_conversation_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_user = self.request.user
        
        # Determine conversation type from query params or URL kwargs
        conversation_type = self.request.GET.get('type') or kwargs.get('conversation_type', 'direct')
        
        # ─────────────────────────────────────────────────────────────
        # UNIFIED SIDEBAR: All conversations (DMs + Groups)
        # ─────────────────────────────────────────────────────────────
        all_sidebar_conversations = self._get_unified_sidebar_conversations(current_user)
        
        context['all_conversations'] = all_sidebar_conversations
        context['conversation_type'] = conversation_type
        context['other_user'] = None  # Initialize as None, will be set if direct message
        context['group'] = None  # Initialize as None, will be set if group message
        
        if conversation_type == 'direct':
            user_id = self.request.GET.get('user_id') or kwargs.get('user_id')
            if not user_id:
                return redirect('conversation_list')
            
            try:
                other_user = get_object_or_404(User, id=user_id)
            except:
                messages.error(self.request, 'User not found.')
                return redirect('conversation_list')
            
            context['other_user'] = other_user
            
            # Prevent self-messaging
            if current_user.id == other_user.id:
                messages.error(self.request, 'You cannot message yourself.')
                return redirect('conversation_list')
            
            # Get or create conversation
            conversation = get_or_create_conversation(current_user, other_user)
            
            # Get messages between users
            messages_list = DirectMessage.objects.filter(
                Q(sender=current_user, recipient=other_user) |
                Q(sender=other_user, recipient=current_user)
            ).order_by('created_at')
            
            # Mark messages as read
            DirectMessage.objects.filter(
                recipient=current_user, 
                sender=other_user, 
                is_read=False
            ).update(is_read=True)
            
            # Get user's online status
            try:
                online_status = other_user.online_status
            except UserOnlineStatus.DoesNotExist:
                online_status = UserOnlineStatus.objects.create(user=other_user)
            
            context.update({
                'conversation_id': conversation.id,
                'other_user': other_user,
                'messages': messages_list,
                'form': DirectMessageForm(),
                'is_online': online_status.is_online,
                'last_seen': online_status.last_seen,
                'active_conversation_id': f'dm-{other_user.id}',
            })
            
        elif conversation_type == 'group':
            group_id = self.request.GET.get('group_id') or kwargs.get('group_id')
            if not group_id:
                return redirect('conversation_list')
                
            group = get_object_or_404(CommunityGroup, id=group_id)
            
            # Check if user is a member
            is_member = group.members.filter(id=current_user.id).exists()
            user_role = None
            is_admin = False
            
            if is_member:
                member_obj = GroupMember.objects.filter(user=current_user, group=group).first()
                if member_obj:
                    user_role = member_obj.role
                    is_admin = member_obj.role == 'admin'
            
            if not is_member and not group.is_public:
                context['error'] = 'You do not have access to this group.'
                return context
            
            # Get messages in group
            messages_list = group.messages.all().select_related('sender').order_by('created_at')
            
            context.update({
                'conversation_id': group.id,
                'group': group,
                'messages': messages_list,
                'form': GroupMessageForm() if is_member else None,
                'is_member': is_member,
                'is_admin': is_admin,
                'is_group_admin': is_admin,
                'user_role': user_role,
                'member_count': group.members.count(),
                'active_conversation_id': f'group-{group.id}',
            })
        
        return context
    
    def _get_unified_sidebar_conversations(self, user):
        """Build unified sidebar with both DM conversations and group conversations."""
        all_conversations = []
        
        # Direct Messages
        conversations = Conversation.objects.filter(
            participants=user
        ).prefetch_related('participants').order_by('-last_message_at')
        
        for conversation in conversations:
            other_users = conversation.participants.exclude(id=user.id)
            if not other_users.exists():
                # Skip conversations without another participant (shouldn't happen, but be safe)
                continue
            
            other_user = other_users.first()
            if not other_user:
                # Skip if other_user is None (shouldn't happen, but be safe)
                continue
            
            # Ensure we have a valid other_user object
            
            # Get last message
            last_msg = DirectMessage.objects.filter(
                Q(sender=user, recipient=other_user) |
                Q(sender=other_user, recipient=user)
            ).order_by('-created_at').first()
            
            # Count unread messages
            unread_count = DirectMessage.objects.filter(
                sender=other_user,
                recipient=user,
                is_read=False
            ).count()
            
            # Get online status
            try:
                online_status = other_user.online_status
            except UserOnlineStatus.DoesNotExist:
                online_status = UserOnlineStatus.objects.create(user=other_user)
            
            all_conversations.append({
                'type': 'direct',
                'id': other_user.id,
                'formatted_id': f'dm-{other_user.id}',
                'name': other_user.get_full_name() or other_user.username,
                'avatar': other_user.profile.image if hasattr(other_user, 'profile') else None,
                'last_message': last_msg,
                'last_message_at': last_msg.created_at if last_msg else conversation.created_at,
                'unread_count': unread_count,
                'is_online': online_status.is_online,
                'user': other_user,
            })
        
        # Group Conversations
        user_groups = user.joined_groups.all()
        
        for group in user_groups:
            # Get last message in group
            last_group_msg = group.messages.order_by('-created_at').first()
            
            all_conversations.append({
                'type': 'group',
                'id': group.id,
                'formatted_id': f'group-{group.id}',
                'name': group.name,
                'avatar': None,  # Groups don't have avatars yet
                'last_message': last_group_msg,
                'last_message_at': last_group_msg.created_at if last_group_msg else group.created_at,
                'unread_count': 0,
                'member_count': group.members.count(),
                'group': group,
            })
        
        # Sort by most recent
        all_conversations.sort(key=lambda x: x['last_message_at'], reverse=True)
        return all_conversations
    
    def post(self, request, **kwargs):
        """Handle message posting for both DM and group conversations."""
        conversation_type = request.GET.get('type', 'direct')
        current_user = request.user
        
        if conversation_type == 'direct':
            user_id = request.GET.get('user_id') or kwargs.get('user_id')
            other_user = get_object_or_404(User, id=user_id)
            
            form = DirectMessageForm(request.POST, request.FILES)
            
            if form.is_valid():
                message = form.save(commit=False)
                message.sender = current_user
                message.recipient = other_user
                message.save()
                
                # Update conversation
                conversation = get_or_create_conversation(current_user, other_user)
                conversation.save()
            
        elif conversation_type == 'group':
            group_id = request.GET.get('group_id') or kwargs.get('group_id')
            group = get_object_or_404(CommunityGroup, id=group_id)
            
            # Check if user is a member
            if not group.members.filter(id=current_user.id).exists():
                messages.error(request, 'You must be a member to post in this group.')
                return self.get(request, **kwargs)
            
            form = GroupMessageForm(request.POST, request.FILES)
            if form.is_valid():
                message = form.save(commit=False)
                message.group = group
                message.sender = current_user
                message.save()
        
        # Re-render template with updated messages
        return self.get(request, **kwargs)


# ─────────────────────────────────────────────────────────────────
# COMMUNITY GROUPS VIEWS
# ─────────────────────────────────────────────────────────────────

class GroupListView(LoginRequiredMixin, TemplateView):
    """List all public groups and user's joined groups."""
    template_name = 'community/group_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get all public groups
        public_groups = CommunityGroup.objects.filter(is_public=True)
        
        # Get user's joined groups
        joined_groups = user.joined_groups.all()
        
        # Get available groups (public groups user hasn't joined)
        available_groups = public_groups.exclude(members=user)
        
        context['joined_groups'] = joined_groups
        context['available_groups'] = available_groups
        context['public_groups'] = public_groups
        
        return context


class GroupDetailView(LoginRequiredMixin, TemplateView):
    """View a specific group and its messages."""
    template_name = 'community/group_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_id = kwargs.get('group_id')
        group = get_object_or_404(CommunityGroup, id=group_id)
        user = self.request.user
        
        # Check if user is a member
        is_member = group.members.filter(id=user.id).exists()
        user_role = None
        is_admin = False
        
        if is_member:
            member_obj = GroupMember.objects.filter(user=user, group=group).first()
            if member_obj:
                user_role = member_obj.role
                is_admin = member_obj.role == 'admin'
        
        if not is_member and not group.is_public:
            context['error'] = 'You do not have access to this group.'
            return context
        
        # Get messages using the related_name 'messages' from GroupMessage model
        messages_list = group.messages.all().select_related('sender').order_by('created_at')
        
        # Get group members with their roles
        group_members = GroupMember.objects.filter(group=group).select_related('user').order_by('-joined_at')
        
        # Get other users for invitation (exclude members)
        other_users = User.objects.exclude(
            id__in=group.members.values_list('id', flat=True)
        ).exclude(id=user.id).order_by('first_name')[:20]  # Limit to 20 for performance
        
        # Get pending invitations for this group (only show to admins)
        pending_invitations = []
        if is_admin:
            pending_invitations = GroupInvitation.objects.filter(
                group=group,
                status='pending'
            ).select_related('invitee', 'created_by').order_by('-created_at')
        
        context['group'] = group
        context['messages'] = messages_list
        context['is_member'] = is_member
        context['is_admin'] = is_admin
        context['user_role'] = user_role
        context['form'] = GroupMessageForm() if is_member else None
        context['group_members'] = group_members
        context['other_users'] = other_users
        context['pending_invitations'] = pending_invitations
        
        # Get all groups for sidebar
        user_groups = user.joined_groups.all().order_by('-created_at')
        groups_sidebar = []
        
        for grp in user_groups:
            grp_messages = grp.messages.count()
            groups_sidebar.append({
                'group': grp,
                'message_count': grp_messages,
                'member_count': grp.members.count(),
                'is_active': grp.id == group.id
            })
        
        context['groups_sidebar'] = groups_sidebar
        
        return context
    
    def post(self, request, **kwargs):
        group_id = kwargs.get('group_id')
        group = get_object_or_404(CommunityGroup, id=group_id)
        
        # Check if user is a member
        if not group.members.filter(id=request.user.id).exists():
            messages.error(request, 'You must be a member to post in this group.')
            return redirect('group_detail', group_id=group_id)
        
        form = GroupMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.group = group
            message.sender = request.user
            message.save()
            messages.success(request, 'Message posted!')
            return redirect('group_detail', group_id=group_id)
        
        return self.get(request, **kwargs)


class CreateGroupView(LoginRequiredMixin, TemplateView):
    """Create a new community group."""
    template_name = 'community/create_group.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CreateGroupForm()
        return context
    
    def post(self, request):
        form = CreateGroupForm(request.POST, request.FILES)
        if form.is_valid():
            group = form.save(commit=False)
            group.creator = request.user
            group.save()
            # Add creator as admin
            GroupMember.objects.create(user=request.user, group=group, role='admin')
            messages.success(request, f'Group "{group.name}" created successfully!')
            return redirect('group_detail', group_id=group.id)
        
        context = {'form': form}
        return render(request, self.template_name, context)


class JoinGroupView(LoginRequiredMixin, TemplateView):
    """Join a public group."""
    
    def post(self, request, group_id):
        group = get_object_or_404(CommunityGroup, id=group_id)
        
        if not group.is_public:
            messages.error(request, 'This group is not public.')
            return redirect('group_list')
        
        # Check if already member
        if group.members.filter(id=request.user.id).exists():
            messages.info(request, 'You are already a member of this group.')
            return redirect('group_detail', group_id=group_id)
        
        # Add user to group
        GroupMember.objects.create(user=request.user, group=group, role='member')
        messages.success(request, f'You joined "{group.name}"!')
        return redirect('group_detail', group_id=group_id)


class LeaveGroupView(LoginRequiredMixin, TemplateView):
    """Leave a group."""
    
    def post(self, request, group_id):
        group = get_object_or_404(CommunityGroup, id=group_id)
        
        # Remove user from group
        GroupMember.objects.filter(user=request.user, group=group).delete()
        messages.success(request, f'You left "{group.name}".')
        return redirect('group_list')


class GroupDiscoveryView(LoginRequiredMixin, TemplateView):
    """Discover and browse public groups with search functionality."""
    template_name = 'community/group_discovery.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        search_query = self.request.GET.get('q', '')
        sort_by = self.request.GET.get('sort', '-created_at')
        
        # Get all public groups
        public_groups = CommunityGroup.objects.filter(is_public=True).prefetch_related('members', 'creator')
        
        # Get user's joined groups
        user_joined_groups = set(user.joined_groups.values_list('id', flat=True))
        
        # Apply search filter
        if search_query:
            public_groups = public_groups.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(creator__first_name__icontains=search_query) |
                Q(creator__last_name__icontains=search_query)
            )
        
        # Apply sorting
        valid_sorts = ['-created_at', 'name', '-members_count']
        if sort_by not in valid_sorts:
            sort_by = '-created_at'
        
        if sort_by == '-members_count':
            public_groups = sorted(public_groups, key=lambda x: x.members.count(), reverse=True)
        else:
            public_groups = public_groups.order_by(sort_by)
        
        # Separate available and joined groups
        available_groups = [g for g in public_groups if g.id not in user_joined_groups]
        
        context['available_groups'] = available_groups
        context['total_groups'] = public_groups.count()
        context['search_query'] = search_query
        context['sort_by'] = sort_by
        context['user_joined_groups'] = user_joined_groups
        
        return context


class SendGroupInviteView(LoginRequiredMixin, TemplateView):
    """Generate and send group invitations to specific users."""
    
    def post(self, request, group_id):
        from django.utils import timezone
        from datetime import timedelta
        import uuid
        
        group = get_object_or_404(CommunityGroup, id=group_id)
        user = request.user
        
        # Check if user is a member
        if not group.members.filter(id=user.id).exists():
            messages.error(request, 'You must be a member of this group.')
            return redirect('group_detail', group_id=group_id)
        
        # Get invitee from POST data
        invitee_id = request.POST.get('invitee_id')
        custom_message = request.POST.get('message', '')
        
        if not invitee_id:
            messages.error(request, 'Please select a user to invite.')
            return redirect('group_detail', group_id=group_id)
        
        try:
            invitee = User.objects.get(id=invitee_id)
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('group_detail', group_id=group_id)
        
        # Check if invitee is already a member
        if group.members.filter(id=invitee.id).exists():
            messages.info(request, f'{invitee.get_full_name()} is already a member of this group.')
            return redirect('group_detail', group_id=group_id)
        
        # Check if invitation already exists
        existing_invite = GroupInvitation.objects.filter(
            group=group,
            invitee=invitee,
            status='pending'
        ).first()
        
        if existing_invite:
            messages.info(request, f'You already have a pending invitation for {invitee.get_full_name()}.')
            return redirect('group_detail', group_id=group_id)
        
        # Create invitation
        from community.models import GroupInvitation
        invite = GroupInvitation.objects.create(
            group=group,
            created_by=user,
            invitee=invitee,
            invite_code=str(uuid.uuid4())[:12].upper(),
            expires_at=timezone.now() + timedelta(days=30),
            message=custom_message
        )
        
        messages.success(request, f'Invitation sent to {invitee.get_full_name()}!')
        return redirect('group_detail', group_id=group_id)


class GroupInvitationsView(LoginRequiredMixin, TemplateView):
    """View pending group invitations for the current user."""
    template_name = 'community/group_invitations.html'
    
    def get_context_data(self, **kwargs):
        from django.utils import timezone
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get all pending invitations for user
        pending_invites = GroupInvitation.objects.filter(
            invitee=user,
            status='pending',
            expires_at__gt=timezone.now()
        ).select_related('group', 'created_by').order_by('-created_at')
        
        # Get expired invitations
        expired_invites = GroupInvitation.objects.filter(
            invitee=user,
            status='pending',
            expires_at__lte=timezone.now()
        ).count()
        
        context['pending_invites'] = pending_invites
        context['expired_count'] = expired_invites
        
        return context
    
    def post(self, request):
        """Accept or decline invitations."""
        action = request.POST.get('action')
        invitation_id = request.POST.get('invitation_id')
        
        try:
            invitation = GroupInvitation.objects.get(id=invitation_id, invitee=request.user)
        except GroupInvitation.DoesNotExist:
            messages.error(request, 'Invitation not found.')
            return redirect('group_invitations')
        
        if action == 'accept':
            from django.utils import timezone
            invitation.status = 'accepted'
            invitation.accepted_at = timezone.now()
            invitation.save()
            
            # Add user to group
            GroupMember.objects.get_or_create(
                user=request.user,
                group=invitation.group,
                defaults={'role': 'member'}
            )
            
            messages.success(request, f'You joined "{invitation.group.name}"!')
        elif action == 'decline':
            invitation.status = 'declined'
            invitation.save()
            messages.info(request, f'You declined the invitation to "{invitation.group.name}".')
        
        return redirect('group_invitations')


# ─────────────────────────────────────────────────────────────────
# COURSE BROADCAST VIEWS (INSTRUCTORS ONLY)
# ─────────────────────────────────────────────────────────────────

class CourseBroadcastView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Instructor can broadcast messages to course participants."""
    template_name = 'community/course_broadcast.html'
    
    def test_func(self):
        return self.request.user.role == 'instructor'
    
    def handle_no_permission(self):
        messages.error(self.request, 'Only instructors can send broadcasts.')
        return redirect('home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get only this instructor's courses
        user_courses = self.request.user.course_set.all()
        form = CourseBroadcastForm()
        form.fields['course'].queryset = user_courses
        context['form'] = form
        return context
    
    def post(self, request):
        form = CourseBroadcastForm(request.POST)
        user_courses = request.user.course_set.all()
        form.fields['course'].queryset = user_courses
        
        if form.is_valid():
            course = form.cleaned_data['course']
            
            # Verify instructor owns this course
            if course.created_by != request.user:
                messages.error(request, 'You can only broadcast to your own courses.')
                return redirect('course_broadcast')
            
            broadcast = form.save(commit=False)
            broadcast.instructor = request.user
            broadcast.save()
            
            messages.success(request, f'Broadcast sent to {course.title}!')
            return redirect('course_broadcasts', course_id=course.id)
        
        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)


class CourseBroadcastListView(LoginRequiredMixin, TemplateView):
    """View all broadcasts for a course."""
    template_name = 'community/course_broadcast_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        
        # Get broadcasts for this course
        broadcasts = CourseBroadcast.objects.filter(course=course).select_related('instructor')
        
        # Check if user is enrolled or instructor
        user = self.request.user
        is_enrolled = Enrollment.objects.filter(course=course, user=user).exists()
        is_instructor = course.created_by == user
        
        context['course'] = course
        context['broadcasts'] = broadcasts
        context['is_enrolled'] = is_enrolled
        context['is_instructor'] = is_instructor
        
        return context


class StudentAnnouncementsView(LoginRequiredMixin, TemplateView):
    """View all incoming broadcast announcements for courses the student is enrolled in."""
    template_name = 'community/announcements.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get courses the user is enrolled in
        enrolled_courses = Course.objects.filter(enrollment__user=user)
        
        # Get all broadcasts from those courses
        broadcasts = CourseBroadcast.objects.filter(course__in=enrolled_courses).select_related('course', 'instructor').order_by('-created_at')
        
        context['broadcasts'] = broadcasts
        return context


def get_or_create_conversation(user1, user2):
    """Helper function to get or create a conversation between two users."""
    conversation = Conversation.objects.filter(
        participants=user1
    ).filter(participants=user2).first()
    
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(user1, user2)
    
    return conversation


# ─────────────────────────────────────────────────────────────────
# GROUP MANAGEMENT VIEWS
# ─────────────────────────────────────────────────────────────────

class GroupEditView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Edit group details - admin only."""
    template_name = 'community/edit_group.html'
    
    def test_func(self):
        """Check if user is group admin."""
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(CommunityGroup, id=group_id)
        
        # Check if user is admin
        try:
            group_member = GroupMember.objects.get(user=self.request.user, group=group)
            return group_member.role == 'admin'
        except GroupMember.DoesNotExist:
            return False
    
    def handle_no_permission(self):
        """Redirect to group detail if not admin."""
        group_id = self.kwargs.get('group_id')
        messages.error(self.request, 'You do not have permission to edit this group.')
        return redirect('group_detail', group_id=group_id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = get_object_or_404(CommunityGroup, id=kwargs.get('group_id'))
        context['group'] = group
        context['form'] = EditGroupForm(instance=group)
        return context
    
    def post(self, request, group_id):
        group = get_object_or_404(CommunityGroup, id=group_id)
        
        # Check admin permission again
        if not self.test_func():
            messages.error(request, 'You do not have permission to edit this group.')
            return redirect('group_detail', group_id=group_id)
        
        form = EditGroupForm(request.POST, request.FILES, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, f'Group "{group.name}" updated successfully!')
            return redirect('group_detail', group_id=group.id)
        
        context = {'group': group, 'form': form}
        return render(request, self.template_name, context)


class GroupMembersView(LoginRequiredMixin, TemplateView):
    """View and manage group members - admin only."""
    template_name = 'community/group_members.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = get_object_or_404(CommunityGroup, id=kwargs.get('group_id'))
        
        # Get all members
        members = GroupMember.objects.filter(group=group).select_related('user')
        
        # Check if current user is admin
        try:
            user_membership = GroupMember.objects.get(user=self.request.user, group=group)
            is_admin = user_membership.role == 'admin'
        except GroupMember.DoesNotExist:
            is_admin = False
        
        context['group'] = group
        context['members'] = members
        context['is_admin'] = is_admin
        return context


class RemoveGroupMemberView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Remove a member from group - admin only."""
    
    def test_func(self):
        """Check if user is group admin."""
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(CommunityGroup, id=group_id)
        
        try:
            group_member = GroupMember.objects.get(user=self.request.user, group=group)
            return group_member.role == 'admin'
        except GroupMember.DoesNotExist:
            return False
    
    def post(self, request, group_id, member_id):
        group = get_object_or_404(CommunityGroup, id=group_id)
        member_user = get_object_or_404(User, id=member_id)
        
        # Check admin permission
        if not self.test_func():
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        # Prevent removing creator
        if group.creator == member_user:
            return JsonResponse({'error': 'Cannot remove group creator'}, status=400)
        
        # Remove member
        try:
            GroupMember.objects.get(user=member_user, group=group).delete()
            return JsonResponse({'success': True, 'message': f'{member_user.first_name or member_user.username} has been removed from the group.'})
        except GroupMember.DoesNotExist:
            return JsonResponse({'error': 'Member not found'}, status=404)
