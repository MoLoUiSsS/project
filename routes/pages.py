from flask import Blueprint, render_template

pages_bp = Blueprint('pages', __name__)


@pages_bp.route('/')
def index():
    return render_template('index.html')


@pages_bp.route('/parking')
def parking_page():
    return render_template('parking.html')


@pages_bp.route('/register')
def register_page():
    return render_template('register.html')


@pages_bp.route('/admin')
def admin_page():
    return render_template('admin.html')


@pages_bp.route('/camera')
def camera_page():
    return render_template('camera.html')
