"""
Utilities for HTMX and WebSocket integration in the community app.
Provides helper functions for async operations and HTMX endpoints.
"""

import json
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from asgiref.sync import sync_to_async
from .models import DirectMessage, GroupMessage, CommunityGroup


def render_message_html(message, is_own_message=False):
    """
    Render a single message HTML for insertion into the DOM.
    """
    if isinstance(message, DirectMessage):
        template_name = 'community/includes/direct_message_item.html'
    elif isinstance(message, GroupMessage):
        template_name = 'community/includes/group_message_item.html'
    else:
        return ''
    
    context = {
        'message': message,
        'is_own_message': is_own_message,
        'user': message.sender,
    }
    
    return render_to_string(template_name, context)


@login_required
@require_http_methods(["POST"])
def upload_message_attachment(request):
    """
    AJAX endpoint for uploading file attachments to messages.
    Returns JSON with file info.
    """
    try:
        if 'file' not in request.FILES:
            return HttpResponse(
                json.dumps({'error': 'No file provided'}),
                status=400,
                content_type='application/json'
            )
        
        file = request.FILES['file']
        max_size = 50 * 1024 * 1024  # 50 MB
        
        if file.size > max_size:
            return HttpResponse(
                json.dumps({'error': f'File size exceeds {max_size / 1024 / 1024}MB limit'}),
                status=400,
                content_type='application/json'
            )
        
        # Save file directly to the location where FileField expects it
        from django.core.files.storage import default_storage
        import uuid
        from datetime import datetime
        
        # Generate filename in the same directory structure as FileField's upload_to
        today = datetime.now()
        file_name = f"message_attachments/{today.year:04d}/{today.month:02d}/{today.day:02d}/{uuid.uuid4().hex}_{file.name}"
        file_path = default_storage.save(file_name, file)
        file_url = default_storage.url(file_path)
        
        return HttpResponse(
            json.dumps({
                'success': True,
                'file_url': file_url,
                'file_path': file_path,
                'file_name': file.name,
            }),
            content_type='application/json'
        )
    except Exception as e:
        return HttpResponse(
            json.dumps({'error': str(e)}),
            status=500,
            content_type='application/json'
        )



@login_required
@require_http_methods(["POST"])
def upload_group_message_attachment(request):
    """
    AJAX endpoint for uploading file attachments to group messages.
    Returns JSON with file info.
    """
    try:
        if 'file' not in request.FILES:
            return HttpResponse(
                json.dumps({'error': 'No file provided'}),
                status=400,
                content_type='application/json'
            )
        
        file = request.FILES['file']
        max_size = 50 * 1024 * 1024  # 50 MB
        
        if file.size > max_size:
            return HttpResponse(
                json.dumps({'error': f'File size exceeds {max_size / 1024 / 1024}MB limit'}),
                status=400,
                content_type='application/json'
            )
        
        # Save file directly to the location where FileField expects it
        from django.core.files.storage import default_storage
        import uuid
        from datetime import datetime
        
        # Generate filename in the same directory structure as FileField's upload_to
        today = datetime.now()
        file_name = f"message_attachments/{today.year:04d}/{today.month:02d}/{today.day:02d}/{uuid.uuid4().hex}_{file.name}"
        file_path = default_storage.save(file_name, file)
        file_url = default_storage.url(file_path)
        
        return HttpResponse(
            json.dumps({
                'success': True,
                'file_url': file_url,
                'file_path': file_path,
                'file_name': file.name,
            }),
            content_type='application/json'
        )
    except Exception as e:
        return HttpResponse(
            json.dumps({'error': str(e)}),
            status=500,
            content_type='application/json'
        )



@login_required
@require_http_methods(["GET"])
def load_message_history(request, user_id):
    """
    HTMX endpoint for loading message history in direct message conversations.
    Supports pagination with limit and offset parameters.
    """
    limit = int(request.GET.get('limit', 20))
    offset = int(request.GET.get('offset', 0))
    
    messages = DirectMessage.objects.filter(
        sender_id__in=[request.user.id, user_id],
        recipient_id__in=[request.user.id, user_id]
    ).select_related('sender', 'recipient').order_by('-created_at')[offset:offset+limit]
    
    # Reverse to show oldest first
    messages = list(reversed(messages))
    
    html = ''
    for message in messages:
        html += render_message_html(message, message.sender == request.user)
    
    return HttpResponse(html)


@login_required
@require_http_methods(["GET"])
def load_group_message_history(request, group_id):
    """
    HTMX endpoint for loading message history in group conversations.
    Supports pagination with limit and offset parameters.
    """
    group = get_object_or_404(CommunityGroup, id=group_id)
    limit = int(request.GET.get('limit', 20))
    offset = int(request.GET.get('offset', 0))
    
    messages = group.messages.all().select_related('sender').order_by('-created_at')[offset:offset+limit]
    
    # Reverse to show oldest first
    messages = list(reversed(messages))
    
    html = ''
    for message in messages:
        html += render_message_html(message, message.sender == request.user)
    
    return HttpResponse(html)


async def get_message_data_async(message):
    """
    Async helper to get message data for WebSocket transmission.
    """
    await sync_to_async(lambda: message.fresh_from_db())()
    from django.utils import timezone
    local_time = timezone.localtime(message.created_at)
    return {
        'id': message.id,
        'content': message.content,
        'sender_id': message.sender_id,
        'sender_name': message.sender.get_full_name() or message.sender.username,
        'timestamp': local_time.strftime('%H:%M'),
        'has_attachment': bool(message.attachment),
        'attachment_url': message.attachment.url if message.attachment else None,
    }
