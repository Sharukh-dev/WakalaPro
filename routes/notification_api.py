from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models.notification import Notification
from models.commission_setting import CommissionSetting

notification_api = Blueprint('notification_api', __name__)

@notification_api.route('/api/notifications/unread-count')
@login_required
def unread_count():
    count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    return jsonify({'count': count})

@notification_api.route('/api/notifications/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    notification.is_read = True
    db.session.commit()
    return jsonify({'success': True})

@notification_api.route('/api/calculate-commission', methods=['POST'])
@login_required
def calculate_commission():
    data = request.get_json()
    amount = float(data.get('amount', 0))
    source = data.get('source', '')
    transaction_type = data.get('transaction_type', '')
    
    if not source or amount <= 0:
        return jsonify({'commission': 0})
    
    # Check for specific transaction type setting
    setting = CommissionSetting.query.filter_by(
        network=source,
        transaction_type=transaction_type,
        is_active=True
    ).first()
    
    # If not found, check for 'all' transaction type
    if not setting:
        setting = CommissionSetting.query.filter_by(
            network=source,
            transaction_type='all',
            is_active=True
        ).first()
    
    if not setting:
        return jsonify({'commission': 0})
    
    commission = 0.0
    if setting.fixed_amount > 0:
        commission += setting.fixed_amount
    if setting.rate > 0:
        commission += (amount * setting.rate / 100)
    
    return jsonify({'commission': round(commission, 2)})