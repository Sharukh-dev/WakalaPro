from flask import Blueprint, render_template
from models.merchant import Merchant
from models.operator import Operator

landing = Blueprint('landing', __name__)

@landing.route('/')
def index():
    """Home page - Landing page"""
    merchants_count = Merchant.query.count()
    operators_count = Operator.query.count()
    
    return render_template('landing.html',
                         merchants_count=merchants_count,
                         operators_count=operators_count)