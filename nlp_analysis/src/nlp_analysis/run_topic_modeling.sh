#!/bin/bash

# This script installs required dependencies and runs the topic modeling script
# Place this file in your nlp_analysis directory and run with:
# ./run_topic_modeling.sh

# Make this script executable with:
# chmod +x run_topic_modeling.sh

# Install dependencies
echo "Installing dependencies..."
pip install pandas numpy scikit-learn matplotlib seaborn tqdm scipy

# Run the topic modeling script
echo "Running topic modeling..."
python topic_modeling.py

echo "Done!"