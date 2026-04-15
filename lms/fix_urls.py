import os

with open('lms/urls.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
'''    path('accounts/login/', RedirectView.as_view(pattern_name='login', permanent=True), name='account_login'),
    path('accounts/', include('allauth.urls')),''',
'''    path('accounts/login/', RedirectView.as_view(pattern_name='login', permanent=True), name='account_login'),
    path('accounts/logout/', RedirectView.as_view(pattern_name='logout', permanent=True), name='account_logout'),
    path('accounts/', include('allauth.urls')),'''
)

with open('lms/urls.py', 'w', encoding='utf-8') as f:
    f.write(text)
