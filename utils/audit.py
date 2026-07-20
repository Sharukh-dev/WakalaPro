from flask_login import current_user
from extensions import db
from models.audit_log import AuditLog


def create_audit(action, description):

    user_id = None


    if current_user.is_authenticated:

        user_id = current_user.id



    log = AuditLog(

        user_id=user_id,

        action=action,

        description=description

    )


    db.session.add(log)