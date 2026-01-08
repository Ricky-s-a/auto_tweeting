import os
import json
import tweepy
import time
import argparse
from datetime import datetime, timedelta, timezone
from google import genai
from openai import OpenAI
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_config(config_path):
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

def generate_tweet_grok(api_key, model_name, prompt, temperature=0.7):
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
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()

def generate_tweet_groq(api_key, model_name, prompt, temperature=0.7):
    client = Groq(api_key=api_key)
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "user", "content": prompt}
        ],
        model=model_name,
        temperature=temperature,
    )
    return chat_completion.choices[0].message.content.strip()

def generate_tweet(provider, config, prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            print(f"Attempting to generate tweet using {provider}...")
            temperature = config.get("temperature", 0.7)
            
            if provider == "gemini":
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key: raise ValueError("GEMINI_API_KEY not found")
                # Gemini support for temperature requires updating the call or client config, 
                # but for now let's focus on Groq as requested or kept by user.
                # If the user switches back to Gemini later, we can add it properly.
                return generate_tweet_gemini(api_key, config["gemini_model"], prompt)
                
            elif provider == "grok":
                api_key = os.getenv("XAI_API_KEY")
                if not api_key: raise ValueError("XAI_API_KEY not found")
                return generate_tweet_grok(api_key, config["grok_model"], prompt, temperature)
                
            elif provider == "groq":
                api_key = os.getenv("GROQ_API_KEY")
                if not api_key: raise ValueError("GROQ_API_KEY not found")
                return generate_tweet_groq(api_key, config["groq_model"], prompt, temperature)
            
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

import random

def main():
    parser = argparse.ArgumentParser(description='Auto Tweeting Bot')
    parser.add_argument('--config', type=str, default='config.json', help='Path to the configuration file')
    args = parser.parse_args()

    config = load_config(args.config)

    # Time restriction: 00:00 - 06:00 JST
    jst = timezone(timedelta(hours=9))
    current_time = datetime.now(jst)
    if 0 <= current_time.hour < 6:
        print(f"Current time is {current_time.strftime('%H:%M')} JST. Skipping tweet during night hours (00:00 - 06:00).")
        return

    # Random delay logic for human-like behavior
    if config.get("enable_random_delay", False):
        # 1. Probability check (Skip execution to be irregular and save Action minutes)
        probability = config.get("tweet_probability", 1.0)
        if random.random() > probability:
            print("🎲 Random check: Skipping this hour to simulate human irregularity.")
            return

        # 2. Short random delay (0-2 mins) to vary exact timing
        max_delay_min = config.get("max_delay_minutes", 0)
        if max_delay_min > 0:
            delay_sec = random.randint(0, max_delay_min * 60)
            print(f"Simulating human behavior: Sleeping for {delay_sec} seconds before tweeting...")
            time.sleep(delay_sec)
    
    # Get Twitter API keys based on the prefix defined in config
    env_prefix = config.get("twitter_env_prefix", "TWITTER")
    
    twitter_keys = {
        "consumer_key": os.getenv(f"{env_prefix}_API_KEY"),
        "consumer_secret": os.getenv(f"{env_prefix}_API_SECRET"),
        "access_token": os.getenv(f"{env_prefix}_ACCESS_TOKEN"),
        "access_token_secret": os.getenv(f"{env_prefix}_ACCESS_TOKEN_SECRET")
    }
    
    if not all(twitter_keys.values()):
        # Debug helper: print which keys are missing (without printing values)
        missing = [k for k, v in twitter_keys.items() if not v]
        raise ValueError(f"One or more Twitter API keys are missing for prefix {env_prefix}: {missing}")

    prompt_text = read_prompt(config["prompt_file"])
    full_prompt = f"{prompt_text}\n\n(Note: Keep it under {config['max_tweet_length']} characters)"
    
    try:
        # Generate tweet using the configured provider
        tweet_content = generate_tweet(config.get("provider", "gemini"), config, full_prompt)
        
        try:
            print(f"Generated Tweet:\n{tweet_content}\n")
        except UnicodeEncodeError:
            print("Generated Tweet: (Content hidden due to console encoding limits)")
            # print(repr(tweet_content)) # Uncomment to debug raw content
        
        if len(tweet_content) > config['max_tweet_length']: 
            tweet_content = tweet_content[:config['max_tweet_length']]

        post_tweet(twitter_keys, tweet_content)
        
    except Exception as e:
        print(f"Final Error: {e}")

if __name__ == "__main__":
    main()
