with open('users/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('        email.attach_alternative(html_message, \"text/html\")\\n', '        email.attach_alternative(html_message, \"text/html\")\n')

with open('users/views.py', 'w', encoding='utf-8') as f:
    f.write(text)
