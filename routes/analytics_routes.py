import sqlite3
import datetime
import csv
import io
from flask import Blueprint, jsonify, make_response
from database import get_db_connection

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/api/analytics/peak_hours')
def get_peak_hours():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
        
    try:
        cursor = conn.cursor()
        # Get count of accesses grouped by hour of the day
        cursor.execute("""
            SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
            FROM access_logs
            GROUP BY hour
            ORDER BY hour
        """)
        results = cursor.fetchall()
        
        # Format for chart.js
        labels = [f"{i:02d}:00" for i in range(24)]
        data = [0] * 24
        
        for row in results:
            if row['hour']:
                hour_idx = int(row['hour'])
                data[hour_idx] = row['count']
                
        return jsonify({
            'labels': labels,
            'data': data
        })
    finally:
        conn.close()

@analytics_bp.route('/api/analytics/summary')
def get_summary():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
        
    try:
        cursor = conn.cursor()
        
        # Today's accesses
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) FROM access_logs WHERE date(timestamp) = ?", (today,))
        today_accesses = cursor.fetchone()[0]
        
        # Total vehicles
        cursor.execute("SELECT COUNT(*) FROM registered_vehicles")
        total_vehicles = cursor.fetchone()[0]
        
        # Rejection rate
        cursor.execute("SELECT COUNT(*) FROM access_logs")
        total_logs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM access_logs WHERE access_granted = 0")
        rejected_logs = cursor.fetchone()[0]
        
        rejection_rate = (rejected_logs / total_logs * 100) if total_logs > 0 else 0
        
        return jsonify({
            'today_accesses': today_accesses,
            'total_vehicles': total_vehicles,
            'rejection_rate': round(rejection_rate, 1)
        })
    finally:
        conn.close()
