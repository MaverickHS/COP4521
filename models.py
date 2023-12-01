"""
This module defines the database models for the application.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import relationship
from config import db

# Association table for the many-to-many relationship between users and news items for likes
user_newsitem_likes = db.Table('user_newsitem_likes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('news_item_id', db.Integer, db.ForeignKey('news_items.id'))
)

# Association table for the many-to-many relationship between users and news items for dislikes
user_newsitem_dislikes = db.Table('user_newsitem_dislikes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('news_item_id', db.Integer, db.ForeignKey('news_items.id'))
)

class NewsItem(db.Model):
    """
    Model representing a news item.
    """
    __tablename__ = 'news_items'

    id = Column(Integer, primary_key=True)
    by = Column(String(80), nullable=False)
    descendants = Column(Integer)
    kids = Column(JSON)  # Storing list of child comments/story IDs as JSON
    score = Column(Integer, default=0)
    time = Column(DateTime, default=datetime.utcnow)
    title = Column(String(250), nullable=False)
    type = Column(String(20), nullable=False)
    url = Column(String(500))  # URL field from Hacker News API

    # Relationship for likes
    likers = relationship('User', secondary=user_newsitem_likes,
                          back_populates='liked_news_items')

    # Relationship for dislikes
    dislikers = relationship('User', secondary=user_newsitem_dislikes,
                             back_populates='disliked_news_items')

    def __repr__(self):
        return f"NewsItem('{self.title}', '{self.by}', '{self.time}', " \
               f"'Score: {self.score}')"


class User(db.Model):
    """
    Model representing a user.
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(20), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    image_file = Column(String(20), nullable=False, default='default.jpg')
    sub = Column(String(255), unique=True, nullable=True)  # Auth0 subject identifier
    auth0_profile = Column(JSON, nullable=True)  # Store Auth0 profile information

    # Relationship for likes
    liked_news_items = relationship('NewsItem', secondary=user_newsitem_likes,
                                    back_populates='likers')

    # Relationship for dislikes
    disliked_news_items = relationship('NewsItem', secondary=user_newsitem_dislikes,
                                       back_populates='dislikers')

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"

# pylint: disable=too-few-public-methods
