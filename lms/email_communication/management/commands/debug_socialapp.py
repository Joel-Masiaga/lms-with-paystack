#!/usr/bin/env python
"""
Django management command to list all SocialApp entries and debug MultipleObjectsReturned
"""

from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from django.db import connection


class Command(BaseCommand):
    help = 'List all SocialApp entries to debug MultipleObjectsReturned error'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('🔍 DEBUGGING SOCIALAPP CONFIGURATION'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # Get ALL SocialApps
        all_apps = SocialApp.objects.all()
        self.stdout.write(f'\nTotal SocialApp entries: {all_apps.count()}')
        
        for app in all_apps:
            self.stdout.write(f'\nApp ID={app.id}:')
            self.stdout.write(f'  Provider: {app.provider}')
            self.stdout.write(f'  Name: {app.name}')
            self.stdout.write(f'  Client ID: {app.client_id[:40]}...' if len(app.client_id) > 40 else f'  Client ID: {app.client_id}')
            self.stdout.write(f'  Sites: {[s.domain for s in app.sites.all()]}')

        # Check for duplicates by provider
        self.stdout.write(f'\n🔍 Checking for duplicate providers...')
        providers = {}
        for app in all_apps:
            if app.provider in providers:
                providers[app.provider].append(app.id)
            else:
                providers[app.provider] = [app.id]

        for provider, ids in providers.items():
            if len(ids) > 1:
                self.stdout.write(self.style.WARNING(f'  ⚠️  DUPLICATE PROVIDER: "{provider}" has {len(ids)} entries (IDs: {ids})'))
            else:
                self.stdout.write(self.style.SUCCESS(f'  ✅ Provider "{provider}": {len(ids)} entry'))

        # Raw database query to be absolutely sure
        self.stdout.write(f'\n📊 Direct database check (raw SQL):')
        with connection.cursor() as cursor:
            cursor.execute('SELECT id, provider, name, client_id FROM socialaccount_socialapp ORDER BY provider, id')
            rows = cursor.fetchall()
            self.stdout.write(f'  Total rows: {len(rows)}')
            for row in rows:
                self.stdout.write(f'    ID={row[0]}, Provider={row[1]}, Name={row[2]}, ClientID={row[3][:30]}...')

        self.stdout.write('\n' + self.style.SUCCESS('=' * 70))
