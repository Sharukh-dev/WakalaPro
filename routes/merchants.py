from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.merchant import Merchant
from models.operator import Operator
from models.transaction import Transaction
from models.merchant_operator_balance import MerchantOperatorBalance
from models.commission import Commission
from sqlalchemy import func
from datetime import datetime

merchants = Blueprint('merchants', __name__)

NETWORKS = ['Vodacom', 'Airtel', 'Tigo', 'Halotel', 'Zantel']

def parse_currency(value):
    """Parse currency string with commas to float"""
    if not value:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    # Remove commas and convert to float
    cleaned = str(value).replace(',', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def get_merchant_data(merchant_id):
    """Helper function to get all merchant data"""
    merchant = Merchant.query.get_or_404(merchant_id)
    
    # Get operator balances
    operator_balances = MerchantOperatorBalance.query.filter_by(
        merchant_id=merchant_id
    ).all()
    
    # Get transaction totals
    total_deposits = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.merchant_id == merchant_id,
        Transaction.transaction_type == 'deposit'
    ).scalar() or 0
    
    total_withdrawals = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.merchant_id == merchant_id,
        Transaction.transaction_type == 'withdraw'
    ).scalar() or 0
    
    total_airtime = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.merchant_id == merchant_id,
        Transaction.transaction_type == 'airtime'
    ).scalar() or 0
    
    net_movement = total_deposits - total_withdrawals - total_airtime
    
    # Recent transactions
    transactions = Transaction.query.filter_by(
        merchant_id=merchant_id
    ).order_by(
        Transaction.created_at.desc()
    ).limit(20).all()
    
    return {
        'merchant': merchant,
        'operator_balances': operator_balances,
        'total_deposits': total_deposits,
        'total_withdrawals': total_withdrawals,
        'total_airtime': total_airtime,
        'net_movement': net_movement,
        'transactions': transactions
    }

