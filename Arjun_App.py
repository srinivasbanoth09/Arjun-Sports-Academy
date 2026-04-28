# ============================================================
#  Arjun Sports Academy  –  ALL-IN-ONE app.py
#  Flask + SQLite + HTML/CSS/JS  (no external template files)
# ============================================================

from flask import Flask, request, redirect, url_for, flash, jsonify, session, send_from_directory, render_template_string
import sqlite3
from datetime import datetime, date
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__)
app.secret_key = 'arjun_sports_academy_production_2024_secure_key'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov', 'mp3', 'wav', 'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash('Access denied!', 'error')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ─────────────────────────────────────────────
#  DATABASE
# ─────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect('sports_academy.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = sqlite3.connect('sports_academy.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student',
        student_id INTEGER,
        created_date DATE DEFAULT CURRENT_DATE,
        status TEXT DEFAULT 'Active'
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT UNIQUE NOT NULL,
        age INTEGER NOT NULL,
        category TEXT NOT NULL,
        registration_date DATE DEFAULT CURRENT_DATE,
        status TEXT DEFAULT 'Active'
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT UNIQUE NOT NULL,
        specialization TEXT NOT NULL,
        experience INTEGER DEFAULT 0,
        registration_date DATE DEFAULT CURRENT_DATE,
        status TEXT DEFAULT 'Active'
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        date DATE NOT NULL,
        status TEXT NOT NULL,
        marked_by INTEGER,
        marked_by_role TEXT,
        FOREIGN KEY (student_id) REFERENCES students (id),
        FOREIGN KEY (marked_by) REFERENCES users (id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS performance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        category TEXT,
        rounds_completed INTEGER DEFAULT 0,
        score REAL DEFAULT 0,
        notes TEXT,
        recorded_by INTEGER,
        record_date DATE DEFAULT CURRENT_DATE,
        FOREIGN KEY (student_id) REFERENCES students (id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS media_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        filename TEXT NOT NULL,
        original_filename TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_size INTEGER,
        upload_date DATE DEFAULT CURRENT_DATE,
        description TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')

    cursor.execute('SELECT COUNT(*) FROM users WHERE username = "Arjun9097Div"')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO users (username,email,phone,password_hash,role) VALUES (?,?,?,?,?)',
            ('Arjun9097Div','arjun.developer@arjunacademy.com','9097000001',
             generate_password_hash('ArDiv_8096_@_123456'),'developer'))

    cursor.execute('SELECT COUNT(*) FROM users WHERE username = "Admin_Seenu"')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO users (username,email,phone,password_hash,role) VALUES (?,?,?,?,?)',
            ('Admin_Seenu','seenu.admin@arjunacademy.com','8096000001',
             generate_password_hash('Seetharam@12345@'),'admin'))

    cursor.execute('SELECT COUNT(*) FROM users WHERE role = "teacher"')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO teachers (teacher_id,name,email,phone,specialization,experience) VALUES (?,?,?,?,?,?)',
            ('CA001','Coach Arjun','teacher@arjunacademy.com','9999999997','Athletics',15))
        tid = cursor.lastrowid
        cursor.execute('INSERT INTO users (username,email,phone,password_hash,role,student_id) VALUES (?,?,?,?,?,?)',
            ('teacher','teacher@arjunacademy.com','9999999997',
             generate_password_hash('teacher123'),'teacher',tid))

    conn.commit()
    conn.close()

def generate_student_id():
    conn = sqlite3.connect('sports_academy.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM students')
    count = cursor.fetchone()[0]
    conn.close()
    return f'AR{count + 1:06d}'

def generate_teacher_id(name):
    conn = sqlite3.connect('sports_academy.db')
    cursor = conn.cursor()
    names = name.split()
    prefix = (names[0][0] + names[-1][0]).upper() if len(names) >= 2 else names[0][:2].upper()
    cursor.execute('SELECT COUNT(*) FROM teachers WHERE teacher_id LIKE ?', (f'{prefix}%',))
    count = cursor.fetchone()[0]
    conn.close()
    return f'{prefix}{count + 1:03d}'

# ─────────────────────────────────────────────
#  SHARED CSS / JS  (embedded into every page)
# ─────────────────────────────────────────────
COMMON_CSS = """
<style>
:root{
  --primary:#0d6efd;--primary-dark:#0a58ca;--success:#198754;
  --warning:#ffc107;--danger:#dc3545;--info:#0dcaf0;
  --grad1:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
  --grad2:linear-gradient(135deg,#ff6b6b 0%,#ee5a24 100%);
  --grad3:linear-gradient(135deg,#56ab2f 0%,#a8e6cf 100%);
}
body{font-family:'Segoe UI',sans-serif;background:#f8f9fa;}
.navbar-brand{font-weight:700;font-size:1.3rem;}
/* ── Hero ── */
.hero-section{background:var(--grad1);border-radius:16px;padding:4rem 2rem;}
.text-gradient{background:var(--grad1);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
/* ── Cards ── */
.card{border:none;border-radius:16px;box-shadow:0 4px 20px rgba(0,0,0,.08);transition:transform .3s,box-shadow .3s;}
.card:hover{transform:translateY(-4px);box-shadow:0 12px 40px rgba(0,0,0,.12);}
.feature-card{border-radius:20px;}
.coach-spotlight{background:linear-gradient(135deg,rgba(102,126,234,.08),rgba(118,75,162,.08));border-radius:20px;}
/* ── Buttons ── */
.btn{border-radius:10px;font-weight:600;transition:all .3s;}
.btn-primary{background:var(--grad1);border:none;}
.btn-primary:hover{background:var(--primary-dark);transform:translateY(-2px);}
/* ── Tables ── */
.table{border-radius:12px;overflow:hidden;}
.table thead{background:var(--grad1);color:#fff;}
.table-hover tbody tr:hover{background:rgba(102,126,234,.06);}
/* ── Sidebar / Dashboard ── */
.sidebar{background:var(--grad1);min-height:100vh;color:#fff;padding:1.5rem 1rem;}
.sidebar .nav-link{color:rgba(255,255,255,.8);border-radius:10px;padding:.6rem 1rem;margin:.2rem 0;transition:all .2s;}
.sidebar .nav-link:hover,.sidebar .nav-link.active{background:rgba(255,255,255,.2);color:#fff;}
.sidebar .nav-link i{width:22px;}
.dash-card{border-radius:16px;padding:1.5rem;color:#fff;border:none;}
.dash-card.blue{background:linear-gradient(135deg,#667eea,#764ba2);}
.dash-card.green{background:var(--grad3);}
.dash-card.orange{background:var(--grad2);}
.dash-card.teal{background:linear-gradient(135deg,#11998e,#38ef7d);}
.dash-card h2{font-size:2.5rem;font-weight:800;}
/* ── Attendance badges ── */
.badge-present{background:#d1fae5;color:#065f46;}
.badge-absent{background:#fee2e2;color:#991b1b;}
/* ── Alerts ── */
.alert{border-radius:12px;border:none;}
/* ── Student portal hero ── */
.student-portal-hero{background:var(--grad1);color:#fff;padding:4rem 0;}
/* ── Login ── */
.login-container{background:var(--grad1);min-height:100vh;}
.login-card{border:none;border-radius:20px;overflow:hidden;}
.login-illustration{background:var(--grad2);display:flex;align-items:center;justify-content:center;min-height:400px;}
.illustration-content{text-align:center;z-index:2;padding:2rem;}
.sports-icons{position:absolute;top:0;left:0;right:0;bottom:0;overflow:hidden;}
.icon-float{position:absolute;font-size:2rem;opacity:.3;animation:float 6s ease-in-out infinite;}
.icon-float:nth-child(1){top:20%;left:20%;animation-delay:0s;}
.icon-float:nth-child(2){top:60%;left:80%;animation-delay:1s;}
.icon-float:nth-child(3){top:80%;left:30%;animation-delay:2s;}
.icon-float:nth-child(4){top:30%;left:70%;animation-delay:3s;}
.icon-float:nth-child(5){top:70%;left:10%;animation-delay:4s;}
@keyframes float{0%,100%{transform:translateY(0);}50%{transform:translateY(-20px);}}
@keyframes pulse{0%,100%{transform:scale(1);}50%{transform:scale(1.05);}}
@keyframes bounce{0%,20%,50%,80%,100%{transform:translateY(0);}40%{transform:translateY(-10px);}60%{transform:translateY(-5px);}}
.login-logo{animation:pulse 2s infinite;}
.input-group-text{background:var(--grad1);border:none;color:#fff;}
.form-control:focus{border-color:#667eea;box-shadow:0 0 0 .2rem rgba(102,126,234,.25);}
/* ── Portal ── */
.portal-card{background:rgba(255,255,255,.95);backdrop-filter:blur(10px);border:none;border-radius:20px;transition:all .3s;}
.portal-card:hover{transform:translateY(-10px) scale(1.05);box-shadow:0 20px 60px rgba(0,0,0,.2);}
.portal-icon{color:#667eea;animation:pulse 2s infinite;}
.sport-item{position:absolute;display:flex;flex-direction:column;align-items:center;background:rgba(255,255,255,.1);backdrop-filter:blur(10px);border-radius:20px;padding:1rem;border:1px solid rgba(255,255,255,.2);}
.sport-item:nth-child(1){top:10%;left:20%;}
.sport-item:nth-child(2){top:30%;right:10%;}
.sport-item:nth-child(3){top:50%;left:10%;}
.sport-item:nth-child(4){top:70%;right:20%;}
.sport-item:nth-child(5){top:20%;left:50%;}
.sport-item:nth-child(6){top:80%;left:40%;}
.sports-illustration{position:relative;height:500px;}
.floating-sports{position:relative;width:100%;height:100%;}
.sport-name{font-size:.8rem;font-weight:600;text-align:center;}
.demo-info{background:linear-gradient(135deg,rgba(102,126,234,.1),rgba(118,75,162,.1));border:none;border-radius:20px;}
.demo-card{background:#fff;border-radius:15px;padding:2rem;margin:1rem;box-shadow:0 10px 30px rgba(0,0,0,.1);}
/* ── Footer ── */
footer a:hover{color:#fff!important;}
/* ── Media gallery ── */
.media-card{border-radius:12px;overflow:hidden;}
.media-thumb{height:180px;object-fit:cover;width:100%;}
.media-icon{height:180px;display:flex;align-items:center;justify-content:center;background:#f1f3f5;}
/* ── Page header ── */
.page-header{background:var(--grad1);color:#fff;padding:2rem;border-radius:16px;margin-bottom:1.5rem;}
/* ── Responsive ── */
@media(max-width:768px){
  .sports-illustration{height:300px;}
  .sport-item{padding:.5rem;}
}
</style>
"""

