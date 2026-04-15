from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from users.models import OTP

@receiver(user_signed_up)
def user_signed_up_signal(request, user, **kwargs):
    if hasattr(user, 'socialaccount_set') and user.socialaccount_set.exists():
        user = kwargs.get('user')
        # We no longer auto-verify emails here because we want them to go through OTP.
        # The OTP is sent in the adapter's save_user.
        pass
