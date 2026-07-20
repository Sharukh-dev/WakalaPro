from flask import Blueprint, render_template

landing = Blueprint('landing', __name__)

@landing.route('/')
def index():
    """Home page - Landing page"""
    return render_template('landing.html')