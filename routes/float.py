from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.merchant import Merchant
from models.operator import Operator
from models.merchant_operator_balance import MerchantOperatorBalance
from models.transaction import Transaction
from datetime import datetime

floats = Blueprint('floats', __name__)

@floats.route('/float')
@login_required
def index():
    if not current_user.has_permission('admin'):
        flash('You do not have permission to view float.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    balances = MerchantOperatorBalance.query.all()
    merchants = Merchant.query.all()
    operators = Operator.query.all()
    
    return render_template('float.html', 
                         balances=balances, 
                         merchants=merchants, 
                         operators=operators)

@floats.route('/float/assign', methods=['POST'])
@login_required
def assign():
    if not current_user.has_permission('admin'):
        flash('You do not have permission to assign float.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    merchant_id = request.form.get('merchant_id')
    operator_id = request.form.get('operator_id')
    amount = float(request.form.get('amount', 0))
    
    if not merchant_id or not operator_id:
        flash('Please select both merchant and operator.', 'danger')
        return redirect(url_for('floats.index'))
    
    # Check if balance exists
    balance = MerchantOperatorBalance.query.filter_by(
        merchant_id=merchant_id,
        operator_id=operator_id
    ).first()
    
    if balance:
        balance.balance += amount
    else:
        balance = MerchantOperatorBalance(
            merchant_id=merchant_id,
            operator_id=operator_id,
            balance=amount
        )
        db.session.add(balance)
    
    db.session.commit()
    flash('Float assigned successfully!', 'success')
    return redirect(url_for('floats.index'))

@floats.route('/float/api/<int:merchant_id>/<int:operator_id>')
@login_required
def get_balance(merchant_id, operator_id):
    balance = MerchantOperatorBalance.query.filter_by(
        merchant_id=merchant_id,
        operator_id=operator_id
    ).first()
    
    return jsonify({
        'balance': balance.balance if balance else 0
    })