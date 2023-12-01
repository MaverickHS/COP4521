"""
hackernews.py -- Module for fetching top Hacker News stories and saving them into the database.
"""

from datetime import datetime
import requests
from sqlalchemy.exc import IntegrityError  # Import the class correctly
from models import NewsItem
from config import app, db


REQUEST_TIMEOUT = 10  # Timeout for requests in seconds

def get_top_story_ids():
    """ Retrieves the top story IDs from the Hacker News API. """
    url = 'https://hacker-news.firebaseio.com/v0/topstories.json?print=pretty'
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    if response.status_code == 200:
        return response.json()  # Returns a list of IDs
    print('Failed to fetch top stories')
    return []

def get_story_details(story_id):
    """ Retrieves the details of a story by its ID from the Hacker News API. """
    url = f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json?print=pretty'
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    if response.status_code == 200:
        return response.json()
    print(f'Failed to fetch details for story ID {story_id}')
    return None

def save_to_database(story_details):
    """
    Saves story details into the database, updating existing entries if necessary.
    """
    required_fields = ['id', 'by', 'title', 'type']
    if all(story_details.get(field) is not None for field in required_fields):
        existing_news_item = db.session.get(NewsItem, story_details.get('id'))
        if existing_news_item:
            # Update existing NewsItem with new data
            existing_news_item.by = story_details['by']
            existing_news_item.descendants = story_details.get('descendants')
            existing_news_item.kids = story_details.get('kids', [])
            existing_news_item.score = story_details.get('score')
            existing_news_item.time = datetime.utcfromtimestamp(story_details.get('time'))
            existing_news_item.title = story_details['title']
            existing_news_item.type = story_details['type']
            existing_news_item.url = story_details.get('url', '')
        else:
            # Create a new NewsItem object with the story details
            news_item = NewsItem(
                id=story_details['id'],
                by=story_details['by'],
                descendants=story_details.get('descendants'),
                kids=story_details.get('kids', []),
                score=story_details.get('score'),
                time=datetime.utcfromtimestamp(story_details.get('time')),
                title=story_details['title'],
                type=story_details['type'],
                url=story_details.get('url', ''),
            )
            # Add to the session
            db.session.add(news_item)
        try:
            db.session.commit()
        except IntegrityError as db_error:
            print(f'Error saving to database: {db_error}')
            db.session.rollback()
    else:
        missing_fields = [field for field in required_fields if story_details.get(field) is None]
        print(f'Story details missing required fields: {missing_fields}. Skipping insert/update.')

def main():
    """ Main execution function fetching top Hacker News stories and
    saving them into the database. """
    top_story_ids = get_top_story_ids()
    recent_story_ids = top_story_ids[:30]
    for story_id in recent_story_ids:
        story_details = get_story_details(story_id)
        if story_details and story_details.get('type') == 'story':
            save_to_database(story_details)

if __name__ == "__main__":
    with app.app_context():
        main()
