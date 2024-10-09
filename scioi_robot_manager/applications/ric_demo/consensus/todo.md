## TODO list

## UI
- [x] Plot for consensus related stuff
- [x] Indication of robot : connected, tracked in optitrack
- [x] Button to start/stop consensus
- [x] UI command to do SCP to all robots

## Code
- [x] Adapt collision avoidance (CBF clipping) and clip large torque input
- [ ] Allow one robot to be out of consensus control loop and controlled entirely by the remote
- [ ] Set boundary for centroid location based on the stage area -- with respect to the formation
- [x] Conditional push - Push robots that are not moving while the target is more than 20cm away
- [x] Clip the derivative of u_safe
- [x] Joystick - send joystick off command back
- [x] Add offset control to joystick input
- [x] run_ideenexpo -- kill previous ideenexpo.py before starting new
- [x] Division by zero -- do not stop at error


## Debugging
- [x] Emergency stop - stopped working -- Removed control thread from twipr -- control mode off from GUI works, but emergency stop doesnt
- [ ]

## Control scenarios
- [x] Simple formation control with joystick control of one robot
- [ ] Trajectory following - setting a sequence of fixed centroid locations
- [ ] 

## Testing scenarios
- [ ] Testing consensus with obstacles
- [ ] Strongly connected graph Vs Spanning tree graph
- [ ] 