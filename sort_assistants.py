#!/usr/bin/env python3
import os
import yaml
import shutil
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from openai import OpenAI
from time import sleep
from dotenv import load_dotenv
import hashlib
import re

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def fix_json_array(json_str: str) -> str:
    """Fix JSON array by adding missing commas between elements."""
    # Remove any markdown code block syntax
    json_str = re.sub(r'```json\s*', '', json_str)
    json_str = re.sub(r'\s*```', '', json_str)
    
    # Fix missing commas in arrays
    json_str = re.sub(r'"\s+(?=")', '", ', json_str)
    return json_str

class AssistantOrganizer:
    def __init__(self, source_dir: str, dest_dir: str):
        self.source_dir = source_dir
        self.dest_dir = dest_dir
        
        # Set up config directory in user's home
        self.config_dir = os.path.expanduser('~/.config/assistant-organizer')
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Cache and categories files in config directory
        self.cache_file = os.path.join(self.config_dir, 'categorization_cache.json')
        self.categories_file = os.path.join(self.config_dir, 'categories.json')
        
        self.cache = self._load_cache()
        self.categories = self._load_categories()

    def _load_cache(self) -> Dict:
        """Load the categorization cache from file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading cache: {e}")
        return {'files': {}, 'hashes': {}}

    def _save_cache(self):
        """Save the categorization cache to file."""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)

    def _load_categories(self) -> List[str]:
        """Load existing categories from file."""
        if os.path.exists(self.categories_file):
            try:
                with open(self.categories_file, 'r') as f:
                    data = json.load(f)
                    return data['categories']
            except Exception as e:
                print(f"Error loading categories: {e}")
        return []

    def _save_categories(self, categories: List[str]):
        """Save categories to file."""
        os.makedirs(os.path.dirname(self.categories_file), exist_ok=True)
        with open(self.categories_file, 'w') as f:
            json.dump({'categories': categories}, f, indent=2)

    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA-256 hash of file contents."""
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

    def _find_file_by_hash(self, file_hash: str) -> str:
        """Find a file's current location by its hash."""
        # Check source directory
        if os.path.exists(self.source_dir):
            for file in os.listdir(self.source_dir):
                if file.endswith('.yaml'):
                    path = os.path.join(self.source_dir, file)
                    if self._compute_file_hash(path) == file_hash:
                        return path
        
        # Check all category folders
        for category in self.categories:
            folder_name = category.lower().replace(' & ', '-').replace(' ', '-')
            folder_path = os.path.join(self.dest_dir, folder_name)
            if os.path.exists(folder_path):
                for file in os.listdir(folder_path):
                    if file.endswith('.yaml'):
                        path = os.path.join(folder_path, file)
                        if self._compute_file_hash(path) == file_hash:
                            return path
        
        return None

    def get_files_to_process(self) -> Tuple[List[str], List[str]]:
        """Get lists of new and modified files that need processing."""
        new_files = []
        modified_files = []
        
        # Get all YAML files from source directory
        for file in os.listdir(self.source_dir):
            if not file.endswith('.yaml'):
                continue
                
            file_path = os.path.join(self.source_dir, file)
            file_hash = self._compute_file_hash(file_path)
            
            # Check if we've seen this hash before
            if file_hash in self.cache['hashes']:
                # File exists but might have been moved
                existing_path = self._find_file_by_hash(file_hash)
                if existing_path and existing_path != file_path:
                    print(f"Found moved file: {file} (previously at {existing_path})")
                    # Update cache with new location
                    self.cache['files'][file] = {
                        'hash': file_hash,
                        'category': self.cache['hashes'][file_hash]['category']
                    }
                    self._save_cache()
            else:
                # Completely new file
                new_files.append(file_path)
                
        return new_files, modified_files

    def read_yaml_file(self, file_path: str) -> Dict:
        """Read and parse a YAML file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return {}

    def get_file_summaries(self, yaml_files: List[str]) -> List[Dict]:
        """Get summaries of YAML files."""
        summaries = []
        for file_path in yaml_files:
            content = self.read_yaml_file(file_path)
            if content:
                name = os.path.basename(file_path)
                description = content.get('description', '')
                purpose = content.get('purpose', '')
                capabilities = content.get('capabilities', [])
                
                summaries.append({
                    'path': file_path,
                    'name': name,
                    'description': description,
                    'purpose': purpose,
                    'capabilities': capabilities
                })
        return summaries

    def determine_categories(self, summaries: List[Dict]) -> List[str]:
        """Use GPT-4 to determine optimal categories based on a sample of assistants."""
        # If we already have categories, use them
        if self.categories:
            return self.categories
            
        # Take a representative sample of assistants
        sample_size = min(50, len(summaries))
        sample = summaries[:sample_size]
        
        # Create a detailed summary for the LLM
        assistant_descriptions = "\n".join([
            f"Name: {s['name']}\nDescription: {s['description']}\nPurpose: {s['purpose']}\n"
            for s in sample
        ])
        
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a skilled taxonomist specializing in AI assistant classification."},
                    {"role": "user", "content": f"""Analyze these AI assistants and create optimal categories for organization.

