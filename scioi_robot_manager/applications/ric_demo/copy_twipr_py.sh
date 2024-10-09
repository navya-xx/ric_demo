#!/bin/bash

# Define variables
# FILE_TO_COPY="twipr.py"
REMOTE_USER="lehmann"  # Replace with your SSH username
REMOTE_MACHINES=(
    "192.168.0.102" 
    "192.168.0.103" 
    "192.168.0.106" 
    "192.168.0.107" 
    "192.168.0.108" 
    )
REMOTE_PATH="/home/lehmann/software/robot/"  # Replace with the destination directory on remote machines
LOCAL_PATH="/mnt/c/Users/demo6g/SCIoI-P11-HardwareManager/scioi_twipr_manager/robot/TWIPR"
PASSWORD="scioip11"

# Function to copy file to a single remote machine
copy_file() {
    local remote_host=$1
    echo "Copying file to $remote_host..."
    sshpass -p $PASSWORD scp -r "${LOCAL_PATH}" "$REMOTE_USER@$remote_host:${REMOTE_PATH}"
    
    if [ $? -eq 0 ]; then
        echo "File successfully copied to $remote_host"
    else
        echo "Failed to copy file to $remote_host"
    fi
}


# Loop through each remote machine and copy the file
for remote in "${REMOTE_MACHINES[@]}"; do
    copy_file "$remote"
done

echo "File copy process complete."