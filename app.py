from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from email_validator import validate_email, EmailNotValidError
from flask_bcrypt import Bcrypt
from authlib.integrations.flask_client import OAuth
import requests
import os
import random
import time
import json
import secrets
import threading

app = Flask(__name__)
app.secret_key = "2c7bb737141b0934dd3c844a6084994e07f7225e6b0047dbe245eaaaf97211c6"

# Database configuration - Use PostgreSQL for production
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///Cloud.db').replace('postgres://', 'postgresql://')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.permanent_session_lifetime = timedelta(days=7)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


# OAuth configuration
oauth = OAuth(app)

# GitHub OAuth setup
github = oauth.register(
    name='github',
    client_id='Ov23liA3iwUjDbRfDFGO',  
    client_secret='c646dfd75b163546d9c68e25ec3708aecd8259b8',  
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email repo'},
    
)

# --------------------- MODELS ---------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=True)
    phoneNumber = db.Column(db.String(20), nullable=True)
    github_id = db.Column(db.String(100), unique=True, nullable=True)
    github_access_token = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    
    # Relationships
    settings = db.relationship('UserSettings', backref='user', uselist=False, lazy=True)
    api_keys = db.relationship('APIKey', backref='user', lazy=True)
    deployments = db.relationship('Deployment', backref='user', lazy=True)

class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    deployment_notifications = db.Column(db.Boolean, default=True)
    security_notifications = db.Column(db.Boolean, default=True)
    product_notifications = db.Column(db.Boolean, default=False)
    slack_webhook = db.Column(db.String(500), nullable=True)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(100), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class APIKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    key = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

class Deployment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    repository = db.Column(db.String(200), nullable=False)
    branch = db.Column(db.String(100), nullable=False, default='main')
    environment = db.Column(db.String(50), nullable=False, default='production')
    status = db.Column(db.String(50), nullable=False, default='pending')
    progress = db.Column(db.Integer, default=0)
    deployment_id = db.Column(db.String(100), unique=True, nullable=False)
    deployment_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DeploymentLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deployment_id = db.Column(db.String(100), db.ForeignKey('deployment.deployment_id'), nullable=False)
    level = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    deployment = db.relationship('Deployment', backref=db.backref('logs', lazy=True))

# -------------------------
# Helper Functions
# -------------------------
    # the router to anlaysis 

def generate_api_key():
    return f"ael_sk_{secrets.token_urlsafe(32)}"

def create_default_settings(user_id):
    """Create default settings for a new user"""
    settings = UserSettings(user_id=user_id)
    db.session.add(settings)
    db.session.commit()

def generate_initial_logs(deployment):
    """Generate initial deployment logs"""
    repo_name = deployment.repository.split('/')[-1]
    initial_logs = [
        ('info', f'Starting deployment process for {deployment.repository}'),
        ('info', f'Deployment ID: {deployment.deployment_id}'),
        ('info', f'Branch: {deployment.branch}'),
        ('info', f'Environment: {deployment.environment}'),
        ('info', f'Target URL: {deployment.deployment_url}'),
        ('info', 'Initializing deployment pipeline...')
    ]
    
    for level, message in initial_logs:
        add_deployment_log(deployment.deployment_id, level, message)

def add_deployment_log(deployment_id, level, message):
    """Add a log entry for deployment"""
    log = DeploymentLog(
        deployment_id=deployment_id,
        level=level,
        message=message
    )
    db.session.add(log)
    db.session.commit()

def run_deployment_simulation(deployment_id):
    """Simulate deployment process"""
    with app.app_context():
        deployment = Deployment.query.filter_by(deployment_id=deployment_id).first()
        if not deployment:
            return
        
        deployment_steps = [
            (10, "Cloning repository from GitHub..."),
            (20, "Repository cloned successfully"),
            (30, "Installing dependencies..."),
            (40, "Running npm install / pip install..."),
            (50, "Dependencies installed successfully"),
            (60, "Building application..."),
            (70, "Running build process..."),
            (75, "Build completed successfully"),
            (80, "Running tests..."),
            (85, "Tests passed successfully"),
            (90, "Deploying to production environment..."),
            (95, "Application deployed successfully"),
            (100, "Running health checks...")
        ]
        
        for progress, message in deployment_steps:
            deployment.progress = progress
            deployment.status = 'deploying'
            
            if 'successfully' in message.lower():
                level = 'success'
            elif 'error' in message.lower() or 'failed' in message.lower():
                level = 'error'
            elif 'warning' in message.lower():
                level = 'warning'
            else:
                level = 'info'
            
            add_deployment_log(deployment_id, level, message)
            db.session.commit()
            time.sleep(random.uniform(1, 3))
        
        final_status = 'success' if random.random() < 0.85 else 'error'
        deployment.status = final_status
        deployment.progress = 100
        
        if final_status == 'success':
            add_deployment_log(deployment_id, 'success', 'Deployment completed successfully!')
            add_deployment_log(deployment_id, 'info', f'Your application is live at: {deployment.deployment_url}')
        else:
            add_deployment_log(deployment_id, 'error', 'Deployment failed due to build errors')
            add_deployment_log(deployment_id, 'info', 'Check your application logs for more details')
        
        db.session.commit()

