from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.user import User
from models.operator import Operator
from models.merchant import Merchant

users = Blueprint('users', __name__)

@users.route('/users')
@login_required
def index():
    if not current_user.has_permission('admin'):
        flash('You do not have permission to view users.', 'danger')
        return redirect(url_for('dashboard.index'))

    users_list = User.query.all()
    return render_template('users.html', users=users_list)

@users.route('/users/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.has_permission('admin'):
        flash('You do not have permission to create users.', 'danger')
        return redirect(url_for('dashboard.index'))

    merchants = Merchant.query.all()

    if request.method == 'POST':
        username = request.form.get('username')
        phone_number = request.form.get('phone_number')
        password = request.form.get('password')
        role = request.form.get('role')
        merchant_id = request.form.get('merchant_id')

        # Check if username exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists.', 'danger')
            return render_template('user_form.html', user=None, merchants=merchants)

        # Check if phone exists
        if phone_number:
            existing_phone = User.query.filter_by(phone_number=phone_number).first()
            if existing_phone:
                flash('Phone number already exists.', 'danger')
                return render_template('user_form.html', user=None, merchants=merchants)

        # Create user
        user = User(
            username=username,
            phone_number=phone_number,
            role=role,
            is_active=True,
            merchant_id=merchant_id if merchant_id else None
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # If role is cashier or manager, also create operator record
        if role in ['cashier', 'manager', 'admin']:
            operator = Operator(
                user_id=user.id,
                full_name=username,
                phone_number=phone_number or '',
                status='active'
            )
            db.session.add(operator)
            db.session.commit()

        flash('User created successfully!', 'success')
        return redirect(url_for('users.index'))

    return render_template('user_form.html', user=None, merchants=merchants)

@users.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    if not current_user.has_permission('admin'):
        flash('You do not have permission to edit users.', 'danger')
        return redirect(url_for('dashboard.index'))

    user = User.query.get_or_404(id)
    merchants = Merchant.query.all()

    if request.method == 'POST':
        user.username = request.form.get('username')
        user.phone_number = request.form.get('phone_number')
        user.role = request.form.get('role')
        user.is_active = True if request.form.get('is_active') else False
        user.merchant_id = request.form.get('merchant_id') if request.form.get('merchant_id') else None

        password = request.form.get('password')
        if password:
            user.set_password(password)

        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('users.index'))

    return render_template('user_form.html', user=user, merchants=merchants)

@users.route('/users/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if not current_user.has_permission('admin'):
        flash('You do not have permission to delete users.', 'danger')
        return redirect(url_for('dashboard.index'))

    user = User.query.get_or_404(id)

    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('users.index'))

    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('users.index'))

@users.route('/users/<int:id>/toggle', methods=['POST'])
@login_required
def toggle(id):
    if not current_user.has_permission('admin'):
        flash('You do not have permission to toggle users.', 'danger')
        return redirect(url_for('dashboard.index'))

    user = User.query.get_or_404(id)

    if user.id == current_user.id:
        flash('You cannot toggle your own account.', 'danger')
        return redirect(url_for('dashboard.index'))

    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {status} successfully!', 'success')
    return redirect(url_for('users.index'))