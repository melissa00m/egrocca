# AGENTS.md — Agent Operating Guidelines & Workspace Directives

> **Notice for AI Coding Agents:**  
> This file contains strict operational rules, architectural context, and development guidelines for autonomous or semi-autonomous coding agents (such as Antigravity, Claude Code, Gemini CLI, Cursor, and GitHub Copilot) operating within this repository.

---

## 1. Project Context & Engineering Pivot

### 1.1 The Pivot: From Aerial Drone to Terrestrial Droid
This project originally explored an autonomous aerial delivery drone (**ShopDrone**). Following regulatory, technical, and environmental evaluations, the project has **pivoted to an autonomous all-terrain ground delivery droid** (**ShopDroid**):
- **Regulatory Freedom:** Autonomous ground vehicles avoid complex Civil Aviation Authority (CAA) commercial drone flight licensing, strict airspace corridors, and visual-line-of-sight (BVLOS) legal bottlenecks.
- **Payload Capacity:** Ground chassis can carry 15–25 kg of critical groceries, tools, and medicine, whereas commercial multirotor drones were constrained to under 2.5 kg.
- **All-Weather Resilience:** Multirotors are vulnerable to high winds, convective thunderstorms, and heavy downpours common in rural southern Africa. A rugged ground droid (conceptualized like an autonomous mechanical horse or heavy-duty all-terrain rover) can traverse mud, gravel, waterlogged ruts, and continue operating safely under adverse weather.
- **Safety:** Failure of a ground droid results in a stationary stop with hazard indicators, avoiding the catastrophic drop hazards associated with airborne UAV failures.

### 1.2 Core Mission
Deliver critical goods from rural retail growth points / shops directly to isolated homesteads across rugged, unpaved, and weather-beaten terrain in rural Zimbabwe using ROS 2 Jazzy and Gazebo Harmonic physics simulation.

---

## 2. Technology Stack & Environment

| Component | Target Version / Tool | Notes |
| :--- | :--- | :--- |
| **Operating System** | Ubuntu 24.04 LTS (Noble) / Linux Mint 22.1 | Host OS environment |
| **Robotics Middleware** | **ROS 2 Jazzy Jalisco** | `rclpy` (Python 3.12) |
| **Physics Simulator** | **Gazebo Harmonic** (`gz-sim8`) | Modern SDF world & robot models |
| **ROS-Gazebo Bridge** | `ros_gz_bridge`, `ros_gz_sim`, `ros_gz_image` | Topic & clock bridging |
| **Build System** | `colcon build --symlink-install` | Standard ROS 2 workflow |
| **Containerization** | Docker + Compose with X11 GUI forwarding | Contained in `docker/` |

---

## 3. Directory Layout

Agents must respect the following organization:

```
group project gazebo/
├── README.md                      # Primary user & collaborator documentation
├── AGENTS.md                      # Instructions & rules for AI agents (this file)
├── collaborators.md               # Human team directory & working groups
├── install_ros2_jazzy_gazebo.sh   # Host setup script for ROS 2 Jazzy + Gazebo
├── docker/
│   ├── Dockerfile                 # Containerized ROS 2 Jazzy + Gazebo environment
│   └── run_sim_docker.sh          # Container launcher with X11 display support
├── docs/
│   ├── images/                    # Visual assets and concept renders
│   └── ShopDrone_Simulation_Guide.html # Interactive simulator docs
└── ros2_ws/                       # ROS 2 Colcon Workspace
    ├── test_prototype.py          # Automated verification & SRS unit test suite
    ├── run_demo_cli.py            # Standalone visualizer (interactive terminal demo)
    └── src/
        └── shopdrone_simulation/  # Primary ROS 2 package
            ├── launch/            # ROS 2 launch files (simulation.launch.py, mission_demo.launch.py)
            ├── models/            # Gazebo SDF models (robot chassis, hub, homestead, obstacles)
            ├── worlds/            # Gazebo 3D worlds (rural_zimbabwe.sdf)
            ├── rviz/              # Preconfigured RViz display profiles
            └── shopdrone_simulation/ # Python node implementations
                ├── flight_controller.py   # Legacy autopilot state machine
                ├── ground_controller.py   # (In progress) Terrestrial all-terrain waypoint controller
                ├── cargo_lock.py          # Secure 4-digit OTP digital payload compartment
                ├── battery_monitor.py     # Energy discharge model & return-to-hub failsafe
                ├── obstacle_monitor.py    # 3D LiDAR / range sensor collision monitoring
                └── telemetry_publisher.py # GPS / GSM / LoRa telemetry broadcast
```

---

## 4. Agent Operational Rules

### Rule 1: Never Break the Build or Verification Suite
Whenever you modify code or models in `ros2_ws/`:
1. Re-build the workspace:
   ```bash
   cd ros2_ws
   source /opt/ros/jazzy/setup.bash
   colcon build --symlink-install
   ```
2. Run the test suite:
   ```bash
   python3 ros2_ws/test_prototype.py
   ```
3. If tests fail or syntax errors are introduced, fix them before completing your turn.

### Rule 2: Backward Compatibility & Progressive Migration
- The codebase is transitioning from aerial UAV models to terrestrial droid models.
- **Do not abruptly delete or break legacy simulation entrypoints** (`flight_controller.py`, `simulation.launch.py`, `test_prototype.py`) unless instructed. Instead, create new ground-specific nodes (e.g., `ground_controller.py`, `terrain_planner.py`, or parameterized launch arguments like `robot_type:=droid`) alongside existing assets.
- Ensure `run_demo_cli.py` remains functional as a zero-dependency interactive demonstration tool.

### Rule 3: ROS 2 Coding Standards
- Use Python 3 type annotations where applicable.
- All nodes must inherit from `rclpy.node.Node`.
- Use ROS 2 logging (`self.get_logger().info()`, `self.get_logger().warn()`, `self.get_logger().error()`) instead of raw `print()` statements inside nodes.
- Maintain clean rate-limiting via `create_timer()`, never use blocking `time.sleep()` inside ROS 2 execution threads.
- Adhere to standard ROS 2 topic naming conventions (`/cmd_vel`, `/odom`, `/shopdroid/lidar`, `/shopdroid/battery_state`).

### Rule 4: Physics & Simulation Safety
- Gazebo models must use valid SDF 1.9+ syntax compatible with Gazebo Harmonic.
- Ground droid collision geometries must include proper friction coefficients (`mu`, `mu2`) suitable for dirt, mud, and rock surfaces.
- Inertial tensors must be physically realistic (prevent high center of mass that causes tipping on steep rural slopes).

### Rule 5: Documentation & Git Hygiene
- When creating or modifying features, keep [README.md](file:///home/mphatic/Desktop/group%20project%20gazebo/README.md) and [collaborators.md](file:///home/mphatic/Desktop/group%20project%20gazebo/collaborators.md) synchronized.
- Create concise, descriptive commit messages if asked to perform git operations.
- Preserve all existing comments and docstrings unrelated to your edits.

---

## 5. Quick Verification Commands for Agents

To verify the state of the system during any agent task:

```bash
# 1. Check workspace integrity
cd "group project gazebo/ros2_ws"
python3 -m py_compile test_prototype.py run_demo_cli.py
python3 -m py_compile src/shopdrone_simulation/shopdrone_simulation/*.py

# 2. Run automated logic & failsafe tests
python3 test_prototype.py

# 3. Test non-blocking execution of CLI demo
python3 run_demo_cli.py --test-mode 2>/dev/null || python3 test_prototype.py
```