# --------------------- ROUTES ---------------------
@app.route('/')
def landing():
    return render_template('landing.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        
        if user and user.password and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['email'] = user.email
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password", "danger")

    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        phoneNumber = request.form.get("phoneNumber")

        try:
            valid = validate_email(email)
            email = valid.email
        except EmailNotValidError:
            flash("Invalid email format", "danger")
            return render_template("signup.html")

        if User.query.filter_by(email=email).first():
            flash("Email is already registered", "warning")
            return render_template("signup.html")

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        new_user = User(username=username, email=email, password=hashed_password, phoneNumber=phoneNumber)
        db.session.add(new_user)
        db.session.commit()

        # Create default settings for new user
        create_default_settings(new_user.id)

        flash("Signup successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")

# -------------------------
# GitHub OAuth login/signup
# -------------------------

@app.route('/login/github')
def login_github():
    redirect_uri = "https://aeloria.onrender.com/github/authorize"
    return oauth.github.authorize_redirect(redirect_uri)

@app.route('/signup/github')
def signup_github():
    redirect_uri = "https://aeloria.onrender.com/github/authorize"
    return oauth.github.authorize_redirect(redirect_uri)

@app.route('/github/authorize')
def github_authorize():
    try:
        token = oauth.github.authorize_access_token()
        if not token or 'access_token' not in token:
            flash("GitHub authorization failed", "danger")
            return redirect(url_for('login'))

        access_token = token['access_token']

        # Fetch user info
        resp = oauth.github.get('user', token=token)
        user_info = resp.json()

        # Fetch user emails
        email_resp = oauth.github.get('user/emails', token=token)
        emails = email_resp.json()
        primary_email = None
        for email in emails:
            if email.get('primary') and email.get('verified'):
                primary_email = email['email']
                break
        if not primary_email:
            primary_email = user_info.get('email') or f"{user_info['login']}@github.com"

        github_id = str(user_info['id'])
        username = user_info['login']

        # Check existing user by GitHub ID
        user = User.query.filter_by(github_id=github_id).first()

        if not user:
            # Check by email
            user = User.query.filter_by(email=primary_email).first()
            if user:
                user.github_id = github_id
                user.github_access_token = access_token
            else:
                user = User(
                    username=username,
                    email=primary_email,
                    password=None,
                    phoneNumber=None,
                    github_id=github_id,
                    github_access_token=access_token
                )
                db.session.add(user)
                db.session.commit()
                
                # Create default settings for new GitHub user
                create_default_settings(user.id)
        else:
            # Update token for existing user
            user.github_access_token = access_token
            db.session.commit()

        # Set session
        session['user_id'] = user.id
        session['username'] = user.username
        session['email'] = user.email
        session['github_username'] = username
        session['github_access_token'] = access_token

        flash(f"Welcome {username}! Successfully logged in with GitHub.", "success")
        return redirect(url_for("dashboard"))

    except Exception as e:
        print(f"GitHub authorize error: {e}")
        flash("Authentication failed. Please try again.", "danger")
        return redirect(url_for('login'))

# -------------------------
# Settings API Routes
# -------------------------

@app.route('/api/settings/notifications', methods=['GET', 'PUT'])
def api_settings_notifications():
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    user = User.query.get(session['user_id'])
    if not user or not user.settings:
        return jsonify({"error": "User or settings not found"}), 404

    if request.method == 'GET':
        settings = user.settings
        return jsonify({
            "deployment_notifications": settings.deployment_notifications,
            "security_notifications": settings.security_notifications,
            "product_notifications": settings.product_notifications,
            "slack_webhook": settings.slack_webhook or ""
        })
    
    elif request.method == 'PUT':
        data = request.get_json()
        settings = user.settings
        
        try:
            if 'deployment_notifications' in data:
                settings.deployment_notifications = bool(data['deployment_notifications'])
            if 'security_notifications' in data:
                settings.security_notifications = bool(data['security_notifications'])
            if 'product_notifications' in data:
                settings.product_notifications = bool(data['product_notifications'])
            if 'slack_webhook' in data:
                settings.slack_webhook = data['slack_webhook']
            
            settings.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "Notification settings updated successfully"
            })
        
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 400

