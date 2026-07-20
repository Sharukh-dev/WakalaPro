from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.commission import Commission
from models.commission_setting import CommissionSetting
from models.operator import Operator
from models.user import User
from sqlalchemy import func
from datetime import datetime, date, timedelta

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

@commission.route('/commission/dashboard')
@login_required
def dashboard():
    """Commission dashboard with operator performance"""
    if not current_user.has_permission('admin'):
        flash('You do not have permission to view commission dashboard.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    today = date.today()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())
    
    # Today's commission by operator
    operator_commissions = db.session.query(
        Operator.full_name,
        Operator.id,
        func.sum(Commission.amount).label('total'),
        func.count(Commission.id).label('count')
    ).join(Commission, Commission.operator_id == Operator.id)\
     .filter(Commission.created_at >= start_of_day, Commission.created_at <= end_of_day)\
     .group_by(Operator.id)\
     .order_by(func.sum(Commission.amount).desc()).all()
    
    # Weekly commission
    week_start = today - timedelta(days=7)
    weekly_total = db.session.query(func.sum(Commission.amount)).filter(
        Commission.created_at >= week_start
    ).scalar() or 0
    
    # Monthly commission
    month_start = date(today.year, today.month, 1)
    monthly_total = db.session.query(func.sum(Commission.amount)).filter(
        Commission.created_at >= month_start
    ).scalar() or 0
    
    # Top operator
    top_operator = db.session.query(
        Operator.full_name,
        func.sum(Commission.amount).label('total')
    ).join(Commission, Commission.operator_id == Operator.id)\
     .group_by(Operator.id)\
     .order_by(func.sum(Commission.amount).desc()).first()
    
    # Commission trend (last 7 days)
    trend_labels = []
    trend_data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        start = datetime.combine(day, datetime.min.time())
        end = datetime.combine(day, datetime.max.time())
        trend_labels.append(day.strftime('%b %d'))
        daily_total = db.session.query(func.sum(Commission.amount)).filter(
            Commission.created_at >= start,
            Commission.created_at <= end
        ).scalar() or 0
        trend_data.append(float(daily_total))
    
    return render_template('commission_dashboard.html',
                         operator_commissions=operator_commissions,
                         weekly_total=weekly_total,
                         monthly_total=monthly_total,
                         top_operator=top_operator,
                         trend_labels=trend_labels,
                         trend_data=trend_data,
                         today=today)

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