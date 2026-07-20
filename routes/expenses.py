from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.expense import Expense
from datetime import datetime

expenses = Blueprint('expenses', __name__)

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

@expenses.route('/expenses')
@login_required
def index():
    if current_user.role not in ['admin', 'super_admin', 'manager']:
        flash('You do not have permission to view expenses.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    expenses_list = Expense.query.order_by(Expense.created_at.desc()).all()
    return render_template('expenses.html', expenses=expenses_list)

@expenses.route('/expenses/create', methods=['GET', 'POST'])
@login_required
def create():
    if current_user.role not in ['admin', 'super_admin', 'manager']:
        flash('You do not have permission to create expenses.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        category = request.form.get('category')
        amount = parse_currency(request.form.get('amount', 0))
        description = request.form.get('description')
        
        expense = Expense(
            title=title,
            category=category,
            amount=amount,
            description=description,
            user_id=current_user.id
        )
        db.session.add(expense)
        db.session.commit()
        
        flash('Expense created successfully!', 'success')
        return redirect(url_for('expenses.index'))
    
    return render_template('expense_form.html', expense=None)