#!/bin/bash

# Script to run the JIRA Analytics tool on Linux
# This script handles the common setup and execution

echo "JIRA Analytics Tool"
echo "==================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if required packages are installed
echo "Checking required packages..."
python3 -c "import requests, pandas, matplotlib, seaborn, numpy, dateutil" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Required packages not found. Installing from requirements.txt..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install required packages"
        exit 1
    fi
fi

echo "All required packages are available."

# Run the analytics tool
echo "Running JIRA Analytics tool..."
python3 jira_analytics.py

echo "Analysis completed!"