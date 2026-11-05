#!/usr/bin/env bash
# ==============================================================================
# Run ShopDrone Simulation in Docker with X11 GUI forwarding
# ==============================================================================

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
WORKSPACE_ROOT="$(dirname "$DIR")/ros2_ws"

echo "Building Docker image 'shopdrone_sim:latest'..."
docker build -t shopdrone_sim:latest -f "$DIR/Dockerfile" "$DIR"

echo "Enabling local X11 display permissions for Docker GUI..."
xhost +local:root || true

echo "Starting ShopDrone ROS 2 container..."
docker run -it --rm \
    --name shopdrone_container \
    --net=host \
    --ipc=host \
    --privileged \
    -e DISPLAY="$DISPLAY" \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v "$WORKSPACE_ROOT":/ros2_ws \
    shopdrone_sim:latest \
    bash -c "cd /ros2_ws && colcon build --symlink-install && source install/setup.bash && ros2 launch shopdrone_simulation mission_demo.launch.py"
