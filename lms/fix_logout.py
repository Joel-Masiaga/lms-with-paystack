import os

with open('users/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
'''def custom_logout(request):
    logout(request)  # Log out the user
    return redirect('logout')''',
'''def custom_logout(request):
    logout(request)  # Log out the user
    return redirect('login')'''
)

with open('users/views.py', 'w', encoding='utf-8') as f:
    f.write(text)
