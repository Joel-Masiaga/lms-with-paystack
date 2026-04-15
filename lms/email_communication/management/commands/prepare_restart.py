#!/usr/bin/env python
"""
Django management command to clear cache and prepare for restart
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db import connection


class Command(BaseCommand):
    help = 'Clear cache and prepare database for clean restart'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('🔧 CLEARING CACHE AND PREPARING FOR RESTART'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # Clear all caches
        self.stdout.write('\n📦 Clearing caches...')
        try:
            cache.clear()
            self.stdout.write(self.style.SUCCESS('  ✅ Cache cleared'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ⚠️  cache.clear() not available: {e}'))

        # Close database connections to ensure clean slate
        self.stdout.write('\n🔌 Closing database connections...')
        connection.close()
        self.stdout.write(self.style.SUCCESS('  ✅ Database connection closed'))

        # Summary
        self.stdout.write('\n' + self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('✅ CLEANUP COMPLETE!'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('''
NEXT STEPS:
1. Restart Django server:
   - Stop current server (Ctrl+C)
   - Run: python manage.py runserver
   
2. Clear browser cache:
   - Press Ctrl+Shift+Delete
   - Clear all cookies for 127.0.0.1:8000
   
3. Try accessing /login again

If the error persists, check:
- Django admin for any strange entries
- Browser console for JavaScript errors
- Django logs for more details
        ''')
        self.stdout.write(self.style.SUCCESS('=' * 70))
