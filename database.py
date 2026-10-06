"""
Smart Campus Complaint System - Database Layer
Manages persistent SQLite database schema, seeding, complaint CRUD, and activity logging.
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

DB_FILE = os.path.join(os.path.dirname(__file__), "campus_complaints.db")

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create complaints table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_no TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        predicted_category TEXT NOT NULL,
        confidence REAL NOT NULL,
        priority TEXT NOT NULL,
        urgency_score INTEGER NOT NULL,
        sentiment TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending',
        department TEXT NOT NULL,
        department_code TEXT NOT NULL,
        assigned_to TEXT,
        reporter_name TEXT NOT NULL,
        reporter_role TEXT NOT NULL DEFAULT 'Student',
        reporter_email TEXT NOT NULL,
        location TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        resolved_at TEXT,
        sla_deadline TEXT NOT NULL,
        is_emergency BOOLEAN NOT NULL DEFAULT 0,
        notes TEXT,
        rating INTEGER,
        feedback TEXT
    );
    """)

    # Create activity logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        actor TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        comment TEXT,
        FOREIGN KEY (complaint_id) REFERENCES complaints (id) ON DELETE CASCADE
    );
    """)

    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student',
        department TEXT DEFAULT 'General',
        avatar TEXT
    );
    """)

    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    import hashlib
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def seed_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    print("Seeding initial user accounts (students and admins)...")
    sample_users = [
        ("student@campus.edu", hash_password("password123"), "Aarav Sharma", "student", "CSE 3rd Year"),
        ("priya.p@campus.edu", hash_password("password123"), "Priya Patel", "student", "Biotech 2nd Year"),
        ("faculty@campus.edu", hash_password("password123"), "Prof. Meera Deshmukh", "faculty", "Physics Department"),
        ("admin@campus.edu", hash_password("admin123"), "Campus Operations Desk", "admin", "All"),
        ("electrical@campus.edu", hash_password("admin123"), "Engr. Rajesh Sharma", "admin", "Electrical & HVAC"),
        ("it-admin@campus.edu", hash_password("admin123"), "Dr. Ananya Roy", "admin", "IT & Network Services")
    ]

    for email, pwd, name, role, dept in sample_users:
        cursor.execute("""
        INSERT OR IGNORE INTO users (email, password_hash, name, role, department)
        VALUES (?, ?, ?, ?, ?)
        """, (email, pwd, name, role, dept))

    conn.commit()
    conn.close()

