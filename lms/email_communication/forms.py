from django import forms
from .models import EmailLog
from courses.models import Course


class CourseEmailForm(forms.Form):
    """Form for sending emails to course students."""
    course = forms.ModelChoiceField(
        queryset=Course.objects.none(),
        label="Select Course",
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white w-full'
        })
    )
    subject = forms.CharField(
        max_length=255,
        label="Email Subject",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white',
            'placeholder': 'Enter email subject'
        })
    )
    body = forms.CharField(
        label="Email Body",
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white',
            'rows': 10,
            'placeholder': 'Enter your message here...'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter courses to only those created by the instructor
        self.fields['course'].queryset = Course.objects.filter(created_by=user)


class PromotionalEmailForm(forms.Form):
    """Form for sending promotional emails to all active users."""
    subject = forms.CharField(
        max_length=255,
        label="Email Subject",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white',
            'placeholder': 'Enter email subject'
        })
    )
    body = forms.CharField(
        label="Email Body",
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white',
            'rows': 10,
            'placeholder': 'Enter your promotional message here...'
        })
    )
    target_audience = forms.ChoiceField(
        choices=[
            ('all', 'All Active Users'),
            ('students', 'Students Only'),
            ('instructors', 'Instructors Only'),
        ],
        label="Target Audience",
        widget=forms.RadioSelect(attrs={
            'class': 'mr-3'
        })
    )
