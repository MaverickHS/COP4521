from flask import Blueprint, request, jsonify, session, url_for, render_template, redirect, flash
from models import NewsItem, User, user_newsitem_likes, user_newsitem_dislikes
from sqlalchemy import func, desc
from config import app, db, oauth
from os import environ as env
from urllib.parse import quote_plus, urlencode
import os

ADMIN_PASSWORD = "LinodeServer123" # for Admin Verification

main = Blueprint('main', __name__)

@main.route("/")
@main.route("/home")
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


@main.route("/profile")
def profile():
    # Check if the user is logged in
    if "user" in session:
        # Retrieve the authenticated user from the session
        user_sub = session["user"]["sub"]
        user = User.query.filter_by(sub=user_sub).first()

        return render_template("profile.html", user=user)
    else:
        # Redirect to the login page if the user is not logged in
        return redirect(url_for("main.login"))

@main.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("main.callback", _external=True)
    )

# Update the callback route
@main.route("/callback", methods=["GET", "POST"])
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

@main.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("main.home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

@main.route('/newsfeeed', methods=['GET'])
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
@main.route("/like/<int:news_item_id>", methods=["POST"])
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

@main.route("/dislike/<int:news_item_id>", methods=["POST"])
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

@main.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form['password']
        if password == ADMIN_PASSWORD:
            session['is_admin'] = True
            flash('You have been logged in as admin!', 'success')
            return redirect(url_for('main.admin_dashboard'))
        else:
            flash('Invalid password', 'danger')

    return render_template('admin_login.html')  # You need to create this template

@main.route("/admin")
def admin_dashboard():
    if not session.get('is_admin'):
        # If the user is not confirmed as admin, redirect to the admin login page
        flash('Please log in to access the admin dashboard.', 'warning')
        return redirect(url_for('main.admin_login'))

    news_items = NewsItem.query.all()
    return render_template("admin.html", posts=news_items)

@main.route("/admin/delete-news-item/<int:news_item_id>", methods=["POST"])
def delete_news_item(news_item_id):
    if not session.get('is_admin'):
        flash('Unauthorized access. Admins only.', 'danger')
        return redirect(url_for('main.admin_login'))

    news_item = NewsItem.query.get_or_404(news_item_id)
    news_item.likers.clear()
    news_item.dislikers.clear()
    db.session.delete(news_item)
    db.session.commit()

    flash('News item has been deleted', 'success')
    return redirect(url_for('main.admin_dashboard'))