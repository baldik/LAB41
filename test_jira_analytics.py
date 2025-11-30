#!/usr/bin/env python3
"""
Simple test file to verify the JIRA Analytics module structure.
"""

import sys
import os

# Add the workspace directory to the Python path
sys.path.insert(0, '/workspace')

try:
    from jira_analytics import JiraAnalytics
    print("✓ Successfully imported JiraAnalytics class")
    
    # Check if required methods exist
    required_methods = [
        'get_issues_by_project',
        'get_issue_transitions', 
        'calculate_open_duration',
        'calculate_time_in_status',
        'generate_open_duration_histogram',
        'generate_status_time_distribution',
        'generate_daily_task_trend',
        'generate_user_task_distribution',
        'generate_logged_time_histogram',
        'generate_priority_distribution',
        'run_full_analysis'
    ]
    
    methods_found = []
    methods_missing = []
    
    for method in required_methods:
        if hasattr(JiraAnalytics, method):
            methods_found.append(method)
        else:
            methods_missing.append(method)
    
    print(f"✓ Found {len(methods_found)} required methods: {', '.join(methods_found)}")
    
    if methods_missing:
        print(f"✗ Missing methods: {', '.join(methods_missing)}")
    else:
        print("✓ All required methods are present")
        
    # Check if main function exists in the module
    import importlib.util
    spec = importlib.util.spec_from_file_location("jira_analytics", "/workspace/jira_analytics.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    if hasattr(module, 'main'):
        print("✓ Main function found")
    else:
        print("✗ Main function not found")
        
    print("\n✓ Module structure verification completed successfully!")
    
except ImportError as e:
    print(f"✗ Failed to import JiraAnalytics: {e}")
except Exception as e:
    print(f"✗ Error during testing: {e}")