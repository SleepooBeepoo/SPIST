from flask import render_template, Blueprint, flash, redirect, url_for, request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from app.models import User, Question, StudentSubmission, Quiz, Subject, QuizSubmission, StudentSubject, Announcement
from app.dashboard.services import DashboardService
import logging

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """Render the dashboard based on user role"""
    if current_user.is_teacher():
        return teacher_dashboard()
    else:
        return student_dashboard()

def teacher_dashboard():
    """Render the teacher dashboard"""
    # Get dashboard data from service
    dashboard_data = DashboardService.get_teacher_dashboard_data(current_user.id)
    
    # Check if there was an error
    if 'error' in dashboard_data:
        flash(dashboard_data['error'], 'danger')
    
    # Create a form instance for CSRF token
    form = FlaskForm()
    dashboard_data['form'] = form
    
    return render_template('auth/teacher_dashboard.html', **dashboard_data)

def student_dashboard():
    """Render the student dashboard"""
    # Get dashboard data from service
    dashboard_data = DashboardService.get_student_dashboard_data(current_user.id)
    
    # Check if there was an error
    if 'error' in dashboard_data:
        flash(dashboard_data['error'], 'danger')
    
    # Create a form instance for CSRF token
    form = FlaskForm()
    dashboard_data['form'] = form
    
    return render_template('auth/student_dashboard.html', **dashboard_data)

@dashboard_bp.route('/approve_enrollment/<int:student_id>/<int:subject_id>', methods=['POST'])
@login_required
def approve_enrollment(student_id, subject_id):
    """Approve a student's enrollment request"""
    if not current_user.is_teacher():
        flash('Only teachers can approve enrollments.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    success, message = DashboardService.update_enrollment_status(
        student_id=student_id,
        subject_id=subject_id,
        teacher_id=current_user.id,
        status='approved'
    )
    
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/reject_enrollment/<int:student_id>/<int:subject_id>', methods=['POST'])
@login_required
def reject_enrollment(student_id, subject_id):
    """Reject a student's enrollment request"""
    if not current_user.is_teacher():
        flash('Only teachers can reject enrollments.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    success, message = DashboardService.update_enrollment_status(
        student_id=student_id,
        subject_id=subject_id,
        teacher_id=current_user.id,
        status='rejected'
    )
    
    flash(message, 'info' if success else 'danger')
    return redirect(url_for('dashboard.index'))