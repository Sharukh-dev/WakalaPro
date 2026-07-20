from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.merchant import Merchant
from models.operator import Operator
from models.transaction import Transaction
from models.expense import Expense
from models.commission import Commission
from models.notification import Notification
from models.user import User
from sqlalchemy import func
from datetime import datetime, timedelta, date

dashboard = Blueprint('dashboard', __name__)

# ONDOA @app.route('/') - hii sasa iko kwenye app.py

@dashboard.route('/dashboard')
@login_required
def index():
    today = date.today()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())

    merchants_count = Merchant.query.count()
    operators_count = Operator.query.count()

    today_transactions = Transaction.query.filter(
        Transaction.created_at >= start_of_day,
        Transaction.created_at <= end_of_day
    ).count()

    today_deposits = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == 'DEPOSIT',
        Transaction.created_at >= start_of_day,
        Transaction.created_at <= end_of_day
    ).scalar() or 0

    today_withdrawals = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == 'WITHDRAW',
        Transaction.created_at >= start_of_day,
        Transaction.created_at <= end_of_day
    ).scalar() or 0

    today_commission = db.session.query(func.sum(Commission.amount)).filter(
        Commission.created_at >= start_of_day,
        Commission.created_at <= end_of_day
    ).scalar() or 0

    today_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.created_at >= start_of_day,
        Expense.created_at <= end_of_day
    ).scalar() or 0

    profit = today_commission - today_expenses
    total_balance = db.session.query(func.sum(Merchant.current_balance)).scalar() or 0

    # Chart data - Last 7 days
    chart_labels = []
    chart_deposits = []
    chart_withdrawals = []
    chart_commissions = []

    for i in range(6, -1, -1):
        day = date.today() - timedelta(days=i)
        start = datetime.combine(day, datetime.min.time())
        end = datetime.combine(day, datetime.max.time())

        chart_labels.append(day.strftime('%b %d'))

        deposit = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.transaction_type == 'DEPOSIT',
            Transaction.created_at >= start,
            Transaction.created_at <= end
        ).scalar() or 0
        chart_deposits.append(float(deposit))

        withdrawal = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.transaction_type == 'WITHDRAW',
            Transaction.created_at >= start,
            Transaction.created_at <= end
        ).scalar() or 0
        chart_withdrawals.append(float(withdrawal))

        commission = db.session.query(func.sum(Commission.amount)).filter(
            Commission.created_at >= start,
            Commission.created_at <= end
        ).scalar() or 0
        chart_commissions.append(float(commission))

    return render_template('dashboard.html',
                         merchants_count=merchants_count,
                         operators_count=operators_count,
                         today_transactions=today_transactions,
                         today_deposits=today_deposits,
                         today_withdrawals=today_withdrawals,
                         today_commission=today_commission,
                         today_expenses=today_expenses,
                         profit=profit,
                         total_balance=total_balance,
                         chart_labels=chart_labels,
                         chart_deposits=chart_deposits,
                         chart_withdrawals=chart_withdrawals,
                         chart_commissions=chart_commissions)

@dashboard.route('/dashboard/stats')
@login_required
def get_stats():
    today = date.today()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())

    merchants_count = Merchant.query.count()
    operators_count = Operator.query.count()

    today_transactions = Transaction.query.filter(
        Transaction.created_at >= start_of_day,
        Transaction.created_at <= end_of_day
    ).count()

    today_deposits = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == 'DEPOSIT',
        Transaction.created_at >= start_of_day,
        Transaction.created_at <= end_of_day
    ).scalar() or 0

    today_withdrawals = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == 'WITHDRAW',
        Transaction.created_at >= start_of_day,
        Transaction.created_at <= end_of_day
    ).scalar() or 0

    today_commission = db.session.query(func.sum(Commission.amount)).filter(
        Commission.created_at >= start_of_day,
        Commission.created_at <= end_of_day
    ).scalar() or 0

    today_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.created_at >= start_of_day,
        Expense.created_at <= end_of_day
    ).scalar() or 0

    profit = today_commission - today_expenses
    total_balance = db.session.query(func.sum(Merchant.current_balance)).scalar() or 0

    return jsonify({
        'merchants_count': merchants_count,
        'operators_count': operators_count,
        'today_transactions': today_transactions,
        'today_deposits': float(today_deposits),
        'today_withdrawals': float(today_withdrawals),
        'today_commission': float(today_commission),
        'today_expenses': float(today_expenses),
        'profit': float(profit),
        'total_balance': float(total_balance)
    })