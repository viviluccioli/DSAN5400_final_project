import pandas as pd
import glob
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import time
import re
import os
from datetime import datetime, timedelta

csv_files = (
    glob.glob("../data/fox/fox*.csv") +
    glob.glob("../data/abc/abc*.csv") +
    glob.glob("../data/msnbc/msnbc*.csv")
)

df = pd.concat([pd.read_csv(file) for file in csv_files], ignore_index=True)

columns_of_interest = [
    "parsed_date", "url", "headline_from_url",
    "V2Themes", "V2Locations", "V2Persons",
    "V2Organizations", "V2Tone"
]
df = df[columns_of_interest]

df["parsed_date"] = pd.to_datetime(df["parsed_date"], errors="coerce").dt.tz_localize(None)

def extract_network(url):
    if 'fox' in url.lower():
        return 'Fox News'
    elif 'abc' in url.lower():
        return 'ABC News'
    elif 'msnbc' in url.lower():
        return 'MSNBC'
    else:
        return 'Unknown'

df['network'] = df['url'].apply(extract_network)

df['tone'] = df['V2Tone'].str.split(',').str[0].astype(float)

election_date = pd.Timestamp('2020-11-03')
month_before = election_date - pd.Timedelta(days=30)
month_after = election_date + pd.Timedelta(days=30)

election_df = df[(df['parsed_date'] >= month_before) & (df['parsed_date'] <= month_after)]

election_df['period'] = 'Before Election'
election_df.loc[election_df['parsed_date'] >= election_date, 'period'] = 'After Election'

try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

sia = SentimentIntensityAnalyzer()

def extract_article_text(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.decompose()
        
        paragraphs = soup.find_all('p')
        article_text = ' '.join([p.get_text() for p in paragraphs])
        
        article_text = re.sub(r'\s+', ' ', article_text).strip()
        
        return article_text
    
    except Exception as e:
        print(f"Error extracting text from {url}: {e}")
        return None

def get_binary_sentiment(text):
    if not text:
        return None
    
    sentiment = sia.polarity_scores(text)
    return 1 if sentiment['compound'] >= 0 else 0

def add_sentiment_analysis(df, output_path='../data/election_2020_sentiment_analysis.csv'):
    result_df = df.copy()
    
    if 'sentiment_analysis' not in result_df.columns:
        result_df['sentiment_analysis'] = None
    
    urls_to_process = df['url'].tolist()
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if os.path.exists(output_path):
        existing_df = pd.read_csv(output_path)
        processed_urls = set(existing_df['url'])
        urls_to_process = [url for url in urls_to_process if url not in processed_urls]
        print(f"Found existing file with {len(processed_urls)} processed URLs.")
        print(f"Remaining URLs to process: {len(urls_to_process)}")
    
    for i, url in enumerate(urls_to_process):
        print(f"Processing URL {i+1}/{len(urls_to_process)}: {url}")
        
        article_text = extract_article_text(url)
        
        if article_text:
            sentiment = get_binary_sentiment(article_text)
            idx = result_df[result_df['url'] == url].index
            result_df.loc[idx, 'sentiment_analysis'] = sentiment
        
        if (i + 1) % 100 == 0:
            if os.path.exists(output_path):
                temp_df = result_df.copy()
                temp_df = temp_df[temp_df['sentiment_analysis'].notnull()]
                
                existing_df = pd.read_csv(output_path)
                
                existing_urls = set(existing_df['url'])
                new_df = temp_df[~temp_df['url'].isin(existing_urls)]
                
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                combined_df.to_csv(output_path, index=False)
                print(f"Progress saved: {len(combined_df)} total rows in {output_path}")
            else:
                temp_df = result_df.copy()
                temp_df = temp_df[temp_df['sentiment_analysis'].notnull()]
                temp_df.to_csv(output_path, index=False)
                print(f"Progress saved: {len(temp_df)} rows in {output_path}")
        
        time.sleep(0.1)
    
    if os.path.exists(output_path):
        temp_df = result_df.copy()
        temp_df = temp_df[temp_df['sentiment_analysis'].notnull()]
        
        existing_df = pd.read_csv(output_path)
        
        existing_urls = set(existing_df['url'])
        new_df = temp_df[~temp_df['url'].isin(existing_urls)]
        
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        combined_df.to_csv(output_path, index=False)
        print(f"Final results saved: {len(combined_df)} total rows in {output_path}")
    else:
        temp_df = result_df.copy()
        temp_df = temp_df[temp_df['sentiment_analysis'].notnull()]
        temp_df.to_csv(output_path, index=False)
        print(f"Final results saved: {len(temp_df)} rows in {output_path}")
    
    return result_df

def generate_election_stats(sentiment_df, output_stats_path='../data/election_2020_sentiment_stats.csv'):
    sentiment_df['parsed_date'] = pd.to_datetime(sentiment_df['parsed_date'])
    
    if 'period' not in sentiment_df.columns:
        sentiment_df['period'] = 'Before Election'
        sentiment_df.loc[sentiment_df['parsed_date'] >= election_date, 'period'] = 'After Election'
    
    sentiment_stats = sentiment_df.groupby(['network', 'period'])['sentiment_analysis'].agg([
        ('Positive', lambda x: x.mean()),
        ('Count', 'count')
    ]).reset_index()
    
    tone_stats = sentiment_df.groupby(['network', 'period'])['tone'].agg([
        ('Mean Tone', 'mean'),
        ('Count', 'count')
    ]).reset_index()
    
    combined_stats = pd.merge(sentiment_stats, tone_stats[['network', 'period', 'Mean Tone']], 
                              on=['network', 'period'])
    
    combined_stats.to_csv(output_stats_path, index=False)
    
    print("\nSentiment Analysis Around 2020 Election:")
    for network in sentiment_df['network'].unique():
        print(f"\n{network}:")
        network_data = combined_stats[combined_stats['network'] == network]
        
        if len(network_data) >= 2:
            before = network_data[network_data['period'] == 'Before Election'].iloc[0]
            after = network_data[network_data['period'] == 'After Election'].iloc[0]
            
            print(f"  Before Election: {before['Count']} articles, {before['Positive']*100:.1f}% positive, Mean Tone: {before['Mean Tone']:.2f}")
            print(f"  After Election: {after['Count']} articles, {after['Positive']*100:.1f}% positive, Mean Tone: {after['Mean Tone']:.2f}")
            
    return combined_stats

print("Processing articles from month before and after 2020 election...")
output_path = '../data/election_2020_sentiment_analysis.csv'
df_with_sentiment = add_sentiment_analysis(election_df, output_path=output_path)

processed_df = pd.read_csv(output_path)
stats = generate_election_stats(processed_df, '../data/election_2020_sentiment_stats.csv')

print("\nFinal Statistics:")
print(f"Total articles processed: {len(processed_df)}")
print(f"Before election: {len(processed_df[processed_df['period'] == 'Before Election'])}")
print(f"After election: {len(processed_df[processed_df['period'] == 'After Election'])}")