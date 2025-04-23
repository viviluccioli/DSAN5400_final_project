"""
This script checks if the media_topics.json file exists and verifies its structure.
Run this after preprocess_data.py to ensure the JSON file was created correctly.
"""

import json
from pathlib import Path
import sys

def check_json_file():
    # Possible locations for the JSON file
    possible_paths = [
        Path("website/data/media_topics.json"),
        Path("website/_site/data/media_topics.json"),
        Path("data/media_topics.json"),
        Path("media_topics.json")
    ]
    
    found_file = None
    
    # Check if the file exists in any of the possible locations
    for path in possible_paths:
        if path.exists():
            found_file = path
            print(f"Found JSON file at: {path}")
            break
    
    if not found_file:
        print("ERROR: JSON file not found in any of the expected locations.")
        print("Make sure you've run preprocess_data.py first.")
        return False
    
    # Try to load and validate the JSON file
    try:
        with open(found_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check basic structure
        if not isinstance(data, dict):
            print("ERROR: JSON file doesn't contain a dictionary as the root element.")
            return False
        
        # Check if the required keys exist
        if not all(key in data for key in ['fox', 'abc', 'msnbc']):
            print("ERROR: JSON file is missing one or more required keys (fox, abc, msnbc).")
            return False
        
        # Check data for each news source
        total_entries = 0
        for source in ['fox', 'abc', 'msnbc']:
            source_data = data[source]
            if not source_data:
                print(f"WARNING: No data found for {source}.")
                continue
            
            # Check years
            print(f"\n{source} data:")
            print(f"  Years: {list(source_data.keys())}")
            
            # Count entries
            source_entries = 0
            for year, months in source_data.items():
                for month, topics in months.items():
                    source_entries += len(topics)
            
            total_entries += source_entries
            print(f"  Total entries: {source_entries}")
        
        print(f"\nTotal entries across all sources: {total_entries}")
        
        if total_entries == 0:
            print("WARNING: No data entries found in the JSON file.")
            return False
        
        print("\nJSON file validation successful! The file exists and has the expected structure.")
        return True
        
    except json.JSONDecodeError:
        print("ERROR: The file is not valid JSON.")
        return False
    except Exception as e:
        print(f"ERROR: An error occurred while checking the JSON file: {e}")
        return False

if __name__ == "__main__":
    print("Checking for media_topics.json file...")
    check_json_file()