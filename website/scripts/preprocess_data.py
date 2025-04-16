import os
import csv
import json
from pathlib import Path
import sys

def preprocess_csv_to_json():
    """
    Convert CSV topic modeling data to JSON format for easier loading in the web app.
    This script can be run from any directory but expects the project structure to be:
    - data/topic_modeling/*.csv
    - website/data/ (output location)
    """
    # Find the project root by looking for the data/topic_modeling directory
    current_dir = Path.cwd()
    project_root = None

    # Check if we're in the project root
    if (current_dir / "data" / "topic_modeling").exists():
        project_root = current_dir
    # Check if we're in website/scripts
    elif (current_dir.parent / "data" / "topic_modeling").exists():
        project_root = current_dir.parent.parent
    # Check if we're in website directory
    elif (current_dir.parent / "data" / "topic_modeling").exists():
        project_root = current_dir.parent
    
    if not project_root:
        print("Error: Cannot find project root with data/topic_modeling directory")
        print("Current directory:", current_dir)
        sys.exit(1)
    
    # Input CSV files
    topic_dir = project_root / "data" / "topic_modeling"
    fox_csv = topic_dir / "fox_headline_topics_sklearn.csv"
    abc_csv = topic_dir / "abc_headline_topics_sklearn.csv"
    msnbc_csv = topic_dir / "msnbc_headline_topics_sklearn.csv"
    
    # Output JSON file
    output_dir = project_root / "website" / "data"
    output_file = output_dir / "media_topics.json"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Print paths for verification
    print(f"Project root: {project_root}")
    print(f"Input data directory: {topic_dir}")
    print(f"Output file: {output_file}")
    
    # Initialize data structure
    media_data = {
        "fox": {},
        "abc": {},
        "msnbc": {}
    }
    
    # Helper function to process a CSV file
    def process_csv(file_path, source_key):
        if not file_path.exists():
            print(f"Warning: {file_path} does not exist")
            return
        
        print(f"Processing {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)  # Skip header row
            
            for row in reader:
                if not row or len(row) < 5:  # Make sure row has enough columns
                    continue
                
                try:
                    month = int(row[0])
                    year = int(row[1])
                    topic = row[2]
                    rank = int(row[4])
                    
                    # Only consider top 3 topics per month
                    if rank > 3:
                        continue
                    
                    # Initialize year dictionary if it doesn't exist
                    if str(year) not in media_data[source_key]:
                        media_data[source_key][str(year)] = {}
                    
                    # Initialize month array if it doesn't exist
                    if str(month) not in media_data[source_key][str(year)]:
                        media_data[source_key][str(year)][str(month)] = []
                    
                    # Add topic with its rank
                    media_data[source_key][str(year)][str(month)].append({
                        "topic": topic,
                        "rank": rank
                    })
                except (ValueError, IndexError) as e:
                    print(f"Error processing row {row}: {e}")
                    continue
        
        # Sort topics by rank for each month
        for year in media_data[source_key]:
            for month in media_data[source_key][year]:
                media_data[source_key][year][month].sort(key=lambda x: x["rank"])
    
    # Process each CSV file
    process_csv(fox_csv, "fox")
    process_csv(abc_csv, "abc")
    process_csv(msnbc_csv, "msnbc")
    
    # Write the combined data to a JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(media_data, f, indent=2)
    
    print(f"Data successfully converted and saved to {output_file}")
    
    # Also copy to the _site directory if it exists
    site_dir = project_root / "website" / "_site" / "data"
    if site_dir.exists():
        site_output = site_dir / "media_topics.json"
        os.makedirs(site_dir, exist_ok=True)
        with open(site_output, 'w', encoding='utf-8') as f:
            json.dump(media_data, f, indent=2)
        print(f"Also copied data to {site_output}")

if __name__ == "__main__":
    preprocess_csv_to_json()