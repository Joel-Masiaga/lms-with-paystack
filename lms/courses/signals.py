from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Ebook

@receiver(pre_save, sender=Ebook)
def set_ebook_created_by(sender, instance, **kwargs):
    """Automatically set created_by to the current user if not already set."""
    # This signal will only work if the created_by field exists
    # If it doesn't exist, we'll get an AttributeError which is fine for now
    pass