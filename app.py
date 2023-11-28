# app.py
# This file serves as the main driver for the Flask Server

from datetime import datetime
from flask import Flask, render_template, url_for, flash, redirect, jsonify, session, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, func, desc
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON
from authlib.integrations.flask_client import OAuth
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv

# .env file initalization
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)   # for Flask
oauth = OAuth(app)      # for Auth0
app.secret_key = env.get("APP_SECRET_KEY")   # for cookies and session management
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hackernews.db'   # for SQLite database
db = SQLAlchemy(app)    # for SQLite

# DATABASES AND SQL
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
    __tablename__ = 'news_items'

    id = Column(Integer, primary_key=True)
    by = Column(String(80), nullable=False)
    descendants = Column(Integer)
    kids = Column(JSON)  # Storing list of child comments/story IDs as JSON
    score = Column(Integer, default=0)
    time = Column(DateTime, default=datetime.utcnow)
    title = Column(String(250), nullable=False)
    type = Column(String(20), nullable=False)
    url = Column(String(500))  # Add this if you want to include the URL field from Hacker News API

    # Relationship for likes
    likers = relationship('User', secondary=user_newsitem_likes, back_populates='liked_news_items')

    # Relationship for dislikes
    dislikers = relationship('User', secondary=user_newsitem_dislikes, back_populates='disliked_news_items')

    def __repr__(self):
        return f"NewsItem('{self.title}', '{self.by}', '{self.time}', 'Score: {self.score}')"

