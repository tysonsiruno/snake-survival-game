"""
Database Models for Snake Survival Game
Includes user authentication, sessions, and game history
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
import secrets

db = SQLAlchemy()


class TokenBlacklist(db.Model):
    """
    Blacklist for invalidated JWT tokens
    Stores token JTI (JWT ID) to prevent use after logout/password change
    """
    __tablename__ = 'token_blacklist'

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), unique=True, nullable=False, index=True)
    token_type = db.Column(db.String(10), nullable=False)  # 'access' or 'refresh'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    blacklisted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.String(100))  # 'logout', 'password_change', 'security'

    @staticmethod
    def is_blacklisted(jti):
        """Check if a token JTI is blacklisted"""
        token = TokenBlacklist.query.filter_by(jti=jti).first()
        return token is not None

    @staticmethod
    def blacklist_token(jti, token_type, user_id, expires_at, reason='logout'):
        """Add a token to the blacklist"""
        blacklisted = TokenBlacklist(
            jti=jti,
            token_type=token_type,
            user_id=user_id,
            expires_at=expires_at,
            reason=reason
        )
        db.session.add(blacklisted)
        return blacklisted

    @staticmethod
    def cleanup_expired():
        """Remove expired blacklisted tokens"""
        now = datetime.now(timezone.utc)
        deleted = TokenBlacklist.query.filter(TokenBlacklist.expires_at < now).delete()
        db.session.commit()
        return deleted


class User(db.Model):
    """User account model for Snake Survival Game"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_guest = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Snake game specific fields
    favorite_difficulty = db.Column(db.String(20), default='medium')
    snake_color = db.Column(db.String(7), default='#00ff00')  # Hex color
    total_games_played = db.Column(db.Integer, default=0)
    total_deaths = db.Column(db.Integer, default=0)
    total_playtime_seconds = db.Column(db.Integer, default=0)
    highest_score = db.Column(db.Integer, default=0)
    highest_length = db.Column(db.Integer, default=0)
    total_apples_dodged = db.Column(db.Integer, default=0)
    total_powerups_collected = db.Column(db.Integer, default=0)

    # Security fields
    account_status = db.Column(db.String(20), default='active')  # active, suspended, deleted
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)

    # Relationships
    sessions = db.relationship('Session', backref='user', lazy=True, cascade='all, delete-orphan')
    game_history = db.relationship('LeaderboardEntry', backref='user', lazy=True)
    password_tokens = db.relationship('PasswordResetToken', backref='user', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        """Convert user to dictionary (exclude sensitive data)"""
        total_games = self.total_games_played if self.total_games_played is not None else 0

        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'snake_color': self.snake_color,
            'favorite_difficulty': self.favorite_difficulty,
            'total_games_played': total_games,
            'total_deaths': self.total_deaths if self.total_deaths is not None else 0,
            'total_playtime_seconds': self.total_playtime_seconds if self.total_playtime_seconds is not None else 0,
            'highest_score': self.highest_score if self.highest_score is not None else 0,
            'highest_length': self.highest_length if self.highest_length is not None else 0,
            'total_apples_dodged': self.total_apples_dodged if self.total_apples_dodged is not None else 0,
            'total_powerups_collected': self.total_powerups_collected if self.total_powerups_collected is not None else 0,
            'survival_rate': round((total_games - self.total_deaths) / total_games * 100 if total_games > 0 else 0, 1)
        }


class PasswordResetToken(db.Model):
    """Password reset tokens"""
    __tablename__ = 'password_reset_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used_at = db.Column(db.DateTime)
    ip_address = db.Column(db.String(50))

    @staticmethod
    def generate_token():
        """Generate a secure random token"""
        return secrets.token_urlsafe(32)

    def is_expired(self):
        """Check if token is expired"""
        if self.expires_at is None:
            return True
        now = datetime.now(timezone.utc) if self.expires_at.tzinfo else datetime.utcnow()
        return now > self.expires_at

    def is_used(self):
        """Check if token has been used"""
        return self.used_at is not None


class Session(db.Model):
    """User sessions for JWT refresh tokens"""
    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    session_token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    refresh_token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_activity = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    device_id = db.Column(db.String(100))
    device_name = db.Column(db.String(100))
    device_type = db.Column(db.String(50))  # 'desktop', 'mobile', 'tablet'

    def is_expired(self):
        """Check if session is expired"""
        if self.expires_at is None:
            return True
        now = datetime.now(timezone.utc) if self.expires_at.tzinfo else datetime.utcnow()
        return now > self.expires_at

    def to_dict(self):
        """Convert session to dictionary for user viewing"""
        return {
            'id': self.id,
            'device_name': self.device_name or 'Unknown Device',
            'device_type': self.device_type or 'unknown',
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'is_active': self.is_active,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

    @staticmethod
    def cleanup_expired():
        """Remove expired sessions from database"""
        now = datetime.now(timezone.utc)
        deleted = Session.query.filter(Session.expires_at < now).delete()
        db.session.commit()
        return deleted

    @staticmethod
    def cleanup_inactive(days=90):
        """Remove old inactive sessions"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        deleted = Session.query.filter(Session.last_activity < cutoff).delete()
        db.session.commit()
        return deleted

    @staticmethod
    def invalidate_all_for_user(user_id):
        """Invalidate all sessions for a user"""
        Session.query.filter_by(user_id=user_id).update({'is_active': False})
        db.session.commit()


class LeaderboardEntry(db.Model):
    """Game history and leaderboard entries"""
    __tablename__ = 'leaderboard_entries'

    # Composite indexes for common queries
    __table_args__ = (
        db.Index('idx_leaderboard_mode', 'mode', 'difficulty', 'score'),
        db.Index('idx_leaderboard_global', 'score', 'length'),
        db.Index('idx_user_games', 'user_id', 'created_at'),
        db.Index('idx_recent_games', 'created_at', 'score'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), index=True)
    username = db.Column(db.String(50), index=True)  # For guest players and deleted accounts
    score = db.Column(db.Integer, nullable=False, index=True)
    length = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.String(20), nullable=False, index=True)
    mode = db.Column(db.String(10), nullable=False, index=True)  # 'ghost' or 'normal'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Additional game stats
    apples_dodged = db.Column(db.Integer, default=0)
    powerups_collected = db.Column(db.Integer, default=0)
    shields_used = db.Column(db.Integer, default=0)
    freeze_time_total = db.Column(db.Integer, default=0)  # Seconds

    def to_dict(self):
        """Convert entry to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'score': self.score,
            'length': self.length,
            'difficulty': self.difficulty,
            'mode': self.mode,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'apples_dodged': self.apples_dodged,
            'powerups_collected': self.powerups_collected,
            'shields_used': self.shields_used,
            'freeze_time_total': self.freeze_time_total
        }


class SecurityAuditLog(db.Model):
    """Security audit log for tracking important events"""
    __tablename__ = 'security_audit_log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    action = db.Column(db.String(100), nullable=False, index=True)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.Text)
    success = db.Column(db.Boolean)
    details = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    @staticmethod
    def log_action(user_id, action, success, ip_address=None, user_agent=None, details=None):
        """Log a security action"""
        log_entry = SecurityAuditLog(
            user_id=user_id,
            action=action,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )
        db.session.add(log_entry)
        return log_entry
