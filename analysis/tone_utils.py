import pandas as pd
import os
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from afinn import Afinn
import time
import logging
from bs4 import BeautifulSoup
import requests
import re
from transformers import pipeline

# 初始化
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

sia = SentimentIntensityAnalyzer()
afinn = Afinn()
sentiment_model = pipeline("sentiment-analysis", model="mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis")

def extract_article_text(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        soup = BeautifulSoup(response.content, 'html.parser')
        for script in soup(['script', 'style']):
            script.decompose()
        return ' '.join([p.get_text() for p in soup.find_all('p')]).strip()
    except Exception as e:
        logging.warning(f"Error extracting text from {url}: {e}")
        return None

def compute_afinn_tone(text):
    words = text.split()
    score = afinn.score(text)
    return (score / len(words)) * 100 if words else 0.0

def get_vader_sentiment_analysis(text):
    if not text:
        return None
    sentiment = sia.polarity_scores(text)
    return 1 if sentiment['compound'] >= 0 else 0

def get_vader_tone_score(text):
    if not text:
        return None
    sentiment = sia.polarity_scores(text)
    return sentiment['compound']

def run_sentiment(df):
    df = df.copy()
    df['vader_sentiment_analysis'] = None
    df['vader_tone_score'] = None
    df['afinn_tone_score'] = None
    df['RoBERTa_sentiment_label'] = None
    texts = []
    indices = []

    for i, row in df.iterrows():
        url = row.get("url")
        if not url:
            continue
        article_text = extract_article_text(url)
        if article_text:
            # RoBERTa 
            texts.append(article_text)
            indices.append(i)

            # VADER & AFINN
            df.at[i, 'vader_sentiment_analysis'] = get_vader_sentiment_analysis(article_text)
            df.at[i, 'vader_tone_score'] = get_vader_tone_score(article_text)
            df.at[i, 'afinn_tone_score'] = compute_afinn_tone(article_text)

        time.sleep(0.1)

    # Huggingface RoBERTa 
    if texts:
        results = sentiment_model(texts, batch_size=16, truncation=True)
        for i, result in zip(indices, results):
            label = result.get("label", "").upper()
            df.at[i, 'RoBERTa_sentiment_label'] = label

    return df
