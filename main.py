import os
import json
import tweepy
import time
from google import genai
from openai import OpenAI
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_config(config_path="config.json"):
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def read_prompt(prompt_path):
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

def generate_tweet_gemini(api_key, model_name, prompt):
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )
    return response.text.strip()

def generate_tweet_grok(api_key, model_name, prompt):
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1",
    )
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that writes tweets."},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()

def generate_tweet_groq(api_key, model_name, prompt):
    client = Groq(api_key=api_key)
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "user", "content": prompt}
        ],
        model=model_name,
    )
    return chat_completion.choices[0].message.content.strip()

def generate_tweet(provider, config, prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            print(f"Attempting to generate tweet using {provider}...")
            
            if provider == "gemini":
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key: raise ValueError("GEMINI_API_KEY not found")
                return generate_tweet_gemini(api_key, config["gemini_model"], prompt)
                
            elif provider == "grok":
                api_key = os.getenv("XAI_API_KEY")
                if not api_key: raise ValueError("XAI_API_KEY not found")
                return generate_tweet_grok(api_key, config["grok_model"], prompt)
                
            elif provider == "groq":
                api_key = os.getenv("GROQ_API_KEY")
                if not api_key: raise ValueError("GROQ_API_KEY not found")
                return generate_tweet_groq(api_key, config["groq_model"], prompt)
            
            else:
                raise ValueError(f"Unknown provider: {provider}")

        except Exception as e:
            print(f"Error with {provider}: {e}")
            if "429" in str(e) or "quota" in str(e).lower():
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 20
                    print(f"Rate limit hit. Retrying in {wait_time} s...")
                    time.sleep(wait_time)
                    continue
            raise e

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
    config = load_config()
    
    twitter_keys = {
        "consumer_key": os.getenv("TWITTER_API_KEY"),
        "consumer_secret": os.getenv("TWITTER_API_SECRET"),
        "access_token": os.getenv("TWITTER_ACCESS_TOKEN"),
        "access_token_secret": os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    }
    
    if not all(twitter_keys.values()):
        raise ValueError("One or more Twitter API keys are missing")

    prompt_text = read_prompt(config["prompt_file"])
    full_prompt = f"{prompt_text}\n\n(Note: Keep it under {config['max_tweet_length']} characters)"
    
    try:
        # Generate tweet using the configured provider
        tweet_content = generate_tweet(config.get("provider", "gemini"), config, full_prompt)
        print(f"Generated Tweet:\n{tweet_content}\n")
        
        if len(tweet_content) > 280: 
            tweet_content = tweet_content[:280]

        post_tweet(twitter_keys, tweet_content)
        
    except Exception as e:
        print(f"Final Error: {e}")

if __name__ == "__main__":
    main()
