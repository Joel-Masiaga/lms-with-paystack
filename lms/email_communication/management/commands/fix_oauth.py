#!/usr/bin/env python
"""
Django management command to fix Google OAuth configuration
Place this in: lms/email_communication/management/commands/fix_oauth.py
"""

from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.db import transaction
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Fix Google OAuth configuration for local development'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('🔧 FIXING GOOGLE OAUTH CONFIGURATION'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # Step 1: Update Site configuration
        self.stdout.write('\n📍 Step 1: Updating Django Sites configuration...')
        try:
            with transaction.atomic():
                site, created = Site.objects.get_or_create(pk=1)
                old_domain = site.domain
                old_name = site.name
                
                site.domain = "127.0.0.1:8000"
                site.name = "Paystack LMS (Local Dev)"
                site.save()
                
                if created:
                    self.stdout.write(f"  ✅ Created new site: {site.domain}")
                else:
                    self.stdout.write(f"  ✅ Updated site configuration:")
                    self.stdout.write(f"     Old: {old_domain} ({old_name})")
                    self.stdout.write(f"     New: {site.domain} ({site.name})")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error updating Site: {e}'))
            return

        # Step 2: Verify Social Application for Google
        self.stdout.write('\n🔑 Step 2: Checking Google OAuth Social Application...')

        GOOGLE_CLIENT_ID = settings.SOCIALACCOUNT_PROVIDERS['google']['APP'].get('client_id', '')
        GOOGLE_SECRET = settings.SOCIALACCOUNT_PROVIDERS['google']['APP'].get('secret', '')

        if not GOOGLE_CLIENT_ID or not GOOGLE_SECRET:
            self.stdout.write(self.style.WARNING(
                '  ⚠️  WARNING: Google OAuth credentials not set properly\n'
                '     Please check GOOGLE_AUTH_CLIENT_ID and GOOGLE_AUTH_SECRET in .env\n'
                '     Then restart Django and run this command again.'
            ))
            return

        try:
            with transaction.atomic():
                google_app, created = SocialApp.objects.get_or_create(
                    provider='google',
                    defaults={
                        'name': 'Google OAuth',
                        'client_id': GOOGLE_CLIENT_ID,
                        'secret': GOOGLE_SECRET,
                    }
                )
                
                # Update credentials if they changed
                if google_app.client_id != GOOGLE_CLIENT_ID:
                    google_app.client_id = GOOGLE_CLIENT_ID
                    google_app.secret = GOOGLE_SECRET
                    google_app.save()
                    self.stdout.write('  ✅ Updated Google credentials')
                else:
                    self.stdout.write(f'  ✅ Google app found: {google_app.name}')
                
                # Ensure correct site is associated
                if not google_app.sites.filter(pk=1).exists():
                    google_app.sites.clear()  # Remove old sites
                    google_app.sites.add(Site.objects.get(pk=1))
                    self.stdout.write('  ✅ Linked Google app to site 127.0.0.1:8000')
                
                self.stdout.write(f'  Provider: {google_app.provider}')
                self.stdout.write(f'  Client ID: {google_app.client_id[:30]}...')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error configuring Social Application: {e}'))
            return

        # Step 3: Summary and next steps
        self.stdout.write('\n' + self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('✅ CONFIGURATION COMPLETE!'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('''
✓ Django Site updated to: 127.0.0.1:8000
✓ Google OAuth app configured
✓ Social app linked to site

NEXT STEPS:
1. Restart Django server (Ctrl+C, then python manage.py runserver)
2. Clear browser cookies for localhost:8000
3. Go to http://127.0.0.1:8000/register
4. Click "Sign up Google"
5. You should now see redirect to 127.0.0.1:8000 (not example.com)

IMPORTANT:
Your Google Client ID must be configured in Google Cloud Console for:
  Redirect URI: http://127.0.0.1:8000/accounts/google/login/callback/
        ''')
        self.stdout.write(self.style.SUCCESS('=' * 70))
