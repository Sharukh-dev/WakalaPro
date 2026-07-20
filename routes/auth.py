from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models.user import User
from models.operator import Operator
from models.password_reset import PasswordReset
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

auth = Blueprint('auth', __name__)

# ============================================
# EMAIL CONFIGURATION
# ============================================
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USER = 'your-email@gmail.com'
EMAIL_PASSWORD = 'your-app-password'

def send_reset_email(email, reset_link):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = email
        msg['Subject'] = 'Password Reset - WakalaPro'
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 40px;">
            <div style="max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #2563eb; text-align: center;">WakalaPro</h2>
                <h3 style="color: #1e293b;">Password Reset Request</h3>
                <p style="color: #475569;">You requested to reset your password. Click the button below to reset it:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" style="background: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block;">Reset Password</a>
                </div>
                <p style="color: #64748b; font-size: 14px;">This link will expire in 24 hours.</p>
                <p style="color: #64748b; font-size: 14px;">If you didn't request this, please ignore this email.</p>
                <hr style="border: none; border-top: 1px solid #e2e8f0;">
                <p style="color: #94a3b8; font-size: 12px; text-align: center;">© 2024 WakalaPro. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash('Invalid username or password.', 'danger')
            return render_template('login.html')

        if not user.is_active:
            flash('Your account has been deactivated.', 'danger')
            return render_template('login.html')

        login_user(user, remember=remember)
        user.last_login = datetime.utcnow()
        db.session.commit()

        flash('Login successful!', 'success')
        
        if user.role in ['admin']:
            return redirect(url_for('dashboard.index'))
        elif user.role == 'cashier':
            return redirect(url_for('transactions.index'))
        else:
            return redirect(url_for('dashboard.index'))

    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page - First user becomes admin"""
    
    # Check if any user exists
    user_exists = User.query.first()
    
    # If user exists and current user is not logged in, redirect to login
    if user_exists and not current_user.is_authenticated:
        flash('System already has a user. Please login.', 'info')
        return redirect(url_for('auth.login'))
    
    # If user exists and current user is not admin, deny access
    if user_exists and current_user.is_authenticated and not current_user.has_permission('admin'):
        flash('You do not have permission to register new users.', 'danger')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validation
        if not username or len(username) < 3:
            flash('Username must be at least 3 characters.', 'danger')
            return render_template('register.html')

        if not email:
            flash('Email is required.', 'danger')
            return render_template('register.html')

        if not phone_number:
            flash('Phone number is required.', 'danger')
            return render_template('register.html')

        if not password or len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html')

        # FIXED: Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match. Please enter the same password in both fields.', 'danger')
            return render_template('register.html')

        # Check if username exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose another.', 'danger')
            return render_template('register.html')

        # Check if email exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('register.html')

        # Check if phone exists
        if User.query.filter_by(phone_number=phone_number).first():
            flash('Phone number already registered.', 'danger')
            return render_template('register.html')

        # Check if this is the first user
        is_first_user = User.query.count() == 0
        
        # If first user, make them admin
        if is_first_user:
            role = 'admin'
            is_admin = True
        else:
            if not current_user.has_permission('admin'):
                flash('You do not have permission to create users.', 'danger')
                return render_template('register.html')
            role = request.form.get('role', 'cashier')
            is_admin = True if role == 'admin' else False

        # Create user
        user = User(
            username=username,
            email=email,
            phone_number=phone_number,
            role=role,
            is_active=True,
            is_admin=is_admin
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Create operator record
        if role in ['admin', 'manager', 'cashier']:
            operator = Operator(
                user_id=user.id,
                full_name=username,
                phone_number=phone_number or '',
                status='active'
            )
            db.session.add(operator)
            db.session.commit()

        # If first user, log them in automatically
        if is_first_user:
            login_user(user, remember=True)
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash(f'✅ Welcome {username}! You are now logged in as Admin.', 'success')
            return redirect(url_for('dashboard.index'))

        flash(f'✅ Account created successfully! Login as {role}.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

# ============================================
# FORGOT PASSWORD
# ============================================

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Please enter your email address.', 'danger')
            return render_template('forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('No account found with that email address.', 'danger')
            return render_template('forgot_password.html')
        
        token = PasswordReset.generate_token(user.id)
        reset_link = url_for('auth.reset_password', token=token, _external=True)
        
        if send_reset_email(email, reset_link):
            flash('Password reset link has been sent to your email.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Failed to send email. Please try again later.', 'danger')
            return render_template('forgot_password.html')
    
    return render_template('forgot_password.html')

@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset = PasswordReset.verify_token(token)
    
    if not reset:
        flash('Invalid or expired reset link. Please request a new one.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('reset_password.html', token=token)
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html', token=token)
        
        user = User.query.get(reset.user_id)
        user.set_password(password)
        reset.mark_used()
        db.session.commit()
        
        flash('Password reset successfully! You can now login with your new password.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html', token=token)