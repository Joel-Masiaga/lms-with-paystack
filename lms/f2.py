import re

with open('users/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
'''        email.attach_alternative(html_message, \"text/html\")
        email.send(fail_silently=False)''',
'''        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [user.email]
        
        email = EmailMultiAlternatives(subject, message, from_email, to_email)
        email.attach_alternative(html_message, \"text/html\")
        email.send(fail_silently=False)'''
)

with open('users/views.py', 'w', encoding='utf-8') as f:
    f.write(text)
