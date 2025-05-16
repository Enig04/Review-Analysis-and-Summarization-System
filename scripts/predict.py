import pandas as pd
import numpy as np
import tensorflow as tf
import tensorflow_text as text
import joblib
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from textblob import TextBlob
from collections import Counter
import torch
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import logging
import os
import sys

logging.basicConfig(level=logging.DEBUG)

def generate_pdf(real_reviews, output_pdf_path):
    try:
        c = canvas.Canvas(output_pdf_path, pagesize=letter)
        width, height = letter

        y_position = height - 40
        for review in real_reviews:
            if y_position <= 40:
                c.showPage()
                y_position = height - 40 
            c.drawString(40, y_position, f"Text: {review['text']}")
            c.drawString(40, y_position - 20, f"Rating: {review['rating']}")
            y_position -= 40  

        c.save()
        return True
    except Exception as e:
        logging.error(f"Error generating PDF: {str(e)}")
        return False

def preprocess_for_prediction(text, rating, model_path="model", 
                              char_model_path="char_vectorizer_model"):
    try:

        token_input = tf.convert_to_tensor([text])

        char_input = tf.convert_to_tensor([text])

        rating_tensor = tf.one_hot([rating], depth=6)[:, 1:] 

        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity

        scaler_polarity = joblib.load("utils/scaler_polarity.pkl")
        scaler_subjectivity = joblib.load("utils/scaler_subjectivity.pkl")
        scaler_burstiness = joblib.load("utils/scaler_burstiness.pkl")
        scaler_perplexity = joblib.load("utils/scaler_perplexity.pkl")
        
        polarity_scaled = scaler_polarity.transform([[polarity]])
        subjectivity_scaled = scaler_subjectivity.transform([[subjectivity]])

        words = text.split()
        word_counts = Counter(words)
        freqs = np.array(list(word_counts.values()))
        burstiness = np.std(freqs) / np.mean(freqs) if np.mean(freqs) > 0 else 0
        burstiness_scaled = scaler_burstiness.transform([[burstiness]])

        gpt2_tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
        gpt2_tokenizer.pad_token = gpt2_tokenizer.eos_token 
        gpt2_model = GPT2LMHeadModel.from_pretrained('gpt2')
        device = "cuda" if torch.cuda.is_available() else "cpu"
        gpt2_model = gpt2_model.to(device)
        
        tokens = gpt2_tokenizer([text], return_tensors="pt", padding=True, truncation=True)
        tokens = {k: v.to(device) for k, v in tokens.items()}
        with torch.no_grad():
            outputs = gpt2_model(tokens["input_ids"], labels=tokens["input_ids"])
            loss = torch.nn.functional.cross_entropy(
                outputs.logits.view(-1, outputs.logits.size(-1)),
                tokens["input_ids"].view(-1),
                reduction='none',
                ignore_index=gpt2_tokenizer.pad_token_id
            ).view(tokens["input_ids"].shape)
            valid_token_counts = (tokens["input_ids"] != gpt2_tokenizer.pad_token_id).sum(dim=1)
            perplexity = torch.exp(loss.sum(dim=1) / valid_token_counts).item()
            perplexity_scaled = scaler_perplexity.transform([[perplexity]])

        return {
            "token_inputs": token_input,
            "char_inputs": char_input,
            "rating_input": tf.convert_to_tensor(rating_tensor, dtype=tf.float32),
            "polarity_input": tf.convert_to_tensor(polarity_scaled, dtype=tf.float32),
            "subjectivity_input": tf.convert_to_tensor(subjectivity_scaled, dtype=tf.float32),
            "perplexity_input": tf.convert_to_tensor(perplexity_scaled, dtype=tf.float32),
            "burstiness_input": tf.convert_to_tensor(burstiness_scaled, dtype=tf.float32),
        }
    except Exception as e:
        logging.error(f"Error during preprocessing: {str(e)}")
        raise

def main():
    try:

        input_csv_path = "data/input_reviews.csv" 
        output_csv_path = "data/real_reviews.csv" 
        output_pdf_path = "data/real_reviews.pdf" 
        sentiment_stats_path = "data/sentiment_stats.json" 

        logging.info(f"Reading {input_csv_path}...")
        if not os.path.exists(input_csv_path):
            logging.error(f"Input file {input_csv_path} not found!")
            return False

        df = pd.read_csv(input_csv_path)

        logging.info("Loading models and scalers...")
        try:
            model = tf.keras.models.load_model("model")
            char_vectorizer_model = tf.keras.models.load_model("char_vectorizer_model")
        except Exception as e:
            logging.error(f"Error loading models: {str(e)}")
            return False

        real_reviews = []
        real_reviews_df = []
        sentiment_counts = {
            "positive": 0,
            "neutral": 0,
            "negative": 0
        }
        total_reviews = 0
        real_reviews_count = 0
        fake_reviews_count = 0

        for idx, row in df.iterrows():
            text = row['text']
            rating = row['rating']
            total_reviews += 1

            try:
                inputs = preprocess_for_prediction(text, rating)
                fake_pred, sentiment_pred = model.predict(inputs, verbose=0)

                if fake_pred[0][0] <= 0.5:
                    real_reviews_count += 1

                    sentiment_category = "neutral"
                    if sentiment_pred[0][0] > 0.6: 
                        sentiment_category = "negative"
                    elif sentiment_pred[0][0] < 0.4: 
                        sentiment_category = "positive"

                    sentiment_counts[sentiment_category] += 1
                    
                    real_reviews.append({
                        'text': text,
                        'rating': rating,
                        'sentiment': sentiment_category
                    })
                    real_reviews_df.append({
                        'text': text,
                        'rating': rating,
                        'sentiment': sentiment_category
                    })
                else:
                    fake_reviews_count += 1
            except Exception as e:
                logging.error(f"Error processing row {idx}: {str(e)}")
                continue

        sentiment_stats = {
            "sentiment_counts": sentiment_counts,
            "total_reviews": total_reviews,
            "real_reviews_count": real_reviews_count,
            "fake_reviews_count": fake_reviews_count
        }
        
        with open(sentiment_stats_path, 'w') as f:
            import json
            json.dump(sentiment_stats, f)
        logging.info(f"Sentiment statistics saved to {sentiment_stats_path}")

        if real_reviews_df:
            pd.DataFrame(real_reviews_df).to_csv(output_csv_path, index=False)
            logging.info(f"Real reviews saved to {output_csv_path}")
        else:
            logging.warning("No real reviews found!")
            return False

        if real_reviews:
            success = generate_pdf(real_reviews, output_pdf_path)
            if success:
                logging.info(f"Real reviews saved to {output_pdf_path}")
                return True
            else:
                logging.error("Failed to generate PDF")
                return False
        else:
            logging.warning("No real reviews found!")
            return False

    except Exception as e:
        logging.error(f"Error in main function: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
