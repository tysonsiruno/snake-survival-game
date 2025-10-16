"""
Snake Survival - Flask Backend
Serves the game and provides global leaderboard API
"""

import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='../static', static_url_path='')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database Configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = 'postgresql://' + DATABASE_URL[11:]

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///snake_survival.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
from server.models import db, LeaderboardEntry

db.init_app(app)

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
