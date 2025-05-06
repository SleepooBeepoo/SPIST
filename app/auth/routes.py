from flask import render_template, redirect, url_for, flash, request, Blueprint
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app.auth.forms import LoginForm, RegistrationForm
from app.auth.services import AuthService
import logging

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        success, message, user = AuthService.login_user(
            username=form.username.data,
            password=form.password.data
        )
        
        if success:
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))
        else:
            flash(message, 'danger')
    
    return render_template('auth/login.html', form=form, title='Login')

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        success, message, user = AuthService.register_user(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            role=form.role.data,
            subject_code=form.subject_code.data if form.role.data == 'teacher' else None
        )
        
        if success:
            flash(message, 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(message, 'danger')
    
    return render_template('auth/register.html', form=form, title='Register')