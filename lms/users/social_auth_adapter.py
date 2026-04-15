from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from users.models import OTP, User

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return

        if 'email' not in sociallogin.account.extra_data:
            return

        email = sociallogin.account.extra_data.get('email').lower()
        try:
            user = User.objects.get(email__iexact=email)
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        user.is_email_verified = False
        user.save()
        otp_obj, created = OTP.objects.get_or_create(user=user)
        otp_obj.is_verified = False
        otp_obj.save()
        
        # Send OTP for social users
        from users.views import send_verification_email
        send_verification_email(request, user, otp_obj)
        
        return user