@app.route('/api/settings/api-keys', methods=['GET', 'POST', 'DELETE'])
def api_settings_api_keys():
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({"error": "User not found"}), 404

    if request.method == 'GET':
        api_keys = APIKey.query.filter_by(user_id=user.id, is_active=True).order_by(APIKey.created_at.desc()).all()
        keys_list = []
        
        for key in api_keys:
            keys_list.append({
                "id": key.id,
                "name": key.name,
                "key": key.key,
                "created_at": key.created_at.strftime("%B %d, %Y"),
                "last_used": key.last_used.strftime("%B %d, %Y") if key.last_used else "Never"
            })
        
        return jsonify(keys_list)
    
    elif request.method == 'POST':
        data = request.get_json()
        key_name = data.get('name', 'New API Key')
        
        # Generate unique API key
        api_key_value = generate_api_key()
        
        new_api_key = APIKey(
            user_id=user.id,
            name=key_name,
            key=api_key_value
        )
        
        try:
            db.session.add(new_api_key)
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "API key generated successfully",
                "api_key": api_key_value,
                "key_id": new_api_key.id
            })
        
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 400
    
    elif request.method == 'DELETE':
        key_id = request.args.get('key_id')
        
        if not key_id:
            return jsonify({"error": "Key ID is required"}), 400
        
        api_key = APIKey.query.filter_by(id=key_id, user_id=user.id).first()
        
        if not api_key:
            return jsonify({"error": "API key not found"}), 404
        
        try:
            api_key.is_active = False
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "API key revoked successfully"
            })
        
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 400

@app.route('/api/settings/security/password', methods=['PUT'])
def api_settings_security_password():
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')
    
    # Validate inputs
    if not all([current_password, new_password, confirm_password]):
        return jsonify({"success": False, "message": "All fields are required"}), 400
    
    # Check if user has a password (GitHub users might not have one)
    if not user.password:
        return jsonify({"success": False, "message": "Password change not available for GitHub accounts"}), 400
    
    # Verify current password
    if not bcrypt.check_password_hash(user.password, current_password):
        return jsonify({"success": False, "message": "Current password is incorrect"}), 400
    
    # Check if new passwords match
    if new_password != confirm_password:
        return jsonify({"success": False, "message": "New passwords do not match"}), 400
    
    # Check password strength
    if len(new_password) < 8:
        return jsonify({"success": False, "message": "Password must be at least 8 characters long"}), 400
    
    try:
        user.password = bcrypt.generate_password_hash(new_password).decode("utf-8")
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Password updated successfully"
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400

@app.route('/api/settings/security/2fa', methods=['POST'])
def api_settings_security_2fa():
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    user = User.query.get(session['user_id'])
    if not user or not user.settings:
        return jsonify({"error": "User or settings not found"}), 404

    data = request.get_json()
    action = data.get('action')  # 'enable' or 'disable'
    
    try:
        settings = user.settings
        
        if action == 'enable':
            settings.two_factor_enabled = True
            # In a real app, you would generate and store a 2FA secret here
            settings.two_factor_secret = secrets.token_hex(16)
            message = "Two-factor authentication enabled successfully"
        elif action == 'disable':
            settings.two_factor_enabled = False
            settings.two_factor_secret = None
            message = "Two-factor authentication disabled successfully"
        else:
            return jsonify({"success": False, "message": "Invalid action"}), 400
        
        settings.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": message,
            "two_factor_enabled": settings.two_factor_enabled
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400

# -------------------------
# Dashboard API routes
# -------------------------

