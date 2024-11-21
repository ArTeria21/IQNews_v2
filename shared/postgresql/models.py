from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from shared.postgresql.core import Base

from datetime import datetime
from uuid import uuid4

class RSS_feed(Base):
    __tablename__ = 'rss_feed'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    url: Mapped[str] = mapped_column(String(255), nullable=False)

    rss_posts = relationship("Post", back_populates="feed")
    subscriptions = relationship("Subscription", back_populates="feed")

    def as_dict(self):
        return {
            'id': str(self.id),
            'url': self.url
        }

class Post(Base):
    __tablename__ = 'rss_posts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String, nullable=False)
    link = Column(String, nullable=False)
    summary = Column(String, nullable=False)
    pub_date = Column(DateTime, nullable=False)
    
    # Внешний ключ на RSS_feed
    feed_id = Column(UUID(as_uuid=True), ForeignKey('rss_feed.id'))
    feed = relationship("RSS_feed", back_populates="rss_posts")

    def as_dict(self):
        return {
            'id': str(self.id),
            'title': self.title,
            'link': self.link,
            'summary': self.summary,
            'pub_date': str(self.pub_date)
        }

class User(Base):
    __tablename__ = 'users'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    username = Column(String, unique=True, nullable=False)
    registration_date = Column(DateTime, default=datetime.now, nullable=False)

    # Связь с подписками, удаление всех подписок при удалении пользователя
    subscriptions = relationship('Subscription', back_populates='user', cascade="all, delete-orphan")

    def as_dict(self):
        return {
            'id': str(self.id),
            'username': self.username,
            'registration_date': str(self.registration_date)
        }

class Subscription(Base):
    __tablename__ = 'subscriptions'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    feed_id = Column(UUID(as_uuid=True), ForeignKey('rss_feed.id'), nullable=False)

    user = relationship('User', back_populates='subscriptions')
    feed = relationship('RSS_feed', back_populates='subscriptions')

    def as_dict(self):
        return {
            'id': str(self.id),
            'user' : self.user.as_dict(),
            'feed' : self.feed.as_dict()
        }