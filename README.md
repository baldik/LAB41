# JIRA Analytics Tool

A Python program that connects to JIRA via REST API and generates analytical reports based on task data.

## Features

This program provides the following analytical reports:

1. **Open Duration Histogram**: Shows the distribution of time tasks spent in open state (from creation to closure)
2. **Status Time Distribution**: Shows how much time tasks spend in each status
3. **Daily Task Trend**: Shows daily created and closed tasks with cumulative totals
4. **User Task Distribution**: Shows task distribution by assignee and reporter (top 30 users)
5. **Logged Time Histogram**: Shows distribution of logged time by users
6. **Priority Distribution**: Shows task distribution by priority level

## Requirements

- Python 3.7 or higher
- Linux operating system (though it should work on other platforms as well)

## Installation

1. Clone or download this repository to your local machine
2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

### Required packages:
- `requests`: For making HTTP requests to JIRA API
- `pandas`: For data manipulation
- `matplotlib`: For creating visualizations
- `seaborn`: For enhanced visualizations
- `python-dateutil`: For date parsing
- `numpy`: For numerical operations

## Configuration

The program can be configured using environment variables:

- `JIRA_URL`: The base URL of your JIRA instance (default: `https://issues.apache.org/jira`)
- `JIRA_USERNAME`: Your JIRA username (not typically needed with API tokens)
- `JIRA_API_TOKEN`: Your JIRA API token for authentication
- `JIRA_PROJECT_KEY`: The project key to analyze (default: `KAFKA`)

For public JIRA instances like Apache, authentication may not be required.

## Usage

### Basic Usage

```bash
python jira_analytics.py
```

### With Environment Variables

```bash
export JIRA_PROJECT_KEY="KAFKA"
python jira_analytics.py
```

For a JIRA instance that requires authentication:

```bash
export JIRA_URL="https://yourcompany.atlassian.net"
export JIRA_USERNAME="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
export JIRA_PROJECT_KEY="YOUR_PROJECT_KEY"
python jira_analytics.py
```

## Running on Linux

On most Linux distributions, you can run the program as follows:

1. Ensure Python 3 is installed:
   ```bash
   python3 --version
   ```

2. Install pip if not already installed:
   ```bash
   # Ubuntu/Debian:
   sudo apt update && sudo apt install python3-pip

   # CentOS/RHEL/Fedora:
   sudo dnf install python3-pip  # or sudo yum install python3-pip
   ```

3. Install the required packages:
   ```bash
   pip3 install -r requirements.txt
   ```

4. Run the program:
   ```bash
   python3 jira_analytics.py
   ```

## Project Support

The program works with any JIRA project, including public projects like Apache Kafka (KAFKA) or Hadoop HDFS (HDFS). By default, it uses the KAFKA project from the Apache JIRA instance.

## Output

The program generates the following visualization files in the current directory:

- `open_duration_histogram.png` - Distribution of time tasks spent in open state
- `status_time_distribution.png` - Time distribution in each status
- `daily_task_trend.png` - Daily created and closed tasks with cumulative totals
- `user_task_distribution.png` - Task distribution by assignee and reporter
- `logged_time_histogram.png` - Distribution of logged time by users
- `priority_distribution.png` - Task distribution by priority

## Error Handling

The program includes comprehensive error handling for:
- Network connection issues
- Authentication problems
- Invalid JIRA responses
- Missing data in issues
- File I/O errors when saving visualizations

## Code Structure

- `JiraAnalytics` class: Handles all JIRA API interactions and data processing
- Data fetching methods: Retrieve issues and their transition history
- Analysis methods: Calculate metrics from the retrieved data
- Visualization methods: Generate the required charts and graphs
- Main function: Orchestrates the entire analysis process