#!/bin/bash

# Get current date in ddmmyy format
DATE=$(date +"%d%m%y")

# Create zip archive
zip -r "assistants_${DATE}.zip" assistants/

# Create tar.gz archive
tar -czf "assistants_${DATE}.tar.gz" assistants/