from flask import Blueprint, request, jsonify
from services import arduino_service

arduino_bp = Blueprint('arduino', __name__)


@arduino_bp.route('/api/arduino/status')
def status():
    return jsonify(arduino_service.get_status())


@arduino_bp.route('/api/arduino/connect', methods=['POST'])
def connect():
    data = request.get_json() or {}
    port = data.get('port')
    success, message = arduino_service.connect(port)
    return jsonify({'success': success, 'message': message})


@arduino_bp.route('/api/arduino/disconnect', methods=['POST'])
def disconnect():
    arduino_service.disconnect()
    return jsonify({'success': True})


@arduino_bp.route('/api/arduino/ports')
def list_ports():
    return jsonify(arduino_service.list_ports())


@arduino_bp.route('/api/arduino/command', methods=['POST'])
def send_command():
    data = request.get_json() or {}
    command = data.get('command', '')
    if command:
        arduino_service.send_command(command)
        return jsonify({'success': True, 'sent': command})
    return jsonify({'success': False, 'error': 'No command'}), 400
