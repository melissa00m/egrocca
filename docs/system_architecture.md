# Egrocca System Architecture

This diagram separates what is present in the repository from systems that still need hardware or team confirmation.

```mermaid
flowchart LR
    subgraph SIM["Implemented: Gazebo Harmonic simulation"]
        WORLD["rural_zimbabwe.sdf"]
        DROID["ShopDroid model"]
        LIDAR["Simulated LiDAR"]
        CAMERA["Simulated camera"]
        WORLD --> DROID
        DROID --> LIDAR
        DROID --> CAMERA
    end

    subgraph ROS["Implemented: ROS 2 Jazzy"]
        BRIDGE["ros_gz_bridge"]
        GROUND["ground_controller"]
        OBS["obstacle_monitor<br/>LiDAR distance threshold"]
        SAFETY["battery_monitor<br/>cargo_lock"]
        TELEMETRY["telemetry_publisher"]
        CMD["/cmd_vel"]
        ALERT["/shopdrone/obstacle_detected<br/>/shopdrone/alerts"]
        STATUS["state, battery and GPS topics"]
    end

    LIDAR -->|LaserScan| BRIDGE
    CAMERA -->|Image| BRIDGE
    BRIDGE -->|ROS topics| OBS
    BRIDGE -->|/odom| GROUND
    OBS -->|obstacle state| GROUND
    OBS --> ALERT
    GROUND --> CMD
    SAFETY --> STATUS
    TELEMETRY --> STATUS
    CMD -->|Twist| BRIDGE
    BRIDGE --> DROID

    subgraph PLANNED["Planned or external: not integrated in this repository"]
        AI["AI vision model"]
        NODE["Optional Node-RED dashboard<br/>HTTP integration"]
        XOD["XOD / physical controller"]
        DB["Database"]
    end

    CAMERA -.->|image processing interface TBD| AI
    AI -.->|HTTP alert interface in Role 2 flow| NODE
    ROS -.->|hardware command mapping TBD| XOD
    NODE -.->|storage schema and connection TBD| DB
```

Solid arrows show the current simulation's data/control paths. Dashed arrows are proposed integration points, not working hardware connections. In particular:

- The repository's `obstacle_monitor.py` is a LiDAR range-threshold node; it is not an AI model.
- The ROS/Gazebo bridge exposes simulated sensor messages and drive commands. It does not configure physical sensor drivers.
- The Node-RED dashboard is an optional HTTP integration, not a ROS node. A vision/ROS client must forward alerts to it; the current launch files do not connect to Node-RED.
- No XOD project, database service/schema, or hardware command mapping is present here. Confirm their intended roles and protocols with the team before treating the dashed links as final.

## Physical wiring diagram status

A pin-accurate Fritzing diagram cannot be made from the simulation files alone. The repository does not specify the physical controller board, sensor models, motor drivers, battery/power regulators, pin assignments, or connector types. Do not infer electrical wiring from the simulated SDF sensor poses.

Before creating the Fritzing file, collect and confirm:

| Required information | Record before drawing |
|---|---|
| Controller and compute unit | Board model, revision, logic voltage, pinout |
| Sensors | Camera and LiDAR models, interfaces, supply voltage, current, connectors |
| Drive system | Motors, motor-driver models, ratings, control and feedback pins |
| Power | Battery chemistry and voltage, fuses, regulators, grounding and emergency stop |
| Wiring | Connector/pin numbers, cable type, colors, and any level shifting |

Once the prototype is available and the design is reviewed by the hardware team, commit the editable Fritzing project and an exported image/PDF under `docs/`. Label power rails, grounds, connectors, and pin numbers, and include the approved component list. Until then, mark this deliverable as pending rather than publishing a speculative wiring diagram.
