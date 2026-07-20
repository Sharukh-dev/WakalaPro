from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.license import License
from models.user import User
from datetime import datetime, timedelta
import secrets
import string

license_admin = Blueprint('license_admin', __name__)

def generate_license_key():
    """Generate a unique license key"""
    alphabet = string.ascii_uppercase + string.digits
    parts = []
    for i in range(4):
        part = ''.join(secrets.choice(alphabet) for _ in range(4))
        parts.append(part)
    return '-'.join(parts)

@license_admin.route('/licenses')
@login_required
def index():
    """Admin license management page"""
    if not current_user.has_permission('admin'):
        flash('You do not have permission to manage licenses.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    licenses = License.query.all()
    return render_template('admin/licenses.html', licenses=licenses)

@license_admin.route('/licenses/create', methods=['POST'])
@login_required
def create():
    """Create a new license for a client"""
    if not current_user.has_permission('admin'):
        flash('You do not have permission to create licenses.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    customer_name = request.form.get('customer_name')
    customer_email = request.form.get('customer_email')
    duration_days = int(request.form.get('duration_days', 30))
    notes = request.form.get('notes', '')
    
    if not customer_name or not customer_email:
        flash('Customer name and email are required.', 'danger')
        return redirect(url_for('license_admin.index'))
    
    # Generate new license
    license_key = generate_license_key()
    
    # Check if license key already exists
    existing = License.query.filter_by(license_key=license_key).first()
    while existing:
        license_key = generate_license_key()
        existing = License.query.filter_by(license_key=license_key).first()
    
    new_license = License(
        license_key=license_key,
        is_active=True,
        is_used=False,
        activated_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=duration_days),
        days_remaining=duration_days,
        customer_name=customer_name,
        customer_email=customer_email,
        notes=notes,
        reminder_sent_7=False,
        reminder_sent_3=False,
        reminder_sent_1=False
    )
    
    db.session.add(new_license)
    db.session.commit()
    
    flash(f'License created successfully! Key: {license_key}', 'success')
    return redirect(url_for('license_admin.index'))

@license_admin.route('/licenses/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit license details"""
    if not current_user.has_permission('admin'):
        flash('You do not have permission to edit licenses.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    license = License.query.get_or_404(id)
    
    if request.method == 'POST':
        license.customer_name = request.form.get('customer_name')
        license.customer_email = request.form.get('customer_email')
        license.notes = request.form.get('notes', '')
        
        db.session.commit()
        flash('License updated successfully!', 'success')
        return redirect(url_for('license_admin.index'))
    
    return render_template('admin/license_edit.html', license=license)

@license_admin.route('/licenses/<int:id>/extend', methods=['POST'])
@login_required
def extend(id):
    """Extend license by days"""
    if not current_user.has_permission('admin'):
        flash('You do not have permission to extend licenses.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    license = License.query.get_or_404(id)
    days = int(request.form.get('days', 30))
    
    license.extend_license(days)
    license.is_active = True
    
    flash(f'License extended by {days} days. New expiry: {license.expires_at.strftime("%Y-%m-%d")}', 'success')
    return redirect(url_for('license_admin.index'))

@license_admin.route('/licenses/<int:id>/deactivate', methods=['POST'])
@login_required
def deactivate(id):
    """Deactivate a license"""
    if not current_user.has_permission('admin'):
        flash('You do not have permission to deactivate licenses.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    license = License.query.get_or_404(id)
    license.is_active = False
    db.session.commit()
    
    flash('License deactivated successfully!', 'success')
    return redirect(url_for('license_admin.index'))

@license_admin.route('/licenses/<int:id>/activate', methods=['POST'])
@login_required
def activate(id):
    """Activate a license"""
    if not current_user.has_permission('admin'):
        flash('You do not have permission to activate licenses.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    license = License.query.get_or_404(id)
    license.is_active = True
    db.session.commit()
    
    flash('License activated successfully!', 'success')
    return redirect(url_for('license_admin.index'))

@license_admin.route('/licenses/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete a license"""
    if not current_user.has_permission('admin'):
        flash('You do not have permission to delete licenses.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    license = License.query.get_or_404(id)
    db.session.delete(license)
    db.session.commit()
    
    flash('License deleted successfully!', 'success')
    return redirect(url_for('license_admin.index'))

@license_admin.route('/licenses/generate-key')
@login_required
def generate_key():
    """Generate a new random license key (AJAX)"""
    if not current_user.has_permission('admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    key = generate_license_key()
    return jsonify({'license_key': key})