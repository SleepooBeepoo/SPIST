"""Tests for service layer components"""
import pytest
import os
import sys
from flask import Flask
from app import create_app
from app.models import db, User, Subject, StudentSubject
from app.auth.services import AuthService
from app.subject.services import SubjectService
from app.dashboard.services import DashboardService
from app.services.config_service import ConfigService

@pytest.fixture
def app():
    """Create and configure a Flask app for testing"""
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test CLI runner for the app"""
    return app.test_cli_runner()

@pytest.fixture
def init_database(app):
    """Initialize test database with sample data"""
    with app.app_context():
        # Create test users
        teacher = User(username='teacher', email='teacher@example.com', role='teacher')
        teacher.set_password('password')
        
        student = User(username='student', email='student@example.com', role='student')
        student.set_password('password')
        
        db.session.add_all([teacher, student])
        db.session.commit()
        
        # Create test subject
        subject = Subject(
            name='Test Subject',
            subject_code='TEST101',
            teacher_id=teacher.id
        )
        db.session.add(subject)
        db.session.commit()
        
        yield

# Auth Service Tests
def test_auth_service_login(app, init_database):
    """Test user login with AuthService"""
    with app.app_context():
        # Test successful login
        success, message, user = AuthService.login_user('teacher', 'password')
        assert success is True
        assert user is not None
        assert user.username == 'teacher'
        
        # Test failed login - wrong password
        success, message, user = AuthService.login_user('teacher', 'wrongpassword')
        assert success is False
        assert user is None
        
        # Test failed login - user doesn't exist
        success, message, user = AuthService.login_user('nonexistent', 'password')
        assert success is False
        assert user is None

def test_auth_service_register(app):
    """Test user registration with AuthService"""
    with app.app_context():
        # Test successful registration
        success, message, user = AuthService.register_user(
            username='newteacher',
            email='newteacher@example.com',
            password='password',
            role='teacher'
        )
        assert success is True
        assert user is not None
        assert user.username == 'newteacher'
        
        # Test duplicate username
        success, message, user = AuthService.register_user(
            username='newteacher',
            email='different@example.com',
            password='password',
            role='teacher'
        )
        assert success is False
        assert 'Username already taken' in message

# Subject Service Tests
def test_subject_service_create(app, init_database):
    """Test subject creation with SubjectService"""
    with app.app_context():
        teacher = User.query.filter_by(username='teacher').first()
        
        # Test successful subject creation
        success, message, subject = SubjectService.create_subject(
            name='New Subject',
            subject_code='NEW101',
            teacher_id=teacher.id
        )
        assert success is True
        assert subject is not None
        assert subject.name == 'New Subject'
        
        # Test duplicate subject code
        success, message, subject = SubjectService.create_subject(
            name='Another Subject',
            subject_code='NEW101',
            teacher_id=teacher.id
        )
        assert success is False
        assert 'already exists' in message

def test_subject_service_enroll(app, init_database):
    """Test student enrollment with SubjectService"""
    with app.app_context():
        student = User.query.filter_by(username='student').first()
        
        # Test successful enrollment
        success, message, status = SubjectService.enroll_student(
            student_id=student.id,
            subject_code='TEST101'
        )
        assert success is True
        assert status == 'new'
        
        # Test duplicate enrollment
        success, message, status = SubjectService.enroll_student(
            student_id=student.id,
            subject_code='TEST101'
        )
        assert success is False
        assert status == 'pending'

# Config Service Tests
def test_config_service():
    """Test configuration service"""
    # Test default secret key
    secret_key = ConfigService.get_secret_key()
    assert secret_key is not None
    
    # Test database URI
    db_uri = ConfigService.get_database_uri()
    assert db_uri is not None
    assert 'sqlite' in db_uri
    
    # Test full config
    config = ConfigService.get_config()
    assert 'SECRET_KEY' in config
    assert 'SQLALCHEMY_DATABASE_URI' in config
    assert 'WTF_CSRF_TIME_LIMIT' in config