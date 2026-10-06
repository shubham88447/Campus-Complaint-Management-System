# Smart Campus Complaint Management System

An AI-powered, full-stack campus complaint management system built with **Python**, **Flask**, **SQLite**, and a **Modern Glassmorphism Web Interface**. Features real-time automatic text categorization, NLP priority detection, urgency scoring, automated department routing, SLA deadline tracking, and interactive analytics.

---

## 🌟 Key Features

1. **Automatic Text Categorization (Python NLP)**:
   - Uses a **TF-IDF + Multinomial Naive Bayes Machine Learning Classifier** paired with keyword heuristic scoring.
   - Categorizes campus complaints into 7 departments:
     - 🏗️ **Infrastructure & Civil**
     - 💻 **IT & Network Services**
     - ⚡ **Electrical & HVAC**
     - 🏢 **Hostel & Mess Services**
     - 🔒 **Campus Security & Safety**
     - 📚 **Academic & Library**
     - 🧹 **Sanitation & Housekeeping**

2. **NLP Priority & Urgency Scoring**:
   - Analyzes text sentiment, intensity, and high-risk emergency triggers (e.g., `fire`, `short circuit`, `water leak`, `theft`).
   - Assigns priority levels: **🚨 CRITICAL (P1)**, **🟧 HIGH (P2)**, **🟨 MEDIUM (P3)**, **🟦 LOW (P4)**.
   - Computes an **Urgency Index (0-100)** and sets guaranteed SLA response deadlines (2h, 12h, 24h, 48h).

3. **Automated Department Routing**:
   - Automatically assigns tickets to designated Department Leads and Officers upon submission.
   - Generates activity logs for complete audit history tracking.

4. **Interactive Modern Web Interface**:
   - **Real-Time Live Typing NLP Feedback**: As students type their complaint summary or description, the system dynamically previews predicted category, confidence %, priority badge, urgency meter, and extracted keywords.
   - **Operations Desk & Routing Queue**: Admin view for searching, filtering by priority/category/status, inspecting ticket details via a `<dialog>` modal, updating ticket status, assigning staff, and adding resolution notes.
   - **Analytics & SLA Dashboard**: Displays KPI metrics (total, pending, critical, resolution rate %, average confidence %) alongside interactive **Chart.js** charts.
   - **Interactive NLP Playground**: Test arbitrary complaint strings against the classifier engine to inspect model predictions and JSON metrics.
   - **Dark / Light Theme Toggle**: Sleek glassmorphic aesthetics with responsive custom CSS.
   - **Export CSV Reports**: Instant download of complaint records.

5. **Persistent SQLite Database**:
   - Pre-seeded with realistic sample campus complaints across all departments so the dashboard is immediately populated.

## 🔐 Dual Portal Login & Roles

The system features role-based access control and separate portals for issue submitters and operations administrators:

### 🎓 Student & Faculty Portal (Issue Submitters)
- **Purpose**: Submit new complaints, view real-time NLP classification previews, and track personal issue status.
- **Demo Credentials**:
  - **Student**: `student@campus.edu` / `password123` (*Aarav Sharma*)
  - **Faculty**: `faculty@campus.edu` / `password123` (*Prof. Meera Deshmukh*)

### 🛡️ Operations Desk & Admin Portal (Routing & Resolution)
- **Purpose**: Manage active complaints across departments, inspect audit logs, change status/assignees, view SLA & NLP analytics, run NLP playground diagnostics, and export CSV reports.
- **Demo Credentials**:
  - **Chief Admin**: `admin@campus.edu` / `admin123` (*Campus Operations Desk*)
  - **IT Supervisor**: `it-admin@campus.edu` / `admin123` (*Dr. Ananya Roy*)
  - **Electrical Supervisor**: `electrical@campus.edu` / `admin123` (*Engr. Rajesh Sharma*)

> **Tip**: You can also use the **1-Click Quick Demo Login** buttons on the login selection screen for instant access!

---

## 📁 Project Structure

```
smart_campus_complaint_system/
├── app.py              # Flask Web Server & REST API
├── database.py         # SQLite Database Schema, CRUD & Seeding
├── nlp_engine.py       # Python NLP Text Processing, ML Classifier & Priority Engine
├── campus_complaints.db# SQLite Persistent Database
├── static/
│   ├── index.html      # Single Page Application HTML markup
│   ├── styles.css      # Custom Modern CSS (Glassmorphism & Themes)
│   └── app.js          # Interactive JavaScript, Chart.js & API calls
└── README.md           # Documentation
```

---

## 🚀 Quick Start Guide

### Option 1: Streamlit App (Recommended)

```bash
# Navigate to project directory
cd C:\Users\shubh\.gemini\antigravity-ide\scratch\smart_campus_complaint_system

# Launch Streamlit Application
.venv\Scripts\streamlit.exe run streamlit_app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser.

---

### Option 2: Flask REST API & Web UI

```bash
# Launch Flask Web Server
.venv\Scripts\python.exe app.py
```
Open **[http://127.0.0.1:5050](http://127.0.0.1:5050)** in your browser.

---

## 🔌 API Endpoints Summary

- `GET /` Serves main web application interface.
- `POST /api/analyze` Analyzes complaint text in real-time and returns predicted category, confidence, priority, urgency score, and SLA target.
- `GET /api/complaints` Retrieves complaints with query filters (`category`, `priority`, `status`, `department`, `search`).
- `POST /api/complaints` Submits new complaint, runs NLP routing, inserts record into database, and returns created ticket.
- `GET /api/complaints/<id>` Fetches complaint details and complete timeline activity logs.
- `PATCH /api/complaints/<id>` Updates complaint status (`Pending`, `In Progress`, `Assigned`, `Resolved`, `Closed`), assignee, or resolution notes.
- `GET /api/analytics` Returns real-time aggregate KPI metrics and breakdown data for charts.
- `GET /api/export` Downloads CSV spreadsheet of complaint records.
