# Node-RED Obstacle Dashboard

This lightweight dashboard uses Node-RED's built-in HTTP and browser nodes; it does not require a dashboard add-on.

## Start the dashboard

1. Install Node-RED using its official installation instructions if it is not already installed.
2. From the repository root, start it with `node-red` and open `http://localhost:1880`. In Windows PowerShell, use `node-red.cmd` if script execution policy blocks `node-red`.
3. In the Node-RED editor, choose **Menu → Import → select a file**, then select `nodered/flows.json` from this repository. Deploy the imported flow.
4. Open `http://localhost:1880/dashboard` to view the dashboard.

The flow provides these endpoints:

| Method and path | Purpose |
|---|---|
| `POST /api/alert` | Receive an obstacle detection or clear event |
| `POST /api/sensors` | Update camera/LiDAR state and optional camera stream URL |
| `GET /api/status` | Read the latest dashboard state |
| `GET /dashboard` | Open the dashboard |

## Send test messages

The standard-library Python client can send a simulated alert:

```bash
python scripts\nodered_client.py alert --state detected --distance-m 1.2 --message "Test obstacle"
python scripts\nodered_client.py alert --state clear --message "Path clear"
python scripts\nodered_client.py sensors --camera online --lidar online
```

The vision script can import and call `post_json` to forward detections:

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

Alert payloads contain a boolean `obstacle_detected` and may include numeric `distance_m` and string `message`. Sensor updates use boolean `camera_online` and/or `lidar_online`. For a remote Node-RED host, use its reachable address instead of `localhost`.

To display a live camera stream, the camera or a separate ROS image streamer must provide a browser-readable HTTP/MJPEG URL. Configure it through the sensor endpoint or paste it into the dashboard. The existing ROS `/shopdroid/camera/image_raw` topic is not itself a browser video URL, and this flow does not convert it. The repo currently has no vision-to-HTTP or ROS-image streaming adapter, so the commands above are test inputs, not evidence of physical camera calibration or a live hardware feed. Calibration on rough terrain remains a hardware test; the physical sensor models and prototype are not available in this repository.

Run Node-RED on a trusted local network only. These HTTP endpoints do not include authentication or encryption; do not expose them directly to the public internet.
