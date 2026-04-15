from django import forms
from django.forms import inlineformset_factory
from .models import Quiz, Question, Answer

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['module', 'title']

class QuestionForm(forms.ModelForm):
    question_text = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:border-primary focus:ring-primary'})
    )
    class Meta:
        model = Question
        fields = ['question_text']

class AnswerForm(forms.ModelForm):
    answer_text = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:border-primary focus:ring-primary'})
    )
    is_correct = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded'})
    )

    class Meta:
        model = Answer
        fields = ['answer_text', 'is_correct']

AnswerFormSet = inlineformset_factory(
    Question,
    Answer,
    form=AnswerForm,
    extra=4, # Give 4 empty forms initially
    can_delete=True
)
