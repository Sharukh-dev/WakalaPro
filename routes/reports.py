from flask import Blueprint, render_template, send_file
from io import BytesIO
from reportlab.pdfgen import canvas
from openpyxl import Workbook
from flask_login import login_required
from utils.permissions import role_required
from sqlalchemy import func
from datetime import date, datetime

from extensions import db

from models.transaction import Transaction
from models.commission import Commission
from models.merchant import Merchant
from models.expense import Expense



reports = Blueprint(
    "reports",
    __name__
)





@reports.route("/reports")
@login_required
@role_required("admin","manager")
def index():


    today = date.today()



    # Existing totals

    total_transactions = Transaction.query.count()



    total_amount = db.session.query(
        func.sum(Transaction.amount)
    ).scalar() or 0




    total_commission = db.session.query(
        func.sum(Commission.amount)
    ).scalar() or 0




    deposit_total = db.session.query(
        func.sum(Transaction.amount)
    ).filter(
        Transaction.transaction_type == "Deposit"
    ).scalar() or 0




    withdrawal_total = db.session.query(
        func.sum(Transaction.amount)
    ).filter(
        Transaction.transaction_type == "Withdraw"
    ).scalar() or 0




    airtime_total = db.session.query(
        func.sum(Transaction.amount)
    ).filter(
        Transaction.transaction_type == "Airtime"
    ).scalar() or 0




    total_merchants = Merchant.query.count()





    # Expenses

    total_expenses = db.session.query(
        func.sum(Expense.amount)
    ).scalar() or 0




    profit = total_commission - total_expenses





    # Today's report

    today_transactions = Transaction.query.filter(
        func.date(Transaction.created_at) == today
    ).count()




    today_amount = db.session.query(
        func.sum(Transaction.amount)
    ).filter(
        func.date(Transaction.created_at) == today
    ).scalar() or 0




    today_commission = db.session.query(
        func.sum(Commission.amount)
    ).join(
        Transaction
    ).filter(
        func.date(Transaction.created_at) == today
    ).scalar() or 0
    today_deposits = db.session.query(
        func.sum(Transaction.amount)
    ).filter(
        func.date(Transaction.created_at) == today,
        Transaction.transaction_type == "Deposit"
    ).scalar() or 0


    today_withdrawals = db.session.query(
        func.sum(Transaction.amount)
    ).filter(
        func.date(Transaction.created_at) == today,
        Transaction.transaction_type.in_(["Withdraw", "Withdrawal"])
    ).scalar() or 0


    today_airtime = db.session.query(
        func.sum(Transaction.amount)
    ).filter(
        func.date(Transaction.created_at) == today,
        Transaction.transaction_type == "Airtime"
    ).scalar() or 0


    today_expenses = db.session.query(
        func.sum(Expense.amount)
    ).filter(
        func.date(Expense.created_at) == today
    ).scalar() or 0


    today_profit = today_commission - today_expenses


    merchant_balances = Merchant.query.order_by(
        Merchant.name
    ).all()





    recent_transactions = Transaction.query.order_by(
        Transaction.created_at.desc()
    ).limit(10).all()





    return render_template(

        "reports.html",

        total_transactions=total_transactions,

        total_amount=total_amount,

        total_commission=total_commission,

        deposit_total=deposit_total,

        withdrawal_total=withdrawal_total,

        airtime_total=airtime_total,

        total_merchants=total_merchants,

        total_expenses=total_expenses,

        profit=profit,

        today_transactions=today_transactions,

        today_amount=today_amount,

        today_commission=today_commission,

        today_deposits=today_deposits,

        today_withdrawals=today_withdrawals,

        today_airtime=today_airtime,

        today_expenses=today_expenses,

        today_profit=today_profit,

        merchant_balances=merchant_balances,

        recent_transactions=recent_transactions

    )

    # Export PDF Report

@reports.route("/reports/pdf")
@login_required
@role_required("admin", "manager")
def export_pdf():


    transactions = Transaction.query.order_by(
        Transaction.created_at.desc()
    ).limit(50).all()



    pdf_buffer = BytesIO()


    pdf = canvas.Canvas(
        pdf_buffer
    )



    pdf.setFont(
        "Helvetica",
        14
    )


    pdf.drawString(
        50,
        800,
        "WakalaPro Business Report"
    )



    y = 760



    for t in transactions:


        text = (
            f"ID: {t.id} | "
            f"Type: {t.transaction_type} | "
            f"Amount: {t.amount} TZS"
        )


        pdf.drawString(
            50,
            y,
            text
        )


        y -= 25



        if y < 50:

            pdf.showPage()

            y = 800




    pdf.save()



    pdf_buffer.seek(0)



    return send_file(

        pdf_buffer,

        download_name="wakalapro_report.pdf",

        as_attachment=True,

        mimetype="application/pdf"

    )






# Export Excel Report

@reports.route("/reports/excel")
@login_required
@role_required("admin", "manager")
def export_excel():


    transactions = Transaction.query.order_by(
        Transaction.created_at.desc()
    ).all()



    workbook = Workbook()


    sheet = workbook.active


    sheet.title = "Transactions"



    sheet.append(
        [
            "ID",
            "Merchant",
            "Type",
            "Amount",
            "Phone",
            "Reference",
            "Date"
        ]
    )



    for t in transactions:


        sheet.append(
            [
                t.id,

                t.merchant.name if t.merchant else "Unknown",

                t.transaction_type,

                t.amount,

                t.phone,

                t.reference,

                str(t.created_at)

            ]
        )



    excel_buffer = BytesIO()


    workbook.save(
        excel_buffer
    )


    excel_buffer.seek(0)



    return send_file(

        excel_buffer,

        download_name="wakalapro_transactions.xlsx",

        as_attachment=True,

        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    )