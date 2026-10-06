"""
Smart Campus Complaint Management System - Streamlit Application
AI Text Categorization, Priority Engine, Department Routing & Dual Portal Dashboard.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import database
from nlp_engine import nlp_engine, DEPARTMENTS

# Set Page Config
st.set_page_config(
    page_title="Smart Campus Ops | AI Complaint Router",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Glassmorphic Dark CSS Theme Injection
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .stApp {
        background-color: #0b0f19;
        background-image: 
            radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.15) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(168, 85, 247, 0.1) 0px, transparent 50%);
    }

    /* Glassmorphic Metric Cards */
    .glass-card {
        background: rgba(18, 24, 38, 0.75);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
    }
    
    /* Badges */
    .prio-badge {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    .prio-critical { background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.4); }
    .prio-high { background: rgba(249, 115, 22, 0.2); color: #f97316; border: 1px solid rgba(249, 115, 22, 0.4); }
    .prio-medium { background: rgba(234, 179, 8, 0.2); color: #eab308; border: 1px solid rgba(234, 179, 8, 0.4); }
    .prio-low { background: rgba(59, 130, 246, 0.2); color: #3b82f6; border: 1px solid rgba(59, 130, 246, 0.4); }

    .status-badge {
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .status-pending { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
    .status-in-progress { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
    .status-assigned { background: rgba(168, 85, 247, 0.2); color: #c084fc; }
    .status-resolved { background: rgba(16, 185, 129, 0.2); color: #34d399; }
    .status-closed { background: rgba(107, 114, 128, 0.2); color: #9ca3af; }

    /* Assigned Officer Box */
    .officer-box {
        background: rgba(99, 102, 241, 0.12);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 10px;
        padding: 0.65rem 0.85rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "user" not in st.session_state:
    st.session_state.user = None

# Ensure DB is initialized
database.init_db()
database.seed_users()
database.seed_database_if_empty()

# LOGIN SCREEN FUNCTION
def show_login_screen():
    st.markdown("<h1 style='text-align: center; font-size: 2.3rem; font-weight: 800; margin-bottom: 0.2rem;'>🎓 Smart Campus Operations Portal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 1.05rem; margin-bottom: 2rem;'>AI-Powered Complaint Router, Priority Engine & Department Dispatch</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("🎓 Student & Faculty Portal")
        st.caption("For submitting complaints & tracking personal issue status")

        stu_email = st.text_input("Campus Email", value="student@campus.edu", key="stu_email")
        stu_pwd = st.text_input("Password", value="password123", type="password", key="stu_pwd")

        if st.button("Log In as Student / Faculty", type="primary", use_container_width=True):
            user = database.authenticate_user(stu_email, stu_pwd)
            if user:
                st.session_state.user = user
                st.success(f"Welcome back, {user['name']}!")
                st.rerun()
            else:
                st.error("Invalid student email or password.")

        st.divider()
        st.markdown("**⚡ 1-Click Quick Demo Accounts:**")
        c_a, c_b = st.columns(2)
        if c_a.button("👤 Aarav Sharma (Student)", use_container_width=True):
            user = database.authenticate_user("student@campus.edu", "password123")
            st.session_state.user = user
            st.rerun()
        if c_b.button("👩‍🏫 Prof. Meera (Faculty)", use_container_width=True):
            user = database.authenticate_user("faculty@campus.edu", "password123")
            st.session_state.user = user
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("🛡️ Operations Desk & Admin Portal")
        st.caption("For department supervisors, technicians & routing managers")

        adm_email = st.text_input("Administrator Email", value="admin@campus.edu", key="adm_email")
        adm_pwd = st.text_input("Password", value="admin123", type="password", key="adm_pwd")

        if st.button("Log In to Operations Desk", type="primary", use_container_width=True):
            user = database.authenticate_user(adm_email, adm_pwd)
            if user and user['role'] in ['admin', 'staff']:
                st.session_state.user = user
                st.success(f"Welcome back, {user['name']}!")
                st.rerun()
            else:
                st.error("Invalid admin credentials or non-admin account.")

        st.divider()
        st.markdown("**⚡ 1-Click Quick Demo Accounts:**")
        c_c, c_d = st.columns(2)
        if c_c.button("🛡️ Chief Ops Admin", use_container_width=True):
            user = database.authenticate_user("admin@campus.edu", "admin123")
            st.session_state.user = user
            st.rerun()
        if c_d.button("💻 Dr. Ananya (IT Admin)", use_container_width=True):
            user = database.authenticate_user("it-admin@campus.edu", "admin123")
            st.session_state.user = user
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# MAIN APPLICATION LOGIC
def main():
    if not st.session_state.user:
        show_login_screen()
        return

    user = st.session_state.user
    is_admin = user['role'] in ['admin', 'staff']

    # Sidebar Header
    st.sidebar.markdown(f"### 👤 {user['name']}")
    role_color = "red" if is_admin else "blue"
    st.sidebar.markdown(f"**Role**: :{role_color}[{user['role'].upper()}]")
    st.sidebar.markdown(f"**Email**: `{user['email']}`")
    if user.get('department'):
        st.sidebar.markdown(f"**Dept / Class**: {user['department']}")

    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        st.session_state.user = None
        st.rerun()

    st.sidebar.divider()

    # Role-Based Tab Rendering
    if is_admin:
        # Operations Desk Admin Portal Navigation
        tab_choice = st.sidebar.radio(
            "Operations Desk Navigation",
            ["🛡️ Operations Desk & Queue", "📊 Analytics & SLA Dashboard"],
            index=0
        )

        if tab_choice == "🛡️ Operations Desk & Queue":
            show_operations_desk()
        elif tab_choice == "📊 Analytics & SLA Dashboard":
            show_analytics_dashboard()

    else:
        # Student & Faculty Portal Navigation
        tab_choice = st.sidebar.radio(
            "Student Portal Navigation",
            ["📌 Submit Ticket", "📋 My Submitted Issues & Status"],
            index=0
        )

        if tab_choice == "📌 Submit Ticket":
            show_submit_ticket_page(user)
        elif tab_choice == "📋 My Submitted Issues & Status":
            show_my_issues_page(user)


# PAGE 1: SUBMIT TICKET PAGE (STUDENTS & FACULTY)
def show_submit_ticket_page(user):
    st.title("📌 Campus Issue Submission Portal")
    st.caption("Submit your grievance below. Our Python NLP classifier automatically determines priority and routes your ticket to the right department.")

    col1, col2 = st.columns([1.1, 0.9])

    with col1:
        st.subheader("Issue Details")
        title = st.text_input("Issue Summary / Title *", placeholder="e.g. Short circuit in Electrical Lab switchboard")
        location = st.text_input("Specific Location / Room *", placeholder="e.g. Science Block Floor 3, Room 302")
        user_cat = st.selectbox("Department Category", ["🤖 Auto-Detect with NLP (Recommended)"] + list(DEPARTMENTS.keys()))
        description = st.text_area("Detailed Description *", placeholder="Describe what happened, any immediate hazard, equipment involved, or severity...", height=140)

        r_name = st.text_input("Reporter Name", value=user['name'])
        r_email = st.text_input("Campus Email", value=user['email'])
        r_role = st.selectbox("Reporter Role", ["Student", "Faculty", "Staff", "Visitor"], index=0 if user['role']=='student' else 1)

        cat_param = None if user_cat.startswith("🤖") else user_cat

        if st.button("🚀 Submit Ticket & Auto-Route", type="primary", use_container_width=True):
            if not title or not description:
                st.error("Please fill in both title and description.")
            else:
                complaint_data = {
                    "title": title,
                    "description": description,
                    "location": location or "Campus Main Building",
                    "category": cat_param,
                    "reporter_name": r_name,
                    "reporter_email": r_email,
                    "reporter_role": r_role
                }
                new_c = database.create_complaint(complaint_data)
                st.balloons()
                st.success(f"🎉 Ticket #{new_c['ticket_no']} submitted successfully and auto-routed to {new_c['department']} ({new_c['assigned_to']})!")

    with col2:
        st.subheader("🤖 Real-Time NLP Intelligence")
        st.caption("Live feedback from TF-IDF + Naive Bayes Classifier")

        if title or description:
            res = nlp_engine.analyze_complaint(title or "", description or "", cat_param)
            
            prio_class = res['priority'].lower()
            st.markdown(f"""
            <div class='glass-card'>
                <h4>Predicted Category: <span style='color: #06b6d4;'>{res['final_category']}</span></h4>
                <p><strong>Match Confidence:</strong> {res['confidence']}%</p>
                <p><strong>Priority Level:</strong> <span class='prio-badge prio-{prio_class}'>{res['priority'].upper()}</span></p>
                <p><strong>Urgency Score:</strong> {res['urgency_score']} / 100</p>
                <p><strong>Auto-Assigned Lead:</strong> {res['department_head']}</p>
                <p><strong>Guaranteed SLA Target:</strong> <span style='color: #10b981; font-weight: 700;'>{res['sla_hours']} Hours</span></p>
                <p><strong>Detected Triggers:</strong> {', '.join(['#' + t for t in res['triggers_found']]) or 'Standard'}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("💡 Type in the Title or Description to see live NLP priority scoring and auto-assigned department officer.")


