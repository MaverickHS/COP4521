# hackernews.py -- get and save hackernews API data into news_items table of hackernews.db database
# git test


import requests
from datetime import datetime
from app import app, db, NewsItem

# Function to get the top story IDs
def get_top_story_ids():
    url = 'https://hacker-news.firebaseio.com/v0/topstories.json?print=pretty'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()  # Returns a list of IDs
    else:
        print('Failed to fetch top stories')
        return []

# Function to get the story details by ID
def get_story_details(story_id):
    url = f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json?print=pretty'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Failed to fetch details for story ID {story_id}')
        return None

# Function to save story details into the database
def save_to_database(story_details):
    # Check if the NewsItem already exists by its ID
    existing_news_item = db.session.get(NewsItem, story_details.get('id'))
    if existing_news_item:
        # Update existing NewsItem
        existing_news_item.by = story_details.get('by')
        existing_news_item.descendants = story_details.get('descendants')
        existing_news_item.kids = story_details.get('kids', [])
        existing_news_item.score = story_details.get('score')
        existing_news_item.time = datetime.utcfromtimestamp(story_details.get('time'))
        existing_news_item.title = story_details.get('title')
        existing_news_item.type = story_details.get('type')
        existing_news_item.url = story_details.get('url', '')
    else:
        # Create a new NewsItem object
        news_item = NewsItem(
            id=story_details.get('id'),
            by=story_details.get('by'),
            descendants=story_details.get('descendants'),
            kids=story_details.get('kids', []),
            score=story_details.get('score'),
            time=datetime.utcfromtimestamp(story_details.get('time')),
            title=story_details.get('title'),
            type=story_details.get('type'),
            url=story_details.get('url', ''),
        )
        # Add to the session
        db.session.add(news_item)
    
    # Commit to save changes in the database
    try:
        db.session.commit()
    except Exception as e:
        print(f'Error saving to database: {e}')
        db.session.rollback()

def main():
    # Fetch top story IDs
    top_story_ids = get_top_story_ids()

    # Take only the first 30 story IDs
    recent_story_ids = top_story_ids[:30]

    # Fetch story details and save to database for each ID
    for story_id in recent_story_ids:
        story_details = get_story_details(story_id)
        if story_details and story_details.get('type') == 'story':
            save_to_database(story_details)

if __name__ == "__main__":
    with app.app_context():
        main()

if __name__ == "__main__":
    with app.app_context():
        main()