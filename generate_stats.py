#!/usr/bin/env python3
import os
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
import requests

def count_yaml_files(directory):
    """Count all YAML files in directory and subdirectories."""
    count = 0
    for root, _, files in os.walk(directory):
        count += sum(1 for f in files if f.endswith('.yaml'))
    return count

def load_historical_data(filename):
    """Load historical data from JSON file."""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}

def save_historical_data(data, filename):
    """Save historical data to JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def generate_chart(data, output_file):
    """Generate line chart showing assistant count over time."""
    dates = [datetime.strptime(d, '%Y-%m-%d') for d in data.keys()]
    counts = list(data.values())

    # Only show last 12 weeks of data
    today = datetime.now()
    cutoff = today - timedelta(weeks=12)
    recent_data = [(d, c) for d, c in zip(dates, counts) if d >= cutoff]
    
    if recent_data:
        dates, counts = zip(*recent_data)
    else:
        dates, counts = [today], [counts[-1]]  # Use latest count if no recent data

    plt.figure(figsize=(10, 6))
    plt.plot(dates, counts, marker='o', linestyle='-', linewidth=2)
    
    # Configure x-axis to show weeks
    ax = plt.gca()
    # Set major ticks to Mondays
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
    # Set minor ticks to days
    ax.xaxis.set_minor_locator(mdates.DayLocator())
    # Format dates as 'Month Day'
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    
    # Rotate labels for better readability
    plt.xticks(rotation=45, ha='right')
    
    plt.title('AI Assistants Count (Last 12 Weeks)')
    plt.xlabel('Date')
    plt.ylabel('Number of Assistants')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()

def update_readme(count, chart_path):
    """Update README.md with current count and chart."""
    with open('README.md', 'r') as f:
        content = f.read()

    # Create badge URL
    badge_url = f"https://img.shields.io/badge/Assistants-{count}-blue"
    
    # Define the new content to insert after the banner
    new_content = f"""![alt text](images/banner.webp)

![Assistant Count]({badge_url})

![Assistants Over Time]({chart_path})

This repository contains an extensive collection of"""

    # Replace the existing banner and following text
    content = content.replace(
        "![alt text](images/banner.webp)\n\nThis repository contains an extensive collection of",
        new_content
    )

    with open('README.md', 'w') as f:
        f.write(content)

def main():
    data_file = 'assistant_counts.json'
    chart_file = 'images/assistants_chart.png'
    
    # Ensure images directory exists
    os.makedirs('images', exist_ok=True)
    
    # Count current assistants
    current_count = count_yaml_files('assistants')
    
    # Load historical data
    historical_data = load_historical_data(data_file)
    
    # Add today's count if it's a new day
    today = datetime.now().strftime('%Y-%m-%d')
    if today not in historical_data:
        historical_data[today] = current_count
        save_historical_data(historical_data, data_file)
    
    # Generate chart
    generate_chart(historical_data, chart_file)
    
    # Update README
    update_readme(current_count, chart_file)

if __name__ == '__main__':
    main()