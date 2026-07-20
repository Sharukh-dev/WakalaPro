from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from extensions import db
from models.license import License
from models.notification import Notification
from models.user import User
from config import Config
from datetime import datetime, timedelta
import hashlib
import secrets
import string

license_bp = Blueprint('license', __name__)

def generate_license_key():
    """Generate a unique license key"""
    alphabet = string.ascii_uppercase + string.digits
    parts = []
    for i in range(4):
        part = ''.join(secrets.choice(alphabet) for _ in range(4))
        parts.append(part)
    return '-'.join(parts)

# ============================================
# OFFLINE LICENSE VERIFICATION
# ============================================
def verify_license_offline(license_key):
    """
    Verify license key using secret key (offline)
    Returns: (is_valid, customer_name, duration_days)
    """
    try:
        parts = license_key.split('-')
        if len(parts) != 4:
            return False, None, 0
        
        customer = parts[0]
        days = int(parts[1])
        random_part = parts[2]
        signature = parts[3]
        
        # Recreate signature using secret key
        data = f"{customer}{days}{random_part}{Config.LICENSE_SECRET_KEY}"
        expected_signature = hashlib.sha256(data.encode()).hexdigest()[:8].upper()
        
        # Verify signature matches
        if signature != expected_signature:
            return False, None, 0
        
        return True, customer, days
        
    except Exception:
        return False, None, 0

def check_license_status():
    """Check if license is valid - called on every request"""
    license = License.query.first()
    
    if not license:
        # No license found - create trial license
        license = License(
            license_key=generate_license_key(),
            is_active=True,
            is_used=False,
            activated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
            days_remaining=30,
            customer_name='Trial User',
            customer_email='trial@wakalapro.com',
            duration_days=30,
            notes='Trial license - 30 days'
        )
        db.session.add(license)
        db.session.commit()
        return True
    
    # Check if license is expired
    if license.is_expired():
        return False
    
    # Update days remaining
    license.days_remaining = license.get_days_remaining()
    db.session.commit()
    return True

def send_license_reminder(license, reminder_type):
    """Send license reminder notification to admin users"""
    days_left = license.get_days_remaining()
    hours_left = license.get_hours_remaining()
    
    admin_users = User.query.filter(User.role.in_(['admin', 'super_admin'])).all()
    
    if reminder_type == '7_days':
        title = '⚠️ License Expiry Warning - 7 Days Remaining'
        message = f"""Your WakalaPro license will expire in {days_left} days.

Please contact support to renew your license.

License Key: {license.license_key}
Days Remaining: {days_left}
Expiry Date: {license.expires_at.strftime('%Y-%m-%d %H:%M')}

Contact: support@wakalapro.com"""
    
    elif reminder_type == '3_days':
        title = '⚠️ URGENT: License Expires in 3 Days'
        message = f"""Your WakalaPro license will expire in {days_left} days.

Contact support immediately to renew your license!

License Key: {license.license_key}
Days Remaining: {days_left}
Expiry Date: {license.expires_at.strftime('%Y-%m-%d %H:%M')}

Contact: support@wakalapro.com"""
    
    elif reminder_type == '1_day':
        title = '🚨 FINAL WARNING: License Expires Tomorrow'
        message = f"""Your WakalaPro license will expire in {days_left} day(s).

Your system will be locked if you do not renew today.

License Key: {license.license_key}
Hours Remaining: {hours_left}
Expiry Date: {license.expires_at.strftime('%Y-%m-%d %H:%M')}

Contact support immediately: support@wakalapro.com"""
    
    elif reminder_type == 'expired_today':
        title = '❌ License Expired - System Locked'
        message = f"""Your WakalaPro license has expired.

Your system has been locked. Please contact support to renew your license.

License Key: {license.license_key}
Expiry Date: {license.expires_at.strftime('%Y-%m-%d %H:%M')}

Contact: support@wakalapro.com"""
    
    else:
        return
    
    for user in admin_users:
        notification = Notification(
            user_id=user.id,
            title=title,
            message=message,
            notification_type='license_reminder',
            is_read=False
        )
        db.session.add(notification)
    
    db.session.commit()

