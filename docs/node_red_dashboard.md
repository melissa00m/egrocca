# Node-RED obstacle dashboard

This deliverable connects obstacle events and sensor status to a simple browser dashboard. The importable flow uses Node-RED's built-in HTTP nodes; no dashboard add-on is required.

## What is included

- `nodered/flows.json`: importable dashboard and HTTP API.
- `scripts/nodered_client.py`: standard-library Python client for test events or a vision script.
- `nodered_bridge`: ROS 2 node that forwards the existing LiDAR obstacle monitor's alerts and camera/LiDAR topic availability.

The current ROS obstacle monitor is a LiDAR distance-threshold detector, not an AI vision model. The adapter demonstrates the integration path; a future vision model can send its detections using the same HTTP API. The camera status indicates whether ROS messages are arriving; it does not certify calibration. The dashboard can show a video only when a browser-readable HTTP/MJPEG stream URL is provided.

## Start the dashboard

1. Install Node-RED using its official installation instructions (if Node.js/npm are installed, `npm install -g node-red`).
2. From the repository root, start it with `node-red` (`node-red.cmd` in Windows PowerShell).
3. Open `http://localhost:1880`, choose **Menu > Import > select a file**, select `nodered/flows.json`, and deploy the flow.
4. Open `http://localhost:1880/dashboard`.

The flow provides these endpoints:

| Method and path | Purpose |
|---|---|
| `POST /api/alert` | Receive an obstacle detected/clear event |
| `POST /api/sensors` | Update camera/LiDAR status and optional stream URL |
| `GET /api/status` | Read the latest dashboard state |
| `GET /dashboard` | Open the browser dashboard |

Alert JSON requires a boolean `obstacle_detected`; it may also contain numeric `distance_m` and string `message`. Sensor JSON may contain booleans `camera_online` and `lidar_online`, plus a `camera_stream_url` using HTTP or HTTPS.

## Demo with sample messages

In another terminal, run:

```powershell
python scripts\nodered_client.py alert --state detected --distance-m 1.2 --message "Test obstacle"
python scripts\nodered_client.py sensors --camera online --lidar online
python scripts\nodered_client.py alert --state clear --message "Path clear"
```

The dashboard should first show the obstacle, then show the clear state. Test these messages before connecting the simulation or a vision script.

## Connect the ROS 2 simulation

Build and source the ROS 2 workspace, then start the simulation:

```bash
cd ros2_ws
colcon build --packages-select shopdrone_simulation
source install/setup.bash
ros2 launch shopdrone_simulation simulation.launch.py
```

In another terminal with the same workspace sourced, run:

```bash
ros2 run shopdrone_simulation nodered_bridge
```

The bridge forwards obstacle state and distance from `/shopdrone/obstacle_detected` and `/shopdrone/min_obstacle_distance`. It marks the camera and LiDAR online when messages arrive on `/shopdroid/camera/image_raw` and `/shopdroid/lidar`. Set another Node-RED host with `--ros-args -p dashboard_url:=http://HOST:1880`.

A vision script can also call the helper directly:

```python
from scripts.nodered_client import post_json

post_json(
    "http://localhost:1880/api/alert",
    {
        "obstacle_detected": bool(detected),
        "distance_m": distance_m,
        "message": "Obstacle detected",
    },
)
```

## Calibration and presentation

Software integration is testable in simulation; physical camera/depth calibration remains a hardware task. For the hardware portion, record the sensor make/model, mounting position, calibration procedure/settings, terrain and lighting, test cases, and measured results. Do not present simulated topic status as proof of physical calibration.

| Calibration record | What to write down |
|---|---|
| Sensor | Make, model, serial number, and driver |
| Installation | Mounting position, orientation, and sensor-to-robot transform |
| Calibration | Tool/procedure, settings, date, and person who performed it |
| Test conditions | Terrain, distance, lighting, and weather |
| Results | Test cases, measured error/limitations, and pass/fail |

For a joint presentation, split the demo simply:

1. **Presenter 1 — Dashboard:** Import the flow, explain the alert/status panels, and send a detected event then a clear event with the Python client.
2. **Presenter 2 — Robot integration:** Show the ROS simulation and bridge, explain that the current obstacle source is LiDAR threshold detection, and show sensor availability on the dashboard.
3. **Together — Calibration and next step:** Present completed hardware calibration records, or clearly state calibration is pending until the physical camera/depth sensors are available. Do not claim simulation data proves physical calibration.

The HTTP endpoints do not provide authentication or encryption. Keep Node-RED on a trusted local network; do not expose it directly to the public internet.