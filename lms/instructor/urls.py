from django.urls import path
from .views import (InstructorView, 
                    InstructorCourseListView, 
                    InstructorCourseCreateView, 
                    InstructorCourseDetailView, 
                    InstructorCourseUpdateView, 
                    InstructorCourseDeleteView,
                    
                    InstructorModuleListView,
                    InstructorModuleDetailView,
                    InstructorModuleCreateView,
                    InstructorModuleUpdateView,
                    InstructorModuleDeleteView,
                    
                    InstructorLessonListView,
                    InstructorLessonCreateView,
                    InstructorLessonDetailView,
                    InstructorLessonUpdateView,
                    InstructorLessonDeleteView,
                    ReorderModulesView,
                    ReorderLessonsView,

                    InstructorQuizCreateView,
                    InstructorQuizDetailView,
                    InstructorQuizUpdateView,
                    InstructorQuizDeleteView,
                    
                    InstructorQuestionCreateView,
                    InstructorQuestionUpdateView,
                    InstructorQuestionDeleteView,
                    
                    InstructorVideoCreateView,
                    InstructorVideoUpdateView,
                    InstructorVideoDeleteView,
                    InstructorEbookListView,
                    InstructorEbookCreateView,
                    InstructorEbookUpdateView,
                    InstructorEbookDeleteView,
                    )

urlpatterns = [
    path('dashboard/', InstructorView.as_view(), name='instructor_dashboard'),
    path('instructor-courses/', InstructorCourseListView.as_view(), name='instructor_course_list'),
    path('create-course/', InstructorCourseCreateView.as_view(), name='create_course'),
    path('course/<int:pk>/', InstructorCourseDetailView.as_view(), name='instructor_course_detail'),
    path('course/<int:pk>/update/', InstructorCourseUpdateView.as_view(), name='update_course'),
    path('course/<int:pk>/delete/', InstructorCourseDeleteView.as_view(), name='delete_course'),

    # Module url paths
    path('course/modules/', InstructorModuleListView.as_view(), name='instructor_module_list'),
    path('module/<int:pk>/', InstructorModuleDetailView.as_view(), name='instructor_module_detail'),
    path('course/<int:pk>/create-module/', InstructorModuleCreateView.as_view(), name='create_module'),
    path('module/<int:pk>/update/', InstructorModuleUpdateView.as_view(), name='update_module'),
    path('module/<int:pk>/delete/', InstructorModuleDeleteView.as_view(), name='delete_module'),

    # Lesson url paths
    path('module/<int:pk>/lessons/', InstructorLessonListView.as_view(), name='instructor_lesson_list'), 
    path('module/<int:pk>/create-lesson/', InstructorLessonCreateView.as_view(), name='create_lesson'),
    path('lesson/<int:pk>/', InstructorLessonDetailView.as_view(), name='instructor_lesson_detail'),
    path('lesson/<int:pk>/update-lesson/', InstructorLessonUpdateView.as_view(), name='update_lesson'),
    path('lesson/<int:pk>/delete-lesson/', InstructorLessonDeleteView.as_view(), name='delete_lesson'),

    # Reorder AJAX paths
    path('course/modules/reorder/', ReorderModulesView.as_view(), name='reorder_modules'),
    path('module/lessons/reorder/', ReorderLessonsView.as_view(), name='reorder_lessons'),

    # Ebook url paths  
    path('ebooks/', InstructorEbookListView.as_view(), name='instructor_ebook_list'),
    path('ebook/create/', InstructorEbookCreateView.as_view(), name='create_ebook'),
    path('ebook/<int:pk>/update/', InstructorEbookUpdateView.as_view(), name='update_ebook'),
    path('ebook/<int:pk>/delete/', InstructorEbookDeleteView.as_view(), name='delete_ebook'),

    # Quiz url paths
    path('module/<int:pk>/create-quiz/', InstructorQuizCreateView.as_view(), name='create_quiz'),
    path('quiz/<int:pk>/', InstructorQuizDetailView.as_view(), name='instructor_quiz_detail'),
    path('quiz/<int:pk>/update/', InstructorQuizUpdateView.as_view(), name='update_quiz'),
    path('quiz/<int:pk>/delete/', InstructorQuizDeleteView.as_view(), name='delete_quiz'),

    # Question url paths
    path('quiz/<int:pk>/create-question/', InstructorQuestionCreateView.as_view(), name='create_question'),
    path('question/<int:pk>/update/', InstructorQuestionUpdateView.as_view(), name='update_question'),
    path('question/<int:pk>/delete/', InstructorQuestionDeleteView.as_view(), name='delete_question'),

    # Video url paths
    path('lesson/<int:pk>/create-video/', InstructorVideoCreateView.as_view(), name='create_video'),
    path('video/<int:pk>/update/', InstructorVideoUpdateView.as_view(), name='update_video'),
    path('video/<int:pk>/delete/', InstructorVideoDeleteView.as_view(), name='delete_video'),
]