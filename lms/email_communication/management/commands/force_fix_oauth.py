#!/usr/bin/env python
"""
Django management command to FORCEFULLY fix duplicate Google OAuth apps
This command will delete ALL Google apps except one and rebuild clean relationships
"""

from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.db import transaction, connection


class Command(BaseCommand):
    help = 'Force-fix duplicate Google OAuth apps causing MultipleObjectsReturned'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('🔨 FORCE-FIXING GOOGLE OAUTH CONFIGURATION'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # Step 1: Check raw database
        self.stdout.write('\n📊 Step 1: Checking raw database state...')
        with connection.cursor() as cursor:
            cursor.execute('SELECT id, provider, name FROM socialaccount_socialapp WHERE provider = "google"')
            google_apps_raw = cursor.fetchall()
            self.stdout.write(f'  Found {len(google_apps_raw)} Google apps in database:')
            for row in google_apps_raw:
                self.stdout.write(f'    - ID={row[0]}, Provider={row[1]}, Name={row[2]}')

        # Step 2: Force delete all duplicates
        if len(google_apps_raw) > 1:
            self.stdout.write(self.style.WARNING(f'\n⚠️  DANGER: {len(google_apps_raw)} duplicate Google apps found!'))
            self.stdout.write('🔨 FORCE-DELETING duplicates...')
            
            try:
                with transaction.atomic():
                    # Get all and delete all except first
                    all_google = SocialApp.objects.filter(provider='google').order_by('id')
                    apps_to_delete = all_google[1:]  # Keep first, delete rest
                    
                    deleted_ids = list(apps_to_delete.values_list('id', flat=True))
                    deleted_count = apps_to_delete.delete()[0]
                    
                    self.stdout.write(self.style.SUCCESS(f'  ✅ Deleted {deleted_count} duplicate apps (IDs: {deleted_ids})'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Error deleting duplicates: {e}'))
                return

        # Step 3: Verify only one Google app remains
        self.stdout.write('\n📱 Step 2: Verifying single Google app...')
        google_app = SocialApp.objects.filter(provider='google').first()
        
        if not google_app:
            self.stdout.write(self.style.ERROR('  ❌ No Google app found!'))
            from django.conf import settings
            
            GOOGLE_CLIENT_ID = settings.SOCIALACCOUNT_PROVIDERS['google']['APP'].get('client_id')
            GOOGLE_SECRET = settings.SOCIALACCOUNT_PROVIDERS['google']['APP'].get('secret')
            
            if GOOGLE_CLIENT_ID and GOOGLE_SECRET:
                self.stdout.write('  Creating new Google app...')
                google_app = SocialApp.objects.create(
                    provider='google',
                    name='Google OAuth',
                    client_id=GOOGLE_CLIENT_ID,
                    secret=GOOGLE_SECRET,
                )
                self.stdout.write(self.style.SUCCESS(f'  ✅ Created Google app ID={google_app.id}'))
            else:
                self.stdout.write(self.style.ERROR('  ❌ No Google credentials in settings!'))
                return
        else:
            self.stdout.write(self.style.SUCCESS(f'  ✅ Google app exists: {google_app.name} (ID={google_app.id})'))

        # Step 4: Verify only one Site (ID=1)
        self.stdout.write('\n🌐 Step 3: Verifying single Site...')
        all_sites = Site.objects.all()
        
        if all_sites.count() > 1:
            self.stdout.write(self.style.WARNING(f'  ⚠️  DANGER: {all_sites.count()} sites found!'))
            self.stdout.write('  Force-deleting extra sites...')
            
            try:
                with transaction.atomic():
                    # Keep ID=1, delete others
                    sites_to_delete = Site.objects.exclude(pk=1)
                    deleted_count = sites_to_delete.delete()[0]
                    self.stdout.write(self.style.SUCCESS(f'  ✅ Deleted {deleted_count} duplicate sites'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Error deleting sites: {e}'))
                return
        
        # Get the official site
        site = Site.objects.get(pk=1)
        self.stdout.write(self.style.SUCCESS(f'  ✅ Site: {site.domain} (ID={site.id})'))

        # Step 5: Clean and rebuild M2M relationship
        self.stdout.write('\n🔗 Step 4: Rebuilding M2M relationships...')
        try:
            with transaction.atomic():
                # Clear all relationships for this app
                google_app.sites.clear()
                
                # Add only site 1
                google_app.sites.add(site)
                
                self.stdout.write(self.style.SUCCESS('  ✅ Cleaned and rebuilt M2M relationship'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error rebuilding M2M: {e}'))
            return

        # Step 6: Verify with raw query
        self.stdout.write('\n📊 Step 5: Verifying final state (raw SQL)...')
        with connection.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM socialaccount_socialapp WHERE provider = "google"')
            google_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM django_site')
            site_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM socialaccount_socialapp_sites')
            relationship_count = cursor.fetchone()[0]
            
            self.stdout.write(f'  Google apps: {google_count}')
            self.stdout.write(f'  Sites: {site_count}')
            self.stdout.write(f'  M2M relationships: {relationship_count}')

        # Summary
        self.stdout.write('\n' + self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('✅ FORCE-FIX COMPLETE!'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('''
✓ All duplicate Google apps deleted
✓ All duplicate sites deleted
✓ M2M relationships rebuilt clean
✓ Database verified

NEXT STEPS:
1. Stop Django server (Ctrl+C)
2. CLEAR PYTHON CACHE:
   a) Find __pycache__ in lms folder
   b) Delete entire __pycache__ directory
   c) Or run: find . -type d -name __pycache__ -exec rm -rf {} + (Linux/Mac)
3. Clear browser cookies (Ctrl+Shift+Delete)
4. Restart Django: python manage.py runserver
5. Try /login again

The error should now be GONE!
        ''')
        self.stdout.write(self.style.SUCCESS('=' * 70))
