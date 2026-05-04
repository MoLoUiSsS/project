import sqlite3
import datetime
from flask import Blueprint, request, jsonify
from database import get_db_connection

_socketio = None
vehicle_bp = Blueprint('vehicles', __name__)


def init(socketio):
    global _socketio
    _socketio = socketio


@vehicle_bp.route('/api/register', methods=['POST'])
def register_vehicle():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    owner_name = data.get('owner_name', '').strip()
    plate = data.get('plaque_immatriculation', '').strip()
    phone = data.get('phone', '').strip()

    if not owner_name or not plate:
        return jsonify({'success': False, 'error': 'Name and plate are required'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500

    try:
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            "INSERT INTO registered_vehicles "
            "(owner_name, plaque_immatriculation, phone, date_registered) VALUES (?, ?, ?, ?)",
            (owner_name, plate, phone, timestamp)
        )
        conn.commit()

        if _socketio:
            _socketio.emit('vehicle_registered', {
                'id': cursor.lastrowid,
                'owner_name': owner_name,
                'plaque_immatriculation': plate,
                'phone': phone,
                'date_registered': timestamp,
                'is_paid': 0
            })

        return jsonify({'success': True, 'id': cursor.lastrowid})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'Ce matricule est déjà enregistré'}), 409
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()


@vehicle_bp.route('/api/vehicles')
def get_vehicles():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM registered_vehicles ORDER BY date_registered DESC")
            return jsonify([dict(row) for row in cursor.fetchall()])
        finally:
            conn.close()
    return jsonify([])


@vehicle_bp.route('/api/vehicles/<int:vehicle_id>/pay', methods=['POST'])
def pay_vehicle(vehicle_id):
    data = request.get_json() or {}
    amount = data.get('amount', 500)

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500

    try:
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            "UPDATE registered_vehicles SET is_paid = 1, payment_date = ?, payment_amount = ? WHERE id = ?",
            (timestamp, amount, vehicle_id)
        )
        conn.commit()
        if cursor.rowcount > 0:
            if _socketio:
                _socketio.emit('vehicle_updated', {'id': vehicle_id, 'is_paid': 1})
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Vehicle not found'}), 404
    finally:
        conn.close()


@vehicle_bp.route('/api/vehicles/<int:vehicle_id>/unpay', methods=['POST'])
def unpay_vehicle(vehicle_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500

    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE registered_vehicles SET is_paid = 0, payment_date = NULL, payment_amount = 0 WHERE id = ?",
            (vehicle_id,)
        )
        conn.commit()
        if cursor.rowcount > 0:
            if _socketio:
                _socketio.emit('vehicle_updated', {'id': vehicle_id, 'is_paid': 0})
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Vehicle not found'}), 404
    finally:
        conn.close()


@vehicle_bp.route('/api/vehicles/<int:vehicle_id>', methods=['DELETE'])
def delete_vehicle(vehicle_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM registered_vehicles WHERE id = ?", (vehicle_id,))
        conn.commit()
        if cursor.rowcount > 0:
            if _socketio:
                _socketio.emit('vehicle_deleted', {'id': vehicle_id})
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Vehicle not found'}), 404
    finally:
        conn.close()
