from .models import SubscribedUser, Notification

def subscription_context(request):
    is_subscribed = False
    if request.user.is_authenticated:
        subscription = SubscribedUser.objects.filter(user=request.user).first() 
        if subscription and subscription.subscribed:
            is_subscribed = True
    return {
        'is_subscribed': is_subscribed,
    }

def notifications_processor(request):
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')[:5]
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return {
            'unread_notifications': unread_notifications,
            'unread_count': unread_count,
        }
    return {
        'unread_notifications': [],
        'unread_count': 0,
    }