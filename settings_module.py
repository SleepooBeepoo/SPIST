from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from forms_settings import ChangePasswordForm, UpdateProfileForm
from models import db, User
from werkzeug.security import check_password_hash

# Create the blueprint
settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """User settings page"""
    password_form = ChangePasswordForm()
    profile_form = UpdateProfileForm()
    
    # Pre-fill profile form with current data
    if request.method == 'GET':
        profile_form.username.data = current_user.username
        profile_form.email.data = current_user.email
    
    # Handle password form submission
    if 'change_password' in request.form and password_form.validate_on_submit():
        if not current_user.check_password(password_form.current_password.data):
            flash('Current password is incorrect.')
            return render_template('settings/settings.html', 
                                password_form=password_form, 
                                profile_form=profile_form)
        
        try:
            current_user.set_password(password_form.new_password.data)
            db.session.commit()
            flash('Password updated successfully!')
            return redirect(url_for('settings.settings'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}')
    
    # Handle profile form submission
    if 'update_profile' in request.form and profile_form.validate_on_submit():
        try:
            # Check if username is being changed and is not already taken
            if profile_form.username.data != current_user.username:
                existing_user = User.query.filter_by(username=profile_form.username.data).first()
                if existing_user:
                    flash('Username already taken. Please choose a different username.')
                    return render_template('settings/settings.html', 
                                        password_form=password_form, 
                                        profile_form=profile_form)
                current_user.username = profile_form.username.data
            
            # Check if email is being changed and is not already taken
            if profile_form.email.data != current_user.email:
                # For students, validate email domain
                if current_user.role == 'student' and not profile_form.email.data.endswith('@spist.edu'):
                    flash('Student email must use the school domain (@spist.edu)')
                    return render_template('settings/settings.html', 
                                        password_form=password_form, 
                                        profile_form=profile_form)
                
                existing_user = User.query.filter_by(email=profile_form.email.data).first()
                if existing_user:
                    flash('Email already registered. Please use a different email.')
                    return render_template('settings/settings.html', 
                                        password_form=password_form, 
                                        profile_form=profile_form)
                current_user.email = profile_form.email.data
            
            db.session.commit()
            flash('Profile updated successfully!')
            return redirect(url_for('settings.settings'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}')
    
    return render_template('settings/settings.html', 
                          password_form=password_form, 
                          profile_form=profile_form)