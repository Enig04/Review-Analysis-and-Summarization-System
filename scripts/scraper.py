import requests
import pandas as pd
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

USERNAME = os.getenv("OXYLABS_USERNAME")
PASSWORD = os.getenv("OXYLABS_PASSWORD")
OXYLABS_API_URL = os.getenv("OXYLABS_API_URL", "https://realtime.oxylabs.io/v1/queries")

def scrape_reviews(asin):
    payload = {
        "source": "amazon_reviews",
        "domain": "in",
        "query": asin,
        "parse": True,
        "pages": 10
    }

    response = requests.post(OXYLABS_API_URL, auth=(USERNAME, PASSWORD), json=payload)
    
    if response.status_code != 200:
        raise Exception(f"Failed to scrape data: {response.status_code} - {response.text}")

    data = response.json()
    reviews = data.get("results", [])[0].get("content", {}).get("reviews", [])

    if not reviews:
        raise Exception("No reviews found or invalid ASIN.")

    review_list = [{"text": r.get("content"), "rating": r.get("rating")} for r in reviews]
    df = pd.DataFrame(review_list)
    df.to_csv("data/input_reviews.csv", index=False)
    print(f"Saved {len(review_list)} reviews to 'data/input_reviews.csv'")

if __name__ == "__main__":
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print("Error: No ASIN provided. Please provide a valid ASIN.")
        sys.exit(1)

    asin = sys.argv[1].strip()
    scrape_reviews(asin)
