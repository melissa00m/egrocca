#!/usr/bin/env bash
# ShopDroid & ShopDrone 3D Simulation Launcher
# Robust startup with process cleanup and graphics environment tuning

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$SCRIPT_DIR/ros2_ws"
PKG_DIR="$WS_DIR/src/shopdrone_simulation"

# 1. Clean up any previous suspended or orphaned simulation processes
echo "[INFO] Ensuring clean simulation environment..."
pkill -9 -f "gz sim" 2>/dev/null || true
pkill -9 -f "ground_controller" 2>/dev/null || true
pkill -9 -f "parameter_bridge" 2>/dev/null || true
sleep 0.5

# 2. Source ROS 2 Jazzy and Colcon workspace overlay
if [ -f "/opt/ros/jazzy/setup.bash" ]; then
    source /opt/ros/jazzy/setup.bash
else
    echo "[ERROR] ROS 2 Jazzy setup file not found at /opt/ros/jazzy/setup.bash"
    exit 1
fi

if [ -f "$WS_DIR/install/setup.bash" ]; then
    source "$WS_DIR/install/setup.bash"
else
    echo "[INFO] Workspace not built yet. Building now with colcon..."
    cd "$WS_DIR"
    colcon build --symlink-install
    source "$WS_DIR/install/setup.bash"
fi

# 3. Export Comprehensive Gazebo Harmonic Resource & Render Paths
export GZ_SIM_RESOURCE_PATH="$PKG_DIR:$PKG_DIR/models:$PKG_DIR/models/shopdroid:$PKG_DIR/models/shopdrone:$PKG_DIR/materials:$PKG_DIR/meshes:$PKG_DIR/worlds:$WS_DIR/install/shopdrone_simulation/share/shopdrone_simulation:${GZ_SIM_RESOURCE_PATH:-}"
export QT_QPA_PLATFORM="xcb"
export MESA_GL_VERSION_OVERRIDE="4.5"
# Force Gazebo Transport to strictly use local loopback (fixes black screen caused by Docker/VPN interfaces)
export GZ_IP="127.0.0.1"
export GZ_PARTITION="shopdroid"

echo "===================================================================="
echo "    Launching ShopDroid Simulation in Gazebo Harmonic & ROS 2       "
echo "===================================================================="
echo "[INFO] GZ Resource Path configured."
echo "[INFO] Starting 3D World: Rural Zimbabwe Savannah..."

ros2 launch shopdrone_simulation simulation.launch.py "$@"
