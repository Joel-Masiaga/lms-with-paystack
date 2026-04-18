from django import forms
from django.forms import inlineformset_factory
from tinymce.widgets import TinyMCE
from courses.models import Course, Module, Lesson, Note, Video, AdditionalMaterial

class CourseForm(forms.ModelForm):
    description = forms.CharField(widget=TinyMCE())
    objectives = forms.CharField(widget=TinyMCE())

    class Meta:
        model = Course
        fields = ['title', 'description', 'objectives', 'image', 'category', 'is_premium', 'actual_price', 'subsidized_price'] 

class ModuleForm(forms.ModelForm):
    description = forms.CharField(widget=TinyMCE(), required=False)

    class Meta:
        model = Module
        fields = ['title', 'description', 'course']

class LessonForm(forms.ModelForm):
    description = forms.CharField(widget=TinyMCE(), required=False)
    objectives = forms.CharField(widget=TinyMCE(), required=False) 
    content = forms.CharField(widget=TinyMCE(), required=False)

    class Meta:
        model = Lesson
        fields = ['module', 'title', 'description', 'objectives', 'image_content', 'content', 'pdf_file']

class NoteForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full flex-1 p-3 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-primary focus:border-primary resize-none',
            'placeholder': 'Add notes for this lesson...',
            'id': 'notes-textarea' # Ensure ID matches JS
        }),
        required=False
    )

    class Meta:
        model = Note
        fields = ['content']

class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['title', 'video_url']

class AdditionalMaterialForm(forms.ModelForm):
    class Meta:
        model = AdditionalMaterial
        fields = ['title', 'material_url']

# Inline formsets — used in LessonCreate/Update views for inline management
VideoInlineFormSet = inlineformset_factory(
    Lesson,
    Video,
    fields=['title', 'video_url'],
    extra=1,
    can_delete=True,
)

AdditionalMaterialInlineFormSet = inlineformset_factory(
    Lesson,
    AdditionalMaterial,
    fields=['title', 'material_url'],
    extra=1,
    can_delete=True,
)
