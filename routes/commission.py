from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.commission import Commission
from models.commission_setting import CommissionSetting
from models.operator import Operator
from sqlalchemy import func
from datetime import date, timedelta

# Create blueprint first
commission = Blueprint('commission', __name__)

NETWORKS = ['Vodacom', 'Airtel', 'Tigo', 'Halotel', 'Zantel']
BANKS = ['CRDB', 'NMB']
TRANSACTION_TYPES = ['deposit', 'withdraw', 'transfer', 'payment', 'all']

@commission.route('/commission')
@login_required
def index():
    if not current_user.has_permission('admin'):
        flash('You do not have permission to view commissions.', 'danger')
        return redirect(url_for('dashboard.index'))

    today = date.today()
    start_of_month = date(today.year, today.month, 1)

    daily_commission = db.session.query(func.sum(Commission.amount)).filter(
        func.date(Commission.created_at) == today
    ).scalar() or 0

    weekly_commission = db.session.query(func.sum(Commission.amount)).filter(
        func.date(Commission.created_at) >= today - timedelta(days=7)
    ).scalar() or 0

    monthly_commission = db.session.query(func.sum(Commission.amount)).filter(
        func.date(Commission.created_at) >= start_of_month
    ).scalar() or 0

    total_commission = db.session.query(func.sum(Commission.amount)).scalar() or 0

    commissions = Commission.query.order_by(Commission.created_at.desc()).limit(100).all()

    operator_commission = db.session.query(
        Operator.full_name,
        func.sum(Commission.amount).label('total')
    ).join(Commission, Commission.operator_id == Operator.id)\
     .group_by(Operator.id)\
     .order_by(func.sum(Commission.amount).desc()).all()

    # Get commission settings
    settings = CommissionSetting.query.all()

    return render_template('commission.html',
                         daily_commission=daily_commission,
                         weekly_commission=weekly_commission,
                         monthly_commission=monthly_commission,
                         total_commission=total_commission,
                         commissions=commissions,
                         operator_commission=operator_commission,
                         settings=settings,
                         networks=NETWORKS,
                         banks=BANKS,
                         transaction_types=TRANSACTION_TYPES)

@commission.route('/commission/setting/create', methods=['POST'])
@login_required
def create_setting():
    if not current_user.has_permission('admin'):
        flash('You do not have permission to create commission settings.', 'danger')
        return redirect(url_for('commission.index'))
    
    network = request.form.get('network')
    transaction_type = request.form.get('transaction_type')
    rate = float(request.form.get('rate', 0))
    fixed_amount = float(request.form.get('fixed_amount', 0))
    
    # Check if setting exists
    existing = CommissionSetting.query.filter_by(
        network=network,
        transaction_type=transaction_type
    ).first()
    
    if existing:
        flash('Setting for this network and transaction type already exists.', 'danger')
        return redirect(url_for('commission.index'))
    
    setting = CommissionSetting(
        network=network,
        transaction_type=transaction_type,
        rate=rate,
        fixed_amount=fixed_amount,
        is_active=True
    )
    db.session.add(setting)
    db.session.commit()
    
    flash('Commission setting created successfully!', 'success')
    return redirect(url_for('commission.index'))

@commission.route('/commission/setting/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_setting(id):
    if not current_user.has_permission('admin'):
        flash('You do not have permission to modify commission settings.', 'danger')
        return redirect(url_for('commission.index'))
    
    setting = CommissionSetting.query.get_or_404(id)
    setting.is_active = not setting.is_active
    db.session.commit()
    
    status = 'activated' if setting.is_active else 'deactivated'
    flash(f'Commission setting {status} successfully!', 'success')
    return redirect(url_for('commission.index'))

@commission.route('/commission/setting/<int:id>/delete', methods=['POST'])
@login_required
def delete_setting(id):
    if not current_user.has_permission('admin'):
        flash('You do not have permission to delete commission settings.', 'danger')
        return redirect(url_for('commission.index'))
    
    setting = CommissionSetting.query.get_or_404(id)
    db.session.delete(setting)
    db.session.commit()
    
    flash('Commission setting deleted successfully!', 'success')
    return redirect(url_for('commission.index'))