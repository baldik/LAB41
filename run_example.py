#!/usr/bin/env python3
"""
Example script to run the JIRA Analytics tool against the Apache Kafka project.
This demonstrates how to use the tool with a real public JIRA instance.
"""

import os
import sys
from jira_analytics import JiraAnalytics

def main():
    """
    Main function to run the example.
    """
    print("JIRA Analytics Tool - Example Run")
    print("="*40)
    
    # Configuration for Apache Kafka project on public JIRA
    jira_url = "https://issues.apache.org/jira"
    username = ""  # Not needed for public access
    api_token = ""  # Not needed for public access
    project_key = "KAFKA"  # Apache Kafka project
    
    print(f"Connecting to JIRA: {jira_url}")
    print(f"Analyzing project: {project_key}")
    print()
    
    # Create JiraAnalytics instance
    jira_analytics = JiraAnalytics(jira_url, username, api_token)
    
    try:
        # Run the full analysis
        jira_analytics.run_full_analysis(project_key)
        
        print("\nAnalysis completed successfully!")
        print("Generated visualization files:")
        print("- open_duration_histogram.png")
        print("- status_time_distribution.png") 
        print("- daily_task_trend.png")
        print("- user_task_distribution.png")
        print("- logged_time_histogram.png")
        print("- priority_distribution.png")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()