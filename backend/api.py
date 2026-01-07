from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import tweepy
import os
from dotenv import load_dotenv

# Load environment variables from the root .env file
load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; specify domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_twitter_client():
    consumer_key = os.getenv("TWITTER_API_KEY")
    consumer_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

    if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
        # Fallback for dev/demo if keys are missing but we want to show UI
        print("Warning: Twitter Keys missing.")
        return None

    return tweepy.Client(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )



import json
from datetime import datetime

# ... (imports)

DATA_FILE = "backend/data/history.json"

def ensure_history_file():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)

def save_metrics(metrics):
    ensure_history_file()
    try:
        with open(DATA_FILE, "r+") as f:
            data = json.load(f)
            
            # Simple deduplication by date (only keep last entry per day or mostly recent)
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Create new entry
            new_entry = {
                "date": today,
                "timestamp": datetime.now().isoformat(),
                "followers": metrics.get("followers_count", 0),
                "following": metrics.get("following_count", 0),
                "tweets": metrics.get("tweet_count", 0),
                "listed": metrics.get("listed_count", 0)
            }
            
            # Check if we already have an entry for today, if so update it, else append
            # For this simple dashboard, let's just append if it's a new check-in time 
            # or update if same day to keep history clean (optional, keeping it simple: always append for granular view, or filter in frontend)
            # Let's save one entry per day effectively to avoid noise? 
            # Actually, let's just append. Frontend can handle visualization.
            
            data.append(new_entry)
            
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
    except Exception as e:
        print(f"Error saving history: {e}")

@app.get("/api/me")
def get_me():
    try:
        client = get_twitter_client()
        if not client:
             raise Exception("Client not initialized (missing keys)")
        
        response = client.get_me(
            user_fields=["profile_image_url", "description", "public_metrics", "created_at"]
        )
        if response.data:
            # Save metrics for history
            if response.data.public_metrics:
                save_metrics(response.data.public_metrics)
            return response.data.data
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        print(f"Error fetching user: {e}")
        # Return mock data
        mock_data = {
            "id": "mock_id",
            "name": "Mock User (API Error)",
            "username": "mock_user",
            "description": f"Failed to fetch real data: {str(e)}",
            "public_metrics": {
                "followers_count": 0,
                "following_count": 0,
                "tweet_count": 0,
                "listed_count": 0
            },
            "profile_image_url": "https://via.placeholder.com/150"
        }
        # Don't save mock data to history
        return mock_data

@app.get("/api/history")
def get_history():
    ensure_history_file()
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

@app.get("/api/tweets")
def get_tweets(limit: int = 100):
    try:
        client = get_twitter_client()
        if not client:
             raise Exception("Client not initialized (missing keys)")

        me = client.get_me()
        user_id = me.data.id
        
        # Requests metrics including impressions (non_public_metrics)
        # Note: non_public_metrics requires OAuth 1.0a User Context (which we have)
        tweets = client.get_users_tweets(
            id=user_id,
            max_results=limit if limit <= 100 else 100,
            tweet_fields=["created_at", "public_metrics", "non_public_metrics", "organic_metrics"]
        )
        
        if tweets.data:
            return tweets.data
        return []
        
    except Exception as e:
        print(f"Error fetching tweets: {e}")
        # Mock data with varied metrics for testing sorting
        return [
            {
                "id": "1",
                "text": "This is a popular tweet! 🚀 #growth",
                "public_metrics": {"retweet_count": 50, "reply_count": 10, "like_count": 200, "quote_count": 5},
                "non_public_metrics": {"impression_count": 5000, "url_link_clicks": 100},
                "created_at": "2026-01-05T12:00:00Z"
            },
            {
                "id": "2",
                "text": "Just a normal update.",
                "public_metrics": {"retweet_count": 2, "reply_count": 1, "like_count": 15, "quote_count": 0},
                "non_public_metrics": {"impression_count": 300, "url_link_clicks": 2},
                "created_at": "2026-01-06T09:00:00Z"
            },
            {
                "id": "3",
                "text": "Viral thread starts here... 🧵",
                "public_metrics": {"retweet_count": 120, "reply_count": 45, "like_count": 500, "quote_count": 20},
                "non_public_metrics": {"impression_count": 15000, "url_link_clicks": 500},
                "created_at": "2026-01-07T10:00:00Z"
            }
        ]

# Mount static files at the end to avoid overriding API routes
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

