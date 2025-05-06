from flask import render_template, redirect, url_for, flash, request, Blueprint
from flask_login import login_required, current_user
from app.models import Subject, User, db
from app.subject.forms import SubjectForm, EnrollmentVerificationForm
from app.subject.services import SubjectService
import logging

subject_bp = Blueprint('subject', __name__)

@subject_bp.route('/<int:subject_id>')
@login_required
def view(subject_id):
    """View a subject's details"""
    subject = SubjectService.get_subject_by_id(subject_id)
    if not subject:
        flash('Subject not found.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Check if user has permission to view this subject
    if current_user.is_teacher() and subject.teacher_id != current_user.id:
        flash('You do not have permission to view this subject.', 'danger')
        return redirect(url_for('dashboard.index'))
    elif current_user.is_student() and subject not in current_user.enrolled_subjects:
        flash('You are not enrolled in this subject.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    return render_template('auth/view_subject.html', subject=subject, title=subject.name)

@subject_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new subject"""
    if not current_user.is_teacher():
        flash('Only teachers can create subjects.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    form = SubjectForm()
    if form.validate_on_submit():
        success, message, subject = SubjectService.create_subject(
            name=form.name.data,
            subject_code=form.subject_code.data,
            teacher_id=current_user.id
        )
        
        if success:
            flash(message, 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash(message, 'danger')
            if 'already exists' in message:
                return render_template('subject/create.html', form=form, title='Create Subject')
    
    return render_template('subject/create.html', form=form, title='Create Subject')

@subject_bp.route('/enroll', methods=['POST'])
@login_required
def enroll():
    """Enroll in a subject"""
    if not current_user.is_student():
        flash('Only students can enroll in subjects.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    subject_code = request.form.get('subject_code')
    if not subject_code:
        flash('Please provide a subject code.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    success, message, status = SubjectService.enroll_student(
        student_id=current_user.id,
        subject_code=subject_code
    )
    
    # Set appropriate flash message category based on status
    category = 'success' if success else (
        'info' if status in ['pending', 'approved'] else 
        'warning' if status == 'rejected' else 'danger'
    )
    
    flash(message, category)
    return redirect(url_for('dashboard.index'))

@subject_bp.route('/remove_student/<int:subject_id>/<int:student_id>', methods=['POST'])
@login_required
def remove_student(subject_id, student_id):
    """Remove a student from a subject"""
    if not current_user.is_teacher():
        flash('Only teachers can remove students from subjects.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    success, message = SubjectService.remove_student(
        subject_id=subject_id,
        student_id=student_id,
        teacher_id=current_user.id
    )
    
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('dashboard.index'))

@subject_bp.route('/verification/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def enrollment_verification(subject_id):
    """Configure enrollment verification settings for a subject"""
    if not current_user.is_teacher():
        flash('Only teachers can configure enrollment verification settings.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    subject = SubjectService.get_subject_by_id(subject_id)
    if not subject:
        flash('Subject not found.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    if subject.teacher_id != current_user.id:
        flash('You do not have permission to modify this subject.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    form = EnrollmentVerificationForm(obj=subject)
    
    if form.validate_on_submit():
        try:
            subject.domain_whitelist = form.domain_whitelist.data
            subject.student_id_pattern = form.student_id_pattern.data
            subject.auto_approve_enabled = form.auto_approve_enabled.data
            
            db.session.commit()
            flash('Enrollment verification settings updated successfully.', 'success')
            return redirect(url_for('subject.view', subject_id=subject_id))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating enrollment verification settings: {str(e)}")
            flash(f"An error occurred: {str(e)}", 'danger')
    
    return render_template('subject/enrollment_verification.html', form=form, subject=subject, title='Enrollment Verification Settings')

@subject_bp.route('/handle_enrollment/<int:subject_id>/<int:student_id>/<action>', methods=['POST'])
@login_required
def handle_enrollment(subject_id, student_id, action):
    """Handle enrollment requests (approve/reject)"""
    if not current_user.is_teacher():
        flash('Only teachers can handle enrollment requests.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    subject = SubjectService.get_subject_by_id(subject_id)
    if not subject or subject.teacher_id != current_user.id:
        flash('You do not have permission to manage this subject.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    enrollment = StudentSubject.query.filter_by(
        student_id=student_id,
        subject_id=subject_id
    ).first()
    
    if not enrollment:
        flash('Enrollment request not found.', 'danger')
        return redirect(url_for('subject.view', subject_id=subject_id))
    
    if action == 'approve':
        enrollment.enrollment_status = 'approved'
        flash('Enrollment request approved.', 'success')
    elif action == 'reject':
        enrollment.enrollment_status = 'rejected'
        flash('Enrollment request rejected.', 'success')
    else:
        flash('Invalid action.', 'danger')
        return redirect(url_for('subject.view', subject_id=subject_id))
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error handling enrollment: {str(e)}")
        flash(f"An error occurred: {str(e)}", 'danger')
    
    return redirect(url_for('subject.view', subject_id=subject_id))