from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.cash_closing import CashClosing
from models.transaction import Transaction
from models.expense import Expense
from models.commission import Commission
from sqlalchemy import func
from datetime import datetime, date

cash_closing = Blueprint('cash_closing', __name__)

def get_today_totals():
    """Get today's transaction totals"""
    today = date.today()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())
    
    # Get totals
    total_deposit = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == 'DEPOSIT',
        Transaction.created_at >= start_of_day,
        Transaction.created_at <= end_of_day
    ).scalar() or 0
    
    total_withdraw = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == 'WITHDRAW',
        Transaction.created_at >= start_of_day,
        Transaction.created_at <= end_of_day
    ).scalar() or 0
    
    total_airtime = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == 'AIRTIME',
        Transaction.created_at >= start_of_day,
        Transaction.created_at <= end_of_day
    ).scalar() or 0
    
    total_commission = db.session.query(func.sum(Commission.amount)).filter(
        Commission.created_at >= start_of_day,
        Commission.created_at <= end_of_day
    ).scalar() or 0
    
    total_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.created_at >= start_of_day,
        Expense.created_at <= end_of_day
    ).scalar() or 0
    
    return {
        'total_deposit': total_deposit,
        'total_withdraw': total_withdraw,
        'total_airtime': total_airtime,
        'total_commission': total_commission,
        'total_expenses': total_expenses
    }

@cash_closing.route('/cash-closing')
@login_required
def index():
    if current_user.role not in ['admin', 'super_admin', 'manager']:
        flash('You do not have permission to view cash closing.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    closings = CashClosing.query.order_by(CashClosing.date.desc()).all()
    
    # Get today's totals
    today = date.today()
    totals = get_today_totals()
    
    # Get previous closing for opening balance
    prev_closing = CashClosing.query.filter(
        CashClosing.date < today
    ).order_by(CashClosing.date.desc()).first()
    opening_cash = prev_closing.closing_cash if prev_closing else 0
    
    # Calculate closing cash
    closing_cash = (
        opening_cash + 
        totals['total_deposit'] - 
        totals['total_withdraw'] - 
        totals['total_airtime'] + 
        totals['total_commission'] - 
        totals['total_expenses']
    )
    
    return render_template('cash_closing.html', 
                         closings=closings,
                         opening_cash=opening_cash,
                         total_deposit=totals['total_deposit'],
                         total_withdraw=totals['total_withdraw'],
                         total_airtime=totals['total_airtime'],
                         total_commission=totals['total_commission'],
                         total_expenses=totals['total_expenses'],
                         closing_cash=closing_cash,
                         today=today)

@cash_closing.route('/cash-closing/create', methods=['GET', 'POST'])
@login_required
def create():
    if current_user.role not in ['admin', 'super_admin', 'manager']:
        flash('You do not have permission to create cash closing.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    today = date.today()
    
    if request.method == 'POST':
        opening_cash = float(request.form.get('opening_cash', 0))
        
        # Check if closing already exists for today
        existing = CashClosing.query.filter_by(date=today).first()
        if existing:
            flash('Cash closing for today already exists.', 'danger')
            return redirect(url_for('cash_closing.index'))
        
        # Get today's totals
        totals = get_today_totals()
        
        closing_cash = (
            opening_cash + 
            totals['total_deposit'] - 
            totals['total_withdraw'] - 
            totals['total_airtime'] + 
            totals['total_commission'] - 
            totals['total_expenses']
        )
        
        closing = CashClosing(
            date=today,
            opening_cash=opening_cash,
            total_deposit=totals['total_deposit'],
            total_withdraw=totals['total_withdraw'],
            total_airtime=totals['total_airtime'],
            total_commission=totals['total_commission'],
            total_expenses=totals['total_expenses'],
            closing_cash=closing_cash,
            user_id=current_user.id
        )
        db.session.add(closing)
        db.session.commit()
        
        flash('Cash closing created successfully!', 'success')
        return redirect(url_for('cash_closing.index'))
    
    # GET - show form with pre-filled data
    totals = get_today_totals()
    
    # Get previous closing
    prev_closing = CashClosing.query.order_by(CashClosing.date.desc()).first()
    opening_cash = prev_closing.closing_cash if prev_closing else 0
    
    return render_template('cash_closing_form.html',
                         opening_cash=opening_cash,
                         total_deposit=totals['total_deposit'],
                         total_withdraw=totals['total_withdraw'],
                         total_airtime=totals['total_airtime'],
                         total_commission=totals['total_commission'],
                         total_expenses=totals['total_expenses'],
                         today=today)

@cash_closing.route('/cash-closing/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if current_user.role not in ['admin', 'super_admin']:
        flash('You do not have permission to delete cash closing.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    closing = CashClosing.query.get_or_404(id)
    db.session.delete(closing)
    db.session.commit()
    flash('Cash closing deleted successfully!', 'success')
    return redirect(url_for('cash_closing.index'))