@license_bp.before_app_request
def check_license_and_reminders():
    """Check license and send reminders on every request"""
    from flask import request
    if request.endpoint in ['license.index', 'license.activate', 'license.extend', 'license.generate']:
        return None
    
    if request.path.startswith('/static'):
        return None
    
    license = License.query.first()
    if not license:
        return None
    
    # Check if license is expired
    if license.is_expired():
        license.is_active = False
        db.session.commit()
        send_license_reminder(license, 'expired_today')
        return None
    
    # Check if reminder should be sent
    reminder_type = license.should_send_reminder()
    if reminder_type:
        send_license_reminder(license, reminder_type)
    
    return None

@license_bp.route('/license')
def index():
    """License status page"""
    license = License.query.first()
    
    if not license:
        license = License(
            license_key=generate_license_key(),
            is_active=True,
            is_used=False,
            activated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
            days_remaining=30,
            customer_name='Trial User',
            customer_email='trial@wakalapro.com',
            duration_days=30,
            notes='Trial license - 30 days'
        )
        db.session.add(license)
        db.session.commit()
    
    reminder_type = license.should_send_reminder()
    if reminder_type:
        send_license_reminder(license, reminder_type)
    
    return render_template('license.html', license=license)

@license_bp.route('/license/activate', methods=['POST'])
def activate():
    """Activate license with key - OFFLINE VERIFICATION"""
    license_key = request.form.get('license_key')
    
    if not license_key:
        flash('Please enter a valid license key.', 'danger')
        return redirect(url_for('license.index'))
    
    # ============================================
    # OFFLINE VERIFICATION - NO INTERNET NEEDED!
    # ============================================
    is_valid, customer, days = verify_license_offline(license_key)
    
    if not is_valid:
        flash('Invalid license key. Please check and try again.', 'danger')
        return redirect(url_for('license.index'))
    
    # Check if license already exists in database
    existing = License.query.filter_by(license_key=license_key).first()
    
    if existing:
        if existing.is_used:
            flash('This license key has already been used.', 'danger')
            return redirect(url_for('license.index'))
        if existing.is_expired():
            flash('This license key has expired.', 'danger')
            return redirect(url_for('license.index'))
        
        # Reactivate existing license
        existing.is_active = True
        existing.is_used = True
        existing.activated_at = datetime.utcnow()
        existing.expires_at = datetime.utcnow() + timedelta(days=days)
        existing.days_remaining = days
        existing.duration_days = days
        existing.customer_name = customer
        existing.used_by = 'system'
        existing.used_at = datetime.utcnow()
        db.session.commit()
        
    else:
        # Create new license from key
        new_license = License(
            license_key=license_key,
            is_active=True,
            is_used=True,
            activated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=days),
            days_remaining=days,
            duration_days=days,
            customer_name=customer,
            used_by='system',
            used_at=datetime.utcnow(),
            notes=f'License verified offline - {days} days'
        )
        db.session.add(new_license)
        db.session.commit()
    
    flash(f'✅ License activated successfully! {days} days remaining.', 'success')
    return redirect(url_for('dashboard.index'))

@license_bp.route('/license/extend', methods=['POST'])
@login_required
def extend():
    """Extend license (admin only - for testing)"""
    if not current_user.has_permission('admin'):
        flash('You do not have permission to extend licenses.', 'danger')
        return redirect(url_for('license.index'))
    
    days = int(request.form.get('days', 30))
    license = License.query.first()
    
    if license:
        license.is_used = False
        remaining = license.extend_license(days)
        flash(f'✅ License extended by {days} days. Remaining: {remaining} days.', 'success')
    else:
        flash('No license found.', 'danger')
    
    return redirect(url_for('license.index'))

@license_bp.route('/license/generate', methods=['POST'])
@login_required
def generate():
    """Generate new license key (admin only - for testing)"""
    if not current_user.has_permission('admin'):
        flash('You do not have permission to generate licenses.', 'danger')
        return redirect(url_for('license.index'))
    
    license = License.query.first()
    
    if license:
        new_key = generate_license_key()
        license.license_key = new_key
        license.is_active = True
        license.is_used = False
        license.expires_at = datetime.utcnow() + timedelta(days=30)
        license.days_remaining = 30
        license.duration_days = 30
        license.activated_at = datetime.utcnow()
        license.reminder_sent_7 = False
        license.reminder_sent_3 = False
        license.reminder_sent_1 = False
        db.session.commit()
        
        flash(f'✅ New license key generated: {new_key}', 'success')
    else:
        flash('No license found.', 'danger')
    
    return redirect(url_for('license.index'))