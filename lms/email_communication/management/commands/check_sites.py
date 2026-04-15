#!/usr/bin/env python
"""
Django management command to check and fix Site configuration issues
"""

from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.db import transaction


class Command(BaseCommand):
    help = 'Check and fix Site and SocialApp configuration'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('🔍 CHECKING SITE CONFIGURATION'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # Check all sites
        all_sites = Site.objects.all()
        self.stdout.write(f'\nTotal sites in database: {all_sites.count()}')
        for site in all_sites:
            self.stdout.write(f'  ID={site.id}: {site.domain} ({site.name})')

        # Check for duplicates
        self.stdout.write(f'\n🔍 Checking for duplicate domains...')
        domains = {}
        duplicates = []
        
        for site in all_sites:
            if site.domain in domains:
                self.stdout.write(self.style.WARNING(f'  ⚠️  DUPLICATE: "{site.domain}" (IDs: {domains[site.domain]} and {site.id})'))
                duplicates.append((site.domain, domains[site.domain], site.id))
            else:
                domains[site.domain] = site.id

        if not duplicates:
            self.stdout.write(self.style.SUCCESS('  ✅ No duplicate domains found'))
        
        # If duplicates exist, clean them up
        if duplicates:
            self.stdout.write(f'\n🔧 Fixing duplicates...')
            try:
                with transaction.atomic():
                    for domain, keep_id, delete_id in duplicates:
                        # Move any SocialApps to the kept site
                        delete_site = Site.objects.get(pk=delete_id)
                        keep_site = Site.objects.get(pk=keep_id)
                        
                        # Transfer SocialApps
                        for app in delete_site.socialapp_set.all():
                            if not app.sites.filter(pk=keep_id).exists():
                                app.sites.add(keep_site)
                            app.sites.remove(delete_site)
                        
                        # Delete the duplicate site
                        delete_site.delete()
                        self.stdout.write(self.style.SUCCESS(f'  ✅ Deleted duplicate site ID={delete_id} ({domain})'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error fixing duplicates: {e}'))
                return

        # Check Google app
        self.stdout.write(f'\n🔑 Checking Google OAuth App...')
        google_apps = SocialApp.objects.filter(provider='google')
        self.stdout.write(f'Total Google apps: {google_apps.count()}')

        for app in google_apps:
            self.stdout.write(f'\nApp: {app.name} (ID={app.id})')
            self.stdout.write(f'  Client ID: {app.client_id[:30]}...')
            self.stdout.write(f'  Sites ({app.sites.count()}):')
            for site in app.sites.all():
                self.stdout.write(f'    - {site.domain}')

        # Summary
        self.stdout.write('\n' + self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('✅ SITE CHECK COMPLETE!'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('''
If MultipleObjectsReturned error persists:
1. Restart Django server
2. Clear browser cookies
3. Try again

If still issues, contact support or manually check Django Admin:
http://localhost:8000/admin/sites/site/
        ''')
        self.stdout.write(self.style.SUCCESS('=' * 70))
