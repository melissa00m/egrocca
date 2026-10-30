# ShopDroid Sensor Setup and Feed Verification

This guide covers the current Gazebo sensor configuration and the checks to perform before claiming that physical sensors are calibrated. The model values below describe the **simulation only**; they are not validated physical mounting measurements.

## Simulated mounting reference

Sensor poses are relative to the ShopDroid `base_link`, in metres and radians, using SDF pose order `x y z roll pitch yaw`. The model uses `+X` as forward and `+Z` as up.

| Sensor | Position (`x y z`) | Orientation (`roll pitch yaw`) | Simulated settings | ROS topic |
|---|---:|---:|---|---|
| LiDAR | `0.15 0 0.56` | `0 0 0` | 360° horizontal scan, 360 samples, 0.15–35 m range | `/shopdroid/lidar` |
| Camera | `0.49 0 0.30` | `0 0 0` | 640 × 480 RGB, 20 Hz, 1.396 rad horizontal field of view | `/shopdroid/camera/image_raw` |
| Camera calibration metadata | — | — | Bridged as `sensor_msgs/msg/CameraInfo` | `/shopdroid/camera/camera_info` |

These are starting points for simulation and a reference for prototype discussions. Before using them on the real chassis, confirm the sensor models, bracket geometry, ground clearance, field of view, cable routing, and the camera manufacturer's required orientation. Record the measured physical poses and update the robot model and this table when the team agrees on final mounts.

## Build and launch the sensor simulation

On the supported ROS 2 Jazzy and Gazebo Harmonic environment, build and launch the dedicated droid simulation:

```bash
cd ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
ros2 launch shopdrone_simulation simulation_droid.launch.py
```

The launch file bridges the simulated LiDAR scan, camera image, and camera calibration metadata from Gazebo to ROS 2. From the repository root, run the following in a second terminal after sourcing the same ROS 2 setup:

```bash
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
ros2 topic type /shopdroid/lidar
ros2 topic type /shopdroid/camera/image_raw
ros2 topic type /shopdroid/camera/camera_info
ros2 topic hz /shopdroid/lidar
ros2 topic hz /shopdroid/camera/image_raw
ros2 topic echo --once /shopdroid/camera/camera_info
```

Expected message types are `sensor_msgs/msg/LaserScan`, `sensor_msgs/msg/Image`, and `sensor_msgs/msg/CameraInfo`, respectively. The simulated camera should publish at approximately 20 Hz. Record the observed LiDAR rate rather than assuming one; it is not explicitly set in the SDF. A successful local ROS topic check verifies the simulation bridge, not transmission from a physical sensor or between separate computers.

To confirm delivery to a separate compute unit, run the ROS 2 topic checks on that unit too, using the same `ROS_DOMAIN_ID` and a network configuration that permits ROS 2 discovery and data traffic. Save the command output and the machine/interface details with the test results. For physical sensors, use the driver's documented ROS topics and message types instead of assuming the simulation topics are available.

## Physical calibration and rough-terrain checks

Do not mark physical calibration complete based on the Gazebo model. Use the actual camera and LiDAR, their final rigid mounts, and the robot's agreed base frame:

1. **Measure and record mounting:** measure each sensor's XYZ position from `base_link`; record roll, pitch, and yaw, units, measurement method, sensor serial/model, and the bracket used. Confirm the camera faces forward and the LiDAR has an unobstructed field of view.
2. **Calibrate the camera:** capture a calibration target (such as a checkerboard) at varied distances, positions, and orientations with the final focus and resolution. Use the camera vendor's calibration procedure or a ROS camera calibration tool; save the resulting intrinsics and distortion parameters and verify the published `CameraInfo` matches the camera image dimensions.
3. **Check LiDAR alignment:** use the sensor vendor's calibration procedure and fixed, measured reference targets or planes to validate range readings and the LiDAR-to-`base_link` transform. Record the transform and the target distances; do not infer a calibration solely from a visually plausible scan.
4. **Exercise terrain cases safely:** collect synchronized camera and LiDAR data on representative flat ground, slopes, loose/uneven surfaces, and safe, controlled pothole-like depressions. Include stationary and moving tests and note lighting, weather, speed, and sensor settings. Secure the robot and keep people clear of moving hardware.
5. **Verify feed at the compute unit:** check that messages arrive continuously on the physical driver's topics at the expected rate and resolution, with valid timestamps and non-empty data. Save logs or a short rosbag plus calibration files and test conditions. Investigate dropped/stale messages, missing metadata, and mismatched frames before relying on perception output.
6. **Review and version results:** have the hardware/perception teammates review the measurements and terrain recordings; version the approved transform and calibration artifacts with the sensor model and date. Clearly label any untested terrain or operating conditions.

Role 1's physical calibration and compute-unit transmission tasks are complete only after these hardware checks have been run and their evidence reviewed. This repository currently supplies a simulation reference and ROS/Gazebo topic bridge; it does not contain physical sensor calibration results or a hardware driver configuration.
