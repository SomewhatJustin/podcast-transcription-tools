#!/usr/bin/env python3

import os
import sys
import requests
from dotenv import load_dotenv
from datetime import datetime
import time
import hashlib
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment variables
load_dotenv()

API_KEY = os.getenv('PODCAST_INDEX_API_KEY')
API_SECRET = os.getenv('PODCAST_INDEX_API_SECRET')
BASE_URL = "https://api.podcastindex.org/api/1.0"

def create_session():
    """Create a requests session with retry strategy"""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def get_headers():
    """Generate headers for API requests"""
    auth_date = str(int(time.time()))
    # Create the hash as specified in the API docs
    hash_input = f"{API_KEY}{API_SECRET}{auth_date}"
    auth_hash = hashlib.sha1(hash_input.encode('utf-8')).hexdigest()
    
    return {
        "X-Auth-Date": auth_date,
        "X-Auth-Key": API_KEY,
        "Authorization": auth_hash,
        "User-Agent": "PodcastSearch/1.0"
    }

def search_podcasts(term: str) -> list:
    """Search for podcasts by term"""
    url = f"{BASE_URL}/search/byterm"
    params = {"q": term}
    
    try:
        session = create_session()
        print(f"Making request to: {url}")
        print(f"With headers: {get_headers()}")
        response = session.get(url, headers=get_headers(), params=params, timeout=10)
        response.raise_for_status()
        return response.json().get("feeds", [])
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: Could not connect to {BASE_URL}. Please check your internet connection.", file=sys.stderr)
        print(f"Detailed error: {str(e)}", file=sys.stderr)
        return []
    except requests.exceptions.Timeout as e:
        print(f"Timeout error: The request took too long to complete.", file=sys.stderr)
        print(f"Detailed error: {str(e)}", file=sys.stderr)
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error searching podcasts: {str(e)}", file=sys.stderr)
        return []

def get_episodes(feed_id: int) -> list:
    """Get episodes for a specific podcast feed"""
    url = f"{BASE_URL}/episodes/byfeedid"
    params = {"id": feed_id, "max": 5}
    
    try:
        session = create_session()
        response = session.get(url, headers=get_headers(), params=params, timeout=10)
        response.raise_for_status()
        return response.json().get("items", [])
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: Could not connect to {BASE_URL}. Please check your internet connection.", file=sys.stderr)
        print(f"Detailed error: {str(e)}", file=sys.stderr)
        return []
    except requests.exceptions.Timeout as e:
        print(f"Timeout error: The request took too long to complete.", file=sys.stderr)
        print(f"Detailed error: {str(e)}", file=sys.stderr)
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error getting episodes: {str(e)}", file=sys.stderr)
        return []

def format_date(timestamp: int) -> str:
    """Format Unix timestamp to readable date"""
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")

def display_podcast(podcast: dict, index: int) -> None:
    """Display podcast information in a formatted way"""
    print(f"\n{index + 1}. {podcast.get('title', 'Unknown Title')}")
    print(f"   Author: {podcast.get('author', 'Unknown Author')}")
    print(f"   Description: {podcast.get('description', 'No description')[:200]}...")
    
    # Handle categories safely
    categories = podcast.get('categories', {})
    if categories:
        print(f"   Categories: {', '.join(categories.values())}")
    else:
        print("   Categories: None")

def display_episode(episode: dict) -> None:
    """Display episode information in a formatted way"""
    print(f"\nTitle: {episode.get('title', 'Unknown Title')}")
    print(f"Date: {format_date(episode.get('datePublished', 0))}")
    print(f"Duration: {episode.get('duration', 0) // 60} minutes")
    print(f"Download URL: {episode.get('enclosureUrl', 'No URL available')}")

def main():
    if not API_KEY:
        print("Error: PODCAST_INDEX_API_KEY not found in .env file", file=sys.stderr)
        sys.exit(1)

    while True:
        # Get search term from user
        search_term = input("\nEnter podcast search term (or 'q' to quit): ").strip()
        if search_term.lower() == 'q':
            break

        # Search for podcasts
        print(f"\nSearching for '{search_term}'...")
        podcasts = search_podcasts(search_term)

        if not podcasts:
            print("No podcasts found.")
            continue

        # Display top 5 results
        print("\nTop 5 Results:")
        for i, podcast in enumerate(podcasts[:5]):
            display_podcast(podcast, i)

        # Get user selection
        while True:
            try:
                selection = input("\nSelect a podcast number (1-5) or 'b' to go back: ").strip()
                if selection.lower() == 'b':
                    break
                
                index = int(selection) - 1
                if 0 <= index < min(5, len(podcasts)):
                    selected_podcast = podcasts[index]
                    print(f"\nLatest episodes for: {selected_podcast.get('title')}")
                    
                    # Get and display episodes
                    episodes = get_episodes(selected_podcast['id'])
                    for episode in episodes:
                        display_episode(episode)
                    break
                else:
                    print("Invalid selection. Please enter a number between 1 and 5.")
            except ValueError:
                print("Please enter a valid number or 'b' to go back.")

if __name__ == "__main__":
    main() 