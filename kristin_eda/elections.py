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
import logging
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def analyze_election_sentiment(election_year):
    """
    Analyze news media sentiment for a specific election year and update original CSV files
    
    Args:
        election_year (int): The election year to analyze (2016, 2020, or 2024)
    """
    logging.info(f"Starting analysis for {election_year} election")
    
    # Define election date based on the year
    if election_year == 2016:
        election_date = pd.Timestamp('2016-11-08')
    elif election_year == 2020:
        election_date = pd.Timestamp('2020-11-03')
    elif election_year == 2024:
        election_date = pd.Timestamp('2024-11-05')
    else:
        raise ValueError("Invalid election year. Must be 2016, 2020, or 2024.")
    
    # Set time period for analysis
    month_before = election_date - pd.Timedelta(days=30)
    month_after = election_date + pd.Timedelta(days=30)
    period_start = month_before.strftime('%Y%m%d')
    period_end = month_after.strftime('%Y%m%d')
    
    logging.info(f"Analyzing period from {month_before.date()} to {month_after.date()}")
    
    # Find CSV files for the given election year
    csv_files = []
    for network in ['fox', 'abc', 'msnbc']:
        # Pattern might need adjustment based on actual file naming conventions
        pattern = f"../data/{network}/{network}*{election_year}*.csv"
        files = glob.glob(pattern)
        if not files:
            logging.warning(f"No {network} files found for {election_year} with pattern {pattern}")
        csv_files.extend(files)
    
    if not csv_files:
        logging.error(f"No CSV files found for {election_year}")
        return None
    
    logging.info(f"Found {len(csv_files)} CSV files for {election_year}")
    
    # Process each CSV file individually to update it in place
    all_processed_dfs = []
    
    for file_path in csv_files:
        try:
            logging.info(f"Processing file: {file_path}")
            
            # Read the CSV
            df = pd.read_csv(file_path)
            
            # Convert parsed_date to datetime
            if "parsed_date" in df.columns:
                df["parsed_date"] = pd.to_datetime(df["parsed_date"], errors="coerce").dt.tz_localize(None)
            
            # Filter for the election period
            if "parsed_date" in df.columns:
                election_period_df = df[(df['parsed_date'] >= month_before) & (df['parsed_date'] <= month_after)].copy()
                
                if len(election_period_df) > 0:
                    # Add election metadata
                    election_period_df.loc[:, 'period'] = 'Before Election'
                    election_period_df.loc[election_period_df['parsed_date'] >= election_date, 'period'] = 'After Election'
                    election_period_df['election_year'] = election_year
                    
                    # Add network column if URL exists
                    if 'url' in election_period_df.columns:
                        election_period_df['network'] = election_period_df['url'].apply(extract_network)
                    
                    # Extract tone from V2Tone if available
                    if 'V2Tone' in election_period_df.columns:
                        election_period_df['tone'] = election_period_df['V2Tone'].str.split(',').str[0].astype(float)
                    
                    # Add sentiment analysis directly to the dataframe
                    processed_df = add_sentiment_analysis_to_df(election_period_df)
                    
                    # Create a mapping from URLs to the new sentiment columns
                    sentiment_map = {}
                    if 'url' in processed_df.columns:
                        for _, row in processed_df.iterrows():
                            url = row['url']
                            sentiment_map[url] = {
                                'vader_sentiment_analysis': row.get('vader_sentiment_analysis'),
                                'vader_tone_score': row.get('vader_tone_score')
                            }
                    
                        # Update the original dataframe with sentiment values
                        for idx, row in df.iterrows():
                            if 'url' in row and row['url'] in sentiment_map:
                                df.at[idx, 'vader_sentiment_analysis'] = sentiment_map[row['url']]['vader_sentiment_analysis']
                                df.at[idx, 'vader_tone_score'] = sentiment_map[row['url']]['vader_tone_score']
                    
                    # Save the updated dataframe back to the original CSV
                    df.to_csv(file_path, index=False)
                    logging.info(f"Updated original CSV file: {file_path}")
                    
                    # Keep track of processed data for statistics
                    all_processed_dfs.append(processed_df)
                else:
                    logging.warning(f"No data in election period for file: {file_path}")
            else:
                logging.warning(f"Missing parsed_date column in file: {file_path}")
                
        except Exception as e:
            logging.error(f"Error processing {file_path}: {e}")
    
    if not all_processed_dfs:
        logging.error("No data was processed for the election period")
        return None
    
    # Combine all processed dataframes for statistics
    combined_df = pd.concat(all_processed_dfs, ignore_index=True)
    
    # Generate statistics
    stats_output_path = f'../data/election_{election_year}_sentiment_stats.csv'
    stats = generate_election_stats(combined_df, stats_output_path)
    
    logging.info(f"\nFinal Statistics for {election_year}:")
    logging.info(f"Total articles processed: {len(combined_df)}")
    logging.info(f"Before election: {len(combined_df[combined_df['period'] == 'Before Election'])}")
    logging.info(f"After election: {len(combined_df[combined_df['period'] == 'After Election'])}")
    
    return combined_df

