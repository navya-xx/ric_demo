## TODO list

## UI
- [x] Plot for consensus related stuff
- [x] Indication of robot : connected, tracked in optitrack
- [x] Button to start/stop consensus
- [x] UI command to do SCP to all robots

## Code
- Adapt collision avoidance (CBF clipping) and clip large torque input
- Allow one robot to be out of consensus control loop and controlled entirely by the remote
- Set boundary for centroid location based on the stage area
- Conditional push - Push robots that are not moving while the target is more than 20cm away
- Clip the derivative of u_safe