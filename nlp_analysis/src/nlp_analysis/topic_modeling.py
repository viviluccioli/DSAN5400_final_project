#!/usr/bin/env python
"""
Simplified GDELT topic modeling using scikit-learn instead of gensim.
This version avoids dependency conflicts in conda environments.
Place this directly in your nlp_analysis/src/nlp_analysis directory and run with:
$ python topic_modeling.py
"""

import pandas as pd
import numpy as np
import os
import re
import logging
from collections import Counter
from typing import List, Dict, Tuple, Optional, Union
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import sys
from pathlib import Path
import seaborn as sns
from tqdm import tqdm

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
os.makedirs(os.path.join(output_viz_dir, 'figures'), exist_ok=True)

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


def get_custom_stopwords():
    """
    Create a list of custom stopwords for news headlines.
    
    Returns:
        List of stopwords
    """
    # Add news-specific stopwords
    custom_stopwords = [
        'said', 'says', 'saying', 'told', 'reported', 'according', 'news', 
        'report', 'reports', 'reported', 'day', 'week', 'month', 'year',
        'today', 'yesterday', 'tomorrow', 'breaking', 'latest', 'update',
        'video', 'watch', 'view', 'click', 'read', 'full', 'story',
        'fox', 'msnbc', 'abc', 'cnn', 'network', 'media', 'new', 'just',
        'get', 'one', 'two', 'three', 'first', 'make', 'many', 'may',
        'show', 'time', 'call', 'back', 'take', 'last', 'week', 'look',
        'see', 'need', 'use', 'like', 'find', 'want', 'good', 'come',
        'way', 'after', 'over', 'think', 'also', 'know', 'right', 'still',
        'now', 'says', 'can', 'top', 'best', 'latest'
    ]
    
    return custom_stopwords

def clean_html_artifacts(text: str) -> str:
    """
    Remove HTML and CSS artifacts from text.
    """
    # Remove HTML tags
    text = re.sub(r'</?[^>]+>', ' ', text)
    # Remove HTML-related terms
    html_terms = ['html', 'http', 'href', 'css', 'src', 'div', 'span']
    for term in html_terms:
        text = re.sub(r'\b' + term + r'\b', '', text, flags=re.IGNORECASE)
    return text

def normalize_topic_label(topic_words: List[str]) -> str:
    """
    Create a normalized topic label by sorting words alphabetically.
    This ensures "police/man" and "man/police" would become the same label.
    """
    # Filter out HTML terms
    filtered_words = [w for w in topic_words if w.lower() not in 
                      ['html', 'http', 'href', 'css', 'src', 'div', 'span']]
    
    if not filtered_words:
        return "misc"
    
    # Prioritize words by importance
    topic_groups = {
        "politics": ["trump", "biden", "harris", "clinton", "obama", "election", 
                     "democrat", "republican", "impeachment", "congress", "senate",
                     "house", "white", "campaign", "president"],
        "crime": ["police", "shooting", "killed", "murder", "death", "suspect", 
                 "arrest", "crime", "court", "investigation"],
        "health": ["covid", "coronavirus", "pandemic", "vaccine", "health", 
                  "hospital", "outbreak", "virus", "infection", "disease"],
        "international": ["border", "immigration", "china", "russia", "ukraine", 
                         "afghanistan", "taliban", "iran", "syria", "israel"]
    }
    
    # Check which group the words belong to
    word_groups = {}
    for word in filtered_words[:5]:  # Consider top 5 words
        for group, terms in topic_groups.items():
            if any(term in word.lower() for term in terms):
                if group not in word_groups:
                    word_groups[group] = []
                word_groups[group].append(word)
    
    # If we found groups, use the most frequent group's top words
    if word_groups:
        top_group = max(word_groups.items(), key=lambda x: len(x[1]))[0]
        if len(word_groups[top_group]) >= 2:
            # Use top 2 words from the dominant group
            sorted_words = sorted(word_groups[top_group][:2])
            return "/".join(sorted_words)
    
    # Fall back to original method if no group dominates
    # Sort words alphabetically for consistency
    sorted_words = sorted(filtered_words[:2])
    return "/".join(sorted_words)

