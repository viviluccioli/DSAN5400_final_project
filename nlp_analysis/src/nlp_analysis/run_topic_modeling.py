#!/usr/bin/env python
"""
Script to run the GDELT topic modeling pipeline.
Place this file in nlp_analysis/src/nlp_analysis/ directory.

Example usage from nlp_analysis directory:
    poetry run python -m src.nlp_analysis.run_topic_modeling
"""

import os
import sys
from pathlib import Path

# Add the root project directory to the Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(project_root))

# Import the topic modeling module
from src.nlp_analysis.topic_modeling import GDELTTopicModeling


def main():
    """
    Run the topic modeling pipeline with default settings.
    """
    # Set up paths
    data_dir = os.path.join(project_root, 'data')
    output_dir = os.path.join(project_root, 'nlp_analysis', 'results', 'topic_modeling')
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize and run the topic modeling pipeline
    topic_modeler = GDELTTopicModeling(
        data_dir=data_dir,
        output_dir=output_dir
    )
    
    # Run the pipeline
    v2themes_results, headline_results = topic_modeler.run_pipeline()
    
    # Print summary of results
    print("\nTopic Modeling Results Summary:")
    print("==============================")
    
    for source in ['fox', 'abc', 'msnbc']:
        print(f"\n{source.upper()} Results:")
        
        if source in v2themes_results:
            v2_count = len(v2themes_results[source])
            print(f"  - V2Themes: {v2_count} topic entries")
            
            # Show sample of top themes
            if not v2themes_results[source].empty:
                top_themes = v2themes_results[source][v2themes_results[source]['rank'] == 1]['topic'].value_counts().head(3)
                print(f"  - Most common top themes: {', '.join(top_themes.index.tolist())}")
        
        if source in headline_results:
            headline_count = len(headline_results[source])
            print(f"  - Headlines: {headline_count} topic entries")
            
            # Show sample of top headline topics
            if not headline_results[source].empty:
                top_headline_topics = headline_results[source][headline_results[source]['rank'] == 1]['topic'].value_counts().head(3)
                print(f"  - Most common headline topics: {', '.join(top_headline_topics.index.tolist())}")
    
    print("\nResults saved to:", output_dir)
    print("Visualizations saved to:", os.path.join(output_dir, 'figures'))


if __name__ == "__main__":
    main()