def extract_network(url):
    """Extract the news network from the URL"""
    if 'fox' in url.lower():
        return 'Fox News'
    elif 'abc' in url.lower():
        return 'ABC News'
    elif 'msnbc' in url.lower():
        return 'MSNBC'
    else:
        return 'Unknown'

def extract_article_text(url):
    """Extract the article text from a URL using web scraping"""
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
        return re.sub(r'\s+', ' ', article_text).strip()
    except Exception as e:
        logging.warning(f"Error extracting text from {url}: {e}")
        return None

# Download VADER lexicon once at the beginning
try:
    nltk.data.find('vader_lexicon')
    logging.info("VADER lexicon already installed")
except LookupError:
    logging.info("Downloading VADER lexicon (one-time download)")
    nltk.download('vader_lexicon', quiet=True)

# Create a single SentimentIntensityAnalyzer instance to reuse
sia = SentimentIntensityAnalyzer()

def get_vader_sentiment_analysis(text):
    """Get binary sentiment (1=positive, 0=negative) using VADER"""
    if not text:
        return None
    
    sentiment = sia.polarity_scores(text)
    return 1 if sentiment['compound'] >= 0 else 0

def get_vader_tone_score(text):
    """Get VADER compound score (-1 to 1) as tone"""
    if not text:
        return None
    
    sentiment = sia.polarity_scores(text)
    return sentiment['compound']

def add_sentiment_analysis_to_df(df):
    """Add VADER sentiment analysis directly to the dataframe without saving to file"""
    result_df = df.copy()
    
    # Add new columns if they don't exist
    if 'vader_sentiment_analysis' not in result_df.columns:
        result_df['vader_sentiment_analysis'] = None
    if 'vader_tone_score' not in result_df.columns:
        result_df['vader_tone_score'] = None
    
    # Make sure URL column exists
    if 'url' not in result_df.columns:
        logging.warning("DataFrame has no URL column, cannot process")
        return result_df
        
    urls_to_process = result_df['url'].dropna().tolist()
    
    # Process each URL
    for i, url in enumerate(urls_to_process):
        if i % 10 == 0:
            logging.info(f"Processing URL {i+1}/{len(urls_to_process)}")
        
        article_text = extract_article_text(url)
        if article_text:
            binary_sentiment = get_vader_sentiment_analysis(article_text)
            compound_tone = get_vader_tone_score(article_text)
            
            idx = result_df[result_df['url'] == url].index
            result_df.loc[idx, 'vader_sentiment_analysis'] = binary_sentiment
            result_df.loc[idx, 'vader_tone_score'] = compound_tone
        
        # Small delay to prevent overloading websites
        time.sleep(0.1)
    
    return result_df