@app.route('/api/user')
def api_user():
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user = User.query.get(session['user_id'])
    if user:
        return jsonify({
            "username": user.username,
            "email": user.email,
            "github_username": session.get('github_username', user.username),
            "role": "Developer"
        })
    return jsonify({"error": "User not found"}), 404

@app.route('/api/repositories')
def api_repositories():
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({"error": "User not found"}), 404

    access_token = session.get('github_access_token') or user.github_access_token
    if not access_token:
        return jsonify({"error": "GitHub access token not found"}), 400

    headers = {
        'Authorization': f'token {access_token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    try:
        response = requests.get(
            'https://api.github.com/user/repos?per_page=100',
            headers=headers
        )
        if response.status_code == 200:
            repos = response.json()
            repositories = [
                {
                    "name": repo['name'],
                    "full_name": repo['full_name'],
                    "private": repo['private'],
                    "html_url": repo['html_url'],
                    "description": repo.get('description'),
                    "language": repo.get('language'),
                    "stars": repo.get('stargazers_count', 0),
                    "forks": repo.get('forks_count', 0)
                }
                for repo in repos
            ]
            return jsonify(repositories)
        elif response.status_code == 401:
            return jsonify({"error": "Invalid or expired GitHub token"}), 401
        else:
            return jsonify({"error": "Failed to fetch repositories"}), response.status_code
    except Exception as e:
        print(f"Error fetching repositories: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/deployments/recent')
def api_recent_deployments():
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Get user's actual deployments, most recent first
    deployments = Deployment.query.filter_by(user_id=user.id).order_by(Deployment.created_at.desc()).limit(5).all()
    
    if not deployments:
        return jsonify([])
    
    deployment_list = []
    for dep in deployments:
        time_diff = datetime.utcnow() - dep.created_at
        if time_diff.total_seconds() < 60:
            timestamp = "Just now"
        elif time_diff.total_seconds() < 3600:
            minutes = int(time_diff.total_seconds() / 60)
            timestamp = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif time_diff.total_seconds() < 86400:
            hours = int(time_diff.total_seconds() / 3600)
            timestamp = f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = int(time_diff.total_seconds() / 86400)
            timestamp = f"{days} day{'s' if days != 1 else ''} ago"
        
        repo_name = dep.repository.split('/')[-1] if '/' in dep.repository else dep.repository
        project_name = repo_name.replace('-', ' ').replace('_', ' ').title()
        
        deployment_list.append({
            "project": project_name,
            "repository": dep.repository,
            "status": dep.status,
            "timestamp": timestamp,
            "branch": dep.branch,
            "environment": dep.environment,
            "progress": dep.progress if dep.status == 'deploying' else None,
            "deployment_id": dep.deployment_id,
            "deployment_url": dep.deployment_url
        })
    
    return jsonify(deployment_list)

@app.route('/api/deployments/<deployment_id>/logs')
def api_deployment_logs(deployment_id):
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    deployment = Deployment.query.filter_by(deployment_id=deployment_id).first()
    if not deployment or deployment.user_id != session['user_id']:
        return jsonify({"error": "Deployment not found"}), 404
    
    logs = DeploymentLog.query.filter_by(deployment_id=deployment_id)\
        .order_by(DeploymentLog.timestamp.asc()).all()
    
    log_list = []
    for log in logs:
        log_list.append({
            'id': log.id,
            'level': log.level,
            'message': log.message,
            'timestamp': log.timestamp.isoformat()
        })
    
    return jsonify(log_list)

@app.route('/api/deployments/stats')
def api_deployment_stats():
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    total_deployments = Deployment.query.filter_by(user_id=user.id).count()
    successful_deployments = Deployment.query.filter_by(user_id=user.id, status='success').count()
    failed_deployments = Deployment.query.filter_by(user_id=user.id, status='error').count()
    
    success_rate = "0%"
    if total_deployments > 0:
        success_percentage = (successful_deployments / total_deployments) * 100
        success_rate = f"{success_percentage:.1f}%"
    
    from sqlalchemy import func
    active_projects = db.session.query(func.count(func.distinct(Deployment.repository))).filter_by(user_id=user.id).scalar() or 0
    
    return jsonify({
        "totalDeployments": total_deployments,
        "deploymentGrowth": "0%",
        "successRate": success_rate,
        "successGrowth": "0%",
        "avgDeployTime": "45s",
        "timeImprovement": "0s faster",
        "activeProjects": active_projects,
        "projectsAdded": f"{active_projects} project{'s' if active_projects != 1 else ''} total"
    })

@app.route('/api/deployments', methods=['POST'])
def api_create_deployment():
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    data = request.json
    repository = data.get('repository')
    branch = data.get('branch', 'main')
    environment = data.get('environment', 'production')
    
    if branch != 'main':
        return jsonify({"error": "Only 'main' branch is allowed for deployment"}), 400
    
    if not repository:
        return jsonify({"error": "Repository is required"}), 400
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    deployment_id = f"dep_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}"
    
    # Generate deployment URL
    repo_name = repository.split('/')[-1].lower().replace('_', '-')
    deployment_url = f"https://{repo_name}.aeloria.app"
    
    new_deployment = Deployment(
        user_id=user.id,
        repository=repository,
        branch=branch,
        environment=environment,
        status='pending',
        progress=0,
        deployment_id=deployment_id,
        deployment_url=deployment_url
    )
    
    db.session.add(new_deployment)
    db.session.commit()
    
    generate_initial_logs(new_deployment)
    
    # Start deployment simulation in background
    thread = threading.Thread(target=run_deployment_simulation, args=(deployment_id,))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "message": f"Deployment started for {repository}",
        "deployment_id": deployment_id,
        "repository": repository,
        "branch": branch,
        "environment": environment,
        "status": "pending",
        "deployment_url": deployment_url,
        "repo_name": repository.split('/')[-1]
    })