def sklearn_topic_modeling(texts: List[str], num_topics: int = 5) -> Tuple[List[int], Dict[int, List[str]]]:
    """
    Perform topic modeling using scikit-learn's LatentDirichletAllocation.
    
    Args:
        texts: List of text documents
        num_topics: Number of topics to extract
        
    Returns:
        Tuple of (topic_ids, topic_words)
    """
    if not texts:
        return [], {}
    
    # Create a custom vectorizer with stopwords
    custom_stopwords = get_custom_stopwords()
    vectorizer = CountVectorizer(
        max_df=0.95, 
        min_df=2, 
        stop_words='english',
        ngram_range=(1, 2),  # Allow bigrams
        max_features=5000
    )
    
    # Add custom stopwords
    if 'stop_words_' in vectorizer.__dict__ and vectorizer.stop_words_ is not None:
        vectorizer.stop_words_.update(custom_stopwords)
    else:
        # If stop_words_ not initialized yet, add after fitting
        pass
    
    # Create document-term matrix
    try:
        dtm = vectorizer.fit_transform(texts)
    except ValueError as e:
        print(f"Error creating document-term matrix: {str(e)}")
        return [], {}
    
    # If there's not enough data, return empty results
    if dtm.shape[0] < 5 or dtm.shape[1] < 10:
        return [], {}
        
    # Add custom stopwords again (in case they weren't added before)
    if 'stop_words_' in vectorizer.__dict__ and vectorizer.stop_words_ is not None:
        vectorizer.stop_words_.update(custom_stopwords)
    
    # Train LDA model
    lda = LatentDirichletAllocation(
        n_components=num_topics,
        random_state=42,
        max_iter=10,
        learning_method='online',
        n_jobs=-1  # Use all available cores
    )
    
    # Fit the model
    try:
        lda.fit(dtm)
    except Exception as e:
        print(f"Error fitting LDA model: {str(e)}")
        return [], {}
    
    # Get topics for each document
    doc_topic_matrix = lda.transform(dtm)
    doc_topics = doc_topic_matrix.argmax(axis=1).tolist()
    
    # Get feature names
    feature_names = vectorizer.get_feature_names_out()
    
    # Get top words for each topic
    topic_words = {}
    for topic_id, topic in enumerate(lda.components_):
        top_indices = topic.argsort()[-10:][::-1]  # Get indices of top 10 words
        words = [feature_names[i] for i in top_indices]
        topic_words[topic_id] = words
    
    return doc_topics, topic_words


def create_simple_topic_label(topic_words: List[str]) -> str:
    """
    Create a very concise topic label from a list of topic words.
    
    Args:
        topic_words: List of words associated with a topic
        
    Returns:
        A concise, readable topic label (2-3 words max)
    """
    if not topic_words:
        return "Misc."
    
    # Filter out very common political terms for more distinctive topics
    common_political_terms = {
        'president', 'trump', 'biden', 'government', 'administration', 'state', 
        'political', 'republican', 'democrat', 'gop', 'election'
    }
    
    # Keep terms that are more distinctive
    filtered_words = [w for w in topic_words if w not in common_political_terms]
    
    # If we filtered out all words, use one political term and one other word
    if not filtered_words:
        if len(topic_words) >= 2:
            return f"{topic_words[0]}/{topic_words[1]}"
        else:
            return topic_words[0]
    
    # Use at most 2 distinctive words for clarity
    if len(filtered_words) >= 2:
        return f"{filtered_words[0]}/{filtered_words[1]}"
    else:
        return filtered_words[0]


