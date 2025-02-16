#!/usr/bin/env python3
import os
import yaml
from typing import Dict, List

def get_assistant_configs(base_dir: str = "assistants") -> List[Dict]:
    """Recursively find and parse all YAML files in the assistants directory."""
    configs = []
    
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.yaml'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                        if config and isinstance(config, dict):
                            # Add the file path to the config for generating links
                            config['_file_path'] = file_path
                            configs.append(config)
                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")
    
    return configs

def generate_markdown_badge(file_path: str, title: str) -> str:
    """Generate a GitHub-style markdown badge that links to the config file."""
    # Convert the file path to use forward slashes for GitHub URLs
    github_path = file_path.replace('\\', '/')
    return f"[![View Config]" \
           f"(https://img.shields.io/badge/View-Config-blue)]" \
           f"({github_path})"

def build_index(configs: List[Dict]) -> str:
    """Build the markdown index content."""
    # Sort configs by title
    sorted_configs = sorted(configs, key=lambda x: x.get('title', '').lower())
    
    # Build markdown content
    content = ["# AI Assistant Index\n"]
    
    for config in sorted_configs:
        title = config.get('title', 'Untitled')
        description = config.get('description', 'No description available')
        file_path = config.get('_file_path', '')
        
        # Add section
        content.extend([
            f"## {title}\n",
            f"{description}\n",
            f"{generate_markdown_badge(file_path, title)}\n\n"
        ])
    
    return '\n'.join(content)

def main():
    """Main function to build the index."""
    # Get all assistant configs
    configs = get_assistant_configs()
    
    # Generate the index content
    index_content = build_index(configs)
    
    # Write to index.md
    with open('index.md', 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print("Index has been built successfully!")

if __name__ == "__main__":
    main()