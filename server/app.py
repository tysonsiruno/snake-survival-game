"""
Snake Survival - Flask Backend
Serves the game and provides global leaderboard API
"""

import os
import secrets
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='../static', static_url_path='')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database Configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Use SQLite as fallback, but with absolute path for Railway
if DATABASE_URL:
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    db_path = os.path.join(os.getcwd(), 'snake_survival.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# Initialize extensions
CORS(app, origins=os.environ.get('CORS_ORIGINS', '*'))

# Rate limiter
rate_limit_storage = os.environ.get('REDIS_URL', 'memory://')
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=rate_limit_storage
)

# Initialize database
from server.models import db, User, Session, LeaderboardEntry, PasswordResetToken, SecurityAuditLog, TokenBlacklist

db.init_app(app)

# Import authentication utilities
from server.auth import (
    hash_password, verify_password, validate_password, validate_username, validate_email,
    generate_access_token, generate_refresh_token, decode_access_token, decode_refresh_token,
    token_required, get_client_ip, get_user_agent, sanitize_input,
    blacklist_token, invalidate_all_user_sessions, simulate_operation_delay
)

# Create database tables
with app.app_context():
    db.create_all()
    print("Database tables created successfully!")

# Security headers middleware
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

# Routes
@app.route('/')
def index():
    """Serve the game"""
    return send_from_directory('../', 'index.html')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

# ============================================================================
# AUTHENTICATION API
# ============================================================================