# -------------------------
# Main Routes
# -------------------------

@app.route('/status/<deployment_id>')
def deployment_status(deployment_id):
    """Individual deployment status page"""
    if "user_id" not in session:
        flash("Please log in first", "warning")
        return redirect(url_for("login"))
    
    # Verify the deployment belongs to the user
    deployment = Deployment.query.filter_by(deployment_id=deployment_id).first()
    if not deployment or deployment.user_id != session['user_id']:
        flash("Deployment not found", "error")
        return redirect(url_for("dashboard"))
    
    return render_template("status.html", deployment_id=deployment_id)

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please log in first", "warning")
        return redirect(url_for("login"))
    return render_template("dashboard.html", username=session.get("username"))

@app.route("/settings")
def settings():
    if "user_id" not in session:
        flash("Please log in first", "warning")
        return redirect(url_for("login"))
    
    user = User.query.get(session['user_id'])
    if not user:
        flash("User not found", "error")
        return redirect(url_for("login"))
    
    return render_template("settings.html", 
                         username=session.get("username"),
                         email=session.get("email"),
                         github_username=session.get("github_username"))

@app.route('/api/settings/profile', methods=['GET', 'PUT'])
def api_settings_profile():
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({"error": "User not found"}), 404

    if request.method == 'GET':
        name_parts = user.username.split(' ', 1)
        first_name = name_parts[0] if name_parts else "User"
        last_name = name_parts[1] if len(name_parts) > 1 else "GitHub"
        
        return jsonify({
            "first_name": first_name,
            "last_name": last_name,
            "email": user.email,
            "phone": user.phoneNumber or "",
            "github_username": session.get('github_username', user.username)
        })
    
    elif request.method == 'PUT':
        data = request.get_json()
        try:
            if 'first_name' in data and 'last_name' in data:
                user.username = f"{data['first_name']} {data['last_name']}"
            if 'phone' in data:
                user.phoneNumber = data['phone']
            
            db.session.commit()

            if 'first_name' in data and 'last_name' in data:
                session['username'] = user.username
            
            return jsonify({
                "success": True,
                "message": "Profile updated successfully",
                "user": {
                    "first_name": data.get('first_name'),
                    "last_name": data.get('last_name'),
                    "email": user.email,
                    "phone": user.phoneNumber,
                    "github_username": session.get('github_username', user.username)
                }
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 400

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out", "info")
    return redirect(url_for("landing"))

@app.route('/logs')
def logs():
    if "user_id" not in session:
        flash("Please log in first", "warning")
        return redirect(url_for("login"))
    return render_template('logs.html')

@app.route('/status')
def status():
    if "user_id" not in session:
        flash("Please log in first", "warning")
        return redirect(url_for("login"))
    return render_template('status.html')

@app.route('/error')
def error():
    return render_template('404.html')


@app.route('/docs')
def docs():
    return render_template('docs.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# Health check endpoint
@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

# Initialize database
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