class User(db.Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(20), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    image_file = Column(String(20), nullable=False, default='default.jpg')
    sub = Column(String(255), unique=True, nullable=True)  # Auth0 subject identifier
    auth0_profile = Column(JSON, nullable=True)  # Store additional Auth0 profile information if needed


    # Relationship for likes
    liked_news_items = relationship('NewsItem', secondary=user_newsitem_likes, back_populates='likers')

    # Relationship for dislikes
    disliked_news_items = relationship('NewsItem', secondary=user_newsitem_dislikes, back_populates='dislikers')

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"

# More Auth0 configurations
oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

@app.route("/")
@app.route("/home")
def home():
    # Retrieve the page number from the query parameters, default to 1 if not provided
    page = request.args.get('page', 1, type=int)

    # Define the number of posts per page
    posts_per_page = 10  # You can adjust this based on your preference

    # Subquery to count likes 
    likes_subquery = db.session.query(
        user_newsitem_likes.c.news_item_id,
        func.count('*').label('likes_count')
    ).group_by(user_newsitem_likes.c.news_item_id).subquery()

    # Subquery to count dislikes
    dislikes_subquery = db.session.query(
        user_newsitem_dislikes.c.news_item_id,
        func.count('*').label('dislikes_count')
    ).group_by(user_newsitem_dislikes.c.news_item_id).subquery()

    # Query the paginated posts using SQLAlchemy's paginate method
    posts = NewsItem.query.outerjoin(
        likes_subquery, NewsItem.id == likes_subquery.c.news_item_id
    ).outerjoin(
        dislikes_subquery, NewsItem.id == dislikes_subquery.c.news_item_id
    ).order_by(
        desc(NewsItem.time),  # Sort by time in descending order (most recent first)
        desc(func.coalesce(likes_subquery.c.likes_count, 0) + func.coalesce(dislikes_subquery.c.dislikes_count, 0))  # Sort by total likes and dislikes
    ).paginate(page=page, per_page=posts_per_page, error_out=False)

    return render_template("home.html", session=session.get('user'), posts=posts)


@app.route("/profile")
def profile():
    # Check if the user is logged in
    if "user" in session:
        # Retrieve the authenticated user from the session
        user_sub = session["user"]["sub"]
        user = User.query.filter_by(sub=user_sub).first()

        return render_template("profile.html", user=user)
    else:
        # Redirect to the login page if the user is not logged in
        return redirect(url_for("login"))

@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

# Update the callback route
@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()

    # Ensure that the userinfo URL includes the correct scheme (https://)
    userinfo_url = f'https://{env.get("AUTH0_DOMAIN")}/userinfo'
    
    resp = oauth.auth0.get(userinfo_url)
    
    userinfo = resp.json()
    user_sub = userinfo["sub"]  # Auth0 subject identifier
    
    # Check if the user already exists in your database
    user = User.query.filter_by(sub=user_sub).first()

    if not user:
        # Create a new user in the database
        user = User(
            username=userinfo["nickname"],  # or any other Auth0 user attribute
            email=userinfo["email"],
            sub=user_sub,
            auth0_profile=userinfo,  # Store additional Auth0 profile information if needed
        )
        db.session.add(user)
        db.session.commit()

    session["user"] = userinfo  # Store Auth0 user data in the session
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

@app.route('/newsfeeed', methods=['GET'])
def news_feed():
    # Retrieve the latest 'k' news items from the database
    k = 30
    
    # Subquery to count likes 
    likes_subquery = db.session.query(
        user_newsitem_likes.c.news_item_id,
        func.count('*').label('likes_count')
    ).group_by(user_newsitem_likes.c.news_item_id).subquery()

    # Subquery to count dislikes
    dislikes_subquery = db.session.query(
        user_newsitem_dislikes.c.news_item_id,
        func.count('*').label('dislikes_count')
    ).group_by(user_newsitem_dislikes.c.news_item_id).subquery()

    # Query news items and join with likes and dislikes subqueries to sort
    latest_news_items = db.session.query(
        NewsItem,
        func.coalesce(likes_subquery.c.likes_count, 0).label('total_likes'),
        func.coalesce(dislikes_subquery.c.dislikes_count, 0).label('total_dislikes')
    ).outerjoin(likes_subquery, NewsItem.id == likes_subquery.c.news_item_id) \
    .outerjoin(dislikes_subquery, NewsItem.id == dislikes_subquery.c.news_item_id) \
    .order_by(
        NewsItem.time.desc(),
        (func.coalesce(likes_subquery.c.likes_count, 0) + func.coalesce(dislikes_subquery.c.dislikes_count, 0)).desc()
    ).limit(k).all()

    # Convert the result into a list of dictionaries
    news_items_list = [
        {
            'id': item.NewsItem.id,
            'by': item.NewsItem.by,
            'descendants': item.NewsItem.descendants,
            'kids': item.NewsItem.kids,
            'score': item.NewsItem.score,
            'time': item.NewsItem.time.isoformat(),  # Convert datetime to ISO format
            'title': item.NewsItem.title,
            'type': item.NewsItem.type,
            'url': item.NewsItem.url,
            'total_likes': item.total_likes,  # Aggregate like count
            'total_dislikes': item.total_dislikes,  # Aggregate dislike count
            # Add any more fields you want to include in the JSON response
        } 
        for item in latest_news_items
    ]

    # Respond with the JSON representation of the news items
    return jsonify(news_items_list)

# Add routes for handling likes and dislikes
@app.route("/like/<int:news_item_id>", methods=["POST"])
def like(news_item_id):
    # Retrieve the authenticated user from the session
    user_sub = session["user"]["sub"]
    user = User.query.filter_by(sub=user_sub).first()

    # Retrieve the news item to be liked
    news_item = NewsItem.query.get(news_item_id)

    # Check if the user has already liked this post
    if user in news_item.likers:
        return jsonify({"message": "You have already liked this post"})

    # Add the user to the likers relationship
    news_item.likers.append(user)
    db.session.commit()

    return jsonify({"message": "Liked successfully"})

@app.route("/dislike/<int:news_item_id>", methods=["POST"])
def dislike(news_item_id):
    # Retrieve the authenticated user from the session
    user_sub = session["user"]["sub"]
    user = User.query.filter_by(sub=user_sub).first()

    # Retrieve the news item to be disliked
    news_item = NewsItem.query.get(news_item_id)

    # Check if the user has already disliked this post
    if user in news_item.dislikers:
        return jsonify({"message": "You have already disliked this post"})

    # Add the user to the dislikers relationship
    news_item.dislikers.append(user)
    db.session.commit()

    return jsonify({"message": "Disliked successfully"})

if __name__ == '__main__':
    app.run(debug=True)