#!/usr/bin/env bash

users=(
  "lehmann@192.168.0.104"
  "lehmann@192.168.0.105"
  "lehmann@192.168.0.103"
)

  password="scioip11"

  python_script="/home/lehmann/software/ideenexpo.py"

  attempt_ssh() {
    user=$1
    while true; do
      sshpass -p "$password" ssh -o StrictHostkeyChecking=no "$user" "python3 ${python_script}"
      if [ $? -eq 0 ]; then
        break
      fi
      sleep 5
    done
  }