def authenticate_user(email: str, password_raw: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    pwd_hash = hash_password(password_raw)
    
    cursor.execute("SELECT id, email, name, role, department FROM users WHERE email = ? AND password_hash = ?", (email.strip().lower(), pwd_hash))
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None

def generate_ticket_no() -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM complaints")
    count = cursor.fetchone()[0] + 101
    conn.close()
    now_year = datetime.now().year
    return f"CMP-{now_year}-{count:04d}"

def seed_database_if_empty():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM complaints")
    count = cursor.fetchone()[0]
    conn.close()

    if count > 0:
        return

    print("Seeding initial campus complaints into database...")

    from nlp_engine import nlp_engine, DEPARTMENTS

    now = datetime.now()

    sample_seed_data = [
        {
            "title": "Severe short circuit & sparks in Electrical Lab 302",
            "description": "Switchboard started sparking violently during lab session. Power cut off for safety. Smells like burnt wire.",
            "reporter_name": "Aarav Sharma",
            "reporter_role": "Student (EEE 3rd Year)",
            "reporter_email": "aarav.s@campus.edu",
            "location": "Electrical Engg Block, Lab 302",
            "status": "In Progress",
            "assigned_to": "Engr. Rajesh Sharma",
            "hours_ago": 1,
            "category": "Electrical & HVAC"
        },
        {
            "title": "Campus Wi-Fi unstable & connection dropping in Hostel Block B",
            "description": "Wi-Fi keeps disconnecting every few minutes in Rooms 201 to 215. Affecting project submissions.",
            "reporter_name": "Priya Patel",
            "reporter_role": "Student (CSE 2nd Year)",
            "reporter_email": "priya.p@campus.edu",
            "location": "Boys Hostel Block B, Floor 2",
            "status": "Pending",
            "assigned_to": "Dr. Ananya Roy",
            "hours_ago": 3,
            "category": "IT & Network Services"
        },
        {
            "title": "Main water pipe leaking in Central Library Washroom",
            "description": "Heavy leak from overhead pipe. Water flooding the floor area near study cubicles.",
            "reporter_name": "Rohan Verma",
            "reporter_role": "Faculty (Mechanical Dept)",
            "reporter_email": "rohan.v@campus.edu",
            "location": "Central Library, Ground Floor",
            "status": "Assigned",
            "assigned_to": "Mr. Vikram Patel",
            "hours_ago": 5,
            "category": "Infrastructure & Civil"
        },
        {
            "title": "Undercooked food and dirty water dispenser in Mess 2",
            "description": "Dinner served last night was undercooked and water filter is emitting yellowish water.",
            "reporter_name": "Kavya Nair",
            "reporter_role": "Student (Biotech 1st Year)",
            "reporter_email": "kavya.n@campus.edu",
            "location": "Girls Hostel Mess 2",
            "status": "In Progress",
            "assigned_to": "Warden S. K. Gupta",
            "hours_ago": 14,
            "category": "Hostel & Mess Services"
        },
        {
            "title": "CCTV camera non-functional at North Gate Parking",
            "description": "The outdoor CCTV camera cable appears damaged and status light is completely off.",
            "reporter_name": "Capt. S. Jha",
            "reporter_role": "Campus Security Staff",
            "reporter_email": "security.north@campus.edu",
            "location": "North Gate Parking Zone A",
            "status": "Resolved",
            "assigned_to": "Chief Officer R. V. Singh",
            "hours_ago": 26,
            "category": "Campus Security & Safety"
        },
        {
            "title": "Projector display flickering in Lecture Hall 4",
            "description": "Projector HDMI connection flickers red and green lines during lectures. Need replacement cable.",
            "reporter_name": "Prof. N. K. Rao",
            "reporter_role": "Faculty (Physics Dept)",
            "reporter_email": "nk.rao@campus.edu",
            "location": "Science Block, Lecture Hall 4",
            "status": "Resolved",
            "assigned_to": "Prof. Meera Deshmukh",
            "hours_ago": 40,
            "category": "Academic & Library"
        },
        {
            "title": "Overflowing garbage bins near Student Canteen",
            "description": "Bins are full and waste is spilling over the walkways. Requires urgent clearance.",
            "reporter_name": "Deepak Mehta",
            "reporter_role": "Student Council Rep",
            "reporter_email": "deepak.m@campus.edu",
            "location": "Central Canteen Plaza",
            "status": "Closed",
            "assigned_to": "Ms. Sunita Verma",
            "hours_ago": 52,
            "category": "Sanitation & Housekeeping"
        },
        {
            "title": "Elevator stuck between 2nd and 3rd Floor Admin Block",
            "description": "Alarm bell activated. Emergency maintenance team requested immediately.",
            "reporter_name": "Sanjay Gupta",
            "reporter_role": "Administrative Officer",
            "reporter_email": "admin.sg@campus.edu",
            "location": "Admin Building Tower A",
            "status": "Resolved",
            "assigned_to": "Mr. Vikram Patel",
            "hours_ago": 68,
            "category": "Electrical & HVAC"
        }
    ]

    conn = get_db_connection()
    cursor = conn.cursor()

    for idx, item in enumerate(sample_seed_data, start=101):
        nlp_res = nlp_engine.analyze_complaint(item["title"], item["description"], item.get("category"))

        created_dt = now - timedelta(hours=item["hours_ago"])
        updated_dt = created_dt + timedelta(minutes=30)
        sla_dt = created_dt + timedelta(hours=nlp_res["sla_hours"])

        ticket_no = f"CMP-2026-{idx:04d}"
        resolved_dt = (created_dt + timedelta(hours=item["hours_ago"] / 2)).strftime("%Y-%m-%d %H:%M:%S") if item["status"] in ["Resolved", "Closed"] else None

        cursor.execute("""
        INSERT INTO complaints (
            ticket_no, title, description, category, predicted_category, confidence,
            priority, urgency_score, sentiment, status, department, department_code,
            assigned_to, reporter_name, reporter_role, reporter_email, location,
            created_at, updated_at, resolved_at, sla_deadline, is_emergency, notes, rating, feedback
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket_no,
            item["title"],
            item["description"],
            nlp_res["final_category"],
            nlp_res["predicted_category"],
            nlp_res["confidence"],
            nlp_res["priority"],
            nlp_res["urgency_score"],
            nlp_res["sentiment"],
            item["status"],
            nlp_res["assigned_department"],
            nlp_res["department_code"],
            item["assigned_to"],
            item["reporter_name"],
            item["reporter_role"],
            item["reporter_email"],
            item["location"],
            created_dt.strftime("%Y-%m-%d %H:%M:%S"),
            updated_dt.strftime("%Y-%m-%d %H:%M:%S"),
            resolved_dt,
            sla_dt.strftime("%Y-%m-%d %H:%M:%S"),
            1 if nlp_res["is_emergency"] else 0,
            f"Automated NLP routing completed. Category: {nlp_res['final_category']} ({nlp_res['confidence']}% match). SLA target: {nlp_res['sla_hours']} hours.",
            5 if item["status"] in ["Resolved", "Closed"] else None,
            "Quick response from maintenance team!" if item["status"] in ["Resolved", "Closed"] else None
        ))

        complaint_id = cursor.lastrowid

        # Insert Activity Logs
        cursor.execute("""
        INSERT INTO activity_logs (complaint_id, action, actor, timestamp, comment)
        VALUES (?, 'Created', ?, ?, 'Ticket submitted and NLP Priority assigned')
        """, (complaint_id, item["reporter_name"], created_dt.strftime("%Y-%m-%d %H:%M:%S")))

        cursor.execute("""
        INSERT INTO activity_logs (complaint_id, action, actor, timestamp, comment)
        VALUES (?, 'Routed', 'Automated Router', ?, ?)
        """, (complaint_id, updated_dt.strftime("%Y-%m-%d %H:%M:%S"), f"Assigned to {nlp_res['assigned_department']} department ({item['assigned_to']})"))

        if item["status"] in ["Resolved", "Closed"]:
            cursor.execute("""
            INSERT INTO activity_logs (complaint_id, action, actor, timestamp, comment)
            VALUES (?, 'Resolved', ?, ?, 'Issue inspected, repaired and verified.')
            """, (complaint_id, item["assigned_to"], resolved_dt))

    conn.commit()
    conn.close()
    print("Database seeding completed successfully.")

def get_all_complaints(
    category: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    department: Optional[str] = None,
    reporter_email: Optional[str] = None
) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM complaints WHERE 1=1"
    params = []

    if category and category != "All":
        query += " AND category = ?"
        params.append(category)

    if priority and priority != "All":
        query += " AND priority = ?"
        params.append(priority)

    if status and status != "All":
        query += " AND status = ?"
        params.append(status)

    if department and department != "All":
        query += " AND department = ?"
        params.append(department)

    if reporter_email:
        query += " AND LOWER(reporter_email) = LOWER(?)"
        params.append(reporter_email)

    if search:
        query += " AND (title LIKE ? OR description LIKE ? OR ticket_no LIKE ? OR location LIKE ? OR reporter_name LIKE ?)"
        s_term = f"%{search}%"
        params.extend([s_term, s_term, s_term, s_term, s_term])

    query += " ORDER BY urgency_score DESC, created_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

def get_complaint_by_id(complaint_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    complaint = dict(row)

    cursor.execute("SELECT * FROM activity_logs WHERE complaint_id = ? ORDER BY timestamp ASC", (complaint_id,))
    logs = [dict(r) for r in cursor.fetchall()]

    conn.close()
    complaint["logs"] = logs
    return complaint

def create_complaint(data: Dict[str, Any]) -> Dict[str, Any]:
    from nlp_engine import nlp_engine

    title = data["title"]
    description = data["description"]
    reporter_name = data.get("reporter_name", "Anonymous Student")
    reporter_role = data.get("reporter_role", "Student")
    reporter_email = data.get("reporter_email", "student@campus.edu")
    location = data.get("location", "Campus Main Building")
    user_category = data.get("category", None)

    nlp_res = nlp_engine.analyze_complaint(title, description, user_category)

    ticket_no = generate_ticket_no()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sla_dt = (datetime.now() + timedelta(hours=nlp_res["sla_hours"])).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO complaints (
        ticket_no, title, description, category, predicted_category, confidence,
        priority, urgency_score, sentiment, status, department, department_code,
        assigned_to, reporter_name, reporter_role, reporter_email, location,
        created_at, updated_at, sla_deadline, is_emergency, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ticket_no,
        title,
        description,
        nlp_res["final_category"],
        nlp_res["predicted_category"],
        nlp_res["confidence"],
        nlp_res["priority"],
        nlp_res["urgency_score"],
        nlp_res["sentiment"],
        nlp_res["assigned_department"],
        nlp_res["department_code"],
        nlp_res["department_head"],
        reporter_name,
        reporter_role,
        reporter_email,
        location,
        now_str,
        now_str,
        sla_dt,
        1 if nlp_res["is_emergency"] else 0,
        f"Automated NLP Priority: {nlp_res['priority']} ({nlp_res['urgency_score']}/100 urgency score). Routed to {nlp_res['department_head']}."
    ))

    complaint_id = cursor.lastrowid

    # Create Initial Activity Log
    cursor.execute("""
    INSERT INTO activity_logs (complaint_id, action, actor, timestamp, comment)
    VALUES (?, 'Submitted', ?, ?, ?)
    """, (complaint_id, reporter_name, now_str, f"Complaint submitted via web portal. Auto-assigned to {nlp_res['assigned_department']}."))

    conn.commit()
    conn.close()

    return get_complaint_by_id(complaint_id)

def update_complaint_status(complaint_id: int, new_status: str, actor: str, note: str = None, assigned_to: str = None) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    resolved_at = now_str if new_status in ["Resolved", "Closed"] else None

    if assigned_to:
        cursor.execute("""
        UPDATE complaints
        SET status = ?, assigned_to = ?, updated_at = ?, resolved_at = COALESCE(resolved_at, ?)
        WHERE id = ?
        """, (new_status, assigned_to, now_str, resolved_at, complaint_id))
    else:
        cursor.execute("""
        UPDATE complaints
        SET status = ?, updated_at = ?, resolved_at = COALESCE(resolved_at, ?)
        WHERE id = ?
        """, (new_status, now_str, resolved_at, complaint_id))

    log_comment = note if note else f"Status changed to {new_status}"
    cursor.execute("""
    INSERT INTO activity_logs (complaint_id, action, actor, timestamp, comment)
    VALUES (?, ?, ?, ?, ?)
    """, (complaint_id, f"Status: {new_status}", actor, now_str, log_comment))

    conn.commit()
    conn.close()

    return get_complaint_by_id(complaint_id)

def get_analytics_summary() -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM complaints")
    total_complaints = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Pending'")
    pending_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'In Progress'")
    in_progress_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status IN ('Resolved', 'Closed')")
    resolved_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE priority = 'Critical'")
    critical_count = cursor.fetchone()[0]

    # Category breakdown
    cursor.execute("SELECT category, COUNT(*) as cnt FROM complaints GROUP BY category ORDER BY cnt DESC")
    cat_counts = {row["category"]: row["cnt"] for row in cursor.fetchall()}

    # Priority breakdown
    cursor.execute("SELECT priority, COUNT(*) as cnt FROM complaints GROUP BY priority")
    prio_counts = {row["priority"]: row["cnt"] for row in cursor.fetchall()}

    # Status breakdown
    cursor.execute("SELECT status, COUNT(*) as cnt FROM complaints GROUP BY status")
    status_counts = {row["status"]: row["cnt"] for row in cursor.fetchall()}

    # Average confidence score
    cursor.execute("SELECT AVG(confidence) FROM complaints")
    avg_confidence = round(cursor.fetchone()[0] or 0.0, 1)

    # Resolution Rate Percentage
    resolution_rate = round((resolved_count / total_complaints * 100), 1) if total_complaints > 0 else 0.0

    conn.close()

    return {
        "total": total_complaints,
        "pending": pending_count,
        "in_progress": in_progress_count,
        "resolved": resolved_count,
        "critical": critical_count,
        "resolution_rate": resolution_rate,
        "avg_confidence": avg_confidence,
        "category_breakdown": cat_counts,
        "priority_breakdown": prio_counts,
        "status_breakdown": status_counts
    }

# Initialize database schema on load
init_db()
seed_users()
seed_database_if_empty()