def add_sentiment_analysis(df, output_path):
    """Add VADER sentiment analysis and save to a new file (legacy function)"""
    result_df = df.copy()
    
    # Add new columns if they don't exist
    if 'vader_sentiment_analysis' not in result_df.columns:
        result_df['vader_sentiment_analysis'] = None
    if 'vader_tone_score' not in result_df.columns:
        result_df['vader_tone_score'] = None
    
    urls_to_process = df['url'].tolist()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Check for existing processed data
    if os.path.exists(output_path):
        existing_df = pd.read_csv(output_path)
        processed_urls = set(existing_df['url'])
        urls_to_process = [url for url in urls_to_process if url not in processed_urls]
        logging.info(f"Found existing file with {len(processed_urls)} processed URLs")
        logging.info(f"Remaining URLs to process: {len(urls_to_process)}")
    
    # Process each URL
    for i, url in enumerate(urls_to_process):
        if i % 10 == 0:
            logging.info(f"Processing URL {i+1}/{len(urls_to_process)}")
        
        article_text = extract_article_text(url)
        if article_text:
            binary_sentiment = get_vader_sentiment_analysis(article_text)
            compound_tone = get_vader_tone_score(article_text)
            
            idx = result_df[result_df['url'] == url].index
            result_df.loc[idx, 'vader_sentiment_analysis'] = binary_sentiment
            result_df.loc[idx, 'vader_tone_score'] = compound_tone
        
        # Save progress periodically
        if (i + 1) % 100 == 0 or i == len(urls_to_process) - 1:
            temp_df = result_df[result_df['vader_sentiment_analysis'].notnull()]
            if os.path.exists(output_path):
                existing_df = pd.read_csv(output_path)
                existing_urls = set(existing_df['url'])
                new_df = temp_df[~temp_df['url'].isin(existing_urls)]
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                combined_df.to_csv(output_path, index=False)
                logging.info(f"Progress saved: {len(combined_df)} total rows in {output_path}")
            else:
                temp_df.to_csv(output_path, index=False)
                logging.info(f"Progress saved: {len(temp_df)} rows in {output_path}")
        
        # Small delay to prevent overloading websites
        time.sleep(0.1)
    
    return result_df

