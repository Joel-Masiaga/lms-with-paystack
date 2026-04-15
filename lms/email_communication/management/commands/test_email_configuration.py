"""
Django Management Command: test_email_configuration

Usage:
    python manage.py test_email_configuration
    python manage.py test_email_configuration --recipient test@example.com
    python manage.py test_email_configuration --verbose
    python manage.py test_email_configuration --skip-send
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail, get_connection
from django.conf import settings
from django.utils import timezone
from email_communication.models import EmailLog, EmailRecipient
from users.models import User
import sys
import os


class Command(BaseCommand):
    help = 'Test email configuration and send a test email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--recipient',
            type=str,
            default=None,
            help='Email recipient for test (default: superuser email)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed configuration information'
        )
        parser.add_argument(
            '--skip-send',
            action='store_true',
            help='Only test configuration, do not send email'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('═' * 70))
        self.stdout.write(self.style.SUCCESS('📧 Email Configuration Testing Assistant'))
        self.stdout.write(self.style.SUCCESS('═' * 70))
        
        # Step 1: Check Settings
        self.check_environment()
        
        # Step 2: Check Configuration
        config_ok = self.check_configuration(options.get('verbose', False))
        
        # Step 3: Test Connection
        if config_ok:
            connection_ok = self.test_connection()
        else:
            connection_ok = False
            self.stdout.write(self.style.WARNING('⚠️  Skipping connection test due to configuration issues'))
        
        # Step 4: Send Test Email
        if connection_ok and not options.get('skip_send'):
            recipient = options.get('recipient')
            if not recipient:
                recipient = self.get_superuser_email()
            self.send_test_email(recipient)
        elif options.get('skip_send'):
            self.stdout.write('\n⏭️  Skipping email send (--skip-send flag used)')
        
        # Step 5: Summary
        self.stdout.write('\n' + self.style.SUCCESS('═' * 70))
        if config_ok and connection_ok:
            self.stdout.write(self.style.SUCCESS('✅ Email configuration test completed successfully!'))
        elif config_ok and not connection_ok:
            self.stdout.write(self.style.WARNING('⚠️  Configuration OK but connection test failed'))
        else:
            self.stdout.write(self.style.ERROR('❌ Email configuration has issues'))
        self.stdout.write(self.style.SUCCESS('═' * 70))

    def check_environment(self):
        """Check Django environment and settings."""
        self.stdout.write('\n🔍 Checking Environment...')
        
        environment = os.getenv('ENVIRONMENT', 'production')
        self.stdout.write(f"  Environment: {self.style.SUCCESS(environment) if environment else self.style.ERROR('NOT SET')}")
        
        if environment == 'development':
            self.stdout.write(self.style.WARNING('  ℹ️  Development mode - emails will print to console'))
        elif environment == 'production':
            self.stdout.write(self.style.SUCCESS('  ✓ Production mode - using SMTP server'))
        else:
            self.stdout.write(self.style.WARNING(f'  ⚠️  Unexpected environment: {environment}'))

    def check_configuration(self, verbose=False):
        """Check email configuration from settings."""
        self.stdout.write('\n📋 Checking Configuration...')
        
        try:
            backend = settings.EMAIL_BACKEND
            self.stdout.write(f"  Backend: {backend}")
            
            if 'console' in backend:
                self.stdout.write(
                    self.style.WARNING('  ⚠️  Console Backend - emails will print to console only')
                )
                return True
            elif 'smtp' in backend:
                self.stdout.write(self.style.SUCCESS('  ✓ SMTP Backend configured'))
                
                # Check required settings
                required_settings = [
                    ('EMAIL_HOST', settings.EMAIL_HOST),
                    ('EMAIL_PORT', settings.EMAIL_PORT),
                    ('EMAIL_USE_TLS', settings.EMAIL_USE_TLS),
                    ('EMAIL_HOST_USER', settings.EMAIL_HOST_USER),
                    ('EMAIL_HOST_PASSWORD', '***' if settings.EMAIL_HOST_PASSWORD else 'NOT SET'),
                    ('DEFAULT_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL),
                ]
                
                all_configured = True
                for setting_name, setting_value in required_settings:
                    if setting_value and not (setting_name == 'EMAIL_HOST_PASSWORD' and setting_value == 'NOT SET'):
                        self.stdout.write(f"    ✓ {setting_name}: {setting_value if setting_name != 'EMAIL_HOST_PASSWORD' else '***'}")
                    else:
                        self.stdout.write(
                            self.style.ERROR(f"    ✗ {setting_name}: NOT CONFIGURED")
                        )
                        all_configured = False
                
                if verbose:
                    self.stdout.write('\n  📊 Detailed Configuration:')
                    self.stdout.write(f"    HOST: {settings.EMAIL_HOST}")
                    self.stdout.write(f"    PORT: {settings.EMAIL_PORT}")
                    self.stdout.write(f"    TLS: {settings.EMAIL_USE_TLS}")
                    self.stdout.write(f"    USER: {settings.EMAIL_HOST_USER}")
                    self.stdout.write(f"    FROM: {settings.DEFAULT_FROM_EMAIL}")
                
                return all_configured
            else:
                self.stdout.write(self.style.ERROR(f'  ✗ Unknown Backend: {backend}'))
                return False
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Configuration Error: {str(e)}'))
            return False

    def test_connection(self):
        """Test SMTP connection."""
        self.stdout.write('\n🔗 Testing SMTP Connection...')
        
        try:
            connection = get_connection()
            connection.open()
            self.stdout.write(self.style.SUCCESS('  ✓ SMTP connection successful!'))
            connection.close()
            return True
        except Exception as e:
            error_str = str(e)
            self.stdout.write(
                self.style.ERROR(f'  ✗ SMTP connection failed: {error_str}')
            )
            
            # Provide specific troubleshooting for common errors
            self.stdout.write(self.style.WARNING('\n  🔧 Troubleshooting Tips:\n'))
            
            if 'Authentication failed' in error_str or 'Username and Password' in error_str:
                self.stdout.write('    • Check your Gmail credentials:')
                self.stdout.write('      1. Go to: https://myaccount.google.com/apppasswords')
                self.stdout.write('      2. Select: Mail, Windows Computer')
                self.stdout.write('      3. Copy the 16-character password')
                self.stdout.write('      4. Paste in .env: EMAIL_HOST_PASSWORD=xxxx-xxxx-xxxx-xxxx')
                self.stdout.write('      5. Ensure 2FA is enabled on your Gmail account')
            
            elif 'Connection' in error_str or 'timeout' in error_str:
                self.stdout.write('    • Check network and firewall:')
                self.stdout.write('      1. Verify your EMAIL_HOST is correct (smtp.gmail.com)')
                self.stdout.write('      2. Verify EMAIL_PORT is 587 (TLS) or 465 (SSL)')
                self.stdout.write('      3. Check firewall allows outbound on that port')
                self.stdout.write('      4. Try: telnet smtp.gmail.com 587')
            
            else:
                self.stdout.write('    • General troubleshooting:')
                self.stdout.write('      1. Verify all EMAIL_* settings in settings.py')
                self.stdout.write('      2. Check .env file for missing variables')
                self.stdout.write('      3. Ensure EMAIL credentials are correct')
                self.stdout.write('      4. Verify Django email backend is smtp (not console)')
            
            return False

    def get_superuser_email(self):
        """Get superuser email or ask for alternative."""
        try:
            superuser = User.objects.filter(is_superuser=True).first()
            if superuser and superuser.email:
                self.stdout.write(f'  Using superuser email: {superuser.email}')
                return superuser.email
        except Exception:
            pass
        
        # Fallback to prompting
        email = input('\n  📧 Enter recipient email address: ').strip()
        if not email or '@' not in email:
            raise CommandError('Invalid email address')
        return email

    def send_test_email(self, recipient):
        """Send test email."""
        self.stdout.write(f'\n📧 Sending Test Email to {recipient}...')
        
        subject = '[LMS Test] Email Configuration Verification'
        body = f"""Hello,

