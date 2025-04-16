#!/usr/bin/env python
"""
Simple script for GDELT topic modeling.
Place this directly in your nlp_analysis/src/nlp_analysis directory and run with:
$ python topic_modeling.py

This script:
1. Extracts top themes from V2Themes column
2. Models topics from headlines
3. Saves datasets to data/topic_modeling
4. Creates visualizations in results/topic_modeling
"""

import pandas as pd
import numpy as np
import os
import re
import logging
from collections import Counter
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Union
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.decomposition import NMF
import sys
from pathlib import Path
import seaborn as sns

# Set up the paths
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent
nlp_analysis_dir = src_dir.parent
project_dir = nlp_analysis_dir.parent

# Input data directory
data_dir = os.path.join(project_dir, 'data')

# Output directories
output_data_dir = os.path.join(project_dir, 'data', 'topic_modeling')
output_viz_dir = os.path.join(project_dir, 'results', 'topic_modeling')

# Create output directories if they don't exist
os.makedirs(output_data_dir, exist_ok=True)
os.makedirs(output_viz_dir, exist_ok=True)
os.makedirs(os.path.join(output_viz_dir, "figures"), exist_ok=True)

# Simple console logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


def parse_v2themes_string(v2themes_str: Union[str, float]) -> List[str]:
    """
    Parse the V2Themes string into a list of individual themes.
    
    Args:
        v2themes_str: String from V2Themes column
        
    Returns:
        List of individual themes
    """
    if pd.isna(v2themes_str) or not isinstance(v2themes_str, str):
        return []
    
    # Split by semicolon
    themes = v2themes_str.split(';')
    
    # Clean up themes (remove empty strings)
    themes = [theme.strip() for theme in themes if theme.strip()]
    
    return themes


def preprocess_headline(headline: str) -> str:
    """
    Preprocess headlines for topic modeling.
    
    Args:
        headline: Raw headline text
        
    Returns:
        Preprocessed headline
    """
    # Convert to string in case it's not
    headline = str(headline)
    
    # Replace URLs with placeholder
    headline = re.sub(r'https?://\S+', '', headline)
    
    # Replace special characters
    headline = re.sub(r'[^\w\s]', ' ', headline)
    
    # Replace multiple spaces with a single space
    headline = re.sub(r'\s+', ' ', headline).strip()
    
    return headline