Sample of assistants:
{assistant_descriptions}

Requirements:
1. Create exactly 20 distinct, practical categories
2. Categories should be 2-4 words
3. Make categories broad enough to be useful but specific enough to be meaningful
4. Consider the full spectrum of AI assistants (development, data, business, etc.)
5. Output MUST be valid JSON with commas between array elements
6. Format must be exactly: {{"categories": ["Category 1", "Category 2", "Category 3"]}}
7. Categories should be clear and professional"""}
                ],
                temperature=0.7
            )
            
            # Get the response content
            content = response.choices[0].message.content.strip()
            print(f"Raw response: {content}")
            
            # Fix and parse the JSON response
            fixed_content = fix_json_array(content)
            print(f"Fixed JSON: {fixed_content}")
            
            try:
                data = json.loads(fixed_content)
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                print(f"At position {e.pos}: {fixed_content[max(0, e.pos-20):min(len(fixed_content), e.pos+20)]}")
                raise
            
            categories = data['categories'][:20]  # Ensure exactly 20 categories
            
            # Save the categories
            self._save_categories(categories)
            self.categories = categories
            
            return categories
            
        except Exception as e:
            print(f"Error determining categories: {e}")
            return []

    def categorize_assistants(self, summaries: List[Dict], batch_size: int = 20) -> Dict[str, str]:
        """Categorize assistants in batches using GPT-3.5 Turbo."""
        if not summaries:
            return {}
            
        categorizations = {}
        batches = [summaries[i:i + batch_size] for i in range(0, len(summaries), batch_size)]
        
        for i, batch in enumerate(batches, 1):
            try:
                batch_descriptions = "\n---\n".join([
                    f"Name: {s['name']}\nDescription: {s['description']}\nPurpose: {s['purpose']}"
                    for s in batch
                ])
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an AI assistant classifier."},
                        {"role": "user", "content": f"""Categorize these AI assistants into the following categories:
{json.dumps(self.categories, indent=2)}

Assistants to categorize:
{batch_descriptions}

