from flask import render_template, Blueprint
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Render the home page"""
    return render_template('home.html', title='Home')

@main_bp.route('/about')
def about():
    """Render the about page"""
    return render_template('about.html', title='About')

@main_bp.route('/contact')
def contact():
    """Render the contact page"""
    return render_template('contact.html', title='Contact')

@main_bp.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('errors/404.html'), 404

@main_bp.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors"""
    return render_template('errors/500.html'), 500