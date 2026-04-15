from django.contrib import admin
from .models import EmailLog, EmailRecipient


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sender', 'email_type', 'recipients_count', 'sent_at')
    list_filter = ('email_type', 'sent_at', 'sender')
    search_fields = ('subject', 'sender__email')
    readonly_fields = ('created_at', 'sent_at')
    fieldsets = (
        ('Email Information', {
            'fields': ('subject', 'body', 'email_type', 'sender')
        }),
        ('Recipients', {
            'fields': ('recipients_count', 'course')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'sent_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EmailRecipient)
class EmailRecipientAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'email_log', 'status', 'sent_at')
    list_filter = ('status', 'sent_at', 'email_log__email_type')
    search_fields = ('recipient__email', 'email_log__subject')
    readonly_fields = ('sent_at',)
