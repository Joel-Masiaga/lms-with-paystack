#!/usr/bin/env python
"""
Django management command to clean up duplicate Social Applications
and fix the MultipleObjectsReturned error
"""

from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.db import transaction


class Command(BaseCommand):
    help = 'Clean up duplicate Social Applications and fix MultipleObjectsReturned error'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('🔍 CHECKING FOR DUPLICATE SOCIAL APPLICATIONS'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # Get all Google apps
        google_apps = SocialApp.objects.filter(provider='google')
        
        self.stdout.write(f'\nFound {google_apps.count()} Google OAuth app(s)')
        
        if google_apps.count() == 0:
            self.stdout.write(self.style.WARNING('⚠️  No Google OAuth apps found!'))
            self.stdout.write('Creating a new one...')
            
            from django.conf import settings
            GOOGLE_CLIENT_ID = settings.SOCIALACCOUNT_PROVIDERS['google']['APP'].get('client_id')
            GOOGLE_SECRET = settings.SOCIALACCOUNT_PROVIDERS['google']['APP'].get('secret')
            
            if not GOOGLE_CLIENT_ID:
                self.stdout.write(self.style.ERROR('❌ No Google credentials in settings!'))
                return
            
            google_app = SocialApp.objects.create(
                provider='google',
                name='Google OAuth',
                client_id=GOOGLE_CLIENT_ID,
                secret=GOOGLE_SECRET,
            )
            google_app.sites.add(Site.objects.get(pk=1))
            self.stdout.write(self.style.SUCCESS('✅ Created new Google OAuth app'))
            return
        
        if google_apps.count() == 1:
            self.stdout.write(self.style.SUCCESS('✅ Only one Google OAuth app exists (good!)'))
            app = google_apps.first()
            
            # Check if it's linked to site 1
            if not app.sites.filter(pk=1).exists():
                self.stdout.write('⚠️  App is not linked to site 127.0.0.1:8000')
                app.sites.clear()
                app.sites.add(Site.objects.get(pk=1))
                self.stdout.write('✅ Linked to site 127.0.0.1:8000')
            
            self.stdout.write(f'\nApp Details:')
            self.stdout.write(f'  Provider: {app.provider}')
            self.stdout.write(f'  Name: {app.name}')
            self.stdout.write(f'  Client ID: {app.client_id[:30]}...')
            self.stdout.write(f'  Sites: {", ".join([s.domain for s in app.sites.all()])}')
            return
        
        # Multiple Google apps found - consolidate
        self.stdout.write(self.style.WARNING(f'⚠️  Found {google_apps.count()} duplicate Google OAuth apps!'))
        self.stdout.write('\nDuplicate apps:')
        
        for i, app in enumerate(google_apps, 1):
            self.stdout.write(f'  {i}. ID={app.id}, Name={app.name}, ClientID={app.client_id[:20]}...')
        
        self.stdout.write('\n🔧 Consolidating apps...')
        
        try:
            with transaction.atomic():
                # Keep the first app, delete others
                apps_to_keep = google_apps.first()
                apps_to_delete = google_apps.exclude(pk=apps_to_keep.pk)
                
                # Clear all site associations first
                apps_to_keep.sites.clear()
                
                # Add the correct site
                apps_to_keep.sites.add(Site.objects.get(pk=1))
                
                # Delete duplicate apps
                deleted_count = apps_to_delete.count()
                apps_to_delete.delete()
                
                self.stdout.write(self.style.SUCCESS(f'✅ Deleted {deleted_count} duplicate app(s)'))
                self.stdout.write(self.style.SUCCESS(f'✅ Kept app: {apps_to_keep.name} (ID={apps_to_keep.id})'))
                self.stdout.write(self.style.SUCCESS(f'✅ Linked to site: 127.0.0.1:8000'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error consolidating apps: {e}'))
            return

        # Summary
        self.stdout.write('\n' + self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('✅ CLEANUP COMPLETE!'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('''
NEXT STEPS:
1. Restart Django server (Ctrl+C, then python manage.py runserver)
2. Clear browser cookies for 127.0.0.1:8000
3. Try accessing http://127.0.0.1:8000/login
4. You should no longer see the MultipleObjectsReturned error
        ''')
        self.stdout.write(self.style.SUCCESS('=' * 70))
