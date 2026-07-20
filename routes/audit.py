from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models.audit_log import AuditLog
from datetime import datetime

audit = Blueprint('audit', __name__)

@audit.route('/audit')
@login_required
def index():
    if not current_user.has_permission('admin'):
        flash('You do not have permission to view audit logs.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    action = request.args.get('action')
    
    query = AuditLog.query
    
    if date_from:
        query = query.filter(AuditLog.created_at >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(AuditLog.created_at <= datetime.strptime(date_to, '%Y-%m-%d'))
    if action:
        query = query.filter(AuditLog.action == action)
    
    logs = query.order_by(AuditLog.created_at.desc()).all()
    
    # Get unique actions for filter
    actions = db.session.query(AuditLog.action).distinct().all()
    actions = [a[0] for a in actions]
    
    return render_template('audit.html', logs=logs, actions=actions)

def log_action(user_id, action, description=None):
    """Helper function to log actions"""
    log = AuditLog(
        user_id=user_id,
        action=action,
        description=description
    )
    db.session.add(log)
    db.session.commit()
    return log