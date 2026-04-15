from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
import json
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (TemplateView, 
                                  ListView,  
                                  CreateView, 
                                  UpdateView, 
                                  DeleteView, 
                                  DetailView,
                                  View)
from courses.models import Course, Module, Lesson, Video, Ebook
from quiz.models import Quiz, Question, Answer
from quiz.forms import QuizForm, QuestionForm, AnswerFormSet
from courses.forms import VideoForm
from django.db import models


# ─────────────────────────────────────────────────────────────────
# EBOOK MANAGEMENT VIEWS
# ─────────────────────────────────────────────────────────────────

class InstructorEbookListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all ebooks uploaded by the instructor."""
    model = Ebook
    template_name = "instructor/instructor_ebook_list.html"
    context_object_name = 'ebooks'
    paginate_by = 12

    def get_queryset(self):
        return Ebook.objects.filter(uploaded_by=self.request.user).order_by('-created_at')

    def test_func(self):
        return self.request.user.role == 'instructor'


class InstructorEbookCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Upload a new ebook."""
    model = Ebook
    template_name = "instructor/ebook_form.html"
    fields = ['title', 'slug', 'description', 'category', 'cover_image', 'file']

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        # Auto-generate slug from title if not provided
        if not form.instance.slug:
            from django.utils.text import slugify
            form.instance.slug = slugify(form.instance.title)
        return super().form_valid(form)

    def test_func(self):
        return self.request.user.role == 'instructor'

    def get_success_url(self):
        return reverse('instructor_ebook_list')


class InstructorEbookUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Edit an ebook."""
    model = Ebook
    template_name = "instructor/ebook_form.html"
    fields = ['title', 'slug', 'description', 'category', 'cover_image', 'file']

    def form_valid(self, form):
        # Auto-generate slug from title if not provided
        if not form.instance.slug:
            from django.utils.text import slugify
            form.instance.slug = slugify(form.instance.title)
        return super().form_valid(form)

    def test_func(self):
        ebook = self.get_object()
        return ebook.uploaded_by == self.request.user

    def get_success_url(self):
        return reverse('instructor_ebook_list')


class InstructorEbookDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete an ebook."""
    model = Ebook
    template_name = "instructor/ebook_confirm_delete.html"

    def test_func(self):
        ebook = self.get_object()
        return ebook.uploaded_by == self.request.user

    def get_success_url(self):
        return reverse('instructor_ebook_list')



class InstructorView(TemplateView):
    template_name = "instructor/dashboard.html"

# Course Management Views
class InstructorCourseListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Course 
    template_name = "instructor/instructor_course_list.html"
    context_object_name = 'courses'

    def get_queryset(self):
        return Course.objects.filter(created_by=self.request.user)
    
    def test_func(self):
        courses = self.get_queryset()
        return all(course.created_by == self.request.user for course in courses)
    
class  InstructorCourseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Course
    fields = ['title', 'description', 'objectives', 'image', 'category', 'is_premium', 'actual_price', 'subsidized_price']
    template_name = "instructor/course_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def test_func(self):
        return self.request.user.role == 'instructor'

    def get_success_url(self):
        return reverse('instructor_course_detail', kwargs={'pk': self.object.pk})

class InstructorCourseDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Course
    template_name = "instructor/instructor_course_detail.html"

    def test_func(self):
        course = self.get_object()
        if self.request.user == course.created_by:
            return True
        return False

class InstructorCourseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Course
    fields = ['title', 'description', 'objectives', 'image', 'category', 'is_premium', 'actual_price', 'subsidized_price']
    template_name = "instructor/course_update_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def test_func(self):
        course = self.get_object()
        if self.request.user == course.created_by:
            return True
        return False

    def get_success_url(self):
        return reverse('instructor_course_detail', kwargs={'pk': self.object.pk})
    
class InstructorCourseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Course
    template_name = "instructor/course_confirm_delete.html"
    success_url = reverse_lazy('instructor_course_list')

    def test_func(self):
        course = self.get_object()
        if self.request.user == course.created_by:
            return True
        return False
    

# Module Management Views 
class InstructorModuleListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "instructor/instructor_module_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instructor = self.request.user
        context['courses'] = Course.objects.filter(created_by=instructor).prefetch_related('modules')
        return context

    def test_func(self):
        instructor = self.request.user
        return Module.objects.filter(course__created_by=instructor).exists()

class InstructorModuleDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Module
    template_name = "instructor/instructor_module_detail.html"
    context_object_name = "module"
    pk_url_kwarg = 'pk' # Use 'pk' as the URL keyword argument for module ID

    def test_func(self):
        module = self.get_object() # Get the module object using get_object()
        return module.course.created_by == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module = self.get_object() # Get the module object again to access related lessons
        context['lessons'] = module.lessons.all() # Add lessons to the context
        return context

class InstructorModuleCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Module
    fields = ['title', 'description', 'course']
    template_name = "instructor/module_form.html"

    def form_valid(self, form):
        selected_course = form.cleaned_data['course'] 
        if selected_course.created_by != self.request.user:
            form.add_error('course', "You can only create modules for courses you own.")
            return self.form_invalid(form)
        return super().form_valid(form)
    
    def test_func(self):
        course_id = self.kwargs.get('pk') 
        if not course_id:
            return False
        course = get_object_or_404(Course, id=course_id)
        return course.created_by == self.request.user

    def get_success_url(self):
        return reverse('instructor_module_detail', kwargs={'pk': self.object.pk})
    
class InstructorModuleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Module
    fields = ['title', 'description', 'course']
    template_name = "instructor/module_update_form.html"

    def form_valid(self, form):
        selected_course = form.cleaned_data['course']
        if selected_course.created_by != self.request.user:
            form.add_error('course', "You can only update modules for courses you own.")
            return self.form_invalid(form)
        return super().form_valid(form)
    
    def test_func(self):
        module = self.get_object() 
        return module.course.created_by == self.request.user
    
    def get_success_url(self):
        return reverse('instructor_module_detail', kwargs={'pk': self.object.pk})
    
class InstructorModuleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Module
    template_name = "instructor/module_confirm_delete.html"
    context_object_name = "module"

    def test_func(self):
        module = self.get_object()
        return module.course.created_by == self.request.user
    
    def get_success_url(self):
        return reverse('instructor_module_list')
    

# Lesson Management Views
class InstructorLessonListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Lesson
    template_name = "instructor/instructor_lesson_list.html"
    context_object_name = "lessons"

    def get_queryset(self):
        module_id = self.kwargs.get('pk')
        self.module = get_object_or_404(Module, id=module_id)
        return Lesson.objects.filter(module=self.module)

    def test_func(self):
        module_id = self.kwargs.get('pk')
        module = get_object_or_404(Module, id=module_id)
        return module.course.created_by == self.request.user

    def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['module'] = self.module
            context['courses'] = Course.objects.filter(created_by=self.request.user).prefetch_related('modules__lessons') #Added courses to context.
            return context


class InstructorLessonCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Lesson
    fields = [ 'module', 'title', 'description', 'objectives', 'image_content', 'content', 'pdf_file']
    template_name = "instructor/lesson_form.html"

    def form_valid(self, form):
        selected_module = form.cleaned_data['module']
        if selected_module.course.created_by != self.request.user:
            form.add_error('module', "You can only create lessons for modules in courses you own.")
            return self.form_invalid(form)
        return super().form_valid(form)
    
    def test_func(self):
        module_id = self.kwargs.get('pk')
        module = get_object_or_404(Module, id=module_id)
        return module.course.created_by == self.request.user

    def get_success_url(self):
        return reverse('instructor_lesson_list', kwargs={'pk': self.object.module.pk})
    
class InstructorLessonDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Lesson
    template_name = "instructor/instructor_lesson_detail.html"
    context_object_name = "lesson"
    pk_url_kwarg = 'pk'

    def test_func(self):
        lesson = self.get_object()
        return lesson.module.course.created_by == self.request.user
    
class InstructorLessonUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Lesson
    fields = [ 'module', 'title', 'description', 'objectives', 'image_content', 'content', 'pdf_file']
    template_name = "instructor/lesson_update_form.html"

    def form_valid(self, form):
        selected_module = form.cleaned_data['module']
        if selected_module.course.created_by != self.request.user:
            form.add_error('module', "You can only update lessons for modules in courses you own.")
            return self.form_invalid(form)
        return super().form_valid(form)
    
    def test_func(self):
        lesson = self.get_object()
        return lesson.module.course.created_by == self.request.user
    
    def get_success_url(self):
        return reverse('instructor_lesson_detail', kwargs={'pk': self.object.pk})
    
class InstructorLessonDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Lesson
    template_name = "instructor/lesson_confirm_delete.html"
    context_object_name = "lesson"

    def test_func(self):
        lesson = self.get_object()
        return lesson.module.course.created_by == self.request.user
    
    def get_success_url(self):
        return reverse('instructor_lesson_list', kwargs={'pk': self.object.module.pk})