This is a test email from your LMS platform.

If you received this email, your email configuration is working correctly!

Test Details:
- Sent at: {timezone.now()}
- Recipient: {recipient}
- Backend: {settings.EMAIL_BACKEND}
- Environment: {os.getenv('ENVIRONMENT', 'production')}

You can now proceed with sending production emails to your users.

---
This is an automated test email. Please ignore if not expected.
"""
        
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False
            )
            
            self.stdout.write(self.style.SUCCESS('  ✓ Email sent successfully!'))
            self.stdout.write(f'  → Check {recipient} for the test email (2-5 minutes)')
            self.stdout.write(
                self.style.WARNING('  → Check spam/junk folder if not in inbox')
            )
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  ✗ Failed to send email: {str(e)}')
            )
            self.stdout.write(
                self.style.WARNING('  → Verify SMTP credentials and connection')
            )
            return False


# Add this to manage.py or create direct file in:
# email_communication/management/commands/test_email_configuration.py

"""
INSTALLATION INSTRUCTIONS:

1. Create directory structure:
   mkdir -p lms/email_communication/management/commands

2. Create __init__.py files:
   touch lms/email_communication/management/__init__.py
   touch lms/email_communication/management/commands/__init__.py

3. Copy this code to:
   lms/email_communication/management/commands/test_email_configuration.py

4. Run the command:
   python manage.py test_email_configuration

USAGE EXAMPLES:

# Test with default (superuser) email
python manage.py test_email_configuration

# Test with specific recipient
python manage.py test_email_configuration --recipient test@example.com

# Show verbose configuration
python manage.py test_email_configuration --verbose

# Only check configuration (no email sent)
python manage.py test_email_configuration --skip-send

# Combine options
python manage.py test_email_configuration --recipient test@example.com --verbose

OUTPUT EXAMPLE:

════════════════════════════════════════════════════════════════
Email Configuration Testing
════════════════════════════════════════════════════════════════

📋 Checking Configuration...
  Backend: django.core.mail.backends.smtp.EmailBackend
  ✓ SMTP Backend configured

🔗 Testing SMTP Connection...
  ✓ SMTP connection successful

📧 Sending Test Email to admin@example.com...
  ✓ Email sent successfully!
  → Check admin@example.com for the test email
  → Check spam/junk folder if not in inbox

════════════════════════════════════════════════════════════════
✓ Email configuration test completed!
════════════════════════════════════════════════════════════════
"""
