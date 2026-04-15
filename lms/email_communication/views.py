from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, ListView
from django.core.mail import send_mail, send_mass_mail
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
import logging

from users.models import User
from courses.models import Course, Enrollment
from .models import EmailLog, EmailRecipient
from .forms import CourseEmailForm, PromotionalEmailForm
from .email_utils import is_valid_email

# Set up logging for email notifications
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# INSTRUCTOR EMAIL VIEWS
# ─────────────────────────────────────────────────────────────────

class InstructorEmailStudentsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Instructor sends email to students enrolled in their course."""
    template_name = 'email_communication/instructor_email.html'
    
    def test_func(self):
        return self.request.user.role == 'instructor'
    
    def handle_no_permission(self):
        messages.error(self.request, 'Only instructors can send course announcements.')
        return redirect('home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = CourseEmailForm(self.request.user, self.request.POST or None)
        context['form'] = form
        context['step'] = self.request.GET.get('step', '1')
        
        # Get selected course for preview
        if self.request.POST.get('course'):
            course_id = self.request.POST.get('course')
            context['selected_course'] = Course.objects.get(id=course_id, created_by=self.request.user)
            # Get enrolled students count
            context['enrolled_students'] = Enrollment.objects.filter(course=context['selected_course']).count()
        
        return context
    
    def post(self, request, *args, **kwargs):
        form = CourseEmailForm(request.user, request.POST)
        
        # Step 1: Form submission and validation
        if request.POST.get('action') == 'preview':
            if form.is_valid():
                # Store data in session for preview
                request.session['email_data'] = {
                    'course_id': form.cleaned_data['course'].id,
                    'subject': form.cleaned_data['subject'],
                    'body': form.cleaned_data['body'],
                }
                return redirect('instructor_email_preview')
            else:
                messages.error(request, 'Please fill in all required fields.')
        
        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)


class InstructorEmailPreviewView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Preview email before sending."""
    template_name = 'email_communication/instructor_email_preview.html'
    
    def test_func(self):
        return self.request.user.role == 'instructor'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        email_data = self.request.session.get('email_data', {})
        
        if email_data:
            course = Course.objects.get(id=email_data['course_id'], created_by=self.request.user)
            enrolled_students = Enrollment.objects.filter(course=course).select_related('user')
            # Extract just the user objects for clean display
            students_list = [enrollment.user for enrollment in enrolled_students]
            recipients_count = len(students_list)
            
            context.update({
                'course': course,
                'subject': email_data['subject'],
                'body': email_data['body'],
                'students_list': students_list,
                'recipients_count': recipients_count,
                'selected_course': course,
            })
        else:
            context['error'] = 'No email data found. Please start over.'
        
        return context
    
    def post(self, request):
        email_data = request.session.get('email_data', {})
        
        if not email_data:
            messages.error(request, 'Email data expired. Please start over.')
            return redirect('instructor_email')
        
        try:
            course = Course.objects.get(id=email_data['course_id'], created_by=request.user)
            enrolled_students = Enrollment.objects.filter(course=course)
            
            # Validate students exist
            if enrolled_students.count() == 0:
                messages.error(request, 'No enrolled students found in this course.')
                return redirect('instructor_email')
            
            # Log the announcement start
            logger.info(f'Starting course announcement: "{email_data["subject"]}" for course "{course.title}" to {enrolled_students.count()} students')
            
            # Create email log
            email_log = EmailLog.objects.create(
                sender=request.user,
                email_type='course_announcement',
                subject=email_data['subject'],
                body=email_data['body'],
                course=course,
                recipients_count=enrolled_students.count(),
                sent_at=timezone.now(),
            )
            
            # Pre-create all EmailRecipient records with 'pending' status
            recipient_objects = []
            recipient_emails = {}  # Store email -> user mapping
            invalid_emails = []
            
            for enrollment in enrolled_students:
                # Validate email format
                user_email = enrollment.user.email
                if not is_valid_email(user_email):
                    invalid_emails.append(user_email)
                    logger.warning(f'Skipping invalid email format: {user_email}')
                    continue
                    
                # Create email recipient record
                email_recipient = EmailRecipient(
                    email_log=email_log,
                    recipient=enrollment.user,
                    status='pending',
                    sent_at=None
                )
                recipient_objects.append(email_recipient)
                recipient_emails[user_email] = enrollment.user
            
            # Log invalid emails if any
            if invalid_emails:
                logger.warning(f'Found {len(invalid_emails)} invalid email addresses: {", ".join(invalid_emails)}')
            
            # Bulk create recipient records
            EmailRecipient.objects.bulk_create(recipient_objects, batch_size=1000)
            logger.info(f'Created {len(recipient_emails)} pending email recipient records')
            
            # Send emails
            sent_count = 0
            failed_count = 0
            
            if recipient_emails:
                try:
                    from django.core.mail import send_mail
                    from django.conf import settings
                    
                    # Log email configuration
                    logger.info(f'Email Config - Backend: {settings.EMAIL_BACKEND}, Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}, User: {settings.EMAIL_HOST_USER}')
                    
                    # Send emails one by one to track individual failures
                    for idx, (recipient_email, user) in enumerate(recipient_emails.items()):
                        try:
                            send_mail(
                                subject=email_data['subject'],
                                message=email_data['body'],
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[recipient_email],
                                fail_silently=False
                            )
                            sent_count += 1
                            if (idx + 1) % 10 == 0:
                                logger.info(f'Progress: {sent_count} emails sent so far...')
                        except Exception as individual_error:
                            failed_count += 1
                            error_str = str(individual_error)
                            logger.warning(f'Failed to send email to {recipient_email}: {error_str[:100]}')
                            # Update this recipient's record with failure status
                            try:
                                EmailRecipient.objects.filter(
                                    email_log=email_log,
                                    recipient=user
                                ).update(
                                    status='failed',
                                    error_message=f'SMTP Error: {error_str[:200]}'
                                )
                            except Exception:
                                pass
                    
                    # Update successful sends
                    EmailRecipient.objects.filter(
                        email_log=email_log,
                        status='pending'
                    ).update(
                        status='sent',
                        sent_at=timezone.now()
                    )
                    
                    logger.info(f'Course announcement for "{course.title}": {sent_count} sent, {failed_count} failed out of {enrolled_students.count()} students')
                    
                except Exception as send_error:
                    # Log the sending error
                    error_message = str(send_error)
                    logger.error(f'Critical error sending course announcement: {error_message}', exc_info=True)
                    
                    # Update all recipient records with failure status
                    EmailRecipient.objects.filter(
                        email_log=email_log,
                        status='pending'
                    ).update(
                        status='failed',
                        error_message=f'SMTP Error: {error_message[:200]}'
                    )
                    
                    messages.error(
                        request,
                        f'Failed to send announcement: {error_message}. Please verify your email configuration and try again.'
                    )
                    return redirect('instructor_email_preview')
            
            # Clear session
            if 'email_data' in request.session:
                del request.session['email_data']
            
            # Show success message with stats
            if failed_count > 0:
                messages.warning(
                    request,
                    f'Course announcement sent: {sent_count} successful, {failed_count} failed out of {enrolled_students.count()} students.'
                )
            else:
                messages.success(
                    request,
                    f'Course announcement sent successfully to {sent_count} student(s)!'
                )
            
            return redirect('instructor_email')
        
        except Exception as e:
            error_message = str(e)
            logger.error(f'Unexpected error in course announcement: {error_message}')
            messages.error(
                request,
                f'An unexpected error occurred: {error_message}. Please try again.'
            )
            return redirect('instructor_email_preview')