COMMON_JS = """
<script>
// Flash auto-dismiss
document.addEventListener('DOMContentLoaded',function(){
  setTimeout(function(){
    document.querySelectorAll('.alert-dismissible').forEach(function(el){
      var bsAlert=bootstrap.Alert.getOrCreateInstance(el);
      bsAlert.close();
    });
  },4000);
});
// Confirm delete
function confirmDelete(msg){return confirm(msg||'Are you sure?');}
</script>
"""

NAVBAR_LINKS = """
<li class="nav-item"><a class="nav-link" href="/">Home</a></li>
<li class="nav-item"><a class="nav-link" href="/student-portal">Student Portal</a></li>
<li class="nav-item"><a class="nav-link" href="/register">Register</a></li>
<li class="nav-item"><a class="nav-link" href="/login">Login</a></li>
"""

def base_head(title):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title} - Arjun Sports Academy</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
{COMMON_CSS}
</head>
<body>
"""

def base_navbar(active=""):
    return f"""
<nav class="navbar navbar-expand-lg navbar-dark bg-primary">
  <div class="container">
    <a class="navbar-brand" href="/"><i class="fas fa-trophy"></i> Arjun Sports Academy</a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navbarNav">
      <ul class="navbar-nav ms-auto">
        <li class="nav-item"><a class="nav-link {'active' if active=='home' else ''}" href="/">Home</a></li>
        <li class="nav-item"><a class="nav-link {'active' if active=='portal' else ''}" href="/student-portal">Student Portal</a></li>
        <li class="nav-item"><a class="nav-link {'active' if active=='register' else ''}" href="/register">Register</a></li>
        <li class="nav-item"><a class="nav-link {'active' if active=='login' else ''}" href="/login">Login</a></li>
        <li class="nav-item"><a class="nav-link" href="/about">About</a></li>
        <li class="nav-item"><a class="nav-link" href="/contact">Contact</a></li>
      </ul>
    </div>
  </div>
</nav>
"""

def base_footer():
    return """
<footer class="bg-dark text-white text-center py-4 mt-5">
  <div class="container">
    <div class="row">
      <div class="col-md-4 mb-3">
        <h5><i class="fas fa-trophy"></i> Arjun Sports Academy</h5>
        <p>Excellence in Sports Training Since 2024</p>
      </div>
      <div class="col-md-4 mb-3">
        <h6>Quick Links</h6>
        <ul class="list-unstyled">
          <li><a href="/about" class="text-white-50">About Us</a></li>
          <li><a href="/register" class="text-white-50">Registration</a></li>
          <li><a href="/contact" class="text-white-50">Contact</a></li>
        </ul>
      </div>
      <div class="col-md-4 mb-3">
        <h6>Connect With Us</h6>
        <div class="social-links">
          <a href="#" class="text-white-50 me-3"><i class="fab fa-facebook fa-2x"></i></a>
          <a href="#" class="text-white-50 me-3"><i class="fab fa-instagram fa-2x"></i></a>
          <a href="#" class="text-white-50"><i class="fab fa-youtube fa-2x"></i></a>
        </div>
      </div>
    </div>
    <hr class="my-4">
    <p>&copy; 2024 Arjun Sports Academy - National Level Training Excellence. All rights reserved.</p>
  </div>
