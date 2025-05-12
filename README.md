# Review-Analysis-and-Summarization-System
AI-powered system for detecting fake reviews, analyzing sentiment, and generating summaries. Combines BERT, embeddings, and deep learning to ensure trustworthy insights for e-commerce and service domains.


This is an AI-driven system that detects fake reviews, performs sentiment analysis, and generates concise summaries to support trustworthy decision-making. Built with a hybrid model of BERT, character embeddings, and token embeddings, the system is designed for use in e-commerce and service-oriented platforms where user feedback heavily influences consumer behavior.

**Features:**

> Detects fake reviews using deep learning and linguistic patterns

> Hybrid NLP model using BERT + token/character embeddings

> Sentiment analysis (polarity, subjectivity, etc.)

> Review summarization with keyword/polarity filtering

> Review screening with personalization options

> Outputs real, trustworthy reviews with summaries

> Easy CSV-based input/output for batch processing


**Tech Stack:**

> Python

> TensorFlow / Keras

> BERT (via Hugging Face Transformers)

> NLTK / TextBlob

> Flask (for deployment)

> Pandas / NumPy

> HTML/CSS/Js

**NOTE:** 

1) This project uses DeepSeek7B (https://ollama.com/library/deepseek-llm) via Ollama (https://ollama.com/) for text summarization.

Make sure you have Ollama installed and the DeepSeek model pulled.


2) This project uses Oxylabs' Web Scraper API for scraping amazon reviews. Make sure you have the required details in order to use the API.
