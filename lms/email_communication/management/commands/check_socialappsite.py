#!/usr/bin/env python
"""
Django management command to check SocialAppSite relationships
"""

from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.db import connection


class Command(BaseCommand):
    help = 'Check and fix broken SocialAppSite relationships'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('🔍 CHECKING SOCIALAPPSITE RELATIONSHIPS'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # Check the through table
        self.stdout.write(f'\n📊 Checking socialaccount_socialapp_sites table (M2M):')
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM socialaccount_socialapp_sites ORDER BY socialapp_id, site_id')
            rows = cursor.fetchall()
            self.stdout.write(f'  Total relationships: {len(rows)}')
            for row in rows:
                self.stdout.write(f'    App ID={row[0]}, Site ID={row[1]}')

        # Now check if there are any orphaned references
        self.stdout.write(f'\n🔍 Checking for orphaned references:')
        orphaned = False
        
        with connection.cursor() as cursor:
            # Check for app IDs that don't exist
            cursor.execute('''
                SELECT DISTINCT socialapp_id FROM socialaccount_socialapp_sites 
                WHERE socialapp_id NOT IN (SELECT id FROM socialaccount_socialapp)
            ''')
            orphaned_apps = cursor.fetchall()
            if orphaned_apps:
                self.stdout.write(self.style.ERROR(f'  ⚠️  Orphaned app IDs: {orphaned_apps}'))
                orphaned = True
            
            # Check for site IDs that don't exist
            cursor.execute('''
                SELECT DISTINCT site_id FROM socialaccount_socialapp_sites 
                WHERE site_id NOT IN (SELECT id FROM django_site)
            ''')
            orphaned_sites = cursor.fetchall()
            if orphaned_sites:
                self.stdout.write(self.style.ERROR(f'  ⚠️  Orphaned site IDs: {orphaned_sites}'))
                orphaned = True
        
        if not orphaned:
            self.stdout.write(self.style.SUCCESS('  ✅ No orphaned references found'))

        # Check each app's sites
        self.stdout.write(f'\n📱 Apps and their sites:')
        for app in SocialApp.objects.all():
            sites = app.sites.all()
            self.stdout.write(f'  App {app.id} ({app.provider}): {[s.domain for s in sites]} ({sites.count()} sites)')

        # Summary
        self.stdout.write('\n' + self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('✅ RELATIONSHIP CHECK COMPLETE'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
