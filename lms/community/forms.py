from django import forms
from .models import DirectMessage, CommunityGroup, GroupMessage, CourseBroadcast


class DirectMessageForm(forms.ModelForm):
    """Form for sending direct messages."""
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    
    class Meta:
        model = DirectMessage
        fields = ['content', 'attachment']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white resize-none',
                'rows': 4,
                'placeholder': 'Type your message here...',
                'id': 'id_content'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*,video/*,audio/*,.pdf,.doc,.docx,.xls,.xlsx,.txt,.zip,.rar',
                'id': 'id_attachment'
            })
        }
    
    def clean(self):
        cleaned_data = super().clean()
        content = cleaned_data.get('content', '').strip()
        attachment = cleaned_data.get('attachment')
        
        # Ensure either content or attachment is provided
        if not content and not attachment:
            raise forms.ValidationError(
                'Please enter a message or attach a file.',
                code='required'
            )
        
        # Validate file size
        if attachment and attachment.size > self.MAX_FILE_SIZE:
            raise forms.ValidationError(
                f'File size exceeds maximum limit of 50 MB.',
                code='file_too_large'
            )
        
        return cleaned_data


class CreateGroupForm(forms.ModelForm):
    """Form for creating community groups."""
    class Meta:
        model = CommunityGroup
        fields = ['name', 'description', 'icon', 'is_public']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white',
                'placeholder': 'Group name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white',
                'rows': 4,
                'placeholder': 'What is this group about?'
            }),
            'icon': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-white hover:file:bg-primary-dark',
                'accept': 'image/*'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4'
            })
        }


class EditGroupForm(forms.ModelForm):
    """Form for editing community groups."""
    class Meta:
        model = CommunityGroup
        fields = ['name', 'description', 'icon', 'is_public']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white',
                'placeholder': 'Group name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white',
                'rows': 4,
                'placeholder': 'What is this group about?'
            }),
            'icon': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-white hover:file:bg-primary-dark',
                'accept': 'image/*'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4'
            })
        }


class GroupMessageForm(forms.ModelForm):
    """Form for posting messages in groups."""
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    
    class Meta:
        model = GroupMessage
        fields = ['content', 'attachment']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white resize-none',
                'rows': 4,
                'placeholder': 'Share your thoughts...',
                'id': 'id_content'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*,video/*,audio/*,.pdf,.doc,.docx,.xls,.xlsx,.txt,.zip,.rar',
                'id': 'id_attachment'
            })
        }
    
    def clean(self):
        cleaned_data = super().clean()
        content = cleaned_data.get('content', '').strip()
        attachment = cleaned_data.get('attachment')
        
        # Ensure either content or attachment is provided
        if not content and not attachment:
            raise forms.ValidationError(
                'Please enter a message or attach a file.',
                code='required'
            )
        
        # Validate file size
        if attachment and attachment.size > self.MAX_FILE_SIZE:
            raise forms.ValidationError(
                f'File size exceeds maximum limit of 50 MB.',
                code='file_too_large'
            )
        
        return cleaned_data


class CourseBroadcastForm(forms.ModelForm):
    """Form for instructors to broadcast messages to course participants."""
    class Meta:
        model = CourseBroadcast
        fields = ['course', 'subject', 'content']
        widgets = {
            'course': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white',
                'placeholder': 'Broadcast subject'
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white',
                'rows': 6,
                'placeholder': 'Your message to course participants...'
            })
        }