@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("5 per hour")
def register():
    """User registration"""
    data = request.json
    username = sanitize_input(data.get('username', ''), 20)
    email = sanitize_input(data.get('email', ''), 255).lower()
    password = data.get('password', '')

    # Validation
    valid, msg = validate_username(username)
    if not valid:
        return jsonify({'success': False, 'message': msg}), 400

    valid, msg = validate_email(email)
    if not valid:
        return jsonify({'success': False, 'message': msg}), 400

    valid, msg = validate_password(password)
    if not valid:
        return jsonify({'success': False, 'message': msg}), 400

    # Check if username or email already exists
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Username already taken'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email already registered'}), 400

    # Create user
    try:
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password)
        )
        db.session.add(user)
        db.session.commit()

        SecurityAuditLog.log_action(user.id, 'register', True, get_client_ip(), get_user_agent())
        db.session.commit()

        return jsonify({'success': True, 'message': 'Registration successful! You can now log in.', 'user_id': user.id})
    except Exception as e:
        db.session.rollback()
        print(f'Registration error occurred')
        return jsonify({'success': False, 'message': 'Registration failed. Please try again.'}), 500

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("10 per 15 minutes")
def login():
    """User login"""
    data = request.json
    username_or_email_raw = data.get('username_or_email', '').strip()
    password = data.get('password', '')
    remember_me = data.get('remember_me', False)

    # Sanitize but don't lowercase username (only lowercase email)
    username_or_email = sanitize_input(username_or_email_raw, 255)

    # Try case-sensitive username first, then case-insensitive email
    user = User.query.filter(User.username == username_or_email).first()
    if not user:
        # Try as email (case-insensitive)
        user = User.query.filter(User.email == username_or_email.lower()).first()

    if not user or not verify_password(password, user.password_hash):
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                import random
                lockout_minutes = random.randint(15, 20)
                user.locked_until = datetime.utcnow() + timedelta(minutes=lockout_minutes)
            db.session.commit()
        SecurityAuditLog.log_action(user.id if user else None, 'login', False, get_client_ip(), get_user_agent())
        db.session.commit()
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        remaining = int((user.locked_until - datetime.utcnow()).total_seconds() / 60)
        return jsonify({'success': False, 'message': f'Account locked. Try again in {remaining} minutes.'}), 403

    # Reset failed attempts and create session
    try:
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        db.session.commit()

        # Generate tokens
        access_token = generate_access_token(user.id, user.username)
        refresh_token_str = secrets.token_urlsafe(32)

        session = Session(
            user_id=user.id,
            session_token=secrets.token_urlsafe(32),
            refresh_token=refresh_token_str,
            expires_at=datetime.utcnow() + (timedelta(days=30) if remember_me else timedelta(days=7)),
            ip_address=get_client_ip(),
            user_agent=get_user_agent()
        )
        db.session.add(session)
        db.session.commit()

        SecurityAuditLog.log_action(user.id, 'login', True, get_client_ip(), get_user_agent())
        db.session.commit()

        return jsonify({
            'success': True,
            'access_token': access_token,
            'refresh_token': refresh_token_str,
            'user': user.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        print(f'Login session creation error occurred')
        return jsonify({'success': False, 'message': 'Login failed. Please try again.'}), 500

@app.route('/api/auth/logout', methods=['POST'])
@token_required
def logout(current_user):
    """Logout user"""
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or ' ' not in auth_header:
            return jsonify({'success': False, 'message': 'Invalid authorization header'}), 401

        parts = auth_header.split(' ')
        if len(parts) != 2:
            return jsonify({'success': False, 'message': 'Invalid authorization header format'}), 401

        token = parts[1]

        # Blacklist the access token
        blacklist_token(token, reason='logout')

        # Invalidate current session
        recent_session = Session.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).order_by(Session.created_at.desc()).first()

        if recent_session:
            db.session.delete(recent_session)
            db.session.commit()

        SecurityAuditLog.log_action(current_user.id, 'logout', True, get_client_ip(), get_user_agent())
        db.session.commit()
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    except Exception as e:
        db.session.rollback()
        print(f'Logout error occurred')
        return jsonify({'success': False, 'message': 'Logout failed. Please try again.'}), 500

@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """Get current user info"""
    return jsonify({'success': True, 'user': current_user.to_dict()})

@app.route('/api/auth/refresh', methods=['POST'])
def refresh_token():
    """Refresh access token using refresh token"""
    auth_header = request.headers.get('Authorization', '')

    if not auth_header or ' ' not in auth_header:
        return jsonify({'success': False, 'message': 'Refresh token required'}), 401

    parts = auth_header.split(' ')
    if len(parts) != 2:
        return jsonify({'success': False, 'message': 'Invalid authorization header format'}), 401

    refresh_token_str = parts[1]

    if not refresh_token_str:
        return jsonify({'success': False, 'message': 'Refresh token required'}), 401

    # Find session with this refresh token
    session = Session.query.filter_by(refresh_token=refresh_token_str, is_active=True).first()

    if not session or session.is_expired():
        return jsonify({'success': False, 'message': 'Invalid or expired refresh token'}), 401

    # Get user
    user = User.query.get(session.user_id)
    if not user or user.account_status != 'active':
        return jsonify({'success': False, 'message': 'User not found or inactive'}), 401

    try:
        access_token = generate_access_token(user.id, user.username)

        # Rotate refresh token for better security
        new_refresh_token = secrets.token_urlsafe(32)
        session.refresh_token = new_refresh_token
        db.session.commit()

        return jsonify({
            'success': True,
            'access_token': access_token,
            'refresh_token': new_refresh_token
        })
    except Exception as e:
        db.session.rollback()
        print(f'Token refresh error occurred')
        return jsonify({'success': False, 'message': 'Token refresh failed. Please try again.'}), 500

# ============================================================================
# LEADERBOARD API
# ============================================================================

@app.route('/api/leaderboard/global', methods=['GET'])
def get_global_leaderboard():
    """Get global leaderboard"""
    mode = request.args.get('mode', 'all')  # 'ghost', 'normal', or 'all'
    difficulty = request.args.get('difficulty', 'all')
    limit = min(int(request.args.get('limit', 50)), 100)

    query = LeaderboardEntry.query

    if mode != 'all':
        query = query.filter_by(mode=mode)

    if difficulty != 'all':
        query = query.filter_by(difficulty=difficulty)

    leaderboard = query.order_by(LeaderboardEntry.score.desc()).limit(limit).all()

    return jsonify({
        "leaderboard": [entry.to_dict() for entry in leaderboard]
    })

@app.route('/api/leaderboard/submit', methods=['POST'])
@limiter.limit("100 per hour")
def submit_score():
    """Submit score to global leaderboard"""
    data = request.json

    # Validate inputs
    try:
        score = int(data.get('score', 0))
        length = int(data.get('length', 0))
        difficulty = data.get('difficulty', 'easy')
        mode = data.get('mode', 'normal')  # 'ghost' or 'normal'

        # Sanity checks
        if score < 0 or score > 100000:
            return jsonify({"success": False, "message": "Invalid score"}), 400
        if length < 1 or length > 50:
            return jsonify({"success": False, "message": "Invalid length"}), 400
        if difficulty not in ['easy', 'medium', 'hard', 'impossible', 'hacker']:
            return jsonify({"success": False, "message": "Invalid difficulty"}), 400
        if mode not in ['ghost', 'normal']:
            return jsonify({"success": False, "message": "Invalid mode"}), 400

    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid input"}), 400

    try:
        # Create leaderboard entry
        entry = LeaderboardEntry(
            score=score,
            length=length,
            difficulty=difficulty,
            mode=mode
        )
        db.session.add(entry)
        db.session.commit()

        return jsonify({"success": True, "entry": entry.to_dict()})
    except Exception as e:
        db.session.rollback()
        print(f'Leaderboard submission error: {e}')
        return jsonify({"success": False, "message": "Failed to submit score"}), 500

@app.route('/api/leaderboard/stats', methods=['GET'])
def get_stats():
    """Get global statistics"""
    total_games = LeaderboardEntry.query.count()
    ghost_games = LeaderboardEntry.query.filter_by(mode='ghost').count()
    normal_games = LeaderboardEntry.query.filter_by(mode='normal').count()

    # Get top score
    top_entry = LeaderboardEntry.query.order_by(LeaderboardEntry.score.desc()).first()
    top_score = top_entry.score if top_entry else 0

    # Average scores
    avg_score_query = db.session.query(db.func.avg(LeaderboardEntry.score)).scalar()
    avg_score = int(avg_score_query) if avg_score_query else 0

    return jsonify({
        "total_games": total_games,
        "ghost_games": ghost_games,
        "normal_games": normal_games,
        "top_score": top_score,
        "average_score": avg_score
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