Requirements:
1. Output MUST be valid JSON with commas between array elements
2. Format must be exactly: {{"categorizations": {{"assistant_name.yaml": "Category Name", ...}}}}
3. Use exact category names from the list
4. Choose the single best category for each assistant"""}
                    ],
                    temperature=0.3
                )
                
                # Get the response content
                content = response.choices[0].message.content.strip()
                
                # Fix and parse the JSON response
                fixed_content = fix_json_array(content)
                
                try:
                    result = json.loads(fixed_content)
                except json.JSONDecodeError as e:
                    print(f"JSON parse error in batch {i}: {e}")
                    print(f"At position {e.pos}: {fixed_content[max(0, e.pos-20):min(len(fixed_content), e.pos+20)]}")
                    raise
                
                categorizations.update(result['categorizations'])
                
                print(f"Processed batch {i}/{len(batches)} ({len(batch)} assistants)")
                
                # Rate limiting
                sleep(0.5)
                
            except Exception as e:
                print(f"Error categorizing batch {i}: {e}")
                # On error, assign default category to all assistants in batch
                for summary in batch:
                    categorizations[summary['name']] = self.categories[0]
        
        return categorizations

    def create_category_folders(self):
        """Create the category folders if they don't exist."""
        for category in self.categories:
            folder_name = category.lower().replace(' & ', '-').replace(' ', '-')
            folder_path = os.path.join(self.dest_dir, folder_name)
            os.makedirs(folder_path, exist_ok=True)

    def move_file_to_category(self, file_path: str, category: str):
        """Move a file to its category folder and update cache."""
        folder_name = category.lower().replace(' & ', '-').replace(' ', '-')
        destination_dir = os.path.join(self.dest_dir, folder_name)
        
        # Create destination directory if it doesn't exist
        os.makedirs(destination_dir, exist_ok=True)
        
        # Get the file name from the path
        file_name = os.path.basename(file_path)
        
        # Compute file hash
        file_hash = self._compute_file_hash(file_path)
        
        # Construct destination path
        destination_path = os.path.join(destination_dir, file_name)
        
        # Move the file
        try:
            shutil.move(file_path, destination_path)
            print(f"Moved {file_name} to {folder_name}/")
            
            # Update cache with both filename and hash mappings
            self.cache['files'][file_name] = {
                'hash': file_hash,
                'category': category
            }
            self.cache['hashes'][file_hash] = {
                'name': file_name,
                'category': category
            }
            self._save_cache()
            
        except Exception as e:
            print(f"Error moving {file_name}: {e}")

    def print_statistics(self):
        """Print statistics about file distribution across categories."""
        category_counts = {}
        for category in self.categories:
            folder_name = category.lower().replace(' & ', '-').replace(' ', '-')
            folder_path = os.path.join(self.dest_dir, folder_name)
            if os.path.exists(folder_path):
                count = len([f for f in os.listdir(folder_path) if f.endswith('.yaml')])
                category_counts[category] = count
        
        print("\nFiles per category:")
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"{category}: {count} files")

    def organize(self):
        """Main organization function."""
        # Get files that need processing
        new_files, modified_files = self.get_files_to_process()
        
        if not new_files and not modified_files:
            print("No new or modified files to process")
            return
        
        print(f"Found {len(new_files)} new files and {len(modified_files)} modified files")
        
        # Get summaries for files that need processing
        files_to_process = new_files + modified_files
        summaries = self.get_file_summaries(files_to_process)
        
        if not summaries:
            print("No valid assistant configurations found")
            return
        
        # Determine or load categories
        if not self.categories:
            print("Analyzing assistants to determine optimal categories (using GPT-4)...")
            self.categories = self.determine_categories(summaries)
            
            if not self.categories:
                print("Error: Could not determine categories")
                return
        
        print("\nUsing categories:")
        for i, category in enumerate(self.categories, 1):
            print(f"{i}. {category}")
        
        # Create category folders
        print("\nEnsuring category folders exist...")
        self.create_category_folders()
        
        # Process assistants in batches
        print("\nCategorizing assistants using GPT-3.5...")
        categorizations = self.categorize_assistants(summaries)
        
        # Move files to their categories
        print("\nMoving files to their respective categories...")
        for summary in summaries:
            category = categorizations.get(summary['name'], self.categories[0])
            self.move_file_to_category(summary['path'], category)
        
        print("\nOrganization complete!")
        self.print_statistics()

def main():
    if 'OPENAI_API_KEY' not in os.environ:
        print("Error: OPENAI_API_KEY environment variable not set")
        return
    
    organizer = AssistantOrganizer('pipeline', 'assistants')
    organizer.organize()

if __name__ == "__main__":
    main()