@merchants.route('/merchants')
@login_required
def index():
    if current_user.role == 'cashier':
        flash('You do not have permission to view merchants.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    merchants_list = Merchant.query.all()
    
    # Calculate totals
    total_crdb = sum(m.crdb_balance for m in merchants_list)
    total_nmb = sum(m.nmb_balance for m in merchants_list)
    total_cash = sum(m.cash_in_hand for m in merchants_list)
    total_network = sum(m.get_network_total() for m in merchants_list)
    total_balance = sum(m.get_total_balance() for m in merchants_list)
    
    return render_template('merchants.html', 
                         merchants=merchants_list,
                         total_crdb=total_crdb,
                         total_nmb=total_nmb,
                         total_cash=total_cash,
                         total_network=total_network,
                         total_balance=total_balance,
                         networks=NETWORKS)

@merchants.route('/merchants/create', methods=['GET', 'POST'])
@login_required
def create():
    # Only admin can create merchants
    if current_user.role not in ['admin', 'super_admin']:
        flash('You do not have permission to create merchants.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    operators = Operator.query.filter_by(status='active').all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        phone_number = request.form.get('phone_number')
        location = request.form.get('location', '')
        
        # Parse all currency values using parse_currency function
        cash_in_hand = parse_currency(request.form.get('cash_in_hand', 0))
        crdb_balance = parse_currency(request.form.get('crdb_balance', 0))
        nmb_balance = parse_currency(request.form.get('nmb_balance', 0))
        
        # Get Network balances
        balance_vodacom = parse_currency(request.form.get('balance_vodacom', 0))
        balance_airtel = parse_currency(request.form.get('balance_airtel', 0))
        balance_tigo = parse_currency(request.form.get('balance_tigo', 0))
        balance_halotel = parse_currency(request.form.get('balance_halotel', 0))
        balance_zantel = parse_currency(request.form.get('balance_zantel', 0))
        
        # Check if merchant exists
        existing = Merchant.query.filter_by(name=name).first()
        if existing:
            flash('Merchant with this name already exists.', 'danger')
            return render_template('merchant_form.html', merchant=None, operators=operators, networks=NETWORKS)
        
        # Calculate total balance
        total_network = (balance_vodacom + balance_airtel + balance_tigo + 
                         balance_halotel + balance_zantel)
        current_balance = cash_in_hand + total_network + crdb_balance + nmb_balance
        
        # Create merchant
        merchant = Merchant(
            name=name,
            phone_number=phone_number,
            location=location,
            network='',
            cash_in_hand=cash_in_hand,
            opening_balance=cash_in_hand,
            current_balance=current_balance,
            crdb_balance=crdb_balance,
            nmb_balance=nmb_balance,
            balance_vodacom=balance_vodacom,
            balance_airtel=balance_airtel,
            balance_tigo=balance_tigo,
            balance_halotel=balance_halotel,
            balance_zantel=balance_zantel
        )
        db.session.add(merchant)
        db.session.flush()  # Get merchant ID
        
        # Handle operator floats
        operator_ids = request.form.getlist('operator_ids[]')
        operator_floats = request.form.getlist('operator_floats[]')
        
        for i, operator_id in enumerate(operator_ids):
            if operator_id and operator_id.strip():
                float_amount = parse_currency(operator_floats[i]) if i < len(operator_floats) else 0
                if float_amount > 0:
                    balance = MerchantOperatorBalance(
                        merchant_id=merchant.id,
                        operator_id=int(operator_id),
                        balance=float_amount
                    )
                    db.session.add(balance)
        
        db.session.commit()
        flash('Merchant created successfully!', 'success')
        return redirect(url_for('merchants.index'))
    
    return render_template('merchant_form.html', merchant=None, operators=operators, networks=NETWORKS)

@merchants.route('/merchants/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    # Only admin can edit merchants
    if current_user.role not in ['admin', 'super_admin']:
        flash('You do not have permission to edit merchants.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    merchant = Merchant.query.get_or_404(id)
    operators = Operator.query.filter_by(status='active').all()
    
    # Get existing operator balances
    existing_balances = MerchantOperatorBalance.query.filter_by(merchant_id=id).all()
    existing_operator_ids = [b.operator_id for b in existing_balances]
    
    if request.method == 'POST':
        merchant.name = request.form.get('name')
        merchant.phone_number = request.form.get('phone_number')
        merchant.location = request.form.get('location', '')
        
        # Parse all currency values
        merchant.cash_in_hand = parse_currency(request.form.get('cash_in_hand', 0))
        merchant.crdb_balance = parse_currency(request.form.get('crdb_balance', 0))
        merchant.nmb_balance = parse_currency(request.form.get('nmb_balance', 0))
        
        # Update Network balances
        merchant.balance_vodacom = parse_currency(request.form.get('balance_vodacom', 0))
        merchant.balance_airtel = parse_currency(request.form.get('balance_airtel', 0))
        merchant.balance_tigo = parse_currency(request.form.get('balance_tigo', 0))
        merchant.balance_halotel = parse_currency(request.form.get('balance_halotel', 0))
        merchant.balance_zantel = parse_currency(request.form.get('balance_zantel', 0))
        
        # Calculate total balance
        total_network = merchant.get_network_total()
        merchant.current_balance = merchant.cash_in_hand + total_network + merchant.crdb_balance + merchant.nmb_balance
        
        # Update operator floats - delete old ones
        MerchantOperatorBalance.query.filter_by(merchant_id=id).delete()
        
        # Add new operator floats
        operator_ids = request.form.getlist('operator_ids[]')
        operator_floats = request.form.getlist('operator_floats[]')
        
        for i, operator_id in enumerate(operator_ids):
            if operator_id and operator_id.strip():
                float_amount = parse_currency(operator_floats[i]) if i < len(operator_floats) else 0
                if float_amount > 0:
                    balance = MerchantOperatorBalance(
                        merchant_id=merchant.id,
                        operator_id=int(operator_id),
                        balance=float_amount
                    )
                    db.session.add(balance)
        
        db.session.commit()
        flash('Merchant updated successfully!', 'success')
        return redirect(url_for('merchants.index'))
    
    return render_template('merchant_form.html', 
                         merchant=merchant, 
                         operators=operators,
                         existing_balances=existing_balances,
                         existing_operator_ids=existing_operator_ids,
                         networks=NETWORKS)

@merchants.route('/merchants/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if current_user.role not in ['admin', 'super_admin']:
        flash('You do not have permission to delete merchants.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    merchant = Merchant.query.get_or_404(id)
    
    if Transaction.query.filter_by(merchant_id=id).first():
        flash('Cannot delete merchant with existing transactions.', 'danger')
        return redirect(url_for('merchants.index'))
    
    # Delete operator balances
    MerchantOperatorBalance.query.filter_by(merchant_id=id).delete()
    
    db.session.delete(merchant)
    db.session.commit()
    flash('Merchant deleted successfully!', 'success')
    return redirect(url_for('merchants.index'))

@merchants.route('/merchants/<int:id>/view')
@login_required
def view(id):
    # Manager and above can view
    if current_user.role == 'cashier':
        flash('You do not have permission to view merchant details.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    data = get_merchant_data(id)
    return render_template('merchant_details.html', **data, networks=NETWORKS)

@merchants.route('/merchants/<int:id>/account')
@login_required
def account(id):
    # Cashier can view account
    if current_user.role == 'viewer':
        flash('You do not have permission to view merchant account.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    data = get_merchant_data(id)
    merchant = data['merchant']
    
    # Get network balances
    network_balances = {
        'Vodacom': merchant.balance_vodacom,
        'Airtel': merchant.balance_airtel,
        'Tigo': merchant.balance_tigo,
        'Halotel': merchant.balance_halotel,
        'Zantel': merchant.balance_zantel
    }
    
    return render_template('merchant_account.html', 
                         merchant=merchant,
                         cash=merchant.cash_in_hand,
                         crdb_balance=merchant.crdb_balance,
                         nmb_balance=merchant.nmb_balance,
                         float_balance=sum(b.balance for b in data['operator_balances']),
                         transactions=data['transactions'],
                         network_balances=network_balances,
                         network_total=merchant.get_network_total(),
                         total_balance=merchant.get_total_balance())