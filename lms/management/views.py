from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, ListView, UpdateView
from django.http import JsonResponse
from django.db.models import Q, Count, Avg
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import timedelta

from users.models import User, Profile
from courses.models import Course, Enrollment, Ebook, Certificate
from quiz.models import Quiz, QuizAttempt


# ─────────────────────────────────────────────────────────────────
# SUPERUSER PERMISSION MIXIN
# ─────────────────────────────────────────────────────────────────

class SuperUserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin that requires user to be a superuser."""
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('home')


# ─────────────────────────────────────────────────────────────────
# ANALYTICS VIEWS
# ─────────────────────────────────────────────────────────────────

class AdminDashboardView(SuperUserRequiredMixin, TemplateView):
    """Main admin dashboard with analytics."""
    template_name = 'management/admin_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # User Statistics
        total_users = User.objects.count()
        total_students = User.objects.filter(role='student').count()
        total_instructors = User.objects.filter(role='instructor').count()
        total_admins = User.objects.filter(is_staff=True).count()
        total_superusers = User.objects.filter(is_superuser=True).count()
        
        # New users in last 30 days
        last_30_days = timezone.now() - timedelta(days=30)
        new_users_30d = User.objects.filter(date_joined__gte=last_30_days).count()
        
        # Course Statistics
        total_courses = Course.objects.count()
        total_students_enrolled = Enrollment.objects.values('user').distinct().count()
        avg_enrollment_data = (
            Enrollment.objects.values('course').annotate(count=Count('id')).aggregate(
                avg_enrollment=Avg('count')
            )
        )
        avg_course_enrollment = avg_enrollment_data['avg_enrollment'] or 0
        
        # Ebook Statistics
        total_ebooks = Ebook.objects.count()
        published_ebooks = Ebook.objects.filter(published=True).count()
        
        # Quiz Statistics
        total_quizzes = Quiz.objects.count()
        total_quiz_attempts = QuizAttempt.objects.count()
        avg_quiz_data = QuizAttempt.objects.filter(completed=True).aggregate(
            avg_score=Avg('score')
        )
        avg_quiz_score = avg_quiz_data['avg_score'] or 0
        
        # Certificate Statistics
        total_certificates_issued = Certificate.objects.count()
        
        # Platform Growth (last 7 days vs previous 7 days)
        today = timezone.now()
        last_7_days_start = today - timedelta(days=7)
        prev_7_days_start = today - timedelta(days=14)
        prev_7_days_end = today - timedelta(days=7)
        
        current_week_signups = User.objects.filter(
            date_joined__gte=last_7_days_start
        ).count()
        previous_week_signups = User.objects.filter(
            date_joined__gte=prev_7_days_start,
            date_joined__lte=prev_7_days_end
        ).count()
        
        growth_percentage = 0
        if previous_week_signups > 0:
            growth_percentage = round(
                ((current_week_signups - previous_week_signups) / previous_week_signups) * 100, 2
            )
        
        # Most active instructors (by course count)
        top_instructors = (
            User.objects.filter(course__isnull=False)
            .annotate(course_count=Count('course'))
            .order_by('-course_count')[:5]
        )
        
        # Most enrolled courses
        top_courses = (
            Course.objects.annotate(enrollment_count=Count('enrollment'))
            .order_by('-enrollment_count')[:5]
        )
        
        context.update({
            'total_users': total_users,
            'total_students': total_students,
            'total_instructors': total_instructors,
            'total_admins': total_admins,
            'total_superusers': total_superusers,
            'new_users_30d': new_users_30d,
            'total_courses': total_courses,
            'total_students_enrolled': total_students_enrolled,
            'avg_course_enrollment': round(avg_course_enrollment, 1),
            'total_ebooks': total_ebooks,
            'published_ebooks': published_ebooks,
            'total_quizzes': total_quizzes,
            'total_quiz_attempts': total_quiz_attempts,
            'avg_quiz_score': round(avg_quiz_score, 1),
            'total_certificates_issued': total_certificates_issued,
            'current_week_signups': current_week_signups,
            'previous_week_signups': previous_week_signups,
            'growth_percentage': growth_percentage,
            'top_instructors': top_instructors,
            'top_courses': top_courses,
        })
        
        return context


# ─────────────────────────────────────────────────────────────────
# USER MANAGEMENT VIEWS
# ─────────────────────────────────────────────────────────────────

class UserManagementView(SuperUserRequiredMixin, ListView):
    """List all users with management options."""
    model = User
    template_name = 'management/user_management.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.all().prefetch_related('profile')
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        
        # Filter by role
        role_filter = self.request.GET.get('role')
        if role_filter:
            queryset = queryset.filter(role=role_filter)
        
        # Sort
        sort_by = self.request.GET.get('sort_by', '-date_joined')
        queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['role_filter'] = self.request.GET.get('role', '')
        context['sort_by'] = self.request.GET.get('sort_by', '-date_joined')
        context['total_users'] = User.objects.count()
        context['total_students'] = User.objects.filter(role='student').count()
        context['total_instructors'] = User.objects.filter(role='instructor').count()
        context['total_admins'] = User.objects.filter(is_staff=True).count()
        context['total_superusers'] = User.objects.filter(is_superuser=True).count()
        return context


class UserRightsManagementView(SuperUserRequiredMixin, TemplateView):
    """Manage user rights and permissions."""
    template_name = 'management/user_rights_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get users grouped by role and staff status
        superusers = User.objects.filter(is_superuser=True)
        admins = User.objects.filter(is_staff=True, is_superuser=False)
        instructors = User.objects.filter(role='instructor')
        students = User.objects.filter(role='student')
        
        context.update({
            'superusers': superusers,
            'admins': admins,
            'instructors': instructors,
            'students': students,
            'total_superusers': superusers.count(),
            'total_admins': admins.count(),
            'total_instructors': instructors.count(),
            'total_students': students.count(),
        })
        
        return context


class UserDetailAdminView(SuperUserRequiredMixin, TemplateView):
    """Detailed view of a single user for admin management."""
    template_name = 'management/user_detail_admin.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_object_or_404(User, id=self.kwargs['user_id'])
        
        # Get user profile
        profile = user.profile if hasattr(user, 'profile') else None
        
        # Get user's courses (if instructor)
        instructed_courses = Course.objects.filter(created_by=user) if user.role == 'instructor' else []
        
        # Get user's enrollments (if student)
        enrolled_courses = Enrollment.objects.filter(user=user).select_related('course')
        
        # Get user's quiz attempts
        quiz_attempts = QuizAttempt.objects.filter(student=user).select_related('quiz')
        
        # Get user's certificates
        certificates = Certificate.objects.filter(user=user)
        
        context.update({
            'user': user,
            'profile': profile,
            'instructed_courses': instructed_courses,
            'enrolled_courses': enrolled_courses,
            'quiz_attempts': quiz_attempts,
            'certificates': certificates,
        })
        
        return context


class UpdateUserRightsView(SuperUserRequiredMixin, TemplateView):
    """Update user rights (admin, instructor, superuser)."""
    template_name = 'management/update_user_rights.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_object_or_404(User, id=self.kwargs['user_id'])
        context['user'] = user
        return context
    
    def post(self, request, user_id):
        """Handle POST request to update user rights."""
        user = get_object_or_404(User, id=user_id)
        
        # Update role
        new_role = request.POST.get('role')
        if new_role in ['student', 'instructor']:
            user.role = new_role
        
        # Update is_staff
        is_staff = request.POST.get('is_staff') == 'on'
        user.is_staff = is_staff
        
        # Update is_superuser
        is_superuser = request.POST.get('is_superuser') == 'on'
        user.is_superuser = is_superuser
        
        # Superuser must be staff
        if is_superuser:
            user.is_staff = True
        
        user.save()
        
        return redirect('user_rights_management')


# ─────────────────────────────────────────────────────────────────
# AJAX ENDPOINTS FOR USER RIGHTS UPDATES
# ─────────────────────────────────────────────────────────────────

class AjaxUpdateUserRoleView(SuperUserRequiredMixin, TemplateView):
    """AJAX endpoint to update user role."""
    
    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            new_role = request.POST.get('role')
            
            if new_role in ['student', 'instructor']:
                user.role = new_role
                user.save()
                return JsonResponse({
                    'success': True,
                    'message': f'User role updated to {new_role}'
                })
            
            return JsonResponse({
                'success': False,
                'message': 'Invalid role'
            }, status=400)
        
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'User not found'
            }, status=404)


class AjaxToggleAdminView(SuperUserRequiredMixin, TemplateView):
    """AJAX endpoint to toggle admin status."""
    
    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            user.is_staff = not user.is_staff
            user.save()
            
            return JsonResponse({
                'success': True,
                'is_staff': user.is_staff,
                'message': f'User is now {"an admin" if user.is_staff else "not an admin"}'
            })
        
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'User not found'
            }, status=404)


class AjaxToggleSuperuserView(SuperUserRequiredMixin, TemplateView):
    """AJAX endpoint to toggle superuser status."""
    
    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            
            # Prevent removing superuser status from last superuser
            if user.is_superuser and User.objects.filter(is_superuser=True).count() == 1:
                return JsonResponse({
                    'success': False,
                    'message': 'Cannot remove superuser status from the last superuser'
                }, status=400)
            
            user.is_superuser = not user.is_superuser
            
            # Superuser must be staff
            if user.is_superuser:
                user.is_staff = True
            
            user.save()
            
            return JsonResponse({
                'success': True,
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff,
                'message': f'User is now {"a superuser" if user.is_superuser else "not a superuser"}'
            })
        
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'User not found'
            }, status=404)
