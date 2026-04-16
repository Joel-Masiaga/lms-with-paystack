from django import template

register = template.Library()

@register.filter
def get_display_name(user):
    """
    Returns the display name for a user.
    If the user has a first and/or last name, returns that.
    Otherwise, returns the email username (everything before @).
    """
    if not user:
        return "Unknown"
    
    # Check if user has first name or last name
    full_name = user.get_full_name().strip() if hasattr(user, 'get_full_name') else ""
    if full_name:
        return full_name
    
    # Fallback to email username (before @)
    if hasattr(user, 'email') and user.email:
        return user.email.split('@')[0]
    
    return "User"

@register.filter
def get_display_name_short(user):
    """
    Returns a short display name (first word only).
    If the user has a first and/or last name, returns first name only.
    Otherwise, returns first word of email username.
    """
    if not user:
        return "Unknown"
    
    full_name = user.get_full_name().strip() if hasattr(user, 'get_full_name') else ""
    if full_name:
        # Return just the first word (first name)
        return full_name.split()[0]
    
    # Fallback to first word of email username
    if hasattr(user, 'email') and user.email:
        email_user = user.email.split('@')[0]
        return email_user.split('.')[0] or email_user
    
    return "User"

@register.filter
def get_avatar_initials(user):
    """
    Returns initials for avatar generation.
    If user has first and last name, returns first letter of each.
    Otherwise, returns first two letters of email (uppercase).
    """
    if not user:
        return "U"
    
    # Try to get initials from first and last name
    first_name = ""
    last_name = ""
    
    # Check from profile if exists
    if hasattr(user, 'profile') and user.profile:
        first_name = (user.profile.first_name or "").strip()
        last_name = (user.profile.last_name or "").strip()
    
    # Fallback to User model first_name and last_name
    if not first_name:
        first_name = (user.first_name or "").strip()
    if not last_name:
        last_name = (user.last_name or "").strip()
    
    # If we have both first and last name
    if first_name and last_name:
        return (first_name[0] + last_name[0]).upper()
    
    # If we have at least first name
    if first_name:
        return first_name[0].upper()
    
    # Fallback to email - take first two letters
    if hasattr(user, 'email') and user.email:
        # Get the part before @ and uppercase
        email_part = user.email.split('@')[0]
        if len(email_part) >= 2:
            return email_part[:2].upper()
        elif len(email_part) == 1:
            return email_part.upper()
    
    return "U"

@register.filter
def get_avatar_label(user):
    """
    Returns a label for avatar - either initials or first letters of email.
    This is used for generating avatar backgrounds when no profile image exists.
    """
    if not user:
        return "Unknown"
    
    # Check if user has a full name (from profile or user model)
    first_name = ""
    last_name = ""
    
    if hasattr(user, 'profile') and user.profile:
        first_name = (user.profile.first_name or "").strip()
        last_name = (user.profile.last_name or "").strip()
    
    if not first_name:
        first_name = (user.first_name or "").strip()
    if not last_name:
        last_name = (user.last_name or "").strip()
    
    # Return full name if available
    if first_name and last_name:
        return f"{first_name} {last_name}"
    elif first_name:
        return first_name
    elif last_name:
        return last_name
    
    # Fallback to formatted email
    if hasattr(user, 'email') and user.email:
        email_part = user.email.split('@')[0]
        # Convert email_part like "nko.pooa" to "Nko Pooa"
        words = email_part.replace('.', ' ').replace('_', ' ').replace('-', ' ').split()
        return ' '.join(word.capitalize() for word in words if word)
    
    return "Unknown"

@register.filter
def mul(value, arg):
    """Multiplies the value by the argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value