def plot_top_themes_by_year(df: pd.DataFrame, title: str, filename: str, min_count: int = 2) -> None:
    """
    Plot top themes by year for a single source, showing only significant patterns.
    
    Args:
        df: DataFrame with theme data
        title: Plot title
        filename: Output filename
        min_count: Minimum count to include in visualization
    """
    # Get only rank 1 themes for each year/month
    rank1_df = df[df['rank'] == 1].copy()
    
    # Count topic occurrences by year
    yearly_topics = rank1_df.groupby(['year', 'topic']).size().reset_index(name='count')
    
    # Filter for topics that appear with significant frequency
    significant_topics = yearly_topics.groupby('topic')['count'].sum()
    significant_topics = significant_topics[significant_topics >= min_count].index.tolist()
    
    # Get top 10 topics by total count
    top_topics = yearly_topics.groupby('topic')['count'].sum().nlargest(10).index.tolist()
    
    # Use intersection of significant and top topics
    topics_to_use = [t for t in top_topics if t in significant_topics][:10]  # Limit to 10
    
    if not topics_to_use:
        print(f"No significant topics found for visualization: {title}")
        return
    
    # Filter for only selected topics
    plot_data = yearly_topics[yearly_topics['topic'].isin(topics_to_use)]
    
    # Pivot data for heatmap
    pivot_data = plot_data.pivot(index='topic', columns='year', values='count').fillna(0)
    
    # Create figure with larger size for readability
    plt.figure(figsize=(14, 8))
    
    try:
        # Create heatmap with improved formatting
        ax = sns.heatmap(
            pivot_data, 
            cmap='YlOrRd', 
            annot=True, 
            fmt='.0f',  # No decimal places
            linewidths=.5,
            cbar_kws={'label': 'Frequency (months as top topic)'}
        )
        
        # Rotate y-axis labels for better readability
        plt.yticks(rotation=0, fontsize=11)
        
    except Exception as e:
        print(f"Error creating heatmap: {str(e)}")
        # Fallback to a simpler visualization
        plt.imshow(pivot_data, cmap='YlOrRd')
        plt.colorbar(label='Frequency (months as top topic)')
    
    # Set title and labels
    plt.title(title, fontsize=16)
    plt.ylabel('Topic', fontsize=12)
    plt.xlabel('Year', fontsize=12)
    
    # Rotate x-axis labels
    plt.xticks(rotation=0, fontsize=10)
    
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
            
        for year in tqdm(years_available, desc=f"Processing {source} years"):
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
    
    # Model headline topics with scikit-learn's LDA
    print("\nModeling headline topics with scikit-learn's LDA...")
    headline_results = {}
    
    for source in news_sources:
        print(f"Modeling headline topics for {source}...")
        # Create a list to store all topic assignments
        all_topics = []
        
        # Combine headline data by year and quarter for better topic coherence
        years_available = list(datasets[source].keys())
        if not years_available:
            print(f"No data available for {source}")
            continue
        
        # Define quarters
        quarters = {
            1: [1, 2, 3],     # Q1: Jan-Mar
            2: [4, 5, 6],     # Q2: Apr-Jun
            3: [7, 8, 9],     # Q3: Jul-Sep
            4: [10, 11, 12]   # Q4: Oct-Dec
        }
        
        # Process by year and quarter
        for year in tqdm(years_available, desc=f"Processing {source} years"):
            df = datasets[source][year]
            
            # Skip if headline column doesn't exist
            if 'headline_from_url' not in df.columns:
                print(f"No headline_from_url column in {source} data for {year}, skipping")
                continue
            
            # Process by quarter to get more coherent topics
            for quarter, months in quarters.items():
                # Get data for this quarter
                quarter_data = df[df['month'].isin(months)]
                
                if len(quarter_data) < 50:  # Need enough data for meaningful topics
                    print(f"Skipping {source} {year} Q{quarter}: insufficient headlines ({len(quarter_data)})")
                    continue
                
                # Get headlines and preprocess
                headlines = quarter_data['headline_from_url'].dropna()
                headlines = headlines.apply(preprocess_headline).tolist()
                
                # Filter empty headlines
                headlines = [h for h in headlines if h.strip()]
                
                if len(headlines) < 50:  # Further check after filtering
                    print(f"Skipping {source} {year} Q{quarter}: insufficient valid headlines ({len(headlines)})")
                    continue
                
                # Get months in this quarter that have data
                represented_months = quarter_data['month'].unique()
                
                # Perform topic modeling
                try:
                    # Determine number of topics based on data size
                    num_topics = min(5, max(3, len(headlines) // 100))
                    
                    # Get topic assignments and words
                    doc_topics, topic_words = sklearn_topic_modeling(headlines, num_topics=num_topics)
                    
                    if not doc_topics or not topic_words:
                        print(f"No topics found for {source} {year} Q{quarter}")
                        continue
                    
                    # Process results
                    topic_counts = Counter(doc_topics)
                    
                    # Get top 3 topics
                    top_topics = topic_counts.most_common(3)
                    
                    # Create simplified topic labels
                    topic_labels = {}
                    for topic_id in topic_words:
                        words = topic_words[topic_id]
                        topic_labels[topic_id] = normalize_topic_label(words)
                    
                    # Add entry for each month in the quarter
                    for month in represented_months:
                        month_data = quarter_data[quarter_data['month'] == month]
                        month_total = len(month_data)
                        
                        for rank, (topic_id, count) in enumerate(top_topics, 1):
                            # For headline topics, proportion the count by month
                            month_count = int(count * (month_total / len(quarter_data)))
                            if month_count < 1:
                                month_count = 1
                            
                            # Get topic label
                            if topic_id in topic_labels:
                                topic_name = topic_labels[topic_id]
                            else:
                                topic_name = f"Topic_{topic_id}"
                            
                            all_topics.append({
                                'month': month,
                                'year': year,
                                'topic': topic_name,
                                'topic_id': topic_id,
                                'rank': rank,
                                'count': month_count,
                                'total_articles': month_total,
                                'percentage': (month_count / month_total) * 100 if month_total > 0 else 0
                            })
                
                except Exception as e:
                    print(f"Error in topic modeling for {source} {year} Q{quarter}: {str(e)}")
                    continue
        
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
            output_file = os.path.join(output_data_dir, f"{source}_headline_topics_sklearn.csv")
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
            os.path.join(output_data_dir, "all_sources_headline_topics_sklearn.csv"),
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
                    filename=f"{source}_headline_topics_sklearn.png"
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
            print(f"  - Headlines (scikit-learn): {headline_count} topic entries")
            
            # Show sample of top headline topics
            if not headline_results[source].empty:
                top_headline_topics = headline_results[source][headline_results[source]['rank'] == 1]['topic'].value_counts().head(3)
                if not top_headline_topics.empty:
                    print(f"  - Most common headline topics: {', '.join(top_headline_topics.index.tolist())}")
    
    print("\nResults saved to:", output_data_dir)
    print("Visualizations saved to:", os.path.join(output_viz_dir, 'figures'))


if __name__ == "__main__":
    main()