class InstructorEmailHistoryView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """View instructor's email sending history."""
    template_name = 'email_communication/instructor_email_history.html'
    context_object_name = 'emaillog_list'  # Django's default for ListView
    paginate_by = 10
    
    def test_func(self):
        return self.request.user.role == 'instructor'
    
    def get_queryset(self):
        return EmailLog.objects.filter(sender=self.request.user, email_type='course_announcement').order_by('-sent_at')


# ─────────────────────────────────────────────────────────────────
# SUPERUSER PROMOTIONAL EMAIL VIEWS
# ─────────────────────────────────────────────────────────────────

class PromotionalEmailView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Superuser sends promotional emails to platform users."""
    template_name = 'email_communication/promotional_email.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def handle_no_permission(self):
        messages.error(self.request, 'Only superusers can send promotional emails.')
        return redirect('home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = PromotionalEmailForm(self.request.POST or None)
        context['form'] = form
        
        # Calculate recipient counts
        all_users = User.objects.filter(is_active=True)
        students = User.objects.filter(is_active=True, role='student')
        instructors = User.objects.filter(is_active=True, role='instructor')
        
        context.update({
            'all_users_count': all_users.count(),
            'students_count': students.count(),
            'instructors_count': instructors.count(),
        })
        
        return context
    
    def post(self, request):
        form = PromotionalEmailForm(request.POST)
        
        if request.POST.get('action') == 'preview':
            if form.is_valid():
                # Validate that recipients exist for selected audience
                target_audience = form.cleaned_data['target_audience']
                if target_audience == 'all':
                    recipients = User.objects.filter(is_active=True)
                elif target_audience == 'students':
                    recipients = User.objects.filter(is_active=True, role='student')
                else:
                    recipients = User.objects.filter(is_active=True, role='instructor')
                
                if recipients.count() == 0:
                    messages.error(request, f'No {target_audience} users found to send email to.')
                    context = self.get_context_data()
                    context['form'] = form
                    return render(request, self.template_name, context)
                
                request.session['promo_email_data'] = {
                    'subject': form.cleaned_data['subject'],
                    'body': form.cleaned_data['body'],
                    'target_audience': form.cleaned_data['target_audience'],
                }
                return redirect('promotional_email_preview')
            else:
                messages.error(request, 'Please fill in all required fields.')
        
        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)


class PromotionalEmailPreviewView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Preview promotional email before sending."""
    template_name = 'email_communication/promotional_email_preview.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        promo_data = self.request.session.get('promo_email_data', {})
        
        if promo_data:
            # Get target users based on audience selection
            target_audience = promo_data['target_audience']
            
            # Get all counts for display
            all_users = User.objects.filter(is_active=True)
            students = User.objects.filter(is_active=True, role='student')
            instructors = User.objects.filter(is_active=True, role='instructor')
            
            if target_audience == 'all':
                recipients = all_users
                audience_label = 'All Active Users'
            elif target_audience == 'students':
                recipients = students
                audience_label = 'Students Only'
            else:  # instructors
                recipients = instructors
                audience_label = 'Instructors Only'
            
            context.update({
                'subject': promo_data['subject'],
                'body': promo_data['body'],
                'target_audience': target_audience,
                'target_audience_display': audience_label,
                'recipients_count': recipients.count(),
                'students_count': students.count(),
                'instructors_count': instructors.count(),
            })
        else:
            context['error'] = 'No email data found. Please start over.'
        
        return context
    
    def post(self, request):
        promo_data = request.session.get('promo_email_data', {})
        
        if not promo_data:
            messages.error(request, 'Email data expired. Please start over.')
            return redirect('promotional_email')
        
        try:
            # Get target users
            target_audience = promo_data['target_audience']
            if target_audience == 'all':
                recipients = User.objects.filter(is_active=True)
            elif target_audience == 'students':
                recipients = User.objects.filter(is_active=True, role='student')
            else:
                recipients = User.objects.filter(is_active=True, role='instructor')
            
            # Validate recipients exist
            if recipients.count() == 0:
                messages.error(request, f'No recipients found for the selected audience.')
                return redirect('promotional_email')
            
            # Log the campaign start
            logger.info(f'Starting promotional email campaign: "{promo_data["subject"]}" to {recipients.count()} {target_audience} users')
            
            # Create email log
            email_log = EmailLog.objects.create(
                sender=request.user,
                email_type='promotional',
                subject=promo_data['subject'],
                body=promo_data['body'],
                recipients_count=recipients.count(),
                sent_at=timezone.now(),
            )
            
            # Pre-create all EmailRecipient records with 'pending' status
            recipient_objects = []
            recipient_emails = []
            invalid_emails = []
            
            for user in recipients:
                # Validate email format
                if not is_valid_email(user.email):
                    invalid_emails.append(user.email)
                    logger.warning(f'Skipping invalid email format: {user.email}')
                    continue
                    
                # Create email recipient record
                email_recipient = EmailRecipient(
                    email_log=email_log,
                    recipient=user,
                    status='pending',
                    sent_at=None
                )
                recipient_objects.append(email_recipient)
                recipient_emails.append(user.email)
            
            # Log invalid emails if any
            if invalid_emails:
                logger.warning(f'Found {len(invalid_emails)} invalid email addresses: {", ".join(invalid_emails)}')
            
            # Bulk create recipient records
            EmailRecipient.objects.bulk_create(recipient_objects, batch_size=1000)
            logger.info(f'Created {len(recipient_emails)} pending email recipient records')
            
            # Send all emails
            sent_count = 0
            failed_count = 0
            
            if recipient_emails:
                try:
                    from django.core.mail import send_mail
                    from django.conf import settings
                    
                    # Log email configuration (without password)
                    logger.info(f'Email Config - Backend: {settings.EMAIL_BACKEND}, Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}, User: {settings.EMAIL_HOST_USER}')
                    
                    # Send emails one by one to track individual failures
                    for idx, recipient_email in enumerate(recipient_emails):
                        try:
                            send_mail(
                                subject=promo_data['subject'],
                                message=promo_data['body'],
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[recipient_email],
                                fail_silently=False
                            )
                            sent_count += 1
                            if (idx + 1) % 10 == 0:
                                logger.info(f'Progress: {sent_count} emails sent so far...')
                        except Exception as individual_error:
                            failed_count += 1
                            error_str = str(individual_error)
                            logger.warning(f'Failed to send email to {recipient_email}: {error_str[:100]}')
                            # Update this recipient's record with failure status
                            try:
                                user = User.objects.get(email=recipient_email)
                                EmailRecipient.objects.filter(
                                    email_log=email_log,
                                    recipient=user
                                ).update(
                                    status='failed',
                                    error_message=f'SMTP Error: {error_str[:200]}'
                                )
                            except Exception:
                                pass
                    
                    # Update successful sends
                    EmailRecipient.objects.filter(
                        email_log=email_log,
                        status='pending'
                    ).update(
                        status='sent',
                        sent_at=timezone.now()
                    )
                    
                    logger.info(f'Promotional email campaign completed: {sent_count} sent, {failed_count} failed out of {recipients.count()} recipients')
                    
                except Exception as send_error:
                    # Log the sending error
                    error_message = str(send_error)
                    logger.error(f'Critical error during promotional email sending: {error_message}', exc_info=True)
                    
                    # Update all recipient records with failure status
                    EmailRecipient.objects.filter(
                        email_log=email_log,
                        status='pending'
                    ).update(
                        status='failed',
                        error_message=f'SMTP Error: {error_message[:200]}'
                    )
                    
                    messages.error(
                        request,
                        f'Failed to send emails: {error_message}. Please verify your email configuration and try again.'
                    )
                    return redirect('promotional_email_preview')
            
            # Clear session
            if 'promo_email_data' in request.session:
                del request.session['promo_email_data']
            
            # Show success message with stats
            if failed_count > 0:
                messages.warning(
                    request,
                    f'Promotional email sent: {sent_count} successful, {failed_count} failed out of {recipients.count()} recipients. Check logs for details.'
                )
            else:
                messages.success(
                    request,
                    f'Promotional email sent successfully to {sent_count} user(s)!'
                )
            
            return redirect('promotional_email')
        
        except Exception as e:
            # Catch any other unexpected errors
            error_message = str(e)
            logger.error(f'Unexpected error in promotional email: {error_message}', exc_info=True)
            messages.error(
                request,
                f'An unexpected error occurred: {error_message}. Please try again.'
            )
            return redirect('promotional_email_preview')


class PromotionalEmailHistoryView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """View superuser's promotional email history."""
    template_name = 'email_communication/promotional_email_history.html'
    context_object_name = 'emaillog_list'  # Django's default for ListView
    paginate_by = 10
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_queryset(self):
        return EmailLog.objects.filter(sender=self.request.user, email_type='promotional').order_by('-sent_at')
