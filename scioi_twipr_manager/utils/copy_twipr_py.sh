#!/bin/bash

# Define variables
FILE_TO_COPY="$1"
REMOTE_USER="your_username"  # Replace with your SSH username
REMOTE_MACHINES=("remote1.example.com" "remote2.example.com" "remote3.example.com")  # Replace with your remote machine addresses
REMOTE_PATH="/path/on/remote/machine"  # Replace with the destination directory on remote machines

# Function to copy file to a single remote machine
copy_file() {
    local remote_host=$1
    echo "Copying file to $remote_host..."
    scp "$FILE_TO_COPY" "$REMOTE_USER@$remote_host:$REMOTE_PATH"
    
    if [ $? -eq 0 ]; then
        echo "File successfully copied to $remote_host"
    else
        echo "Failed to copy file to $remote_host"
    fi
}

# Check if file to copy is passed as an argument
if [ -z "$FILE_TO_COPY" ]; then
    echo "Usage: $0 <file-to-copy>"
    exit 1
fi

# Check if the file exists
if [ ! -f "$FILE_TO_COPY" ]; then
    echo "Error: File '$FILE_TO_COPY' not found."
    exit 1
fi

# Loop through each remote machine and copy the file
for remote in "${REMOTE_MACHINES[@]}"; do
    copy_file "$remote"
done

echo "File copy process complete."