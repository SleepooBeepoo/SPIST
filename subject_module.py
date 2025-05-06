from flask import Blueprint, render_template, redirect, url_for, flash, request, session, Response
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, HiddenField, FileField
from wtforms.validators import DataRequired, Length, Email, ValidationError
from models import db, Subject, StudentSubject, User, Announcement
from datetime import datetime
import pandas as pd
import os
from werkzeug.utils import secure_filename

# Create the blueprint
subject_bp = Blueprint('subject', __name__)

# Subject creation form
class SubjectForm(FlaskForm):
    name = StringField('Subject Name', validators=[DataRequired(), Length(min=3, max=100)])
    subject_code = StringField('Subject Code', validators=[DataRequired(), Length(min=3, max=20)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    submit = SubmitField('Create Subject')

# Subject code enrollment form
class SubjectCodeForm(FlaskForm):
    subject_code = StringField('Subject Code', validators=[DataRequired(), Length(min=3, max=20)])
    submit = SubmitField('Enroll')

# Enrollment verification form
class EnrollmentVerificationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Verify Enrollment')
    
    def validate_email(self, email):
        # Ensure student email uses school domain
        if not email.data.endswith('@spist.edu'):
            raise ValidationError('Student email must use the school domain (@spist.edu)')

# CSV Import Form
class CSVImportForm(FlaskForm):
    csv_file = FileField('CSV File', validators=[DataRequired()])
    submit = SubmitField('Import Students')

@subject_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_subject():
    """Create a new subject"""
    if current_user.role != 'teacher':
        flash('Only teachers can create subjects.')
        return redirect(url_for('dashboard'))
    
    form = SubjectForm()
    if form.validate_on_submit():
        # Check if subject code already exists
        existing_subject = Subject.query.filter_by(subject_code=form.subject_code.data).first()
        if existing_subject:
            flash('Subject code already exists. Please choose a different code.')
            return render_template('subject/create.html', form=form)
        
        try:
            # Create new subject
            subject = Subject(
                name=form.name.data,
                subject_code=form.subject_code.data,
                teacher_id=current_user.id
            )
            db.session.add(subject)
            db.session.commit()
            flash('Subject created successfully!')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while creating the subject: {str(e)}')
    
    return render_template('subject/create.html', form=form)

@subject_bp.route('/<int:subject_id>')
@login_required
def view_subject(subject_id):
    """View a subject's details"""
    subject = Subject.query.get_or_404(subject_id)
    
    # Check if user has permission to view this subject
    if current_user.role == 'teacher' and subject.teacher_id != current_user.id:
        flash('You do not have permission to view this subject.')
        return redirect(url_for('dashboard'))
    elif current_user.role == 'student':
        # Check if student is enrolled in this subject
        enrollment = StudentSubject.query.filter_by(
            student_id=current_user.id,
            subject_id=subject_id,
            enrollment_status='approved'
        ).first()
        
        if not enrollment:
            flash('You are not enrolled in this subject.')
            return redirect(url_for('dashboard'))
    
    # Get all enrolled students if teacher
    enrolled_students = []
    if current_user.role == 'teacher':
        enrollments = StudentSubject.query.filter_by(
            subject_id=subject_id,
            enrollment_status='approved'
        ).all()
        enrolled_students = [enrollment.student for enrollment in enrollments]
    
    # Get announcements for this subject
    announcements = Announcement.query.filter_by(subject_id=subject_id).order_by(Announcement.created_at.desc()).all()
    
    return render_template('subject/view.html', 
                           subject=subject, 
                           enrolled_students=enrolled_students,
                           announcements=announcements)

@subject_bp.route('/import_students/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def import_students(subject_id):
    """Import students from CSV file"""
    if current_user.role != 'teacher':
        flash('Only teachers can import students.')
        return redirect(url_for('dashboard'))
    
    subject = Subject.query.filter_by(id=subject_id, teacher_id=current_user.id).first_or_404()
    form = CSVImportForm()
    
    if form.validate_on_submit():
        try:
            # Create uploads directory if it doesn't exist
            uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
            if not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir, exist_ok=True)
            
            # Save the uploaded file
            csv_file = request.files['csv_file']
            filename = secure_filename(csv_file.filename)
            file_path = os.path.join(uploads_dir, filename)
            csv_file.save(file_path)
            
            # Process the CSV file with enhanced error handling
            try:
                # For newer pandas versions, with data type specifications
                df = pd.read_csv(file_path, 
                    on_bad_lines='skip', 
                    delimiter=',',
                    dtype={
                        'Full Name': str,
                        'Course and Year': str,
                        'Student Email': str,
                        'Subject Code': str  # Ensure subject code is treated as string
                    })
            except TypeError:
                # For older pandas versions
                df = pd.read_csv(file_path, error_bad_lines=False, delimiter=',')
                
            required_columns = ['Full Name', 'Course and Year', 'Student Email', 'Subject Code']
            
            # Check if all required columns are present
            if not all(col in df.columns for col in required_columns):
                flash('CSV file must contain columns: Full Name, Course and Year, Student Email, Subject Code')
                return redirect(url_for('subject.import_students', subject_id=subject_id))
            
            # Clean and validate data
            df = df.fillna('')  # Replace NaN with empty strings
            df = df.applymap(lambda x: str(x).strip() if isinstance(x, str) else x)  # Strip whitespace
            
            # Convert subject codes to strings for comparison
            df['Subject Code'] = df['Subject Code'].astype(str)
            current_subject_code = str(subject.subject_code)
            
            # Filter rows for the current subject with proper string comparison
            subject_df = df[df['Subject Code'].str.strip() == current_subject_code.strip()]
            
            if len(subject_df) == 0:
                flash(f'No students found for subject code {current_subject_code} in the CSV file.')
                return redirect(url_for('subject.import_students', subject_id=subject_id))
            
            # Initialize counters and error tracking
            success_count = 0
            error_count = 0
            already_enrolled = 0
            already_registered = 0
            error_details = []  # Track specific error messages
            
            for _, row in subject_df.iterrows():
                full_name = row['Full Name']
                email = row['Student Email']
                
                # Enhanced email validation
                email = str(email).strip().lower()
                if not email or not email.endswith('@spist.edu'):
                    error_count += 1
                    error_details.append(f"Invalid email format for {full_name}: {email}")
                    continue
                
                # Check if user already exists
                user = User.query.filter_by(email=email).first()
                
                if not user:
                    # Create new user
                    username = email.split('@')[0]  # Use part before @ as username
                    user = User(
                        username=username,
                        email=email,
                        role='student'
                    )
                    # Set a default password (students should reset this)
                    user.set_password('changeme')
                    db.session.add(user)
                    db.session.flush()  # Get user ID without committing
                    already_registered += 1
                
                # Check if student is already enrolled
                existing_enrollment = StudentSubject.query.filter_by(
                    student_id=user.id,
                    subject_id=subject.id
                ).first()
                
                if existing_enrollment:
                    already_enrolled += 1
                    continue
                
                # Create enrollment
                enrollment = StudentSubject(
                    student_id=user.id,
                    subject_id=subject.id,
                    enrollment_status='approved'  # Auto-approve since it's from master list
                )
                db.session.add(enrollment)
                success_count += 1
            
            # Commit all changes
            db.session.commit()
            
            # Delete the uploaded file
            os.remove(file_path)
            
            # Prepare detailed status message
            status_msg = f'Import Summary:\n'
            status_msg += f'- Successfully imported: {success_count} students\n'
            status_msg += f'- Already enrolled: {already_enrolled}\n'
            status_msg += f'- New accounts created: {already_registered}\n'
            status_msg += f'- Errors: {error_count}'
            
            if error_details:
                status_msg += '\n\nError Details:\n'
                status_msg += '\n'.join(error_details[:5])  # Show first 5 errors
                if len(error_details) > 5:
                    status_msg += f'\n...and {len(error_details) - 5} more errors'
            
            flash(status_msg)
            
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while importing students: {str(e)}')
        
        return redirect(url_for('dashboard'))
    
    return render_template('subject/import_students.html', form=form, subject=subject)

@subject_bp.route('/download_csv_template')
@login_required
def download_csv_template():
    """Download a CSV template for student import"""
    if current_user.role != 'teacher':
        flash('Only teachers can download the CSV template.')
        return redirect(url_for('dashboard'))
    
    # Create a sample DataFrame
    data = {
        'Full Name': ['John Doe', 'Jane Smith', 'Robert Johnson'],
        'Course and Year': ['BSCS 1', 'BSIT 2', 'BSCS 3'],
        'Student Email': ['john.doe@spist.edu', 'jane.smith@spist.edu', 'robert.johnson@spist.edu'],
        'Subject Code': ['1234', '1234', '1234']
    }
    df = pd.DataFrame(data)
    
    # Create a CSV string
    csv_data = df.to_csv(index=False)
    
    # Return as a downloadable file
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=student_import_template.csv"}
    )

@subject_bp.route('/enroll/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def enroll_subject(subject_id):
    """Enroll in a subject"""
    if current_user.role != 'student':
        flash('Only students can enroll in subjects.')
        return redirect(url_for('dashboard'))
    
    subject = Subject.query.get_or_404(subject_id)
    
    # Check if already enrolled
    existing_enrollment = StudentSubject.query.filter_by(
        student_id=current_user.id,
        subject_id=subject_id
    ).first()
    
    if existing_enrollment:
        if existing_enrollment.enrollment_status == 'approved':
            flash('You are already enrolled in this subject.')
        elif existing_enrollment.enrollment_status == 'pending':
            flash('Your enrollment request is pending approval.')
        else:
            flash('Your enrollment request was rejected.')
        return redirect(url_for('dashboard'))
    
    # Create enrollment request
    enrollment = StudentSubject(
        student_id=current_user.id,
        subject_id=subject_id,
        enrollment_status='pending'
    )
    db.session.add(enrollment)
    db.session.commit()
    
    flash('Enrollment request submitted. Waiting for teacher approval.')
    return redirect(url_for('dashboard'))

@subject_bp.route('/enroll-by-code', methods=['GET', 'POST'])
@login_required
def enroll_by_code():
    """Enroll in a subject using a subject code"""
    if current_user.role != 'student':
        flash('Only students can enroll in subjects.')
        return redirect(url_for('dashboard'))
    
    form = SubjectCodeForm()
    
    if form.validate_on_submit():
        subject_code = form.subject_code.data
        
        # Find subject with the given code
        subject = Subject.query.filter_by(subject_code=subject_code).first()
        
        if not subject:
            flash('Invalid subject code. Please check and try again.', 'danger')
            return render_template('subject/enroll_by_code.html', form=form)
        
        # Check if already enrolled
        existing_enrollment = StudentSubject.query.filter_by(
            student_id=current_user.id,
            subject_id=subject.id
        ).first()
        
        if existing_enrollment:
            if existing_enrollment.enrollment_status == 'approved':
                flash('You are already enrolled in this subject.')
            elif existing_enrollment.enrollment_status == 'pending':
                flash('Your enrollment request is pending approval.')
            else:
                flash('Your enrollment request was rejected.')
            return redirect(url_for('dashboard'))
        
        # Create enrollment request
        enrollment = StudentSubject(
            student_id=current_user.id,
            subject_id=subject.id,
            enrollment_status='pending'
        )
        db.session.add(enrollment)
        db.session.commit()
        
        flash('Enrollment request submitted. Waiting for teacher approval.', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('subject/enroll_by_code.html', form=form)

@subject_bp.route('/approve_enrollment/<int:subject_id>/<int:student_id>')
@login_required
def approve_enrollment(subject_id, student_id):
    """Approve a student's enrollment request"""
    if current_user.role != 'teacher':
        flash('Only teachers can approve enrollment requests.')
        return redirect(url_for('dashboard'))
    
    subject = Subject.query.filter_by(id=subject_id, teacher_id=current_user.id).first_or_404()
    enrollment = StudentSubject.query.filter_by(
        student_id=student_id,
        subject_id=subject_id,
        enrollment_status='pending'
    ).first_or_404()
    
    enrollment.enrollment_status = 'approved'
    db.session.commit()
    
    flash('Student enrollment approved.')
    return redirect(url_for('subject.view_subject', subject_id=subject_id))

@subject_bp.route('/reject_enrollment/<int:subject_id>/<int:student_id>')
@login_required
def reject_enrollment(subject_id, student_id):
    """Reject a student's enrollment request"""
    if current_user.role != 'teacher':
        flash('Only teachers can reject enrollment requests.')
        return redirect(url_for('dashboard'))
    
    subject = Subject.query.filter_by(id=subject_id, teacher_id=current_user.id).first_or_404()
    enrollment = StudentSubject.query.filter_by(
        student_id=student_id,
        subject_id=subject_id,
        enrollment_status='pending'
    ).first_or_404()
    
    enrollment.enrollment_status = 'rejected'
    db.session.commit()
    
    flash('Student enrollment rejected.')
    return redirect(url_for('subject.view_subject', subject_id=subject_id))

@subject_bp.route('/remove_student/<int:subject_id>/<int:student_id>', methods=['POST'])
@login_required
def remove_student(subject_id, student_id):
    """Remove a student from a subject"""
    if current_user.role != 'teacher':
        flash('Only teachers can remove students from subjects.')
        return redirect(url_for('dashboard'))
    
    subject = Subject.query.filter_by(id=subject_id, teacher_id=current_user.id).first_or_404()
    enrollment = StudentSubject.query.filter_by(
        student_id=student_id,
        subject_id=subject_id,
        enrollment_status='approved'
    ).first_or_404()
    
    db.session.delete(enrollment)
    db.session.commit()
    
    flash('Student has been removed from the subject.')
    return redirect(url_for('subject.view_subject', subject_id=subject_id))