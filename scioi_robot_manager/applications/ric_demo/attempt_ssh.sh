#!/usr/bin/env bash

password="scioip11"
python_script="/home/lehmann/software/ideenexpo.py"


user=$1

sshpass -p $password ssh -o StrictHostkeyChecking=no "lehmann@${user}" "python3 ${python_script}"
if [ $? -eq 0 ]; then
  echo "Failed to connect to ${user}"
fi

