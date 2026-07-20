from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models.transaction import Transaction
from models.business_settings import BusinessSettings

receipts = Blueprint('receipts', __name__)

@receipts.route('/receipt/<int:transaction_id>')
@login_required
def view(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Check permission
    if current_user.role == 'viewer':
        flash('You do not have permission to view receipts.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    settings = BusinessSettings.query.first()
    
    return render_template('receipts.html', 
                         transaction=transaction, 
                         settings=settings)