</footer>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
""" + COMMON_JS + "</body></html>"

def flash_html():
    return """
{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <div class="container mt-2">
      {% for cat,msg in messages %}
        <div class="alert alert-{{ 'danger' if cat=='error' else 'success' if cat=='success' else 'info' }} alert-dismissible fade show" role="alert">
          {{ msg }}
          <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
      {% endfor %}
    </div>
  {% endif %}
{% endwith %}
"""

def dashboard_sidebar(role, username):
    links = {
        'developer': [
            ('/developer/dashboard','fa-tachometer-alt','Dashboard'),
            ('/students/list','fa-users','All Students'),
            ('/register','fa-user-plus','Register'),
            ('/attendance/mark','fa-calendar-check','Attendance'),
            ('/performance/add','fa-chart-line','Performance'),
            ('/media/gallery','fa-photo-video','Media Gallery'),
            ('/media/upload','fa-upload','Upload Media'),
        ],
        'admin': [
            ('/admin/dashboard','fa-tachometer-alt','Dashboard'),
            ('/students/list','fa-users','Students List'),
            ('/register','fa-user-plus','Register Student'),
            ('/attendance/mark','fa-calendar-check','Mark Attendance'),
            ('/performance/add','fa-chart-line','Add Performance'),
            ('/media/gallery','fa-photo-video','Media Gallery'),
        ],
        'teacher': [
            ('/teacher/dashboard','fa-tachometer-alt','Dashboard'),
            ('/students/list','fa-users','Students List'),
            ('/attendance/mark','fa-calendar-check','Mark Attendance'),
            ('/media/gallery','fa-photo-video','Media Gallery'),
            ('/media/upload','fa-upload','Upload Media'),
        ],
        'student': [
            ('/student/dashboard','fa-tachometer-alt','My Dashboard'),
            ('/media/gallery','fa-photo-video','Media Gallery'),
            ('/media/upload','fa-upload','Upload Media'),
        ],
    }
    items = links.get(role, [])
    html = f"""
<div class="sidebar d-flex flex-column" style="min-width:220px;max-width:220px;">
  <div class="text-center mb-4">
    <i class="fas fa-medal fa-3x mb-2"></i>
    <div class="fw-bold">Arjun Sports Academy</div>
    <small class="text-white-50">@{username}</small>
    <span class="badge bg-warning text-dark ms-1">{role.title()}</span>
  </div>
  <nav class="nav flex-column flex-grow-1">
"""
    for href, icon, label in items:
        html += f'<a class="nav-link" href="{href}"><i class="fas {icon} me-2"></i>{label}</a>\n'
    html += f"""
  </nav>
  <div class="mt-auto pt-3 border-top border-white-50">
    <a href="/logout" class="nav-link text-danger"><i class="fas fa-sign-out-alt me-2"></i>Logout</a>
  </div>
</div>
"""
    return html

# ─────────────────────────────────────────────
#  TEMPLATE STRINGS
# ─────────────────────────────────────────────

# ── INDEX ──
INDEX_TEMPLATE = """
""" + base_head("Home") + base_navbar("home") + flash_html() + """
<main class="container mt-4">
  <div class="hero-section text-white py-5 mb-5">
    <div class="text-center">
      <h1 class="display-4 fw-bold"><i class="fas fa-medal"></i> Arjun Sports Academy</h1>
      <p class="lead">National Level Sports Training Excellence</p>
      <p class="fs-5">Empowering 1000+ Athletes to Achieve Their Dreams</p>
      <div class="mt-4">
        <a href="/register" class="btn btn-light btn-lg me-3"><i class="fas fa-user-plus"></i> Join Our Academy</a>
        <a href="/student-portal" class="btn btn-outline-light btn-lg"><i class="fas fa-sign-in-alt"></i> Student Portal</a>
      </div>
    </div>
  </div>

  <div class="row">
    <div class="col-md-4 mb-4">
      <div class="card h-100 text-center">
        <div class="card-body">
          <i class="fas fa-users fa-3x text-primary mb-3"></i>
          <h5 class="card-title">1000+ Students</h5>
          <p class="card-text">Training athletes across multiple sports categories with personalized coaching from Coach Arjun.</p>
        </div>
      </div>
    </div>
    <div class="col-md-4 mb-4">
      <div class="card h-100 text-center">
        <div class="card-body">
          <i class="fas fa-trophy fa-3x text-warning mb-3"></i>
          <h5 class="card-title">National Level Coach</h5>
          <p class="card-text">Coached by Arjun, a national-level sportsman with proven track record in developing champions.</p>
        </div>
      </div>
    </div>
    <div class="col-md-4 mb-4">
      <div class="card h-100 text-center">
        <div class="card-body">
          <i class="fas fa-chart-line fa-3x text-success mb-3"></i>
          <h5 class="card-title">Performance Tracking</h5>
          <p class="card-text">Advanced monitoring system to track progress, attendance, and optimize training performance.</p>
        </div>
      </div>
    </div>
  </div>

  <div class="row mt-5">
    <div class="col-md-6">
      <div class="card feature-card h-100">
        <div class="card-body">
          <h3><i class="fas fa-bullseye text-primary"></i> Our Mission</h3>
          <p class="lead">To develop world-class athletes through systematic training, performance monitoring, and personalized coaching.</p>
          <ul class="list-unstyled">
            <li><i class="fas fa-check text-success"></i> Individual attention and personalized training</li>
            <li><i class="fas fa-check text-success"></i> Scientific approach to sports development</li>
            <li><i class="fas fa-check text-success"></i> Character building and discipline</li>
            <li><i class="fas fa-check text-success"></i> Preparation for competitions</li>
          </ul>
        </div>
      </div>
    </div>
    <div class="col-md-6">
      <div class="card feature-card h-100">
        <div class="card-body">
          <h3><i class="fas fa-star text-warning"></i> Training Categories</h3>
          <p class="lead">Comprehensive training programs across multiple sports disciplines:</p>
          <div class="row">
            <div class="col-6">
              <ul class="list-unstyled">
                <li><i class="fas fa-running text-primary"></i> Athletics</li>
                <li><i class="fas fa-futbol text-primary"></i> Football</li>
                <li><i class="fas fa-basketball-ball text-primary"></i> Basketball</li>
                <li><i class="fas fa-table-tennis text-primary"></i> Table Tennis</li>
              </ul>
            </div>
            <div class="col-6">
              <ul class="list-unstyled">
                <li><i class="fas fa-swimmer text-primary"></i> Swimming</li>
                <li><i class="fas fa-dumbbell text-primary"></i> Fitness Training</li>
                <li><i class="fas fa-baseball-ball text-primary"></i> Cricket</li>
                <li><i class="fas fa-shuttlecock text-primary"></i> Badminton</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="row mt-5">
    <div class="col-12">
      <div class="card coach-spotlight">
        <div class="card-body text-center p-5">
          <i class="fas fa-medal fa-5x text-warning mb-4"></i>
          <h2 class="text-gradient mb-3">Meet Coach Arjun</h2>
          <p class="lead mb-4">National-level sportsman with over 15 years of experience in training athletes across multiple disciplines. Coach Arjun has mentored hundreds of students to achieve excellence.</p>
          <blockquote class="blockquote">
            <p class="fs-4">"Excellence is not a skill, it's an attitude. Every day is an opportunity to become better than yesterday. Together, we're building the champions of tomorrow."</p>
          </blockquote>
          <footer class="blockquote-footer mt-3"><cite>Arjun, National Level Sportsman &amp; Head Coach</cite></footer>
        </div>
      </div>
    </div>
  </div>

  <div class="text-center mt-5 mb-4">
    <h2 class="text-gradient mb-4">Ready to Start Your Journey?</h2>
    <a href="/register" class="btn btn-primary btn-lg me-3"><i class="fas fa-rocket"></i> Register Now</a>
    <a href="/student-portal" class="btn btn-outline-primary btn-lg me-3"><i class="fas fa-sign-in-alt"></i> Student Login</a>
    <a href="/contact" class="btn btn-success btn-lg"><i class="fas fa-phone"></i> Contact Us</a>
  </div>
</main>
""" + base_footer()

# ── LOGIN ──
LOGIN_TEMPLATE = """
""" + base_head("Login") + flash_html() + """
<div class="login-container">
  <div class="row justify-content-center align-items-center min-vh-100">
    <div class="col-md-10 col-lg-8 p-3">
      <div class="card login-card shadow-lg">
        <div class="row g-0">
          <div class="col-md-5 login-illustration position-relative">
            <div class="sports-icons">
              <div class="icon-float">🏆</div>
              <div class="icon-float">⚽</div>
              <div class="icon-float">🏀</div>
              <div class="icon-float">🏊‍♂️</div>
              <div class="icon-float">🏃‍♂️</div>
            </div>
            <div class="illustration-content">
              <h3 class="text-white mb-3">Welcome to Excellence</h3>
              <p class="text-white-50">Join Coach Arjun's journey to sporting greatness</p>
            </div>
          </div>
          <div class="col-md-7">
            <div class="card-body p-5">
              <div class="text-center mb-4">
                <div class="login-logo"><i class="fas fa-medal fa-3x text-primary mb-3"></i></div>
                <h4 class="fw-bold">Arjun Sports Academy</h4>
                <p class="text-muted">Sign in to your account</p>
              </div>
              <form id="loginForm" method="POST" action="/login">
                <div class="mb-3">
                  <label class="form-label">Login As</label>
                  <div class="row g-2">
                    <div class="col-6">
                      <input type="radio" class="btn-check" name="role" id="developer" value="developer" autocomplete="off">
                      <label class="btn btn-outline-primary w-100" for="developer"><i class="fas fa-code"></i><br>Developer</label>
                    </div>
                    <div class="col-6">
                      <input type="radio" class="btn-check" name="role" id="admin" value="admin" autocomplete="off">
                      <label class="btn btn-outline-success w-100" for="admin"><i class="fas fa-user-shield"></i><br>Admin</label>
                    </div>
                    <div class="col-6">
                      <input type="radio" class="btn-check" name="role" id="teacher" value="teacher" autocomplete="off">
                      <label class="btn btn-outline-warning w-100" for="teacher"><i class="fas fa-chalkboard-teacher"></i><br>Teacher</label>
                    </div>
                    <div class="col-6">
                      <input type="radio" class="btn-check" name="role" id="student" value="student" autocomplete="off" checked>
                      <label class="btn btn-outline-info w-100" for="student"><i class="fas fa-user-graduate"></i><br>Student</label>
                    </div>
                  </div>
                </div>
                <div class="mb-3">
                  <label for="username" class="form-label">Username</label>
                  <div class="input-group">
                    <span class="input-group-text"><i class="fas fa-user"></i></span>
                    <input type="text" class="form-control" id="username" name="username" required>
                  </div>
                </div>
                <div class="mb-4">
                  <label for="password" class="form-label">Password</label>
                  <div class="input-group">
                    <span class="input-group-text"><i class="fas fa-lock"></i></span>
                    <input type="password" class="form-control" id="password" name="password" required>
                  </div>
                </div>
                <button type="submit" class="btn btn-primary w-100 mb-3"><i class="fas fa-sign-in-alt"></i> Sign In</button>
              </form>
              <div class="text-center">
                <p class="text-muted mb-2">Don't have an account?</p>
                <a href="/register" class="btn btn-outline-primary"><i class="fas fa-user-plus"></i> Register</a>
              </div>
              <div class="alert alert-info mt-4">
                <strong>Demo Credentials:</strong><br>
                Developer: <code>Arjun9097Div</code> / <code>ArDiv_8096_@_123456</code><br>
                Admin: <code>Admin_Seenu</code> / <code>Seetharam@12345@</code><br>
                Teacher: <code>teacher</code> / <code>teacher123</code><br>
                <small class="text-muted">Students get credentials after registration</small>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
""" + COMMON_JS + """
<style>
.btn-check:checked + .btn{background-color:var(--primary);border-color:var(--primary);color:#fff;}
</style>
</body></html>
"""

# ── REGISTER ──
REGISTER_TEMPLATE = """
""" + base_head("Register") + base_navbar("register") + flash_html() + """
<main class="container mt-4">
  <div class="row justify-content-center">
    <div class="col-md-8">
      <div class="card">
        <div class="card-header bg-primary text-white">
          <h4><i class="fas fa-user-plus"></i> Student Registration</h4>
        </div>
        <div class="card-body">
          <div class="alert alert-info">
            <i class="fas fa-info-circle"></i>
            <strong>Note:</strong> Only Arjun (Developer) and Admin can register students and teachers.
          </div>
          <form id="registrationForm" method="POST" action="/register">
            <div class="mb-3">
              <label class="form-label">Registration Type</label>
              <div class="row g-2">
                <div class="col-6">
                  <input type="radio" class="btn-check" name="role" id="roleStudent" value="student" autocomplete="off" checked onchange="toggleFields()">
                  <label class="btn btn-outline-primary w-100" for="roleStudent"><i class="fas fa-user-graduate"></i> Student</label>
                </div>
                <div class="col-6">
                  <input type="radio" class="btn-check" name="role" id="roleTeacher" value="teacher" autocomplete="off" onchange="toggleFields()">
                  <label class="btn btn-outline-success w-100" for="roleTeacher"><i class="fas fa-chalkboard-teacher"></i> Teacher</label>
                </div>
              </div>
            </div>
            <div class="row">
              <div class="col-md-6 mb-3">
                <label for="name" class="form-label">Full Name *</label>
                <input type="text" class="form-control" id="name" name="name" required>
              </div>
              <div class="col-md-6 mb-3">
                <label for="email" class="form-label">Email Address *</label>
                <input type="email" class="form-control" id="email" name="email" required>
              </div>
            </div>
            <div class="row">
              <div class="col-md-6 mb-3">
                <label for="phone" class="form-label">Phone Number *</label>
                <input type="tel" class="form-control" id="phone" name="phone" required>
              </div>
              <div class="col-md-6 mb-3">
                <label for="age" class="form-label">Age *</label>
                <input type="number" class="form-control" id="age" name="age" min="5" max="70" required>
              </div>
            </div>
            <!-- Student fields -->
            <div id="studentFields">
              <div class="mb-3">
                <label for="category" class="form-label">Sports Category *</label>
                <select class="form-select" id="category" name="category">
                  <option value="">Select Category</option>
                  <option>Athletics</option><option>Football</option><option>Basketball</option>
                  <option>Table Tennis</option><option>Swimming</option>
                  <option>Fitness Training</option><option>Cricket</option><option>Badminton</option>
                </select>
              </div>
            </div>
            <!-- Teacher fields -->
            <div id="teacherFields" style="display:none;">
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="specialization" class="form-label">Specialization</label>
                  <input type="text" class="form-control" id="specialization" name="specialization">
                </div>
                <div class="col-md-6 mb-3">
                  <label for="experience" class="form-label">Years of Experience</label>
                  <input type="number" class="form-control" id="experience" name="experience" min="0">
                </div>
              </div>
            </div>
            <div class="mb-3">
              <label for="password" class="form-label">Password *</label>
              <input type="password" class="form-control" id="password" name="password" minlength="6" required>
              <div class="form-text">Minimum 6 characters</div>
            </div>
            <div class="mb-3">
              <div class="form-check">
                <input class="form-check-input" type="checkbox" id="terms" required>
                <label class="form-check-label" for="terms">
                  I agree to the <a href="#" data-bs-toggle="modal" data-bs-target="#termsModal">Terms and Conditions</a> *
                </label>
              </div>
            </div>
            <div class="d-flex justify-content-end gap-2">
              <a href="/" class="btn btn-secondary"><i class="fas fa-arrow-left"></i> Back</a>
              <button type="submit" class="btn btn-primary"><i class="fas fa-user-plus"></i> Register</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>

  <!-- Terms Modal -->
  <div class="modal fade" id="termsModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title"><i class="fas fa-file-contract"></i> Terms and Conditions</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <h6>1. Registration Policy</h6>
          <ul>
            <li>Each student can register only once with unique email and phone number</li>
            <li>All information provided must be accurate and truthful</li>
            <li>Registration is subject to availability and coach approval</li>
          </ul>
          <h6>2. Training Commitment</h6>
          <ul>
            <li>Regular attendance is mandatory for optimal performance</li>
            <li>Minimum 80% attendance required to continue in the program</li>
          </ul>
          <h6>3. Code of Conduct</h6>
          <ul>
            <li>Respectful behavior towards coaches and fellow students</li>
            <li>No use of prohibited substances or performance enhancers</li>
          </ul>
          <div class="alert alert-warning mt-3">
            <strong>By registering, you acknowledge that you have read and agree to all terms.</strong>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          <button type="button" class="btn btn-primary" onclick="acceptTerms()">I Agree</button>
        </div>
      </div>
    </div>
  </div>
</main>
""" + base_footer() + """
<script>
function toggleFields(){
  var isTeacher=document.getElementById('roleTeacher').checked;
  document.getElementById('studentFields').style.display=isTeacher?'none':'block';
  document.getElementById('teacherFields').style.display=isTeacher?'block':'none';
  document.getElementById('category').required=!isTeacher;
}
function acceptTerms(){
  document.getElementById('terms').checked=true;
  bootstrap.Modal.getInstance(document.getElementById('termsModal')).hide();
}
</script>
"""

# ── STUDENT PORTAL ──
STUDENT_PORTAL_TEMPLATE = """
""" + base_head("Student Portal") + base_navbar("portal") + flash_html() + """
<div class="student-portal-hero">
  <div class="container">
    <div class="row align-items-center py-5">
      <div class="col-md-6">
        <h1 class="display-4 fw-bold text-white mb-4">🏆 Student Portal</h1>
        <p class="lead text-white mb-4">Access your personal dashboard, track your progress, and stay connected with Coach Arjun's training program.</p>
        <div class="row g-4">
          <div class="col-sm-6">
            <div class="card portal-card h-100">
              <div class="card-body text-center p-4">
                <div class="portal-icon mb-3"><i class="fas fa-user-graduate fa-3x"></i></div>
                <h5>Existing Student</h5>
                <p class="text-muted">Login to your account</p>
                <a href="/login" class="btn btn-primary"><i class="fas fa-sign-in-alt"></i> Login</a>
              </div>
            </div>
          </div>
          <div class="col-sm-6">
            <div class="card portal-card h-100">
              <div class="card-body text-center p-4">
                <div class="portal-icon mb-3"><i class="fas fa-user-plus fa-3x"></i></div>
                <h5>New Student</h5>
                <p class="text-muted">Join our academy</p>
                <a href="/register" class="btn btn-success"><i class="fas fa-rocket"></i> Register</a>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="col-md-6 d-none d-md-block">
        <div class="sports-illustration">
          <div class="floating-sports">
            <div class="sport-item float-element" style="animation:float 6s ease-in-out infinite;top:10%;left:20%">
              <span style="font-size:2rem">🏃‍♂️</span><span class="sport-name text-white">Athletics</span>
            </div>
            <div class="sport-item float-element" style="animation:float 6s ease-in-out infinite 1s;top:30%;right:10%">
              <span style="font-size:2rem">⚽</span><span class="sport-name text-white">Football</span>
            </div>
            <div class="sport-item float-element" style="animation:float 6s ease-in-out infinite 2s;top:50%;left:10%">
              <span style="font-size:2rem">🏀</span><span class="sport-name text-white">Basketball</span>
            </div>
            <div class="sport-item float-element" style="animation:float 6s ease-in-out infinite 3s;top:70%;right:20%">
              <span style="font-size:2rem">🏊‍♂️</span><span class="sport-name text-white">Swimming</span>
            </div>
            <div class="sport-item float-element" style="animation:float 6s ease-in-out infinite 4s;top:20%;left:50%">
              <span style="font-size:2rem">🏓</span><span class="sport-name text-white">Table Tennis</span>
            </div>
            <div class="sport-item float-element" style="animation:float 6s ease-in-out infinite 5s;top:80%;left:40%">
              <span style="font-size:2rem">🏸</span><span class="sport-name text-white">Badminton</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<div class="container mt-5">
  <div class="row">
    <div class="col-md-4 mb-4">
      <div class="card feature-card h-100">
        <div class="card-body text-center">
          <div style="animation:bounce 2s infinite"><i class="fas fa-chart-line fa-3x text-primary mb-3"></i></div>
          <h5>Track Progress</h5>
          <p class="text-muted">Monitor your performance, scores, and improvement over time with detailed analytics.</p>
        </div>
      </div>
    </div>
    <div class="col-md-4 mb-4">
      <div class="card feature-card h-100">
        <div class="card-body text-center">
          <div style="animation:bounce 2s infinite .5s"><i class="fas fa-calendar-check fa-3x text-success mb-3"></i></div>
          <h5>Attendance Record</h5>
          <p class="text-muted">View your attendance history and maintain consistency in your training schedule.</p>
        </div>
      </div>
    </div>
    <div class="col-md-4 mb-4">
      <div class="card feature-card h-100">
        <div class="card-body text-center">
          <div style="animation:bounce 2s infinite 1s"><i class="fas fa-trophy fa-3x text-warning mb-3"></i></div>
          <h5>Achievements</h5>
          <p class="text-muted">Celebrate your milestones and achievements in your sporting journey.</p>
        </div>
      </div>
    </div>
  </div>

  <div class="row mt-4">
    <div class="col-12">
      <div class="card demo-info">
        <div class="card-body text-center p-5">
          <h3 class="text-gradient mb-4">Demo Access Information</h3>
          <div class="row justify-content-center">
            <div class="col-md-5">
              <div class="demo-card">
                <h5><i class="fas fa-user-shield"></i> Admin Access</h5>
                <p><strong>Username:</strong> Admin_Seenu</p>
                <p><strong>Password:</strong> Seetharam@12345@</p>
                <p class="text-muted">Full academy management access</p>
              </div>
            </div>
            <div class="col-md-5">
              <div class="demo-card">
                <h5><i class="fas fa-user-graduate"></i> Student Access</h5>
                <p>Register as a new student to get your login credentials</p>
                <p class="text-muted">Personal dashboard and progress tracking</p>
              </div>
            </div>
          </div>
          <div class="mt-4">
            <a href="/login" class="btn btn-primary btn-lg me-3"><i class="fas fa-sign-in-alt"></i> Try Demo Login</a>
            <a href="/register" class="btn btn-success btn-lg"><i class="fas fa-user-plus"></i> Register Now</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
""" + base_footer()

# ── DEVELOPER DASHBOARD ──
DEV_DASHBOARD_TEMPLATE = """
""" + base_head("Developer Dashboard") + flash_html() + """
<div class="d-flex" style="min-height:100vh;">
  {{ sidebar|safe }}
  <div class="flex-grow-1 p-4">
    <div class="page-header">
      <h2><i class="fas fa-code"></i> Developer Dashboard</h2>
      <p class="mb-0">Full system overview and control</p>
    </div>
    <div class="row g-4 mb-4">
      <div class="col-md-3">
        <div class="card dash-card blue">
          <div class="card-body"><h6>Total Students</h6><h2>{{ total_students }}</h2><small><i class="fas fa-users"></i> Active</small></div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card dash-card green">
          <div class="card-body"><h6>Total Teachers</h6><h2>{{ total_teachers }}</h2><small><i class="fas fa-chalkboard-teacher"></i> Active</small></div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card dash-card orange">
          <div class="card-body"><h6>Total Users</h6><h2>{{ total_users }}</h2><small><i class="fas fa-user-cog"></i> All roles</small></div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card dash-card teal">
          <div class="card-body"><h6>Roles</h6><h2>{{ user_roles|length }}</h2><small><i class="fas fa-layer-group"></i> Distinct</small></div>
        </div>
      </div>
    </div>
    <div class="row g-4">
      <div class="col-md-6">
        <div class="card">
          <div class="card-header bg-primary text-white"><h5 class="mb-0"><i class="fas fa-layer-group"></i> Users by Role</h5></div>
          <div class="card-body">
            <table class="table table-hover">
              <thead><tr><th>Role</th><th>Count</th></tr></thead>
              <tbody>
                {% for role,cnt in user_roles %}
                <tr><td><span class="badge bg-primary">{{ role }}</span></td><td>{{ cnt }}</td></tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card">
          <div class="card-header bg-success text-white"><h5 class="mb-0"><i class="fas fa-bolt"></i> Quick Actions</h5></div>
          <div class="card-body d-grid gap-2">
            <a href="/students/list" class="btn btn-outline-primary"><i class="fas fa-users"></i> Manage Students</a>
            <a href="/register" class="btn btn-outline-success"><i class="fas fa-user-plus"></i> Register New User</a>
            <a href="/attendance/mark" class="btn btn-outline-warning"><i class="fas fa-calendar-check"></i> Mark Attendance</a>
            <a href="/performance/add" class="btn btn-outline-info"><i class="fas fa-chart-line"></i> Add Performance</a>
            <a href="/media/gallery" class="btn btn-outline-secondary"><i class="fas fa-photo-video"></i> Media Gallery</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
""" + COMMON_JS + "</body></html>"

# ── ADMIN DASHBOARD ──
ADMIN_DASHBOARD_TEMPLATE = """
""" + base_head("Admin Dashboard") + flash_html() + """
<div class="d-flex" style="min-height:100vh;">
  {{ sidebar|safe }}
  <div class="flex-grow-1 p-4">
    <div class="page-header">
      <h2><i class="fas fa-user-shield"></i> Admin Dashboard</h2>
      <p class="mb-0">Academy management overview</p>
    </div>
    <div class="row g-4 mb-4">
      <div class="col-md-4">
        <div class="card dash-card blue">
          <div class="card-body"><h6>Total Students</h6><h2>{{ total_students }}</h2></div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card dash-card green">
          <div class="card-body"><h6>Total Teachers</h6><h2>{{ total_teachers }}</h2></div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card dash-card orange">
          <div class="card-body"><h6>Categories</h6><h2>{{ categories|length }}</h2></div>
        </div>
      </div>
    </div>
    <div class="row g-4">
      <div class="col-md-6">
        <div class="card">
          <div class="card-header bg-primary text-white"><h5 class="mb-0"><i class="fas fa-chart-pie"></i> Students by Category</h5></div>
          <div class="card-body">
            <table class="table table-hover">
              <thead><tr><th>Category</th><th>Count</th></tr></thead>
              <tbody>
                {% for cat,cnt in categories %}
                <tr><td>{{ cat }}</td><td><span class="badge bg-primary">{{ cnt }}</span></td></tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card">
          <div class="card-header bg-success text-white"><h5 class="mb-0"><i class="fas fa-clock"></i> Recent Registrations</h5></div>
          <div class="card-body">
            <table class="table table-hover">
              <thead><tr><th>Name</th><th>Category</th><th>Date</th></tr></thead>
              <tbody>
                {% for name,cat,dt in recent_students %}
                <tr><td>{{ name }}</td><td>{{ cat }}</td><td>{{ dt }}</td></tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
""" + COMMON_JS + "</body></html>"

# ── TEACHER DASHBOARD ──
TEACHER_DASHBOARD_TEMPLATE = """
""" + base_head("Teacher Dashboard") + flash_html() + """
<div class="d-flex" style="min-height:100vh;">
  {{ sidebar|safe }}
  <div class="flex-grow-1 p-4">
    <div class="page-header">
      <h2><i class="fas fa-chalkboard-teacher"></i> Teacher Dashboard</h2>
      <p class="mb-0">Manage your students and attendance</p>
    </div>
    <div class="row g-4 mb-4">
      <div class="col-md-4">
        <div class="card dash-card blue">
          <div class="card-body"><h6>Total Students</h6><h2>{{ total_students }}</h2></div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card dash-card green">
          <div class="card-body"><h6>Categories</h6><h2>{{ categories|length }}</h2></div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card dash-card orange">
          <div class="card-body"><h6>Attendance Records</h6><h2>{{ recent_attendance|length }}</h2><small>Recent</small></div>
        </div>
      </div>
    </div>
    <div class="row g-4">
      <div class="col-md-6">
        <div class="card">
          <div class="card-header bg-primary text-white"><h5 class="mb-0"><i class="fas fa-layer-group"></i> Category Breakdown</h5></div>
          <div class="card-body">
            <table class="table table-hover">
              <thead><tr><th>Category</th><th>Students</th></tr></thead>
              <tbody>
                {% for cat,cnt in categories %}
                <tr><td>{{ cat }}</td><td>{{ cnt }}</td></tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card">
          <div class="card-header bg-success text-white"><h5 class="mb-0"><i class="fas fa-history"></i> Recent Attendance</h5></div>
          <div class="card-body">
            {% if recent_attendance %}
            <table class="table table-hover">
              <thead><tr><th>Student</th><th>Date</th><th>Status</th></tr></thead>
              <tbody>
                {% for name,dt,st in recent_attendance %}
                <tr>
                  <td>{{ name }}</td><td>{{ dt }}</td>
                  <td><span class="badge {{ 'badge-present' if st=='Present' else 'badge-absent' }}">{{ st }}</span></td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
            {% else %}
            <p class="text-muted text-center py-3">No attendance records yet.</p>
            {% endif %}
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
""" + COMMON_JS + "</body></html>"

# ── STUDENT DASHBOARD ──
STUDENT_DASHBOARD_TEMPLATE = """
""" + base_head("My Dashboard") + flash_html() + """
<div class="d-flex" style="min-height:100vh;">
  {{ sidebar|safe }}
  <div class="flex-grow-1 p-4">
    <div class="page-header">
      <h2><i class="fas fa-user-graduate"></i> My Dashboard</h2>
      <p class="mb-0">Welcome back, {{ student[2] if student else 'Student' }}!</p>
    </div>
    {% if student %}
    <div class="row g-4 mb-4">
      <div class="col-md-3">
        <div class="card dash-card blue">
          <div class="card-body"><h6>Student ID</h6><h5>{{ student[1] }}</h5></div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card dash-card green">
          <div class="card-body"><h6>Category</h6><h5>{{ student[6] }}</h5></div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card dash-card orange">
          <div class="card-body">
            <h6>Attendance</h6>
            {% if attendance_stats and attendance_stats[0] %}
              <h5>{{ attendance_stats[1] or 0 }}/{{ attendance_stats[0] }}</h5>
              <small>{{ ((attendance_stats[1] or 0) / attendance_stats[0] * 100)|round(1) }}%</small>
            {% else %}
              <h5>0/0</h5>
            {% endif %}
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card dash-card teal">
          <div class="card-body"><h6>Status</h6><h5>{{ student[8] }}</h5></div>
        </div>
      </div>
    </div>
    <div class="row g-4">
      <div class="col-md-6">
        <div class="card">
          <div class="card-header bg-primary text-white"><h5 class="mb-0"><i class="fas fa-id-card"></i> Profile Information</h5></div>
          <div class="card-body">
            <table class="table">
              <tr><th width="40%">Name</th><td>{{ student[2] }}</td></tr>
              <tr><th>Email</th><td>{{ student[3] }}</td></tr>
              <tr><th>Phone</th><td>{{ student[4] }}</td></tr>
              <tr><th>Age</th><td>{{ student[5] }}</td></tr>
              <tr><th>Category</th><td>{{ student[6] }}</td></tr>
              <tr><th>Joined</th><td>{{ student[7] }}</td></tr>
            </table>
          </div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card">
          <div class="card-header bg-success text-white"><h5 class="mb-0"><i class="fas fa-chart-bar"></i> Performance Summary</h5></div>
          <div class="card-body">
            {% if performance_stats and performance_stats[0] %}
            <table class="table">
              <tr><th>Avg Score</th><td>{{ performance_stats[0]|round(2) }}</td></tr>
              <tr><th>Total Sessions</th><td>{{ performance_stats[1] }}</td></tr>
            </table>
            {% else %}
            <p class="text-muted text-center py-4"><i class="fas fa-chart-line fa-3x mb-3 d-block"></i>No performance records yet.</p>
            {% endif %}
          </div>
        </div>
      </div>
    </div>
    {% endif %}
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
""" + COMMON_JS + "</body></html>"

# ── STUDENTS LIST ──
STUDENTS_LIST_TEMPLATE = """
""" + base_head("Students List") + flash_html() + """
<div class="d-flex" style="min-height:100vh;">
  {{ sidebar|safe }}
  <div class="flex-grow-1 p-4">
    <div class="page-header d-flex justify-content-between align-items-center">
      <div><h2><i class="fas fa-users"></i> Students List</h2><p class="mb-0">All registered active students</p></div>
      {% if session.get('username') in ['Arjun9097Div','Admin_Seenu'] %}
      <a href="/register" class="btn btn-light"><i class="fas fa-user-plus"></i> Add Student</a>
      {% endif %}
    </div>
    <div class="card">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-hover mb-0">
            <thead>
              <tr>
                <th>#</th><th>Student ID</th><th>Name</th><th>Category</th>
                <th>Phone</th><th>Age</th><th>Attendance</th><th>Registered</th>
                {% if session.get('username') in ['Arjun9097Div','Admin_Seenu'] %}<th>Actions</th>{% endif %}
              </tr>
            </thead>
            <tbody>
              {% for s in students %}
              <tr>
                <td>{{ loop.index }}</td>
                <td><code>{{ s[1] }}</code></td>
                <td><strong>{{ s[2] }}</strong></td>
                <td><span class="badge bg-primary">{{ s[6] }}</span></td>
                <td>{{ s[4] }}</td>
                <td>{{ s[5] }}</td>
                <td>
                  {% set total = s[9] or 0 %}
                  {% set present = s[10] or 0 %}
                  {% if total > 0 %}
                    {{ present }}/{{ total }}
                    <div class="progress" style="height:4px;">
                      <div class="progress-bar bg-success" style="width:{{ (present/total*100)|round }}%"></div>
                    </div>
                  {% else %}
                    <span class="text-muted">No records</span>
                  {% endif %}
                </td>
                <td>{{ s[7] }}</td>
                {% if session.get('username') in ['Arjun9097Div','Admin_Seenu'] %}
                <td>
                  <form method="POST" action="/student/delete/{{ s[0] }}" onsubmit="return confirmDelete('Delete {{ s[2] }}?')">
                    <button type="submit" class="btn btn-sm btn-outline-danger"><i class="fas fa-trash"></i></button>
                  </form>
                </td>
                {% endif %}
              </tr>
              {% endfor %}
              {% if not students %}
              <tr><td colspan="9" class="text-center py-4 text-muted">No students registered yet.</td></tr>
              {% endif %}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
""" + COMMON_JS + "</body></html>"

# ── MARK ATTENDANCE ──
MARK_ATTENDANCE_TEMPLATE = """
""" + base_head("Mark Attendance") + flash_html() + """
<div class="d-flex" style="min-height:100vh;">
  {{ sidebar|safe }}
  <div class="flex-grow-1 p-4">
    <div class="page-header">
      <h2><i class="fas fa-calendar-check"></i> Mark Attendance</h2>
      <p class="mb-0">Record daily attendance for students</p>
    </div>
    <div class="row justify-content-center">
      <div class="col-md-7">
        <div class="card">
          <div class="card-header bg-primary text-white"><h5 class="mb-0">Attendance Form</h5></div>
          <div class="card-body">
            <form method="POST" action="/attendance/mark">
              <div class="mb-3">
                <label for="student_id" class="form-label">Select Student *</label>
                <select class="form-select" id="student_id" name="student_id" required>
                  <option value="">-- Select Student --</option>
                  {% for sid, sname, scat in students %}
                  <option value="{{ sid }}">{{ sname }} ({{ scat }})</option>
                  {% endfor %}
                </select>
              </div>
              <div class="mb-3">
                <label for="date" class="form-label">Date *</label>
                <input type="date" class="form-control" id="date" name="date" value="{{ today }}" required>
              </div>
              <div class="mb-4">
                <label class="form-label">Status *</label>
                <div class="d-flex gap-3">
                  <div class="form-check">
                    <input class="form-check-input" type="radio" name="status" id="present" value="Present" checked>
                    <label class="form-check-label text-success fw-bold" for="present">✅ Present</label>
                  </div>
                  <div class="form-check">
                    <input class="form-check-input" type="radio" name="status" id="absent" value="Absent">
                    <label class="form-check-label text-danger fw-bold" for="absent">❌ Absent</label>
                  </div>
                </div>
              </div>
              <button type="submit" class="btn btn-primary w-100"><i class="fas fa-save"></i> Mark Attendance</button>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
""" + COMMON_JS + "</body></html>"

# ── ADD PERFORMANCE ──
ADD_PERFORMANCE_TEMPLATE = """
""" + base_head("Add Performance") + flash_html() + """
<div class="d-flex" style="min-height:100vh;">
  {{ sidebar|safe }}
  <div class="flex-grow-1 p-4">
    <div class="page-header">
      <h2><i class="fas fa-chart-line"></i> Add Performance Record</h2>
      <p class="mb-0">Record student performance metrics</p>
    </div>
    <div class="row justify-content-center">
      <div class="col-md-7">
        <div class="card">
          <div class="card-header bg-primary text-white"><h5 class="mb-0">Performance Form</h5></div>
          <div class="card-body">
            <form method="POST" action="/performance/add">
              <div class="mb-3">
                <label for="student_id" class="form-label">Select Student *</label>
                <select class="form-select" id="student_id" name="student_id" required>
                  <option value="">-- Select Student --</option>
                  {% for sid, stuid, sname in students %}
                  <option value="{{ sid }}">{{ sname }} ({{ stuid }})</option>
                  {% endfor %}
                </select>
              </div>
              <div class="mb-3">
                <label for="category" class="form-label">Category *</label>
                <select class="form-select" id="category" name="category" required>
                  <option value="">Select Category</option>
                  <option>Athletics</option><option>Football</option><option>Basketball</option>
                  <option>Table Tennis</option><option>Swimming</option>
                  <option>Fitness Training</option><option>Cricket</option><option>Badminton</option>
                </select>
              </div>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="rounds_completed" class="form-label">Rounds Completed</label>
                  <input type="number" class="form-control" id="rounds_completed" name="rounds_completed" min="0" value="0">
                </div>
                <div class="col-md-6 mb-3">
                  <label for="score" class="form-label">Score (0-100)</label>
                  <input type="number" class="form-control" id="score" name="score" min="0" max="100" step="0.1" value="0">
                </div>
              </div>
              <div class="mb-4">
                <label for="notes" class="form-label">Notes</label>
                <textarea class="form-control" id="notes" name="notes" rows="3" placeholder="Additional observations..."></textarea>
              </div>
              <button type="submit" class="btn btn-primary w-100"><i class="fas fa-save"></i> Save Performance Record</button>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
""" + COMMON_JS + "</body></html>"

# ── UPLOAD MEDIA ──
UPLOAD_MEDIA_TEMPLATE = """
""" + base_head("Upload Media") + flash_html() + """
<div class="d-flex" style="min-height:100vh;">
  {{ sidebar|safe }}
  <div class="flex-grow-1 p-4">
    <div class="page-header">
      <h2><i class="fas fa-upload"></i> Upload Media</h2>
      <p class="mb-0">Upload images, videos, audio, PDFs, and documents</p>
    </div>
    <div class="row justify-content-center">
      <div class="col-md-7">
        <div class="card">
          <div class="card-header bg-primary text-white"><h5 class="mb-0">File Upload</h5></div>
          <div class="card-body">
            <div class="alert alert-info">
              <i class="fas fa-info-circle"></i>
              <strong>Allowed types:</strong> Images (PNG, JPG, GIF), Videos (MP4, AVI, MOV), Audio (MP3, WAV), Documents (PDF, DOC, DOCX)<br>
              <strong>Max size:</strong> 500MB for videos/audio
            </div>
            <form method="POST" action="/media/upload" enctype="multipart/form-data">
              <div class="mb-3">
                <label for="file" class="form-label">Choose File *</label>
                <input type="file" class="form-control" id="file" name="file" required
                  accept=".png,.jpg,.jpeg,.gif,.mp4,.avi,.mov,.mp3,.wav,.pdf,.doc,.docx">
              </div>
              <div class="mb-4">
                <label for="description" class="form-label">Description</label>
                <input type="text" class="form-control" id="description" name="description" placeholder="Brief description of the file...">
              </div>
              <button type="submit" class="btn btn-primary w-100"><i class="fas fa-cloud-upload-alt"></i> Upload File</button>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
""" + COMMON_JS + "</body></html>"

# ── MEDIA GALLERY ──
MEDIA_GALLERY_TEMPLATE = """
""" + base_head("Media Gallery") + flash_html() + """
<div class="d-flex" style="min-height:100vh;">
  {{ sidebar|safe }}
  <div class="flex-grow-1 p-4">
    <div class="page-header d-flex justify-content-between align-items-center">
      <div><h2><i class="fas fa-photo-video"></i> Media Gallery</h2><p class="mb-0">All uploaded files</p></div>
      <a href="/media/upload" class="btn btn-light"><i class="fas fa-upload"></i> Upload New</a>
    </div>
    {% if all_files %}
    <div class="row g-4">
      {% for f in all_files %}
      <div class="col-md-3 col-sm-6">
        <div class="card media-card h-100">
          {% set ftype = f[5] %}
          {% if ftype in ['jpg','jpeg','png','gif'] %}
            <img src="/static/uploads/{{ f[2] }}" class="media-thumb" alt="{{ f[3] }}">
          {% elif ftype in ['mp4','avi','mov'] %}
            <div class="media-icon"><i class="fas fa-film fa-4x text-danger"></i></div>
          {% elif ftype in ['mp3','wav'] %}
            <div class="media-icon"><i class="fas fa-music fa-4x text-success"></i></div>
          {% elif ftype == 'pdf' %}
            <div class="media-icon"><i class="fas fa-file-pdf fa-4x text-danger"></i></div>
          {% else %}
            <div class="media-icon"><i class="fas fa-file-word fa-4x text-primary"></i></div>
          {% endif %}
          <div class="card-body p-2">
            <p class="fw-bold mb-1 text-truncate" title="{{ f[3] }}">{{ f[3] }}</p>
            <small class="text-muted">{{ f[8] or f[7] }} &bull; {{ f[9] }}</small>
            <div class="d-flex justify-content-between align-items-center mt-2">
              <a href="/static/uploads/{{ f[2] }}" target="_blank" class="btn btn-sm btn-outline-primary">
                <i class="fas fa-eye"></i>
              </a>
              {% if session.get('user_id') == f[1] or session.get('role') in ['admin','teacher','developer'] %}
              <form method="POST" action="/media/delete/{{ f[0] }}" onsubmit="return confirmDelete('Delete this file?')">
                <button type="submit" class="btn btn-sm btn-outline-danger"><i class="fas fa-trash"></i></button>
              </form>
              {% endif %}
            </div>
          </div>
        </div>
      </div>
      {% endfor %}
    </div>
    {% else %}
    <div class="text-center py-5">
      <i class="fas fa-photo-video fa-5x text-muted mb-4"></i>
      <h4 class="text-muted">No media files yet</h4>
      <a href="/media/upload" class="btn btn-primary mt-3"><i class="fas fa-upload"></i> Upload First File</a>
    </div>
    {% endif %}
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
""" + COMMON_JS + "</body></html>"

# ── ABOUT ──
ABOUT_TEMPLATE = """
""" + base_head("About") + base_navbar() + flash_html() + """
<main class="container mt-4">
  <div class="page-header text-center mb-5">
    <h1 class="display-5 fw-bold"><i class="fas fa-info-circle"></i> About Arjun Sports Academy</h1>
    <p class="lead">Excellence in Sports Training Since 2024</p>
  </div>
  <div class="row g-4">
    <div class="col-md-6">
      <div class="card h-100">
        <div class="card-body">
          <h3 class="text-gradient"><i class="fas fa-bullseye"></i> Our Mission</h3>
          <p>To develop world-class athletes through systematic training, performance monitoring, and personalized coaching. We believe in nurturing talent and building champions who excel at national and international levels.</p>
        </div>
      </div>
    </div>
    <div class="col-md-6">
      <div class="card h-100">
        <div class="card-body">
          <h3 class="text-gradient"><i class="fas fa-eye"></i> Our Vision</h3>
          <p>To become India's premier sports academy, recognized for producing national and international champions across multiple sports disciplines while maintaining the highest standards of training and character development.</p>
        </div>
      </div>
    </div>
  </div>
  <div class="card mt-4 coach-spotlight">
    <div class="card-body text-center p-5">
      <i class="fas fa-medal fa-5x text-warning mb-4"></i>
      <h2 class="text-gradient mb-3">Meet Coach Arjun</h2>
      <p class="lead">National-level sportsman with over 15 years of experience. Coach Arjun has dedicated his life to nurturing the next generation of sporting champions.</p>
    </div>
  </div>
</main>
""" + base_footer()

# ── CONTACT ──
CONTACT_TEMPLATE = """
""" + base_head("Contact") + base_navbar() + flash_html() + """
<main class="container mt-4">
  <div class="page-header text-center mb-5">
    <h1 class="display-5 fw-bold"><i class="fas fa-phone"></i> Contact Us</h1>
    <p class="lead">Get in touch with Arjun Sports Academy</p>
  </div>
  <div class="row g-4 justify-content-center">
    <div class="col-md-4">
      <div class="card text-center h-100">
        <div class="card-body p-4">
          <i class="fas fa-phone fa-3x text-primary mb-3"></i>
          <h5>Phone</h5>
          <p class="text-muted">+91 90970 00001</p>
        </div>
      </div>
    </div>
    <div class="col-md-4">
      <div class="card text-center h-100">
        <div class="card-body p-4">
          <i class="fas fa-envelope fa-3x text-success mb-3"></i>
          <h5>Email</h5>
          <p class="text-muted">arjun@arjunacademy.com</p>
        </div>
      </div>
    </div>
    <div class="col-md-4">
      <div class="card text-center h-100">
        <div class="card-body p-4">
          <i class="fas fa-map-marker-alt fa-3x text-danger mb-3"></i>
          <h5>Location</h5>
          <p class="text-muted">India</p>
        </div>
      </div>
    </div>
  </div>
</main>
""" + base_footer()

# ─────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────

def render(template, **kwargs):
    """Render a template string with session available."""
    kwargs.setdefault('session', session)
    return render_template_string(template, **kwargs)

@app.route('/')
def index():
    return render(INDEX_TEMPLATE)

@app.route('/about')
def about():
    return render(ABOUT_TEMPLATE)

@app.route('/contact')
def contact():
    return render(CONTACT_TEMPLATE)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('sports_academy.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username=? AND status="Active"', (username,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user[4], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[5]
            session['student_id'] = user[6]
            flash(f'Welcome {user[1]}!', 'success')
            if user[5] == 'developer': return redirect(url_for('developer_dashboard'))
            elif user[5] == 'admin':   return redirect(url_for('admin_dashboard'))
            elif user[5] == 'teacher': return redirect(url_for('teacher_dashboard'))
            else:                      return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid username or password!', 'error')
    return render(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/student-portal')
def student_portal():
    return render(STUDENT_PORTAL_TEMPLATE)

@app.route('/register', methods=['GET','POST'])
def register():
    if session.get('username') not in ['Arjun9097Div','Admin_Seenu']:
        flash('Access denied! Only Arjun and Admin can register students.', 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        name     = request.form['name']
        email    = request.form['email']
        phone    = request.form['phone']
        age      = request.form['age']
        password = request.form['password']
        role     = request.form.get('role','student')
        conn = sqlite3.connect('sports_academy.db')
        cursor = conn.cursor()
        try:
            if role == 'teacher':
                specialization = request.form.get('specialization','General')
                experience     = request.form.get('experience', 0)
                tid = generate_teacher_id(name)
                cursor.execute('INSERT INTO teachers (teacher_id,name,email,phone,specialization,experience) VALUES (?,?,?,?,?,?)',
                    (tid,name,email,phone,specialization,experience))
                db_tid = cursor.lastrowid
                cursor.execute('INSERT INTO users (username,email,phone,password_hash,role,student_id) VALUES (?,?,?,?,?,?)',
                    (tid.lower(), email, phone, generate_password_hash(password), 'teacher', db_tid))
                flash(f'Teacher registered! ID: {tid}, Username: {tid.lower()}', 'success')
            else:
                category   = request.form.get('category','Athletics')
                student_id = generate_student_id()
                cursor.execute('INSERT INTO students (student_id,name,email,phone,age,category) VALUES (?,?,?,?,?,?)',
                    (student_id,name,email,phone,age,category))
                db_sid = cursor.lastrowid
                cursor.execute('INSERT INTO users (username,email,phone,password_hash,role,student_id) VALUES (?,?,?,?,?,?)',
                    (student_id.lower(), email, phone, generate_password_hash(password), 'student', db_sid))
                flash(f'Student registered! ID: {student_id}, Username: {student_id.lower()}', 'success')
            conn.commit()
            return redirect(url_for('students_list'))
        except sqlite3.IntegrityError as e:
            err = str(e).lower()
            if 'email' in err: flash('Email already exists!', 'error')
            elif 'phone' in err: flash('Phone already exists!', 'error')
            else: flash('Registration failed! Email or phone already exists.', 'error')
        finally:
            conn.close()
    return render(REGISTER_TEMPLATE)

@app.route('/developer/dashboard')
@login_required('developer')
def developer_dashboard():
    conn = sqlite3.connect('sports_academy.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM students WHERE status="Active"'); ts = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM teachers WHERE status="Active"'); tt = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM users WHERE status="Active"');    tu = cursor.fetchone()[0]
    cursor.execute('SELECT role,COUNT(*) FROM users GROUP BY role');        ur = cursor.fetchall()
    conn.close()
    sb = dashboard_sidebar('developer', session.get('username',''))
    return render(DEV_DASHBOARD_TEMPLATE, sidebar=sb,
                  total_students=ts, total_teachers=tt, total_users=tu, user_roles=ur)

@app.route('/admin/dashboard')
@login_required('admin')
def admin_dashboard():
    conn = sqlite3.connect('sports_academy.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM students WHERE status="Active"'); ts = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM teachers WHERE status="Active"'); tt = cursor.fetchone()[0]
    cursor.execute('SELECT category,COUNT(*) FROM students WHERE status="Active" GROUP BY category'); cats = cursor.fetchall()
    cursor.execute('SELECT name,category,registration_date FROM students ORDER BY registration_date DESC LIMIT 5'); recent = cursor.fetchall()
    conn.close()
    sb = dashboard_sidebar('admin', session.get('username',''))
    return render(ADMIN_DASHBOARD_TEMPLATE, sidebar=sb,
                  total_students=ts, total_teachers=tt, categories=cats, recent_students=recent)

@app.route('/teacher/dashboard')
@login_required('teacher')
def teacher_dashboard():
    conn = sqlite3.connect('sports_academy.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM students WHERE status="Active"'); ts = cursor.fetchone()[0]
    cursor.execute('SELECT category,COUNT(*) FROM students WHERE status="Active" GROUP BY category'); cats = cursor.fetchall()
    cursor.execute('''SELECT s.name,a.date,a.status FROM attendance a
        JOIN students s ON a.student_id=s.id WHERE a.marked_by=?
        ORDER BY a.date DESC LIMIT 10''', (session['user_id'],))
    recent = cursor.fetchall()
    conn.close()
    sb = dashboard_sidebar('teacher', session.get('username',''))
    return render(TEACHER_DASHBOARD_TEMPLATE, sidebar=sb,
                  total_students=ts, categories=cats, recent_attendance=recent)

@app.route('/student/dashboard')
@login_required('student')
def student_dashboard():
    sid = session.get('student_id')
    conn = sqlite3.connect('sports_academy.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students WHERE id=?', (sid,)); student = cursor.fetchone()
    cursor.execute('''SELECT COUNT(*),SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END)
        FROM attendance WHERE student_id=?''', (sid,))
    att = cursor.fetchone()
    cursor.execute('SELECT AVG(score),COUNT(*) FROM performance WHERE student_id=?', (sid,))
    perf = cursor.fetchone()
    conn.close()
    sb = dashboard_sidebar('student', session.get('username',''))
    return render(STUDENT_DASHBOARD_TEMPLATE, sidebar=sb,
                  student=student, attendance_stats=att, performance_stats=perf)

@app.route('/students/list')
@login_required()
def students_list():
    conn = sqlite3.connect('sports_academy.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT s.*,
        CAST(COUNT(a.id) AS INTEGER),
        CAST(SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS INTEGER),
        MAX(a.date)
        FROM students s LEFT JOIN attendance a ON s.id=a.student_id
        WHERE s.status="Active" GROUP BY s.id ORDER BY s.name''')
    students = cursor.fetchall()
    conn.close()
    sb = dashboard_sidebar(session.get('role','student'), session.get('username',''))
    return render(STUDENTS_LIST_TEMPLATE, sidebar=sb, students=students)

@app.route('/attendance/mark', methods=['GET','POST'])
def mark_attendance():
    if session.get('role') not in ['admin','teacher','developer']:
        flash('Access denied!', 'error')
        return redirect(url_for('students_list'))
    if request.method == 'POST':
        conn = sqlite3.connect('sports_academy.db')
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO attendance (student_id,date,status,marked_by,marked_by_role) VALUES (?,?,?,?,?)',
            (request.form['student_id'], request.form['date'], request.form['status'],
             session['user_id'], session['role']))
        conn.commit(); conn.close()
        flash('Attendance marked!', 'success')
        return redirect(url_for('mark_attendance'))
    conn = sqlite3.connect('sports_academy.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id,name,category FROM students WHERE status="Active" ORDER BY name')
    students = cursor.fetchall()
    conn.close()
    sb = dashboard_sidebar(session.get('role',''), session.get('username',''))
    return render(MARK_ATTENDANCE_TEMPLATE, sidebar=sb, students=students,
                  today=date.today().isoformat())

@app.route('/student/delete/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    if session.get('username') not in ['Arjun9097Div','Admin_Seenu']:
        flash('Access denied!', 'error')
        return redirect(url_for('students_list'))
    conn = sqlite3.connect('sports_academy.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE students SET status="Inactive" WHERE id=?', (student_id,))
    cursor.execute('UPDATE users SET status="Inactive" WHERE student_id=? AND role="student"', (student_id,))
    conn.commit(); conn.close()
    flash('Student removed.', 'success')
    return redirect(url_for('students_list'))

@app.route('/performance/add', methods=['GET','POST'])
def add_performance():
    if session.get('username') not in ['Arjun9097Div','Admin_Seenu']:
        flash('Access denied!', 'error')
        return redirect(url_for('students_list'))
    if request.method == 'POST':
        conn = sqlite3.connect('sports_academy.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO performance (student_id,category,rounds_completed,score,notes,recorded_by) VALUES (?,?,?,?,?,?)',
            (request.form['student_id'], request.form['category'],
             request.form['rounds_completed'], request.form['score'],
             request.form.get('notes',''), session['user_id']))
        conn.commit(); conn.close()
        flash('Performance recorded!', 'success')
        return redirect(url_for('students_list'))
    conn = sqlite3.connect('sports_academy.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id,student_id,name FROM students WHERE status="Active" ORDER BY name')
    students = cursor.fetchall()
    conn.close()
    sb = dashboard_sidebar(session.get('role',''), session.get('username',''))
    return render(ADD_PERFORMANCE_TEMPLATE, sidebar=sb, students=students)

@app.route('/media/upload', methods=['GET','POST'])
@login_required()
def upload_media():
    if request.method == 'POST':
        if 'file' not in request.files or request.files['file'].filename == '':
            flash('No file selected!', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename  = secure_filename(file.filename)
            filename  = datetime.now().strftime('%Y%m%d_%H%M%S_') + filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            file_size = os.path.getsize(file_path)
            file_type = filename.rsplit('.',1)[1].lower()
            if file_type in ['mp4','avi','mov','mp3','wav'] and file_size > 500*1024*1024:
                os.remove(file_path)
                flash('File too large! Max 500MB for video/audio.', 'error')
                return redirect(request.url)
            conn = sqlite3.connect('sports_academy.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO media_files (user_id,filename,original_filename,file_type,file_size,description) VALUES (?,?,?,?,?,?)',
                (session['user_id'], filename, file.filename, file_type, file_size,
                 request.form.get('description','')))
            conn.commit(); conn.close()
            flash('File uploaded!', 'success')
            return redirect(url_for('media_gallery'))
        else:
            flash('Invalid file type!', 'error')
    sb = dashboard_sidebar(session.get('role',''), session.get('username',''))
    return render(UPLOAD_MEDIA_TEMPLATE, sidebar=sb)

@app.route('/media/gallery')
@login_required()
def media_gallery():
    conn = sqlite3.connect('sports_academy.db')
    cursor = conn.cursor()
    if session.get('role') in ['admin','teacher','developer']:
        cursor.execute('''SELECT m.*,u.username FROM media_files m
            JOIN users u ON m.user_id=u.id ORDER BY m.upload_date DESC''')
    else:
        cursor.execute('''SELECT m.*,u.username FROM media_files m
            JOIN users u ON m.user_id=u.id WHERE m.user_id=? ORDER BY m.upload_date DESC''',
            (session['user_id'],))
    all_files = cursor.fetchall()
    conn.close()
    sb = dashboard_sidebar(session.get('role',''), session.get('username',''))
    return render(MEDIA_GALLERY_TEMPLATE, sidebar=sb, all_files=all_files)

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/media/delete/<int:file_id>', methods=['POST'])
@login_required()
def delete_media(file_id):
    conn = sqlite3.connect('sports_academy.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM media_files WHERE id=?', (file_id,))
    mf = cursor.fetchone()
    if not mf:
        flash('File not found!', 'error')
        return redirect(url_for('media_gallery'))
    if mf[1] != session['user_id'] and session.get('role') not in ['admin','teacher','developer']:
        flash('Access denied!', 'error')
        return redirect(url_for('media_gallery'))
    fp = os.path.join(app.config['UPLOAD_FOLDER'], mf[2])
    if os.path.exists(fp): os.remove(fp)
    cursor.execute('DELETE FROM media_files WHERE id=?', (file_id,))
    conn.commit(); conn.close()
    flash('File deleted!', 'success')
    return redirect(url_for('media_gallery'))

@app.route('/api/student/<int:student_id>/stats')
def student_stats(student_id):
    conn = sqlite3.connect('sports_academy.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT COUNT(*),SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END)
        FROM attendance WHERE student_id=?''', (student_id,))
    att = cursor.fetchone()
    cursor.execute('''SELECT AVG(score),SUM(rounds_completed),COUNT(*)
        FROM performance WHERE student_id=?''', (student_id,))
    perf = cursor.fetchone()
    conn.close()
    total = att[0] or 0
    present = att[1] or 0
    return jsonify({
        'attendance': {
            'total_days': total, 'present_days': present,
            'attendance_rate': round(present/max(total,1)*100, 2)
        },
        'performance': {
            'avg_score': round(perf[0] or 0, 2),
            'total_rounds': perf[1] or 0,
            'total_sessions': perf[2] or 0
        }
    })

# ─────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)