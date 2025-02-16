#!/usr/bin/env python3
import os
from datetime import datetime
from collections import Counter, defaultdict
import pathlib

def analyze_assistants(directory="assistants"):
    """Analyze assistants directory for comprehensive statistics"""
    total_count = 0
    format_counter = Counter()
    category_counter = defaultdict(int)
    
    for path in pathlib.Path(directory).rglob('*'):
        if path.is_file():
            total_count += 1
            # Get file extension without the dot
            ext = path.suffix.lstrip('.')
            if ext:
                format_counter[ext.upper()] += 1
            
            # Get category from parent directory name
            category = path.parent.name
            category_counter[category] += 1
    
    return total_count, format_counter, category_counter

def generate_markdown_content(count, formats, categories):
    """Generate comprehensive markdown content with statistics"""
    current_time = datetime.now().strftime("%H:%M:%S")
    
    # Format the file formats string
    format_str = ", ".join(f"{fmt} ({count})" for fmt, count in formats.most_common())
    
    # Basic stats table
    content = f"""# Assistant Export Statistics

## Overview
Generated at {current_time}

### Basic Statistics
| Time | Assistant Count | Formats |
|------|-----------------|----------|
| {current_time} | {count} | {format_str} |

### Categories Breakdown
| Category | Count |
|----------|-------|
"""
    
    # Add sorted categories
    for category, cat_count in sorted(categories.items(), key=lambda x: (-x[1], x[0])):
        if category:  # Skip empty category names
            content += f"| {category} | {cat_count} |\n"
    
    # Add summary section
    content += f"""
## Summary
- Total number of assistants: {count}
- Number of categories: {len(categories)}
- Top categories:
"""
    
    # Add top 5 categories
    for category, cat_count in sorted(categories.items(), key=lambda x: (-x[1], x[0]))[:5]:
        if category:
            percentage = (cat_count / count) * 100
            content += f"  - {category}: {cat_count} assistants ({percentage:.1f}%)\n"
    
    return content

def main():
    # Create release-notes directory if it doesn't exist
    os.makedirs("release-notes", exist_ok=True)
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%d%m%y")
    filename = f"release-notes/{timestamp}.md"
    
    # Get comprehensive stats
    total_count, formats, categories = analyze_assistants()
    
    # Generate content
    content = generate_markdown_content(total_count, formats, categories)
    
    # Write to file
    with open(filename, 'w') as f:
        f.write(content)
    
    print(f"Release notes generated: {filename}")

if __name__ == "__main__":
    main()