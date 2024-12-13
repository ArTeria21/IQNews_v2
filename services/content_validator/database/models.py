"""
Models for the user manager service.
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Index
from datetime import datetime

from config import Base


class User(Base):
    """Модель пользователя."""
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    is_pro = Column(Boolean, nullable=False, default=False)
    preferences = Column(Text, nullable=True)
    keywords = Column(Text, nullable=True)

    # Add indexes
    __table_args__ = (
        Index('ix_users_user_id', 'user_id'),
        Index('ix_users_username', 'username'),
    )
    
    def __repr__(self):
        return f'<User {self.username}:{self.user_id}>'
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'preferences': self.preferences,
            'keywords': self.keywords,
            'is_pro': self.is_pro,
        }