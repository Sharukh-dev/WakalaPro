from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.operator import Operator
from models.user import User

operators = Blueprint('operators', __name__)

@operators.route('/operators')
@login_required
def index():
    if not current_user.has_permission('admin'):
        flash('You do not have permission to view operators.', 'danger')
        return redirect(url_for('dashboard.index'))

    operators_list = Operator.query.all()
    return render_template('operators.html', operators=operators_list)

@operators.route('/operators/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.has_permission('admin'):
        flash('You do not have permission to create operators.', 'danger')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        full_name = request.form.get('full_name')
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        address = request.form.get('address')

        # Check if user already has operator
        existing = Operator.query.filter_by(user_id=user_id).first()
        if existing:
            flash('This user is already assigned as an operator.', 'danger')
            return render_template('operator_form.html', operator=None)

        operator = Operator(
            user_id=user_id,
            full_name=full_name,
            phone_number=phone_number,
            email=email,
            address=address,
            status='active'
        )
        db.session.add(operator)
        db.session.commit()

        flash('Operator created successfully!', 'success')
        return redirect(url_for('operators.index'))

    users = User.query.filter(User.role.in_(['admin', 'manager', 'cashier'])).all()
    return render_template('operator_form.html', operator=None, users=users)

@operators.route('/operators/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    if not current_user.has_permission('admin'):
        flash('You do not have permission to edit operators.', 'danger')
        return redirect(url_for('dashboard.index'))

    operator = Operator.query.get_or_404(id)

    if request.method == 'POST':
        operator.full_name = request.form.get('full_name')
        operator.phone_number = request.form.get('phone_number')
        operator.email = request.form.get('email')
        operator.address = request.form.get('address')
        operator.status = request.form.get('status')

        db.session.commit()
        flash('Operator updated successfully!', 'success')
        return redirect(url_for('operators.index'))

    users = User.query.filter(User.role.in_(['admin', 'manager', 'cashier'])).all()
    return render_template('operator_form.html', operator=operator, users=users)

@operators.route('/operators/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if not current_user.has_permission('admin'):
        flash('You do not have permission to delete operators.', 'danger')
        return redirect(url_for('dashboard.index'))

    operator = Operator.query.get_or_404(id)
    db.session.delete(operator)
    db.session.commit()
    flash('Operator deleted successfully!', 'success')
    return redirect(url_for('operators.index'))