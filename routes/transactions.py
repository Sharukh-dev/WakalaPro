from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.transaction import Transaction
from models.merchant import Merchant
from models.operator import Operator
from models.commission import Commission
from models.commission_setting import CommissionSetting
from models.merchant_operator_balance import MerchantOperatorBalance
from datetime import datetime
import uuid

# Create blueprint FIRST
transactions = Blueprint('transactions', __name__)

NETWORKS = ['Vodacom', 'Airtel', 'Tigo', 'Halotel', 'Zantel']
BANKS = ['CRDB', 'NMB']

def parse_currency(value):
    """Parse currency string with commas to float"""
    if not value:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = str(value).replace(',', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def calculate_commission(amount, source, transaction_type):
    """Calculate commission based on settings"""
    if not source or amount <= 0:
        return 0.0
    
    # Check for specific transaction type setting
    setting = CommissionSetting.query.filter_by(
        network=source,
        transaction_type=transaction_type,
        is_active=True
    ).first()
    
    # If not found, check for 'all' transaction type
    if not setting:
        setting = CommissionSetting.query.filter_by(
            network=source,
            transaction_type='all',
            is_active=True
        ).first()
    
    if not setting:
        return 0.0
    
    commission = 0.0
    if setting.fixed_amount > 0:
        commission += setting.fixed_amount
    if setting.rate > 0:
        commission += (amount * setting.rate / 100)
    
    return round(commission, 2)

@transactions.route('/transactions')
@login_required
def index():
    if current_user.role == 'viewer':
        flash('You do not have permission to view transactions.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    query = Transaction.query
    
    # If user is cashier and has a merchant assigned, filter by that merchant
    if current_user.role == 'cashier' and current_user.merchant_id:
        query = query.filter_by(merchant_id=current_user.merchant_id)
    
    if current_user.role == 'manager' and current_user.merchant_id:
        query = query.filter_by(merchant_id=current_user.merchant_id)
    
    # Date filters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    if date_from:
        query = query.filter(Transaction.created_at >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(Transaction.created_at <= datetime.strptime(date_to, '%Y-%m-%d'))
    
    # Merchant filter
    merchant_id = request.args.get('merchant_id')
    if merchant_id and current_user.has_permission('admin'):
        query = query.filter_by(merchant_id=merchant_id)
    
    # Transaction type filter
    transaction_type = request.args.get('type')
    if transaction_type:
        query = query.filter_by(transaction_type=transaction_type)
    
    # Search logic
    search_by = request.args.get('search_by')
    search_value = request.args.get('search_value')
    
    if search_by and search_value:
        search_value = search_value.strip()
        
        if search_by == 'phone':
            query = query.filter(Transaction.customer_phone.like(f'%{search_value}%'))
        
        elif search_by == 'amount':
            try:
                amount_val = float(search_value.replace(',', ''))
                query = query.filter(Transaction.amount == amount_val)
            except ValueError:
                pass
        
        elif search_by == 'reference':
            query = query.filter(Transaction.reference_number.like(f'%{search_value}%'))
        
        elif search_by == 'network':
            networks = ['Vodacom', 'Airtel', 'Tigo', 'Halotel', 'Zantel']
            if search_value in networks:
                query = query.filter(Transaction.description.like(f'%{search_value}%'))
        
        elif search_by == 'bank':
            banks = ['CRDB', 'NMB']
            if search_value in banks:
                query = query.filter(Transaction.description.like(f'%{search_value}%'))
    
    transactions_list = query.order_by(Transaction.created_at.desc()).all()
    merchants = Merchant.query.all()
    
    return render_template('transactions.html', 
                         transactions=transactions_list, 
                         merchants=merchants)

@transactions.route('/transactions/create', methods=['GET', 'POST'])
@login_required
def create():
    if current_user.role not in ['admin', 'super_admin', 'manager', 'cashier']:
        flash('You do not have permission to create transactions.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get merchants based on user role
    if current_user.role == 'cashier' and current_user.merchant_id:
        merchants = Merchant.query.filter_by(id=current_user.merchant_id).all()
    elif current_user.role == 'manager' and current_user.merchant_id:
        merchants = Merchant.query.filter_by(id=current_user.merchant_id).all()
    else:
        merchants = Merchant.query.all()
    
    networks = NETWORKS
    banks = BANKS
    
    if request.method == 'POST':
        merchant_id = request.form.get('merchant_id')
        transaction_type = request.form.get('transaction_type')
        transaction_source = request.form.get('transaction_source')
        source_type = request.form.get('source_type')
        amount = parse_currency(request.form.get('amount', 0))
        description = request.form.get('description')
        reference_number = request.form.get('reference_number') or str(uuid.uuid4())[:8].upper()
        
        merchant = Merchant.query.get(merchant_id)
        if not merchant:
            flash('Merchant not found.', 'danger')
            return render_template('transaction_form.html', transaction=None, merchants=merchants, networks=networks, banks=banks)
        
        # Check if user has permission for this merchant
        if current_user.role == 'cashier' and current_user.merchant_id != merchant.id:
            flash('You do not have permission to transact for this merchant.', 'danger')
            return render_template('transaction_form.html', transaction=None, merchants=merchants, networks=networks, banks=banks)
        
        if current_user.role == 'manager' and current_user.merchant_id != merchant.id:
            flash('You do not have permission to transact for this merchant.', 'danger')
            return render_template('transaction_form.html', transaction=None, merchants=merchants, networks=networks, banks=banks)
        
        # Calculate commission based on source
        commission = calculate_commission(amount, transaction_source, transaction_type)
        
        # Update merchant balance based on transaction type
        if transaction_type == 'DEPOSIT':
            merchant.current_balance += amount
        elif transaction_type == 'WITHDRAW':
            if merchant.current_balance < amount:
                flash('Insufficient balance in merchant account.', 'danger')
                return render_template('transaction_form.html', transaction=None, merchants=merchants, networks=networks, banks=banks)
            merchant.current_balance -= amount
        elif transaction_type == 'TRANSFER':
            if merchant.current_balance < amount:
                flash('Insufficient balance in merchant account.', 'danger')
                return render_template('transaction_form.html', transaction=None, merchants=merchants, networks=networks, banks=banks)
            merchant.current_balance -= amount
        
        # Update specific source balance
        if source_type == 'network':
            network_attr = f'balance_{transaction_source.lower()}'
            if hasattr(merchant, network_attr):
                if transaction_type == 'DEPOSIT':
                    setattr(merchant, network_attr, getattr(merchant, network_attr) + amount)
                elif transaction_type == 'WITHDRAW':
                    if getattr(merchant, network_attr) < amount:
                        flash(f'Insufficient balance in {transaction_source} network.', 'danger')
                        return render_template('transaction_form.html', transaction=None, merchants=merchants, networks=networks, banks=banks)
                    setattr(merchant, network_attr, getattr(merchant, network_attr) - amount)
        elif source_type == 'bank':
            bank_attr = f'{transaction_source.lower()}_balance'
            if hasattr(merchant, bank_attr):
                if transaction_type == 'DEPOSIT':
                    setattr(merchant, bank_attr, getattr(merchant, bank_attr) + amount)
                elif transaction_type == 'WITHDRAW':
                    if getattr(merchant, bank_attr) < amount:
                        flash(f'Insufficient balance in {transaction_source} bank.', 'danger')
                        return render_template('transaction_form.html', transaction=None, merchants=merchants, networks=networks, banks=banks)
                    setattr(merchant, bank_attr, getattr(merchant, bank_attr) - amount)
        
        # Update total balance
        merchant.current_balance = (merchant.cash_in_hand + merchant.get_network_total() + 
                                   merchant.crdb_balance + merchant.nmb_balance)
        
        # Get operator ID if user is operator
        operator_id = None
        if hasattr(current_user, 'operator') and current_user.operator:
            operator_id = current_user.operator.id
        
        # Create transaction
        transaction = Transaction(
            merchant_id=merchant_id,
            operator_id=operator_id,
            user_id=current_user.id,
            transaction_type=transaction_type,
            customer_name=merchant.name,
            customer_phone=merchant.phone_number,
            amount=amount,
            commission=commission,
            reference_number=reference_number,
            description=f"{source_type} - {transaction_source}: {description}" if description else f"{source_type} - {transaction_source}",
            status='completed'
        )
        db.session.add(transaction)
        db.session.flush()
        
        # Create commission record if commission > 0
        if commission > 0:
            commission_record = Commission(
                transaction_id=transaction.id,
                merchant_id=merchant_id,
                operator_id=operator_id,
                amount=commission
            )
            db.session.add(commission_record)
        
        db.session.commit()
        flash(f'Transaction created successfully! Commission: TSh {commission:,.2f}', 'success')
        return redirect(url_for('transactions.index'))
    
    return render_template('transaction_form.html', 
                         transaction=None, 
                         merchants=merchants, 
                         networks=networks, 
                         banks=banks)

@transactions.route('/transactions/<int:id>/receipt')
@login_required
def receipt(id):
    transaction = Transaction.query.get_or_404(id)
    
    # Check if user has permission for this merchant
    if current_user.role == 'cashier' and current_user.merchant_id != transaction.merchant_id:
        flash('You do not have permission to view this receipt.', 'danger')
        return redirect(url_for('transactions.index'))
    
    if current_user.role == 'manager' and current_user.merchant_id != transaction.merchant_id:
        flash('You do not have permission to view this receipt.', 'danger')
        return redirect(url_for('transactions.index'))
    
    return render_template('receipts.html', transaction=transaction)