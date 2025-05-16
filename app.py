import os
import logging
from flask import Flask, render_template, request, jsonify
import subprocess
import json
import re

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__, template_folder="templates")
app.secret_key = os.environ.get("SESSION_SECRET", "default-dev-key")

def extract_asin_from_url(url):
    """Extract ASIN from Amazon URL"""
    asin_match = re.search(r'(?:\/dp\/|\/gp\/product\/|asin=|\/ASIN\/|product\/)([A-Z0-9]{10})', url)
    if asin_match:
        return asin_match.group(1)
    return None

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json()
        amazon_url = data.get("amazon_url")
        
        if not amazon_url:
            return jsonify({"error": "No Amazon URL provided"}), 400
        
        asin = extract_asin_from_url(amazon_url)
        if not asin:
            return jsonify({"error": "Could not extract ASIN from URL. Please provide a valid Amazon product URL."}), 400
        
        return jsonify({"status": "success", "asin": asin})
    
    except Exception as e:
        logging.error(f"Error in analyze endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/scrape", methods=["POST"])
def scrape():
    try:
        data = request.get_json()
        asin = data.get("asin")
        
        if not asin:
            return jsonify({"error": "No ASIN provided"}), 400

        command = ["python", "scripts/scraper.py", asin]
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            logging.error(f"Scraper error: {result.stderr}")
            return jsonify({"error": "Error during scraping", "details": result.stderr}), 500
        
        return jsonify({"status": "success", "message": "Reviews scraped successfully"})
    
    except Exception as e:
        logging.error(f"Error in scrape endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/predict", methods=["POST"])
def predict():
    try:
        result = subprocess.run(["python", "scripts/predict.py"], capture_output=True, text=True)
        
        if result.returncode != 0:
            logging.error(f"Prediction error: {result.stderr}")
            return jsonify({"error": "Error during prediction", "details": result.stderr}), 500
        
        return jsonify({"status": "success", "message": "Fake reviews identified successfully"})
    
    except Exception as e:
        logging.error(f"Error in predict endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/summarize", methods=["POST"])
def summarize():
    try:
        import scripts.summary as summary_module
        
        summary_text = summary_module.run_summary()
        
        if not summary_text:
            return jsonify({"error": "Failed to generate summary"}), 500
        
        sentiment_stats_path = "data/sentiment_stats.json"
        sentiment_stats = {
            "sentiment_counts": {"positive": 0, "neutral": 0, "negative": 0},
            "total_reviews": 0,
            "real_reviews_count": 0,
            "fake_reviews_count": 0
        }

        if os.path.exists(sentiment_stats_path):
            try:
                with open(sentiment_stats_path, 'r') as f:
                    sentiment_stats = json.load(f)
                logging.info("Loaded sentiment statistics")
            except Exception as e:
                logging.error(f"Error loading sentiment statistics: {str(e)}")

        return jsonify({
            "status": "success", 
            "summary": summary_text,
            "sentiment_stats": sentiment_stats
        })
    
    except Exception as e:
        logging.error(f"Error in summarize endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host='add-your-host-ip-here', port='add-your-port-here', use_reloader=False)
