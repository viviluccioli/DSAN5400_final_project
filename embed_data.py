import json
import os
from pathlib import Path

def embed_json_in_js():
    """
    Embed JSON data directly in the calendar.js file as a JavaScript variable
    to avoid CORS/file loading issues.
    """
    # Find project paths
    script_dir = Path.cwd()
    
    # Try to locate the JSON file
    json_paths = [
        script_dir / "website" / "data" / "media_topics.json",
        script_dir / "data" / "media_topics.json",
        script_dir / "website" / "_site" / "data" / "media_topics.json"
    ]
    
    json_file = None
    for path in json_paths:
        if path.exists():
            json_file = path
            print(f"Found JSON file at: {path}")
            break
    
    if not json_file:
        print("ERROR: Could not find media_topics.json file.")
        print("Please run preprocess_data.py first.")
        return False
    
    # Load the JSON data
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        print(f"Successfully loaded JSON data with {len(json_data.keys())} sources.")
    except Exception as e:
        print(f"ERROR loading JSON data: {e}")
        return False
    
    # Find the calendar.js file
    js_paths = [
        script_dir / "website" / "scripts" / "calendar.js",
        script_dir / "website" / "_site" / "scripts" / "calendar.js"
    ]
    
    js_file = None
    for path in js_paths:
        if path.exists():
            js_file = path
            print(f"Found calendar.js at: {path}")
            break
    
    if not js_file:
        print("ERROR: Could not find calendar.js file.")
        return False
    
    # Read the current JS file
    try:
        with open(js_file, 'r', encoding='utf-8') as f:
            js_content = f.read()
    except Exception as e:
        print(f"ERROR reading JS file: {e}")
        return False
    
    # Convert JSON to JavaScript
    json_str = json.dumps(json_data, indent=2)
    
    # Create the new JS content with embedded data
    embedded_js = f"""// calendar.js with embedded data

// Embedded topic data (generated automatically)
const embeddedTopicData = {json_str};

document.addEventListener('DOMContentLoaded', function() {{
    console.log("DOM loaded, initializing calendar with embedded data...");
    
    // Use the embedded data directly
    Object.assign(topicData.fox, embeddedTopicData.fox || {{}});
    Object.assign(topicData.abc, embeddedTopicData.abc || {{}});
    Object.assign(topicData.msnbc, embeddedTopicData.msnbc || {{}});
    
    // Create all year sections
    createYearSections();
    
    // Highlight the current year in navigation
    highlightCurrentYearInNav();
    
    // Set up scroll monitoring to update nav highlighting
    setupScrollMonitoring();
    
    // Set up year navigation buttons
    setupYearNavigation();
}});

// Keep track of loaded topic data
const topicData = {{
    fox: {{}},
    abc: {{}},
    msnbc: {{}}
}};

// No longer needed since we have embedded data
function loadTopicData() {{
    // This function is kept for compatibility but doesn't do anything anymore
    console.log("Using embedded data instead of loading from file");
    return Promise.resolve();
}}

// Function to generate placeholder data when JSON file can't be loaded
function generatePlaceholderData() {{
    console.log("Generating placeholder data...");
    // Create some sample data for visualization testing
    const years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025];
    
    const foxTopics = ['Immigration', 'Economy', 'National Security', 'Crime', 'Foreign Policy', 'Military'];
    const abcTopics = ['Healthcare', 'Economy', 'Education', 'Politics', 'International', 'Science'];
    const msnbcTopics = ['Social Justice', 'Healthcare', 'Climate Change', 'Economy', 'Education', 'Civil Rights'];
    
    // Generate data for each source, year and month
    for (const year of years) {{
        topicData.fox[year] = {{}};
        topicData.abc[year] = {{}};
        topicData.msnbc[year] = {{}};
        
        const maxMonth = year === 2025 ? 4 : 12;
        
        for (let month = 1; month <= maxMonth; month++) {{
            // Generate Fox topics
            topicData.fox[year][month] = [
                {{ topic: foxTopics[Math.floor(Math.random() * 3)], rank: 1 }},
                {{ topic: foxTopics[Math.floor(Math.random() * 3) + 3], rank: 2 }},
                {{ topic: 'Other', rank: 3 }}
            ];
            
            // Generate ABC topics
            topicData.abc[year][month] = [
                {{ topic: abcTopics[Math.floor(Math.random() * 3)], rank: 1 }},
                {{ topic: abcTopics[Math.floor(Math.random() * 3) + 3], rank: 2 }},
                {{ topic: 'Other', rank: 3 }}
            ];
            
            // Generate MSNBC topics
            topicData.msnbc[year][month] = [
                {{ topic: msnbcTopics[Math.floor(Math.random() * 3)], rank: 1 }},
                {{ topic: msnbcTopics[Math.floor(Math.random() * 3) + 3], rank: 2 }},
                {{ topic: 'Other', rank: 3 }}
            ];
        }}
    }}
    console.log("Placeholder data generated. Sample:", topicData.fox[2015][1]);
}}

"""
    
    # Append the rest of the original JS (excluding the initial parts we replaced)
    # Look for the first function after the initial setup
    if "function createYearSections()" in js_content:
        start_idx = js_content.find("function createYearSections()")
        embedded_js += js_content[start_idx:]
    else:
        print("WARNING: Could not find createYearSections function in JS file.")
        print("The generated file might not work correctly.")
        # Just append everything after our custom code
    
    # Write the new JS file
    output_js = js_file.with_name("calendar_embedded.js")
    try:
        with open(output_js, 'w', encoding='utf-8') as f:
            f.write(embedded_js)
        print(f"Successfully created JS file with embedded data at: {output_js}")
        
        # Create backup of original
        backup_js = js_file.with_name("calendar_original.js")
        with open(backup_js, 'w', encoding='utf-8') as f:
            f.write(js_content)
        print(f"Backed up original JS to: {backup_js}")
        
        # Replace the original file
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(embedded_js)
        print(f"Successfully updated original JS file with embedded data.")
        
        return True
    except Exception as e:
        print(f"ERROR writing JS file: {e}")
        return False

if __name__ == "__main__":
    print("Embedding JSON data in calendar.js...")
    embed_json_in_js()