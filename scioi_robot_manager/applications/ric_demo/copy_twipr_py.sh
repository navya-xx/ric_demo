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
REMOTE_PATH="/home/lehmann/software/"  # Replace with the destination directory on remote machines
LOCAL_PATH="/mnt/c/Users/demo6g/SCIoI-P11-HardwareManager/scioi_twipr_manager/"
TWIPR_FOLDER="robot/TWIPR"
CM4_FOLDER="cm4_core"

PASSWORD="scioip11"

# Function to copy file to a single remote machine
copy_file() {
    local remote_host=$1

    echo "Copying folder $LOCAL_PATH$TWIPR_FOLDER to $remote_host..."
    sshpass -p $PASSWORD scp -r "${LOCAL_PATH}${TWIPR_FOLDER}" "$REMOTE_USER@$remote_host:${REMOTE_PATH}robot/"

    if [ $? -eq 0 ]; then
        echo "Folder $LOCAL_PATH$TWIPR_FOLDER successfully copied to $remote_host"
    else
        echo "Failed to copy file to $remote_host"
    fi

    # echo "Copying folder $LOCAL_PATH$CM4_FOLDER to $remote_host..."
    # sshpass -p $PASSWORD scp -r "${LOCAL_PATH}${CM4_FOLDER}" "$REMOTE_USER@$remote_host:${REMOTE_PATH}"

    # if [ $? -eq 0 ]; then
    #     echo "Folder $LOCAL_PATH$CM4_FOLDER successfully copied to $remote_host"
    # else
    #     echo "Failed to copy file to $remote_host"
    # fi
}


# Loop through each remote machine and copy the file
for remote in "${REMOTE_MACHINES[@]}"; do
    copy_file "$remote"
done

echo "File copy process complete."