# Reorder Views
class ReorderModulesView(LoginRequiredMixin, UserPassesTestMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            module_ids = data.get('module_ids', [])
            for index, mod_id in enumerate(module_ids):
                Module.objects.filter(id=mod_id, course__created_by=request.user).update(order=index)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    def test_func(self):
        return self.request.user.role == 'instructor'

class ReorderLessonsView(LoginRequiredMixin, UserPassesTestMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            lesson_ids = data.get('lesson_ids', [])
            for index, lesson_id in enumerate(lesson_ids):
                Lesson.objects.filter(id=lesson_id, module__course__created_by=request.user).update(order=index)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    def test_func(self):
        return self.request.user.role == 'instructor'

# Quiz Management Views
class InstructorQuizCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Quiz
    form_class = QuizForm
    template_name = "instructor/quiz_form.html"

    def get_initial(self):
        initial = super().get_initial()
        if 'pk' in self.kwargs:
            initial['module'] = self.kwargs.get('pk')
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        selected_module = form.cleaned_data['module']
        if selected_module.course.created_by != self.request.user:
            form.add_error('module', "You can only create quizzes for modules in courses you own.")
            return self.form_invalid(form)
        return super().form_valid(form)
    
    def test_func(self):
        module_id = self.kwargs.get('pk')
        module = get_object_or_404(Module, id=module_id)
        return module.course.created_by == self.request.user

    def get_success_url(self):
        return reverse('instructor_quiz_detail', kwargs={'pk': self.object.pk})

class InstructorQuizDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Quiz
    template_name = "instructor/instructor_quiz_detail.html"
    context_object_name = "quiz"

    def test_func(self):
        quiz = self.get_object()
        return quiz.module.course.created_by == self.request.user

class InstructorQuizUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Quiz
    form_class = QuizForm
    template_name = "instructor/quiz_update_form.html"

    def test_func(self):
        quiz = self.get_object()
        return quiz.module.course.created_by == self.request.user

    def get_success_url(self):
        return reverse('instructor_quiz_detail', kwargs={'pk': self.object.pk})

class InstructorQuizDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Quiz
    template_name = "instructor/quiz_confirm_delete.html"

    def test_func(self):
        quiz = self.get_object()
        return quiz.module.course.created_by == self.request.user

    def get_success_url(self):
        return reverse('instructor_module_detail', kwargs={'pk': self.object.module.pk})

# Question Management Views
class InstructorQuestionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = "instructor/question_form.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['answers'] = AnswerFormSet(self.request.POST)
        else:
            data['answers'] = AnswerFormSet()
        data['quiz'] = get_object_or_404(Quiz, pk=self.kwargs.get('pk'))
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        answers = context['answers']
        quiz = context['quiz']
        form.instance.quiz = quiz

        if form.is_valid() and answers.is_valid():
            self.object = form.save()
            answers.instance = self.object
            answers.save()
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def test_func(self):
        quiz_id = self.kwargs.get('pk')
        quiz = get_object_or_404(Quiz, pk=quiz_id)
        return quiz.module.course.created_by == self.request.user

    def get_success_url(self):
        return reverse('instructor_quiz_detail', kwargs={'pk': self.kwargs.get('pk')})


class InstructorQuestionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = "instructor/question_update_form.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['answers'] = AnswerFormSet(self.request.POST, instance=self.object)
        else:
            data['answers'] = AnswerFormSet(instance=self.object)
        data['quiz'] = self.object.quiz
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        answers = context['answers']
        if form.is_valid() and answers.is_valid():
            self.object = form.save()
            answers.instance = self.object
            answers.save()
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def test_func(self):
        question = self.get_object()
        return question.quiz.module.course.created_by == self.request.user

    def get_success_url(self):
        return reverse('instructor_quiz_detail', kwargs={'pk': self.object.quiz.pk})


class InstructorQuestionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Question
    template_name = "instructor/question_confirm_delete.html"

    def test_func(self):
        question = self.get_object()
        return question.quiz.module.course.created_by == self.request.user

    def get_success_url(self):
        return reverse('instructor_quiz_detail', kwargs={'pk': self.object.quiz.pk})


# Video Management Views
class InstructorVideoCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Video
    form_class = VideoForm
    template_name = "instructor/video_form.html"

    def form_valid(self, form):
        lesson_id = self.kwargs.get('pk')
        lesson = get_object_or_404(Lesson, pk=lesson_id)
        form.instance.lesson = lesson
        return super().form_valid(form)

    def test_func(self):
        lesson_id = self.kwargs.get('pk')
        lesson = get_object_or_404(Lesson, pk=lesson_id)
        return lesson.module.course.created_by == self.request.user

    def get_success_url(self):
        return reverse('instructor_lesson_detail', kwargs={'pk': self.kwargs.get('pk')})


class InstructorVideoUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Video
    form_class = VideoForm
    template_name = "instructor/video_update_form.html"

    def test_func(self):
        video = self.get_object()
        return video.lesson.module.course.created_by == self.request.user

    def get_success_url(self):
        return reverse('instructor_lesson_detail', kwargs={'pk': self.object.lesson.pk})


class InstructorVideoDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Video
    template_name = "instructor/video_confirm_delete.html"

    def test_func(self):
        video = self.get_object()
        return video.lesson.module.course.created_by == self.request.user

    def get_success_url(self):
        return reverse('instructor_lesson_detail', kwargs={'pk': self.object.lesson.pk})