"""
Models for the rss manager service.
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Index, ForeignKey, UUID, URL
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4

from config import Base

class RssFeed(Base):
    """Модель RSS-потока."""
    __tablename__ = 'rss_feeds'
    feed_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    url = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    last_post_date = Column(DateTime, nullable=True)
    posts = relationship('RssPost', back_populates='feed')
    subscriptions = relationship('Subscription', back_populates='feed')

    def __repr__(self):
        return f'<RssFeed {self.url}:{self.feed_id}>'
    
    def to_dict(self):
        return {
            'feed_id': self.feed_id,
            'url': self.url,
            'created_at': self.created_at,
            'last_post_date': self.last_post_date,
        }

class RssPost(Base):
    """Модель RSS-поста."""
    __tablename__ = 'rss_posts'
    post_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    feed_id = Column(UUID(as_uuid=True), ForeignKey('rss_feeds.feed_id'))
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=True)
    link = Column(String(255), nullable=False)
    published_at = Column(DateTime, nullable=False)
    feed = relationship('RssFeed', back_populates='posts')
    
    def __repr__(self):
        return f'<RssPost {self.title}:{self.post_id}>'
    
    def to_dict(self):
        return {
            'post_id': self.post_id,
            'feed_id': self.feed_id,
            'title': self.title,
            'content': self.content,
            'link': self.link,
            'published_at': self.published_at,
        }

class Subscription(Base):
    """Подписка пользователя на RSS-поток."""
    __tablename__ = 'subscriptions'
    subscription_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    feed_id = Column(UUID(as_uuid=True), ForeignKey('rss_feeds.feed_id'))
    feed = relationship('RssFeed', back_populates='subscriptions')
    
    def __repr__(self):
        return f'<Subscription {self.user_id}:{self.subscription_id}>'
    
    def to_dict(self):
        return {
            'subscription_id': self.subscription_id,
            'user_id': self.user_id,
            'created_at': self.created_at,
            'feed_id': self.feed_id,
        }