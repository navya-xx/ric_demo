#!/bin/bash

# Define variables
FILE_TO_COPY="twipr.py"
REMOTE_USER="lehmann"  # Replace with your SSH username
REMOTE_MACHINES=(
    "192.168.0.102" 
    "192.168.0.103" 
    "192.168.0.106" 
    "192.168.0.107" 
    "192.168.0.108" 
    )
REMOTE_PATH="/home/lehmann/software/"  # Replace with the destination directory on remote machines
LOCAL_PATH="../../../scioi_twipr_manager/robot/TWIPR/"
PASSWORD="scioip11"

# Function to copy file to a single remote machine
copy_file() {
    local remote_host=$1
    echo "Copying file to $remote_host..."
    sshpass -p "${PASSWORD}" scp "${LOCAL_PATH}${FILE_TO_COPY}" "$REMOTE_USER@$remote_host:${REMOTE_PATH}${FILE_TO_COPY}"
    
    if [ $? -eq 0 ]; then
        echo "File successfully copied to $remote_host"
    else
        echo "Failed to copy file to $remote_host"
    fi
}


# Check if the file exists
if [ ! -f "${LOCAL_PATH}${FILE_TO_COPY}" ]; then
    echo "Error: File '$FILE_TO_COPY' not found."
    exit 1
fi

# Loop through each remote machine and copy the file
for remote in "${REMOTE_MACHINES[@]}"; do
    copy_file "$remote"
done

echo "File copy process complete."