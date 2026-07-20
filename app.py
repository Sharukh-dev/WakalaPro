from flask import Flask, render_template, session
from config import Config
from extensions import db, login_manager
import os

def create_app():
    app = Flask(__name__)
    app.config["SESSION_PERMANENT"] = False
    app.config.from_object(Config)

    # ==========================
    # DATABASE
    # ==========================
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Ensure instance directory exists
        instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
        if not os.path.exists(instance_path):
            os.makedirs(instance_path)
        db_path = os.path.join(instance_path, 'wakala.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    if os.environ.get('FLASK_ENV') == 'production':
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # ==========================
    # CUSTOM FILTERS
    # ==========================
    @app.template_filter('format_number')
    def format_number(value):
        if value is None:
            return "0"
        try:
            num = int(float(value))
            return "{:,.0f}".format(num)
        except (ValueError, TypeError):
            return str(value)

    @app.template_filter('format_currency')
    def format_currency(value):
        if value is None:
            return "TSh 0"
        try:
            num = int(float(value))
            return "TSh {:,.0f}".format(num)
        except (ValueError, TypeError):
            return "TSh 0"

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @app.before_request
    def check_session():
        if "server_restart" not in session:
            session["server_restart"] = True

    # ==========================
    # IMPORT MODELS
    # ==========================
    from models.user import User
    from models.operator import Operator
    from models.merchant import Merchant
    from models.merchant_operator_balance import MerchantOperatorBalance
    from models.transaction import Transaction
    from models.expense import Expense
    from models.commission import Commission
    from models.commission_setting import CommissionSetting
    from models.notification import Notification
    from models.cash_closing import CashClosing
    from models.audit_log import AuditLog
    from models.business_settings import BusinessSettings
    from models.license import License

    # ==========================
    # LOGIN MANAGER
    # ==========================
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ==========================
    # LICENSE CHECK
    # ==========================
    @app.before_request
    def check_license():
        from flask import request, redirect, url_for, flash
        exempt_routes = [
            'auth.login',
            'auth.register',
            'license.index',
            'license.activate',
            'license.extend',
            'license.generate',
            'static'
        ]
        
        if request.endpoint in exempt_routes:
            return None
        
        if request.path.startswith('/static'):
            return None
        
        from routes.license import check_license_status
        
        if not check_license_status():
            flash('Your license has expired. Please activate your license.', 'danger')
            return redirect(url_for('license.index'))
        
        return None

    # ==========================
    # GLOBAL NOTIFICATIONS
    # ==========================
    @app.context_processor
    def inject_notifications():
        notifications_count = 0
        latest_notifications = []

        try:
            notifications_count = Notification.query.filter_by(
                is_read=False
            ).count()

            latest_notifications = Notification.query.filter_by(
                is_read=False
            ).order_by(
                Notification.created_at.desc()
            ).limit(5).all()
        except Exception:
            notifications_count = 0
            latest_notifications = []

        return dict(
            notifications_count=notifications_count,
            latest_notifications=latest_notifications
        )

    # ==========================
    # IMPORT ROUTES
    # ==========================
    from routes.auth import auth
    from routes.dashboard import dashboard
    from routes.merchants import merchants
    from routes.transactions import transactions
    from routes.reports import reports
    from routes.settings import settings
    from routes.commission import commission
    from routes.expenses import expenses
    from routes.receipts import receipts
    from routes.notifications import notifications
    from routes.notification_api import notification_api
    from routes.users import users
    from routes.cash_closing import cash_closing
    from routes.audit import audit
    from routes.operators import operators
    from routes.float import floats
    from routes.license import license_bp
    from routes.landing import landing  # ADDED: Landing page route

    # ==========================
    # REGISTER BLUEPRINTS
    # ==========================
    app.register_blueprint(auth)
    app.register_blueprint(dashboard)
    app.register_blueprint(merchants)
    app.register_blueprint(transactions)
    app.register_blueprint(reports)
    app.register_blueprint(settings)
    app.register_blueprint(commission)
    app.register_blueprint(expenses)
    app.register_blueprint(receipts)
    app.register_blueprint(notifications)
    app.register_blueprint(notification_api)
    app.register_blueprint(users)
    app.register_blueprint(cash_closing)
    app.register_blueprint(audit)
    app.register_blueprint(operators)
    app.register_blueprint(floats)
    app.register_blueprint(license_bp)
    app.register_blueprint(landing)  # ADDED: Landing page blueprint

    # ==========================
    # CREATE TABLES - ONLY IF NOT EXISTS
    # ==========================
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Create trial license if none exists
        from models.license import License
        from routes.license import generate_license_key
        from datetime import datetime, timedelta
        
        license = License.query.first()
        if not license:
            trial_license = License(
                license_key=generate_license_key(),
                is_active=True,
                is_used=False,
                activated_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30),
                days_remaining=30,
                customer_name='Trial User',
                customer_email='trial@wakalapro.com',
                duration_days=30,
                notes='Trial license - 30 days'
            )
            db.session.add(trial_license)
            db.session.commit()
            print("✅ Trial license created! 30 days remaining.")
        
        print("✅ Database tables created successfully!")

    # ==========================
    # ERROR HANDLER
    # ==========================
    @app.errorhandler(403)
    def forbidden(error):
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("500.html"), 500

    # ==========================
    # SECURITY HEADERS
    # ==========================
    @app.after_request
    def add_security_headers(response):
        if os.environ.get('FLASK_ENV') == 'production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)