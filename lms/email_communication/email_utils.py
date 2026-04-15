"""
Email utilities for validation and handling
"""
import re
from django.core.exceptions import ValidationError


def is_valid_email(email):
    """
    Validate email format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_and_filter_recipients(email_list):
    """
    Validate email list and return valid and invalid emails separately
    
    Returns:
        tuple: (valid_emails, invalid_emails)
    """
    valid_emails = []
    invalid_emails = []
    
    for email in email_list:
        email = email.strip()
        if is_valid_email(email):
            valid_emails.append(email)
        else:
            invalid_emails.append(email)
    
    return valid_emails, invalid_emails
