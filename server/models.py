"""
Database Models for Snake Survival
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class LeaderboardEntry(db.Model):
    """Global leaderboard entry"""
    __tablename__ = 'leaderboard'

    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False, index=True)
    length = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.String(20), nullable=False, index=True)
    mode = db.Column(db.String(10), nullable=False, index=True)  # 'ghost' or 'normal'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'score': self.score,
            'length': self.length,
            'difficulty': self.difficulty,
            'mode': self.mode,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<LeaderboardEntry {self.score} - {self.difficulty} - {self.mode}>'
