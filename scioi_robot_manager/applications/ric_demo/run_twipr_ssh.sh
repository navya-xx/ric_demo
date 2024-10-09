#!/usr/bin/env bash

REMOTE_MACHINES=(
    "192.168.0.102" 
    "192.168.0.103" 
    "192.168.0.106" 
    "192.168.0.107" 
    "192.168.0.108" 
    )

for remote in ${REMOTE_MACHINES[@]}; do
  bash kill_ideenexpo.sh $remote
done

if [[ "$1" == "kill" ]]; then
  echo "existing after killing running instances of ideenexpo.py"
  exit 0
fi

sleep 1

# Start a new tmux session named 'remote_ssh'
tmux kill-session -t remote_ssh
tmux new-session -d -s remote_ssh

# Split the window into three horizontal columns
tmux split-window -h
tmux split-window -h

# Select the first pane (leftmost) and split it vertically
tmux select-pane -t 0
tmux split-window -v

# Select the second pane (middle column) and split it vertically
tmux select-pane -t 1
tmux split-window -v

# Now we assign remote machines to the panes
tmux select-pane -t 0; tmux send-keys "bash -c './attempt_ssh.sh ${REMOTE_MACHINES[0]}'" C-m
tmux select-pane -t 2; tmux send-keys "bash -c './attempt_ssh.sh ${REMOTE_MACHINES[1]}'" C-m
tmux select-pane -t 1; tmux send-keys "bash -c './attempt_ssh.sh ${REMOTE_MACHINES[2]}'" C-m
tmux select-pane -t 3; tmux send-keys "bash -c './attempt_ssh.sh ${REMOTE_MACHINES[3]}'" C-m
tmux select-pane -t 4; tmux send-keys "bash -c './attempt_ssh.sh ${REMOTE_MACHINES[4]}'" C-m

# Attach to the session
tmux attach-session -t remote_ssh

