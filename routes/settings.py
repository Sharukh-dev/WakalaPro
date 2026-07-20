from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.business_settings import BusinessSettings
from datetime import datetime

settings = Blueprint('settings', __name__)

@settings.route('/settings')
@login_required
def index():
    if not current_user.has_permission('admin'):
        flash('You do not have permission to view settings.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get or create settings
    business_settings = BusinessSettings.get_settings()
    
    return render_template('settings.html', settings=business_settings)

@settings.route('/settings/update', methods=['POST'])
@login_required
def update():
    if not current_user.has_permission('admin'):
        flash('You do not have permission to update settings.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get or create settings
    business_settings = BusinessSettings.get_settings()
    
    # Update all fields
    business_settings.business_name = request.form.get('business_name', '')
    business_settings.phone = request.form.get('phone', '')
    business_settings.address = request.form.get('address', '')
    business_settings.currency = request.form.get('currency', 'TSh')
    business_settings.receipt_footer = request.form.get('receipt_footer', 'Thank you for using WakalaPro')
    business_settings.email = request.form.get('email', '')
    business_settings.website = request.form.get('website', '')
    business_settings.tax_id = request.form.get('tax_id', '')
    business_settings.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    flash('Settings updated successfully!', 'success')
    return redirect(url_for('settings.index'))