def nmf_modeling(texts: List[str]) -> Tuple[List[int], np.ndarray, Dict[int, List[str]]]:
    """
    Perform topic modeling using NMF.
    
    Args:
        texts: List of text documents
        
    Returns:
        Tuple of (topic_ids, document-topic matrix, topic_words)
    """
    # Initialize TF-IDF vectorizer
    tfidf_vectorizer = TfidfVectorizer(
        max_df=0.95, 
        min_df=2, 
        stop_words='english',
        ngram_range=(1, 2)  # Include bigrams for better topics
    )
    
    # Create document-term matrix
    dtm = tfidf_vectorizer.fit_transform(texts)
    
    # Get feature names
    feature_names = np.array(tfidf_vectorizer.get_feature_names_out())
    
    # Determine number of topics based on corpus size
    n_topics = min(10, max(3, len(texts) // 20))
    
    # Apply NMF - removed alpha parameter which is causing errors
    # Use default parameters for NMF to ensure compatibility
    nmf = NMF(
        n_components=n_topics,
        random_state=42,
        max_iter=200
    )
    
    # Get document-topic matrix
    doc_topic = nmf.fit_transform(dtm)
    
    # Get the dominant topic for each document
    topic_ids = doc_topic.argmax(axis=1)
    
    # Get topic-word matrix
    topic_word = nmf.components_
    
    # Extract top words for each topic
    topic_words = {}
    for topic_idx, topic in enumerate(topic_word):
        top_word_indices = topic.argsort()[:-11:-1]  # Get indices of top 10 words
        top_words = [feature_names[i] for i in top_word_indices]
        topic_words[topic_idx] = top_words
    
    return topic_ids, doc_topic, topic_words


def plot_top_themes_by_year(df: pd.DataFrame, title: str, filename: str) -> None:
    """
    Plot top themes by year for a single source.
    
    Args:
        df: DataFrame with theme data
        title: Plot title
        filename: Output filename
    """
    # Get only rank 1 themes for each year/month
    rank1_df = df[df['rank'] == 1].copy()
    
    # Create a year-month string for ordering
    rank1_df['year_month'] = rank1_df.apply(lambda x: f"{x['year']}-{x['month']:02d}", axis=1)
    
    # Sort by year and month
    rank1_df = rank1_df.sort_values(['year', 'month'])
    
    # Count topic occurrences by year
    yearly_topics = rank1_df.groupby(['year', 'topic']).size().reset_index(name='count')
    
    # Get top 10 topics by total count
    top_topics = yearly_topics.groupby('topic')['count'].sum().nlargest(10).index.tolist()
    
    # Filter for only top topics
    plot_data = yearly_topics[yearly_topics['topic'].isin(top_topics)]
    
    # Pivot data for heatmap
    pivot_data = plot_data.pivot(index='topic', columns='year', values='count').fillna(0)
    
    # Create figure
    plt.figure(figsize=(12, 8))
    
    try:
        # Create heatmap
        ax = sns.heatmap(
            pivot_data, 
            cmap='YlOrRd', 
            annot=True, 
            fmt='g', 
            linewidths=.5,
            cbar_kws={'label': 'Count (months as top topic)'}
        )
    except Exception as e:
        print(f"Error creating heatmap: {str(e)}")
        # Fallback to a simpler visualization
        plt.imshow(pivot_data, cmap='YlOrRd')
        plt.colorbar(label='Count (months as top topic)')
    
    # Set title and labels
    plt.title(title, fontsize=16)
    plt.ylabel('Topic')
    plt.xlabel('Year')
    
    # Rotate x-axis labels
    plt.xticks(rotation=0)
    
    # Save figure
    plt.tight_layout()
    plt.savefig(os.path.join(output_viz_dir, 'figures', filename), dpi=300)
    plt.close()


def main():
    """
    Main function to run the topic modeling pipeline.
    """
    news_sources = ["fox", "abc", "msnbc"]
    years = list(range(2015, 2026))  # 2015-2025
    
    print("\n==== Starting topic modeling pipeline ====\n")
    
    # Dictionary to store datasets
    datasets = {source: {} for source in news_sources}
    
    # Load datasets
    print("Loading datasets...")
    for source in news_sources:
        for year in years:
            file_path = os.path.join(data_dir, source, f"{source}{year}.csv")
            if os.path.exists(file_path):
                print(f"Loading {source} data for {year}...")
                try:
                    df = pd.read_csv(file_path)
                    
                    # Extract month and year from parsed_date
                    if 'parsed_date' in df.columns:
                        df['date'] = pd.to_datetime(df['parsed_date'])
                        df['month'] = df['date'].dt.month
                        df['year'] = df['date'].dt.year
                    else:
                        print(f"No 'parsed_date' column in {file_path}, trying to extract from DATE")
                        if 'DATE' in df.columns:
                            # Convert GDELT DATE format (YYYYMMDDHHMMSS) to datetime
                            df['date'] = pd.to_datetime(df['DATE'].astype(str), format='%Y%m%d%H%M%S', errors='coerce')
                            df['month'] = df['date'].dt.month
                            df['year'] = df['date'].dt.year
                        else:
                            print(f"No date column found in {file_path}, skipping")
                            continue
                    
                    # Clean up headline column
                    if 'headline_from_url' in df.columns:
                        df['headline_from_url'] = df['headline_from_url'].astype(str).apply(
                            lambda x: x if x != 'nan' else ""
                        )
                    
                    datasets[source][year] = df
                    print(f"Loaded {len(df)} rows from {file_path}")
                except Exception as e:
                    print(f"Error loading {file_path}: {str(e)}")
            else:
                print(f"File not found - {file_path}")
    
    # Extract themes from V2Themes
    print("\nExtracting V2Themes topics...")
    v2themes_results = {}
    
    for source in news_sources:
        print(f"Extracting V2Themes for {source}...")
        # Create a list to store all theme counts
        all_theme_counts = []
        
        years_available = list(datasets[source].keys())
        if not years_available:
            print(f"No data available for {source}")
            continue
            
        for year in years_available:
            df = datasets[source][year]
            
            # Skip if V2Themes column doesn't exist
            if 'V2Themes' not in df.columns:
                print(f"No V2Themes column in {source} data for {year}, skipping")
                continue
            
            # Group by month and year
            grouped = df.groupby(['year', 'month'])
            
            for (yr, mn), group in grouped:
                # Extract all themes from the group
                all_themes = []
                for themes_str in group['V2Themes'].dropna():
                    themes = parse_v2themes_string(themes_str)
                    all_themes.extend(themes)
                
                # Count themes
                if all_themes:
                    theme_counter = Counter(all_themes)
                    top_themes = theme_counter.most_common(3)
                    
                    # Add to results
                    for rank, (theme, count) in enumerate(top_themes, 1):
                        all_theme_counts.append({
                            'month': mn,
                            'year': yr,
                            'topic': theme,
                            'rank': rank,
                            'count': count,
                            'total_articles': len(group)
                        })
        
        # Convert to dataframe
        if all_theme_counts:
            v2themes_results[source] = pd.DataFrame(all_theme_counts)
            
            # Calculate percentage
            v2themes_results[source]['percentage'] = (v2themes_results[source]['count'] / 
                                                   v2themes_results[source]['total_articles']) * 100
        else:
            v2themes_results[source] = pd.DataFrame(
                columns=['month', 'year', 'topic', 'rank', 'count', 'total_articles', 'percentage']
            )
    
    # Model headline topics
    print("\nModeling headline topics...")
    headline_results = {}
    
    for source in news_sources:
        print(f"Modeling headline topics for {source}...")
        # Create a list to store all topic assignments
        all_topics = []
        
        years_available = list(datasets[source].keys())
        if not years_available:
            print(f"No data available for {source}")
            continue
            
        for year in years_available:
            df = datasets[source][year]
            
            # Skip if headline column doesn't exist
            if 'headline_from_url' not in df.columns:
                print(f"No headline_from_url column in {source} data for {year}, skipping")
                continue
            
            # Group by month and year
            grouped = df.groupby(['year', 'month'])
            
            for (yr, mn), group in grouped:
                # Get headlines and preprocess
                headlines = group['headline_from_url'].dropna()
                headlines = headlines.apply(preprocess_headline).tolist()
                
                # Filter empty headlines
                headlines = [h for h in headlines if h.strip()]
                
                if len(headlines) < 10:  # Skip if too few headlines
                    print(f"Skipping {source} {yr}-{mn}: insufficient headlines ({len(headlines)})")
                    continue
                
                # Perform topic modeling
                try:
                    topics, topic_probs, topic_words = nmf_modeling(headlines)
                except Exception as e:
                    print(f"Error in topic modeling for {source} {yr}-{mn}: {str(e)}")
                    continue
                
                # Get top 3 topics
                topic_counter = Counter(topics)
                
                top_topics = topic_counter.most_common(3)
                
                # Add to results
                for rank, (topic_id, count) in enumerate(top_topics, 1):
                    # Get topic words
                    if topic_id in topic_words:
                        topic_name = ' '.join(topic_words[topic_id][:3])
                    else:
                        topic_name = f"Topic_{topic_id}"
                    
                    all_topics.append({
                        'month': mn,
                        'year': yr,
                        'topic': topic_name,
                        'topic_id': topic_id,
                        'rank': rank,
                        'count': count,
                        'total_articles': len(headlines),
                        'percentage': (count / len(headlines)) * 100 if len(headlines) > 0 else 0
                    })
        
        # Convert to dataframe
        if all_topics:
            headline_results[source] = pd.DataFrame(all_topics)
        else:
            headline_results[source] = pd.DataFrame(
                columns=['month', 'year', 'topic', 'topic_id', 'rank', 
                         'count', 'total_articles', 'percentage']
            )
    
    # Save results
    print("\nSaving results...")
    for source in news_sources:
        if source in v2themes_results:
            output_file = os.path.join(output_data_dir, f"{source}_v2themes_topics.csv")
            print(f"Saving V2Themes results to {output_file}")
            v2themes_results[source].to_csv(output_file, index=False)
        
        if source in headline_results:
            output_file = os.path.join(output_data_dir, f"{source}_headline_topics.csv")
            print(f"Saving headline topics to {output_file}")
            headline_results[source].to_csv(output_file, index=False)
    
    # Create combined files
    # Combine V2Themes results
    all_v2themes = []
    for source, df in v2themes_results.items():
        df = df.copy()
        df['source'] = source
        all_v2themes.append(df)
    
    if all_v2themes:
        combined_v2themes = pd.concat(all_v2themes, ignore_index=True)
        combined_v2themes.to_csv(
            os.path.join(output_data_dir, "all_sources_v2themes_topics.csv"),
            index=False
        )
    
    # Combine headline topics
    all_headlines = []
    for source, df in headline_results.items():
        df = df.copy()
        df['source'] = source
        all_headlines.append(df)
    
    if all_headlines:
        combined_headlines = pd.concat(all_headlines, ignore_index=True)
        combined_headlines.to_csv(
            os.path.join(output_data_dir, "all_sources_headline_topics.csv"),
            index=False
        )
    
    # Create visualizations
    print("\nCreating visualizations...")
    for source in news_sources:
        if source in v2themes_results and not v2themes_results[source].empty:
            try:
                plot_top_themes_by_year(
                    v2themes_results[source], 
                    title=f"Top V2Themes for {source.upper()} News by Year",
                    filename=f"{source}_v2themes_by_year.png"
                )
                print(f"Created {source} V2Themes visualization")
            except Exception as e:
                print(f"Error creating visualization for {source} V2Themes: {str(e)}")
        
        if source in headline_results and not headline_results[source].empty:
            try:
                plot_top_themes_by_year(
                    headline_results[source], 
                    title=f"Top Headline Topics for {source.upper()} News by Year",
                    filename=f"{source}_headline_topics_by_year.png"
                )
                print(f"Created {source} headline topics visualization")
            except Exception as e:
                print(f"Error creating visualization for {source} headline topics: {str(e)}")
    
    print("\nPipeline completed successfully!")
    
    # Print summary of results
    print("\nTopic Modeling Results Summary:")
    print("==============================")
    
    for source in news_sources:
        print(f"\n{source.upper()} Results:")
        
        if source in v2themes_results:
            v2_count = len(v2themes_results[source])
            print(f"  - V2Themes: {v2_count} topic entries")
            
            # Show sample of top themes
            if not v2themes_results[source].empty:
                top_themes = v2themes_results[source][v2themes_results[source]['rank'] == 1]['topic'].value_counts().head(3)
                if not top_themes.empty:
                    print(f"  - Most common top themes: {', '.join(top_themes.index.tolist())}")
        
        if source in headline_results:
            headline_count = len(headline_results[source])
            print(f"  - Headlines: {headline_count} topic entries")
            
            # Show sample of top headline topics
            if not headline_results[source].empty:
                top_headline_topics = headline_results[source][headline_results[source]['rank'] == 1]['topic'].value_counts().head(3)
                if not top_headline_topics.empty:
                    print(f"  - Most common headline topics: {', '.join(top_headline_topics.index.tolist())}")
    
    print("\nResults saved to:", output_data_dir)
    print("Visualizations saved to:", os.path.join(output_viz_dir, 'figures'))


if __name__ == "__main__":
    main()