def generate_election_stats(sentiment_df, output_stats_path):
    """Generate statistics for the sentiment analysis"""
    # Ensure parsed_date is datetime
    sentiment_df['parsed_date'] = pd.to_datetime(sentiment_df['parsed_date'])
    
    # Add period column if it doesn't exist
    if 'period' not in sentiment_df.columns:
        election_year = sentiment_df['election_year'].iloc[0] if 'election_year' in sentiment_df.columns else 2020
        
        if election_year == 2016:
            election_date = pd.Timestamp('2016-11-08')
        elif election_year == 2020:
            election_date = pd.Timestamp('2020-11-03')
        elif election_year == 2024:
            election_date = pd.Timestamp('2024-11-05')
        
        sentiment_df['period'] = 'Before Election'
        sentiment_df.loc[sentiment_df['parsed_date'] >= election_date, 'period'] = 'After Election'
    
    # Calculate sentiment statistics
    sentiment_stats = sentiment_df.groupby(['network', 'period']).agg(
        Positive_VADER=('vader_sentiment_analysis', 'mean'),
        Count=('vader_sentiment_analysis', 'count')
    ).reset_index()
    
    # Calculate tone statistics
    tone_columns = []
    if 'tone' in sentiment_df.columns:
        tone_columns.append('tone')
    if 'vader_tone_score' in sentiment_df.columns:
        tone_columns.append('vader_tone_score')
    
    if tone_columns:
        tone_stats = sentiment_df.groupby(['network', 'period'])[tone_columns].mean().reset_index()
        tone_stats.columns = [col if col in ['network', 'period'] else f'Mean {col.replace("_score", "")}' for col in tone_stats.columns]
        
        # Merge sentiment and tone statistics
        combined_stats = pd.merge(sentiment_stats, tone_stats, on=['network', 'period'])
    else:
        combined_stats = sentiment_stats
    
    # Save statistics to CSV
    combined_stats.to_csv(output_stats_path, index=False)
    
    # Log statistics summary
    election_year = sentiment_df['election_year'].iloc[0] if 'election_year' in sentiment_df.columns else 2020
    logging.info(f"\nSentiment Analysis Around {election_year} Election:")
    
    for network in sentiment_df['network'].unique():
        logging.info(f"\n{network}:")
        network_data = combined_stats[combined_stats['network'] == network]
        
        if len(network_data) >= 2:
            before = network_data[network_data['period'] == 'Before Election'].iloc[0]
            after = network_data[network_data['period'] == 'After Election'].iloc[0]
            
            logging.info(f"  Before Election: {before['Count']} articles, {before['Positive_VADER']*100:.1f}% positive")
            if 'Mean vader_tone' in before:
                logging.info(f"    VADER Tone: {before['Mean vader_tone']:.2f}")
            if 'Mean tone' in before:
                logging.info(f"    GDELT Tone: {before['Mean tone']:.2f}")
            
            logging.info(f"  After Election: {after['Count']} articles, {after['Positive_VADER']*100:.1f}% positive")
            if 'Mean vader_tone' in after:
                logging.info(f"    VADER Tone: {after['Mean vader_tone']:.2f}")
            if 'Mean tone' in after:
                logging.info(f"    GDELT Tone: {after['Mean tone']:.2f}")
    
    return combined_stats

def compare_elections():
    """Compare sentiment across multiple elections"""
    all_stats = []
    
    for year in [2016, 2020, 2024]:
        stats_file = f'../data/election_{year}_sentiment_stats.csv'
        
        if os.path.exists(stats_file):
            stats = pd.read_csv(stats_file)
            stats['election_year'] = year
            all_stats.append(stats)
        else:
            logging.warning(f"No statistics file found for {year}")
    
    if all_stats:
        combined_stats = pd.concat(all_stats, ignore_index=True)
        combined_stats.to_csv('../data/all_elections_sentiment_comparison.csv', index=False)
        
        logging.info("\nCross-Election Comparison:")
        for network in combined_stats['network'].unique():
            logging.info(f"\n{network}:")
            
            network_data = combined_stats[combined_stats['network'] == network]
            for year in sorted(network_data['election_year'].unique()):
                year_data = network_data[network_data['election_year'] == year]
                
                if len(year_data) >= 2:
                    before = year_data[year_data['period'] == 'Before Election'].iloc[0]
                    after = year_data[year_data['period'] == 'After Election'].iloc[0]
                    
                    logging.info(f"  {year} Election:")
                    logging.info(f"    Before: {before['Count']} articles, {before['Positive_VADER']*100:.1f}% positive")
                    logging.info(f"    After: {after['Count']} articles, {after['Positive_VADER']*100:.1f}% positive")
                    
                    if 'Mean vader_tone' in before and 'Mean vader_tone' in after:
                        tone_change = after['Mean vader_tone'] - before['Mean vader_tone']
                        logging.info(f"    VADER Tone Change: {tone_change:.2f}")
    
    return all_stats

def main():
    """Main function to run the analysis for all election years"""
    try:
        # Process each election year and update the original CSV files
        all_results = []
        for year in [2016, 2020, 2024]:
            result = analyze_election_sentiment(year)
            if result is not None:
                all_results.append(result)
        
        # Compare results across elections
        if all_results:
            compare_elections()
            logging.info("Analysis complete for all elections")
        else:
            logging.warning("No results were processed for any election year")
    
    except Exception as e:
        logging.error(f"Error in main execution: {e}", exc_info=True)

if __name__ == "__main__":
    main()