import os
import json
import tweepy
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_config(config_path="config.json"):
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def read_prompt(prompt_path):
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

def generate_tweet(api_key, model_name, prompt):
    # Initialize the new GenAI client
    client = genai.Client(api_key=api_key)
    
    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )
    return response.text.strip()

def post_tweet(api_keys, tweet_content):
    client = tweepy.Client(
        consumer_key=api_keys["consumer_key"],
        consumer_secret=api_keys["consumer_secret"],
        access_token=api_keys["access_token"],
        access_token_secret=api_keys["access_token_secret"]
    )
    
    try:
        response = client.create_tweet(text=tweet_content)
        print(f"Tweet posted successfully! ID: {response.data['id']}")
    except Exception as e:
        print(f"Error posting tweet: {e}")

def main():
    # Load configuration
    config = load_config()
    
    # Get API Keys from environment variables
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
        
    twitter_keys = {
        "consumer_key": os.getenv("TWITTER_API_KEY"),
        "consumer_secret": os.getenv("TWITTER_API_SECRET"),
        "access_token": os.getenv("TWITTER_ACCESS_TOKEN"),
        "access_token_secret": os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    }
    
    if not all(twitter_keys.values()):
        raise ValueError("One or more Twitter API keys are missing")

    # Generate Tweet content
    prompt_text = read_prompt(config["prompt_file"])
    # Add constraint to prompt mostly to be safe
    full_prompt = f"{prompt_text}\n\n(Note: Keep it under {config['max_tweet_length']} characters)"
    
    print("Generating tweet content...")
    try:
        tweet_content = generate_tweet(gemini_api_key, config["gemini_model"], full_prompt)
        print(f"Generated Tweet:\n{tweet_content}\n")
        
        # Check length just in case
        if len(tweet_content) > 280: 
            print("Warning: Tweet exceeds 280 characters. Truncating...")
            tweet_content = tweet_content[:280]

        # Post Tweet
        print("Posting to X...")
        post_tweet(twitter_keys, tweet_content)
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
