# ShopDroid Integrated Deliverables Report

**Project:** ShopDroid autonomous rural delivery droid

**Repository:** [melissa00m/egrocca](https://github.com/melissa00m/egrocca)

**Submission date:** 2 November 2026

**Contributors:** [Your full name] and [Partner's full name]

**Course / supervisor:** [Add course and supervisor, if required]

> Before submission, replace the bracketed fields and make sure the contribution table reflects what each person actually did. Both contributors should review the final copy.

## Abstract

This report summarizes three related software deliverables for the ShopDroid project: simulated sensor setup and feed-verification guidance, a Node-RED obstacle dashboard with an HTTP integration path, and system architecture and setup documentation. The work connects existing ROS 2 and Gazebo simulation interfaces to a practical monitoring demonstration while distinguishing verified software behavior from work that still requires the physical robot and sensors.

The deliverables are merged into the repository's `main` branch. The dashboard flow and Python sender were exercised with test messages. The ROS integration is provided in source code, but this report does not claim that a complete ROS/Gazebo build or physical calibration was performed as part of the dashboard test. Physical camera/LiDAR calibration and hardware feed verification remain future validation tasks.

## 1. Project context and objective

ShopDroid is a ground delivery robot project using ROS 2 and Gazebo. Its simulated system includes a robot model, LiDAR and camera topics, a ROS-Gazebo bridge, and ROS nodes for obstacle monitoring and robot behavior. The objective of these deliverables was to document sensor interfaces, display obstacle and sensor status for testing, and explain how implemented software relates to planned hardware and external systems.

The work is scoped to software and simulation integration. It does not certify the physical robot, prove camera-based AI detection, or provide a pin-accurate electrical wiring design.

## 2. Deliverables

### ShopDroid sensor setup and feed verification

The sensor guide records the simulated LiDAR and camera mounting references, sensor topics, expected message types, and commands for checking topic availability and publishing rates. The ROS 2 launch files bridge camera calibration metadata (`CameraInfo`) along with sensor data.

The guide also provides a procedure for measuring physical sensor poses, calibrating the camera, checking LiDAR alignment, exercising representative terrain conditions safely, and recording results. Simulated poses are explicitly identified as simulation values, not verified physical measurements.

**Repository file:** [`docs/sensor_setup.md`](sensor_setup.md)

### Node-RED obstacle dashboard and integration

The importable Node-RED flow provides a browser dashboard and HTTP endpoints for obstacle alerts, camera/LiDAR status, and reading the latest dashboard state. A Python client sends test events or can be called by another script. A ROS 2 bridge is provided to forward obstacle state and distance and report whether the simulated camera and LiDAR topics are arriving. The obstacle source currently used by the ROS monitor is LiDAR distance-threshold detection; it is not an AI vision model.

The dashboard can display a camera image only when a browser-readable HTTP/MJPEG stream is supplied. A ROS image topic by itself is not a browser video URL. The HTTP endpoints do not include authentication or encryption and are intended for trusted local testing, not direct public exposure.

**Repository files:** [`nodered/flows.json`](../nodered/flows.json), [`scripts/nodered_client.py`](../scripts/nodered_client.py), [`nodered_bridge`](../ros2_ws/src/shopdrone_simulation/shopdrone_simulation/nodered_bridge.py), [`docs/node_red_dashboard.md`](node_red_dashboard.md)

### System architecture and setup documentation

The architecture guide separates implemented ROS 2/Gazebo data paths from planned or external interfaces, including AI vision, Node-RED, XOD, and a database. It documents the current setup and explains why a reliable pin-level wiring diagram cannot be inferred without confirmed physical component models, ratings, connectors, and pin assignments.

**Repository file:** [`docs/system_architecture.md`](system_architecture.md)

## 3. Tools and technologies

| Tool / technology | Use in the deliverables |
|---|---|
| ROS 2 Jazzy | Robot nodes, sensor topics, and the optional dashboard bridge |
| Gazebo Harmonic | Simulated robot, terrain, and sensors |
| `ros_gz_bridge` | Bridges simulated sensor and robot messages between Gazebo and ROS 2 |
| Node-RED | Importable HTTP flow and browser-based monitoring dashboard |
| Python 3 | HTTP test client and ROS-to-Node-RED adapter |
| Git and GitHub | Version control, review, and delivery of the work |

## 4. Verification performed

- The Node-RED flow JSON was parsed successfully and its HTTP endpoints were checked.
- The flow was run in Node-RED, and the Python client sent an obstacle-detected event, sensor status, and a clear-path event.
- The dashboard page returned successfully; the latest status reflected the test messages.
- An invalid obstacle payload was rejected with HTTP 400.
- Python syntax checks passed for the client and ROS bridge.
- The three deliverables were merged into `main` through GitHub pull requests.

The live dashboard checks used sample data. They do not prove physical sensor calibration, a live camera stream, or safe autonomous navigation. A ROS 2/Gazebo build and hardware tests should be run on the project's supported robot development environment before claiming those results.

## 5. Current limitations and next steps

1. Perform camera calibration and LiDAR alignment with the actual sensors and final robot mounts; save calibration files, transforms, test conditions, and reviewed results.
2. Verify ROS topic delivery and expected rates on the physical compute unit, including timestamps, frame IDs, image dimensions, and dropped-message behavior.
3. Build the ROS 2 workspace and run the simulation bridge with Node-RED on the target development setup.
4. If live video is required, provide and test a browser-readable HTTP/MJPEG stream; the current flow does not convert ROS images to video.
5. Add authentication and encryption before using the HTTP endpoints beyond a trusted local test network.
6. Confirm the physical controller, motors, sensors, power system, pins, and connectors before producing or approving a wiring diagram.

## 6. Shared contribution record

Complete this table together before submission so it accurately reflects each contributor's work.

| Contributor | Work completed / responsibility | Evidence or section presented |
|---|---|---|
| [Your full name] | [Describe your actual contribution] | [Guide, code, tests, or presentation section] |
| [Partner's full name] | [Describe your partner's actual contribution] | [Guide, code, tests, or presentation section] |

The guides describe project deliverables and shared technical results. They do not by themselves establish which person performed each task; the contributors should agree on and complete the table.

## 7. Suggested joint demonstration

1. Show the sensor guide and explain which settings are simulation references and which physical tests are still pending.
2. Import and deploy `nodered/flows.json`, open the dashboard, and send a detected event followed by a clear event with the Python client.
3. Explain how the ROS bridge connects obstacle and sensor topics to the dashboard, distinguishing LiDAR threshold monitoring from AI vision.
4. Present the architecture diagram and identify implemented paths versus planned integrations.
5. Close with the physical calibration and hardware-validation plan and clearly state any work not yet performed.

## 8. Repository record

The three deliverables are available from the `main` branch:

- [Sensor setup and feed verification](sensor_setup.md)
- [Node-RED obstacle dashboard](node_red_dashboard.md)
- [System architecture and setup](system_architecture.md)

The corresponding merged pull requests are [#11](https://github.com/melissa00m/egrocca/pull/11), [#12](https://github.com/melissa00m/egrocca/pull/12), and [#13](https://github.com/melissa00m/egrocca/pull/13).
