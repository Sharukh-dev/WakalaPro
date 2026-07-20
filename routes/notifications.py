from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.notification import Notification
from datetime import datetime

notifications = Blueprint('notifications', __name__)

@notifications.route('/notifications')
@login_required
def index():
    notifications_list = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Notification.created_at.desc()
    ).all()

    unread_count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()

    return render_template('notifications.html',
                         notifications=notifications_list,
                         unread_count=unread_count)

@notifications.route('/notifications/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != current_user.id:
        flash('You do not have permission to mark this notification.', 'danger')
        return redirect(url_for('notifications.index'))
    
    notification.is_read = True
    db.session.commit()
    flash('Notification marked as read.', 'success')
    return redirect(url_for('notifications.index'))

@notifications.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    
    db.session.commit()
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('notifications.index'))

@notifications.route('/notifications/delete/<int:notification_id>', methods=['POST'])
@login_required
def delete(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != current_user.id:
        flash('You do not have permission to delete this notification.', 'danger')
        return redirect(url_for('notifications.index'))
    
    db.session.delete(notification)
    db.session.commit()
    flash('Notification deleted.', 'success')
    return redirect(url_for('notifications.index'))