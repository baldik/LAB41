#!/usr/bin/env python3
"""
JIRA Analytics Tool

This program connects to JIRA via REST API and generates analytical reports
based on the provided requirements.
"""

import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from dateutil import parser
import numpy as np
import sys
import os
from typing import Dict, List, Tuple, Optional
from collections import defaultdict


class JiraAnalytics:
    """
    A class to connect to JIRA via REST API and generate analytical reports.
    """
    
    def __init__(self, jira_url: str, username: str, api_token: str):
        """
        Initialize the JiraAnalytics class with connection parameters.
        
        Args:
            jira_url (str): Base URL of the JIRA instance
            username (str): JIRA username
            api_token (str): JIRA API token
        """
        self.jira_url = jira_url.rstrip('/')
        self.auth = (username, api_token)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({'Content-Type': 'application/json'})
        
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Make a request to the JIRA API.
        
        Args:
            endpoint (str): API endpoint
            params (Dict): Request parameters
            
        Returns:
            Dict: JSON response from the API
        """
        url = f"{self.jira_url}{endpoint}"
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}")
            return {}
    
    def get_issues_by_project(self, project_key: str, max_results: int = 1000) -> List[Dict]:
        """
        Get all issues for a specific project.
        
        Args:
            project_key (str): Project key (e.g., 'KAFKA', 'HDFS')
            max_results (int): Maximum number of results to return
            
        Returns:
            List[Dict]: List of issues
        """
        jql = f"project = '{project_key}' ORDER BY created DESC"
        params = {
            'jql': jql,
            'maxResults': max_results,
            'fields': 'key,summary,status,created,updated,assignee,reporter,priority,timetracking,issuetype'
        }
        
        # Get total number of issues first
        response = self._make_request('/rest/api/2/search', {'jql': jql, 'maxResults': 0})
        total_issues = response.get('total', 0)
        
        # Now fetch all issues in batches
        all_issues = []
        start_at = 0
        
        while start_at < total_issues:
            params['startAt'] = start_at
            response = self._make_request('/rest/api/2/search', params)
            issues = response.get('issues', [])
            all_issues.extend(issues)
            start_at += max_results
            
        return all_issues
    
    def get_issue_transitions(self, issue_key: str) -> List[Dict]:
        """
        Get transition history for a specific issue.
        
        Args:
            issue_key (str): Issue key (e.g., 'KAFKA-1234')
            
        Returns:
            List[Dict]: List of transitions with timestamps
        """
        response = self._make_request(f'/rest/api/2/issue/{issue_key}', {
            'expand': 'changelog'
        })
        
        transitions = []
        changelog = response.get('changelog', {})
        histories = changelog.get('histories', [])
        
        for history in histories:
            for item in history.get('items', []):
                if item.get('field') == 'status':
                    transitions.append({
                        'issue_key': issue_key,
                        'timestamp': history['created'],
                        'from_status': item.get('fromString'),
                        'to_status': item.get('toString'),
                        'author': history.get('author', {}).get('displayName', 'Unknown')
                    })
        
        # Sort transitions by timestamp
        transitions.sort(key=lambda x: x['timestamp'])
        return transitions
    
    def calculate_open_duration(self, issue: Dict) -> Optional[float]:
        """
        Calculate the duration a task was open (from creation to closure).
        
        Args:
            issue (Dict): JIRA issue data
            
        Returns:
            Optional[float]: Duration in days, or None if not closed
        """
        created_str = issue['fields']['created']
        created = parser.parse(created_str)
        
        # Check if the issue is closed by looking at status
        status_name = issue['fields']['status']['name'].lower()
        if 'closed' not in status_name and 'resolved' not in status_name and 'done' not in status_name:
            return None  # Not a closed issue
        
        # Find the actual closed date from transitions if possible
        # For now, we'll use the updated date as the closed date
        updated_str = issue['fields']['updated']
        updated = parser.parse(updated_str)
        
        duration = (updated - created).total_seconds() / (24 * 3600)  # Convert to days
        return duration
    
    def get_all_transitions_for_project(self, project_key: str, issues: List[Dict]) -> List[Dict]:
        """
        Get all transitions for all issues in a project.
        
        Args:
            project_key (str): Project key
            issues (List[Dict]): List of issues
            
        Returns:
            List[Dict]: All transitions for the project
        """
        all_transitions = []
        for issue in issues:
            transitions = self.get_issue_transitions(issue['key'])
            all_transitions.extend(transitions)
        return all_transitions
    
    def calculate_time_in_status(self, issue: Dict) -> Dict[str, float]:
        """
        Calculate time spent in each status for an issue.
        
        Args:
            issue (Dict): JIRA issue data
            
        Returns:
            Dict[str, float]: Time spent in each status (in days)
        """
        transitions = self.get_issue_transitions(issue['key'])
        if not transitions:
            return {}
        
        # Get the creation time as the starting point
        created = parser.parse(issue['fields']['created'])
        time_in_status = {}
        
        # Start with the initial status
        current_status = issue['fields']['status']['name']
        status_start_time = created
        
        # Process each transition
        for transition in transitions:
            transition_time = parser.parse(transition['timestamp'])
            
            # Add time spent in the previous status
            if transition['from_status']:
                time_spent = (transition_time - status_start_time).total_seconds() / (24 * 3600)
                if transition['from_status'] not in time_in_status:
                    time_in_status[transition['from_status']] = 0
                time_in_status[transition['from_status']] += time_spent
            
            # Update for next status
            status_start_time = transition_time
            current_status = transition['to_status']
        
        # Handle the final status (until issue was closed)
        if 'closed' in current_status.lower() or 'resolved' in current_status.lower() or 'done' in current_status.lower():
            updated = parser.parse(issue['fields']['updated'])
            final_time_spent = (updated - status_start_time).total_seconds() / (24 * 3600)
            if current_status not in time_in_status:
                time_in_status[current_status] = 0
            time_in_status[current_status] += final_time_spent
        
        return time_in_status
    
    def generate_open_duration_histogram(self, issues: List[Dict]) -> None:
        """
        Generate histogram of time tasks spent in open state.
        
        Args:
            issues (List[Dict]): List of JIRA issues
        """
        durations = []
        for issue in issues:
            duration = self.calculate_open_duration(issue)
            if duration is not None:
                durations.append(duration)
        
        if not durations:
            print("No closed issues found for analysis.")
            return
        
        plt.figure(figsize=(12, 6))
        plt.hist(durations, bins=30, edgecolor='black')
        plt.title('Distribution of Time Tasks Spent in Open State')
        plt.xlabel('Time in Open State (days)')
        plt.ylabel('Number of Tasks')
        plt.grid(axis='y', alpha=0.75)
        plt.tight_layout()
        plt.savefig('open_duration_histogram.png')
        plt.show()
        print("Open duration histogram saved as 'open_duration_histogram.png'")
    
    def generate_status_time_distribution(self, issues: List[Dict]) -> None:
        """
        Generate distribution of time spent in each status.
        
        Args:
            issues (List[Dict]): List of JIRA issues
        """
        all_status_times = defaultdict(list)
        
        for issue in issues:
            status_times = self.calculate_time_in_status(issue)
            for status, time_spent in status_times.items():
                all_status_times[status].append(time_spent)
        
        # Create separate plots for each status
        fig, axes = plt.subplots(len(all_status_times), 1, figsize=(12, 6*len(all_status_times)))
        if len(all_status_times) == 1:
            axes = [axes]
        
        for i, (status, times) in enumerate(all_status_times.items()):
            axes[i].hist(times, bins=20, edgecolor='black')
            axes[i].set_title(f'Time Distribution in Status: {status}')
            axes[i].set_xlabel('Time (days)')
            axes[i].set_ylabel('Number of Tasks')
            axes[i].grid(axis='y', alpha=0.75)
        
        plt.tight_layout()
        plt.savefig('status_time_distribution.png')
        plt.show()
        print("Status time distribution saved as 'status_time_distribution.png'")
    
    def generate_daily_task_trend(self, issues: List[Dict]) -> None:
        """
        Generate graph showing daily created and closed tasks with cumulative totals.
        
        Args:
            issues (List[Dict]): List of JIRA issues
        """
        created_dates = []
        closed_dates = []
        
        for issue in issues:
            # Add creation date
            created = parser.parse(issue['fields']['created']).date()
            created_dates.append(created)
            
            # Add closure date if the issue is closed
            status_name = issue['fields']['status']['name'].lower()
            if 'closed' in status_name or 'resolved' in status_name or 'done' in status_name:
                updated = parser.parse(issue['fields']['updated']).date()
                closed_dates.append(updated)
        
        # Create date ranges
        if not created_dates and not closed_dates:
            print("No issues found for analysis.")
            return
            
        all_dates = set(created_dates + closed_dates)
        min_date = min(all_dates)
        max_date = max(all_dates)
        
        date_range = pd.date_range(start=min_date, end=max_date, freq='D')
        
        # Count daily created and closed tasks
        created_counts = [created_dates.count(date.date()) for date in date_range]
        closed_counts = [closed_dates.count(date.date()) for date in date_range]
        
        # Calculate cumulative totals
        cumulative_created = np.cumsum(created_counts)
        cumulative_closed = np.cumsum(closed_counts)
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(14, 8))
        ax.plot(date_range, created_counts, label='Created Daily', marker='o', linestyle='-', alpha=0.7)
        ax.plot(date_range, closed_counts, label='Closed Daily', marker='s', linestyle='-', alpha=0.7)
        ax.plot(date_range, cumulative_created, label='Cumulative Created', linestyle='--', linewidth=2)
        ax.plot(date_range, cumulative_closed, label='Cumulative Closed', linestyle='--', linewidth=2)
        
        ax.set_title('Daily Task Creation and Closure with Cumulative Totals')
        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Tasks')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('daily_task_trend.png')
        plt.show()
        print("Daily task trend saved as 'daily_task_trend.png'")
    
    def generate_user_task_distribution(self, issues: List[Dict], top_n: int = 30) -> None:
        """
        Generate graph showing task distribution by user (assignee and reporter).
        
        Args:
            issues (List[Dict]): List of JIRA issues
            top_n (int): Number of top users to display
        """
        assignee_counts = defaultdict(int)
        reporter_counts = defaultdict(int)
        
        for issue in issues:
            # Count assignees
            assignee = issue['fields'].get('assignee')
            if assignee and 'displayName' in assignee:
                assignee_counts[assignee['displayName']] += 1
            
            # Count reporters
            reporter = issue['fields'].get('reporter')
            if reporter and 'displayName' in reporter:
                reporter_counts[reporter['displayName']] += 1
        
        # Get top N assignees and reporters
        top_assignees = sorted(assignee_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
        top_reporters = sorted(reporter_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        # Create subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
        
        # Plot assignees
        if top_assignees:
            assignees, counts = zip(*top_assignees)
            ax1.barh(range(len(assignees)), counts)
            ax1.set_yticks(range(len(assignees)))
            ax1.set_yticklabels(assignees)
            ax1.set_xlabel('Number of Tasks')
            ax1.set_title(f'Top {top_n} Assignees by Task Count')
            ax1.invert_yaxis()
        
        # Plot reporters
        if top_reporters:
            reporters, counts = zip(*top_reporters)
            ax2.barh(range(len(reporters)), counts)
            ax2.set_yticks(range(len(reporters)))
            ax2.set_yticklabels(reporters)
            ax2.set_xlabel('Number of Tasks')
            ax2.set_title(f'Top {top_n} Reporters by Task Count')
            ax2.invert_yaxis()
        
        plt.tight_layout()
        plt.savefig('user_task_distribution.png')
        plt.show()
        print("User task distribution saved as 'user_task_distribution.png'")
    
    def generate_logged_time_histogram(self, issues: List[Dict]) -> None:
        """
        Generate histogram of logged time by users.
        
        Args:
            issues (List[Dict]): List of JIRA issues
        """
        user_logged_times = defaultdict(float)  # Total logged time per user in hours
        
        for issue in issues:
            # Check if the issue has timetracking information
            timetracking = issue['fields'].get('timetracking', {})
            if 'timeSpentSeconds' in timetracking:
                time_spent_seconds = timetracking['timeSpentSeconds']
                time_spent_hours = time_spent_seconds / 3600.0  # Convert to hours
                
                # Attribute to the assignee
                assignee = issue['fields'].get('assignee')
                if assignee and 'displayName' in assignee:
                    user_logged_times[assignee['displayName']] += time_spent_hours
        
        if not user_logged_times:
            print("No logged time information found in the issues.")
            return
        
        logged_times = list(user_logged_times.values())
        
        plt.figure(figsize=(12, 6))
        plt.hist(logged_times, bins=30, edgecolor='black')
        plt.title('Distribution of Logged Time by Users')
        plt.xlabel('Logged Time (hours)')
        plt.ylabel('Number of Tasks')
        plt.grid(axis='y', alpha=0.75)
        plt.tight_layout()
        plt.savefig('logged_time_histogram.png')
        plt.show()
        print("Logged time histogram saved as 'logged_time_histogram.png'")
    
    def generate_priority_distribution(self, issues: List[Dict]) -> None:
        """
        Generate graph showing task distribution by priority.
        
        Args:
            issues (List[Dict]): List of JIRA issues
        """
        priority_counts = defaultdict(int)
        
        for issue in issues:
            priority = issue['fields'].get('priority', {}).get('name', 'Unknown')
            priority_counts[priority] += 1
        
        if not priority_counts:
            print("No priority information found in the issues.")
            return
        
        priorities, counts = zip(*priority_counts.items())
        
        plt.figure(figsize=(12, 6))
        bars = plt.bar(priorities, counts)
        plt.title('Task Distribution by Priority')
        plt.xlabel('Priority')
        plt.ylabel('Number of Tasks')
        plt.xticks(rotation=45)
        
        # Add value labels on bars
        for bar, count in zip(bars, counts):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(count), ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig('priority_distribution.png')
        plt.show()
        print("Priority distribution saved as 'priority_distribution.png'")
    
    def run_full_analysis(self, project_key: str) -> None:
        """
        Run the complete analysis and generate all reports.
        
        Args:
            project_key (str): Project key to analyze
        """
        print(f"Starting analysis for project: {project_key}")
        
        # Get all issues for the project
        print("Fetching issues from JIRA...")
        issues = self.get_issues_by_project(project_key)
        print(f"Fetched {len(issues)} issues")
        
        # Filter for closed/resolved issues only for some analyses
        closed_issues = []
        for issue in issues:
            status_name = issue['fields']['status']['name'].lower()
            if 'closed' in status_name or 'resolved' in status_name or 'done' in status_name:
                closed_issues.append(issue)
        
        print(f"Found {len(closed_issues)} closed issues")
        
        # Generate all reports
        print("Generating Open Duration Histogram...")
        self.generate_open_duration_histogram(closed_issues)
        
        print("Generating Status Time Distribution...")
        self.generate_status_time_distribution(closed_issues)
        
        print("Generating Daily Task Trend...")
        self.generate_daily_task_trend(issues)
        
        print("Generating User Task Distribution...")
        self.generate_user_task_distribution(issues)
        
        print("Generating Logged Time Histogram...")
        self.generate_logged_time_histogram(closed_issues)
        
        print("Generating Priority Distribution...")
        self.generate_priority_distribution(issues)
        
        print("Analysis complete! All reports saved as PNG files.")


def main():
    """
    Main function to run the JIRA Analytics tool.
    """
    # Configuration - these should be set based on your JIRA instance
    jira_url = os.getenv('JIRA_URL', 'https://issues.apache.org/jira')
    username = os.getenv('JIRA_USERNAME', '')  # Not typically used with API tokens
    api_token = os.getenv('JIRA_API_TOKEN', '')
    
    # If no credentials provided via environment, prompt user
    if not api_token:
        print("Please set JIRA_API_TOKEN environment variable.")
        print("For public JIRA instances like Apache, you might not need authentication.")
        # For Apache JIRA, we can proceed without authentication
        jira_analytics = JiraAnalytics(jira_url, '', '')
    else:
        jira_analytics = JiraAnalytics(jira_url, username, api_token)
    
    # Default to Apache Kafka project for demonstration
    project_key = os.getenv('JIRA_PROJECT_KEY', 'KAFKA')
    
    try:
        jira_analytics.run_full_analysis(project_key)
    except Exception as e:
        print(f"Error during analysis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()