# PAGE 2: MY ISSUES & STATUS DASHBOARD (STUDENTS & FACULTY)
def show_my_issues_page(user):
    st.title("📋 My Submitted Issues & Live Status")
    st.caption(f"Showing all tickets reported by {user['name']} ({user['email']})")

    my_complaints = database.get_all_complaints(reporter_email=user['email'])

    # KPI Summary Cards
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Submitted", len(my_complaints))
    active_cnt = len([c for c in my_complaints if c['status'] not in ['Resolved', 'Closed']])
    resolved_cnt = len([c for c in my_complaints if c['status'] in ['Resolved', 'Closed']])
    c2.metric("Active / In Progress", active_cnt)
    c3.metric("Resolved Issues", resolved_cnt)

    st.divider()

    if not my_complaints:
        st.info("You haven't submitted any complaints yet. Use the 'Submit Ticket' page to report a campus issue.")
        return

    for c in my_complaints:
        prio_class = c['priority'].lower()
        status_class = f"status-{c['status'].lower().replace(' ', '-')}"
        assigned_officer = c['assigned_to'] or 'Department Supervisor'

        with st.expander(f"🎫 {c['ticket_no']} - {c['title']} | Status: {c['status']}", expanded=True):
            col_a, col_b = st.columns([1.2, 0.8])
            
            with col_a:
                st.markdown(f"**Description**: {c['description']}")
                st.markdown(f"**Location**: 📍 `{c['location']}`")
                st.markdown(f"**Submitted On**: `{c['created_at']}`")
                st.markdown(f"**Target SLA Deadline**: `{c['sla_deadline']}`")

            with col_b:
                st.markdown(f"""
                <div class='officer-box'>
                    <div style='font-size: 0.75rem; color: #94a3b8; font-weight: 700; text-transform: uppercase;'>Assigned Officer / Lead</div>
                    <div style='font-size: 1rem; font-weight: 800; color: #06b6d4; margin-top: 0.2rem;'>
                        👨‍🔧 {assigned_officer}
                    </div>
                    <div style='font-size: 0.8rem; color: #cbd5e1;'>
                        🏢 {c['department']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"**Priority**: <span class='prio-badge prio-{prio_class}'>{c['priority'].upper()}</span>", unsafe_allow_html=True)

            # Activity Log
            ticket_details = database.get_complaint_by_id(c['id'])
            if ticket_details and ticket_details.get('logs'):
                st.markdown("**📜 Ticket Progress Activity Log:**")
                for log in ticket_details['logs']:
                    st.text(f"• [{log['timestamp']}] {log['action']} by {log['actor']} - {log['comment'] or ''}")


# PAGE 3: OPERATIONS DESK & ROUTING QUEUE (ADMIN ONLY)
def show_operations_desk():
    st.title("🛡️ Campus Operations & Routing Desk")
    st.caption("Manage active complaints across all campus departments, re-assign field technicians, and update issue statuses.")

    # Filter Bar
    f1, f2, f3, f4 = st.columns(4)
    search_q = f1.text_input("🔍 Search Ticket #, Title, Location", "")
    cat_filter = f2.selectbox("Filter Category", ["All"] + list(DEPARTMENTS.keys()))
    prio_filter = f3.selectbox("Filter Priority", ["All", "Critical", "High", "Medium", "Low"])
    status_filter = f4.selectbox("Filter Status", ["All", "Pending", "In Progress", "Assigned", "Resolved", "Closed"])

    complaints = database.get_all_complaints(
        category=cat_filter,
        priority=prio_filter,
        status=status_filter,
        search=search_q
    )

    st.subheader(f"Active Tickets Queue ({len(complaints)} found)")

    if not complaints:
        st.warning("No tickets found matching the selected filters.")
        return

    for c in complaints:
        prio_class = c['priority'].lower()
        status_class = f"status-{c['status'].lower().replace(' ', '-')}"

        with st.expander(f"🎫 Ticket #{c['ticket_no']} - {c['title']} ({c['priority']} Priority)", expanded=False):
            col_l, col_r = st.columns([1.2, 0.8])
            
            with col_l:
                st.markdown(f"**Description**: {c['description']}")
                st.markdown(f"**Location**: 📍 `{c['location']}`")
                st.markdown(f"**Reporter**: {c['reporter_name']} ({c['reporter_role']}) - `{c['reporter_email']}`")
                st.markdown(f"**NLP Match Confidence**: {c['confidence']}%")
                st.markdown(f"**Submitted At**: `{c['created_at']}` | **SLA**: `{c['sla_deadline']}`")

            with col_r:
                st.markdown(f"**Department**: `{c['department']}`")
                st.markdown(f"**Current Status**: <span class='status-badge {status_class}'>{c['status']}</span>", unsafe_allow_html=True)
                st.markdown(f"**Current Assignee**: `{c['assigned_to'] or 'Unassigned'}`")

                # Action Controls
                new_st = st.selectbox("Update Status", ["Pending", "In Progress", "Assigned", "Resolved", "Closed"], index=["Pending", "In Progress", "Assigned", "Resolved", "Closed"].index(c['status']), key=f"st_{c['id']}")
                new_assignee = st.text_input("Assigned Technician / Lead", value=c['assigned_to'] or "", key=f"as_{c['id']}")
                update_note = st.text_input("Operational Note", placeholder="Add inspection comment...", key=f"nt_{c['id']}")

                if st.button("💾 Save Ticket Update", key=f"btn_{c['id']}", type="primary"):
                    updated = database.update_complaint_status(
                        complaint_id=c['id'],
                        new_status=new_st,
                        actor=st.session_state.user['name'],
                        note=update_note,
                        assigned_to=new_assignee
                    )
                    st.success(f"Ticket #{c['ticket_no']} updated to {new_st}!")
                    st.rerun()


# PAGE 4: ANALYTICS & SLA DASHBOARD (ADMIN ONLY)
def show_analytics_dashboard():
    st.title("📊 Campus Analytics & SLA Metrics")
    st.caption("Real-time operational benchmarks, resolution rate, category distribution, and SLA compliance metrics.")

    summary = database.get_analytics_summary()

    # KPI Grid
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Total Tickets", summary['total'])
    k2.metric("Pending", summary['pending'])
    k3.metric("Critical", summary['critical'], delta_color="inverse")
    k4.metric("Resolved", summary['resolved'])
    k5.metric("Resolution Rate", f"{summary['resolution_rate']}%")
    k6.metric("Avg Accuracy", f"{summary['avg_confidence']}%")

    st.divider()

    ch1, ch2 = st.columns(2)

    with ch1:
        st.subheader("Category Distribution")
        cat_df = pd.DataFrame(list(summary['category_breakdown'].items()), columns=['Category', 'Count'])
        fig_cat = px.pie(cat_df, values='Count', names='Category', hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3)
        fig_cat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#ffffff")
        st.plotly_chart(fig_cat, use_container_width=True)

    with ch2:
        st.subheader("Priority Level Breakdown")
        prio_df = pd.DataFrame(list(summary['priority_breakdown'].items()), columns=['Priority', 'Count'])
        color_map = {'Critical': '#ef4444', 'High': '#f97316', 'Medium': '#eab308', 'Low': '#3b82f6'}
        fig_prio = px.bar(prio_df, x='Priority', y='Count', color='Priority', color_discrete_map=color_map)
        fig_prio.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#ffffff", showlegend=False)
        st.plotly_chart(fig_prio, use_container_width=True)


if __name__ == "__main__":
    main()
