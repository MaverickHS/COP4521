from datetime import datetime
from flask import Flask, render_template, url_for, flash, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from forms import RegistrationForm, LoginForm
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)   # for Flask
oauth = OAuth(app)      # for Auth0
app.config['SECRET_KEY'] = 'vM5iNI2GN2FWC96NHBkurcHd3Ly56N51'   # for Flask security and cookies
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
    password = Column(String(60), nullable=False)

    # Relationship for likes
    liked_news_items = relationship('NewsItem', secondary=user_newsitem_likes, back_populates='likers')

    # Relationship for dislikes
    disliked_news_items = relationship('NewsItem', secondary=user_newsitem_dislikes, back_populates='dislikers')

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html')


@app.route("/about")
def about():
    return render_template('about.html', title='About')

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('home'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.email.data == 'admin@blog.com' and form.password.data == 'password':
            flash('You have been logged in!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/newsfeeed', methods=['GET'])
@app.route('/newsfeed', methods=['GET'])
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

if __name__ == '__main__':
    app.run(debug=True)