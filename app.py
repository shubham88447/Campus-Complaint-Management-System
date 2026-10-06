"""
Smart Campus Complaint System - Flask API Server
Serves static web UI and provides RESTful endpoints for NLP analysis, complaint submission,
status tracking, department management, and real-time analytics.
"""

import csv
import io
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import database
from nlp_engine import nlp_engine, DEPARTMENTS

app = Flask(__name__, static_folder='static')
CORS(app)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    portal_type = data.get('portal_type', 'student') # 'student' or 'admin'

    if not email or not password:
        return jsonify({"success": False, "error": "Email and password are required"}), 400

    user = database.authenticate_user(email, password)
    if not user:
        return jsonify({"success": False, "error": "Invalid email credentials or password"}), 401

    # Verify portal permissions
    if portal_type == 'admin' and user['role'] not in ['admin', 'staff']:
        return jsonify({
            "success": False,
            "error": "Access Denied: This account does not have Operations Desk Administrative access."
        }), 403

    return jsonify({
        "success": True,
        "message": f"Welcome back, {user['name']}!",
        "user": user
    })

@app.route('/api/departments', methods=['GET'])
def get_departments():
    return jsonify({
        "success": True,
        "departments": DEPARTMENTS
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_complaint_text():
    data = request.get_json() or {}
    title = data.get('title', '')
    description = data.get('description', '')
    user_category = data.get('category', None)

    if not title and not description:
        return jsonify({
            "success": False,
            "error": "Please provide a title or description for NLP analysis"
        }), 400

    analysis = nlp_engine.analyze_complaint(title, description, user_category)
    return jsonify({
        "success": True,
        "analysis": analysis
    })

@app.route('/api/complaints', methods=['GET'])
def list_complaints():
    category = request.args.get('category')
    priority = request.args.get('priority')
    status = request.args.get('status')
    search = request.args.get('search')
    department = request.args.get('department')
    reporter_email = request.args.get('reporter_email')

    complaints = database.get_all_complaints(
        category=category,
        priority=priority,
        status=status,
        search=search,
        department=department,
        reporter_email=reporter_email
    )

    return jsonify({
        "success": True,
        "count": len(complaints),
        "complaints": complaints
    })

@app.route('/api/complaints/<int:complaint_id>', methods=['GET'])
def get_complaint(complaint_id):
    complaint = database.get_complaint_by_id(complaint_id)
    if not complaint:
        return jsonify({"success": False, "error": "Complaint ticket not found"}), 404
    
    return jsonify({
        "success": True,
        "complaint": complaint
    })

@app.route('/api/complaints', methods=['POST'])
def create_complaint():
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()

    if not title or not description:
        return jsonify({"success": False, "error": "Both title and description are required"}), 400

    new_complaint = database.create_complaint(data)
    return jsonify({
        "success": True,
        "message": "Complaint submitted successfully and routed by NLP engine!",
        "complaint": new_complaint
    }), 201

@app.route('/api/complaints/<int:complaint_id>', methods=['PATCH'])
def update_complaint(complaint_id):
    data = request.get_json() or {}
    new_status = data.get('status')
    actor = data.get('actor', 'Campus Administrator')
    note = data.get('note')
    assigned_to = data.get('assigned_to')

    if not new_status:
        return jsonify({"success": False, "error": "Status field is required"}), 400

    updated = database.update_complaint_status(
        complaint_id=complaint_id,
        new_status=new_status,
        actor=actor,
        note=note,
        assigned_to=assigned_to
    )

    if not updated:
        return jsonify({"success": False, "error": "Complaint not found"}), 404

    return jsonify({
        "success": True,
        "message": f"Complaint #{complaint_id} updated to {new_status}",
        "complaint": updated
    })

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    summary = database.get_analytics_summary()
    return jsonify({
        "success": True,
        "analytics": summary
    })

@app.route('/api/export', methods=['GET'])
def export_csv():
    complaints = database.get_all_complaints()
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'Ticket No', 'Title', 'Category', 'Predicted Category', 'Confidence (%)',
        'Priority', 'Urgency Score', 'Status', 'Department', 'Assigned To',
        'Reporter Name', 'Reporter Email', 'Location', 'Submitted At', 'SLA Deadline', 'Resolved At'
    ])

    for c in complaints:
        writer.writerow([
            c['ticket_no'], c['title'], c['category'], c['predicted_category'], c['confidence'],
            c['priority'], c['urgency_score'], c['status'], c['department'], c['assigned_to'] or 'Unassigned',
            c['reporter_name'], c['reporter_email'], c['location'], c['created_at'], c['sla_deadline'], c['resolved_at'] or 'N/A'
        ])

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-disposition": "attachment; filename=campus_complaints_export.csv"}
    )

if __name__ == '__main__':
    database.init_db()
    database.seed_database_if_empty()
    print("Starting Smart Campus Complaint Management Server on http://127.0.0.1:5050")
    app.run(host='0.0.0.0', port=5050, debug=False)
