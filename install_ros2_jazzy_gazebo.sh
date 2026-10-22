#!/usr/bin/env bash
# ==============================================================================
# ShopDrone - Automated Installer for ROS 2 Jazzy & Gazebo Harmonic
# Tailored for Linux Mint 22.1 (Xia) / Ubuntu 24.04 (Noble Numbat)
# National University of Science and Technology (NUST) - Group Project
# ==============================================================================

set -e

# Terminal colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}====================================================================${NC}"
echo -e "${GREEN}  ShopDrone Project: ROS 2 Jazzy & Gazebo Harmonic Installation     ${NC}"
echo -e "${CYAN}====================================================================${NC}"

# Check for root / sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERROR] Please run this script with sudo:${NC}"
    echo -e "        ${YELLOW}sudo ./install_ros2_jazzy_gazebo.sh${NC}"
    exit 1
fi

# Detect Ubuntu Codename (Handles Linux Mint properly)
if [ -f /etc/os-release ]; then
    . /etc/os-release
    # Linux Mint uses UBUNTU_CODENAME for the underlying Ubuntu release (e.g. noble)
    TARGET_CODENAME="${UBUNTU_CODENAME:-$VERSION_CODENAME}"
else
    TARGET_CODENAME="noble"
fi

echo -e "${BLUE}[INFO] Detected distribution base codename:${NC} ${YELLOW}$TARGET_CODENAME${NC}"
if [ "$TARGET_CODENAME" != "noble" ]; then
    echo -e "${YELLOW}[WARN] Target codename is not 'noble' (Ubuntu 24.04). Overriding to 'noble' for ROS 2 Jazzy compatibility.${NC}"
    TARGET_CODENAME="noble"
fi

echo -e "\n${BLUE}[1/5] Setting up system locales...${NC}"
apt update && apt install -y locales curl gnupg lsb-release software-properties-common
locale-gen en_US en_US.UTF-8
update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

echo -e "\n${BLUE}[2/5] Adding Ubuntu Universe repository...${NC}"
add-apt-repository -y universe

echo -e "\n${BLUE}[3/5] Adding ROS 2 Jazzy GPG key and APT repository...${NC}"
install -d -m 0755 /usr/share/keyrings
curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $TARGET_CODENAME main" \
    | tee /etc/apt/sources.list.d/ros2.list > /dev/null

echo -e "\n${BLUE}[4/5] Installing ROS 2 Jazzy, Gazebo Harmonic, and Build Tools...${NC}"
apt update
apt install -y \
    ros-jazzy-ros-base \
    ros-jazzy-ros-gz \
    ros-jazzy-teleop-twist-keyboard \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-pip \
    build-essential

# Initialize rosdep if not already done
if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
    echo -e "${BLUE}[INFO] Initializing rosdep...${NC}"
    rosdep init || true
fi

echo -e "\n${BLUE}[5/5] Configuring environment variables...${NC}"
# Setup bashrc entry for regular user if running via sudo
TARGET_USER="${SUDO_USER:-$USER}"
USER_HOME=$(eval echo "~$TARGET_USER")

if ! grep -q "source /opt/ros/jazzy/setup.bash" "$USER_HOME/.bashrc" 2>/dev/null; then
    echo "" >> "$USER_HOME/.bashrc"
    echo "# ROS 2 Jazzy & Gazebo Environment for ShopDrone" >> "$USER_HOME/.bashrc"
    echo "source /opt/ros/jazzy/setup.bash" >> "$USER_HOME/.bashrc"
    echo "export GZ_VERSION=harmonic" >> "$USER_HOME/.bashrc"
    echo -e "${GREEN}[SUCCESS] Added ROS 2 Jazzy environment source to $USER_HOME/.bashrc${NC}"
fi

echo -e "\n${CYAN}====================================================================${NC}"
echo -e "${GREEN}  INSTALLATION COMPLETE! 🎉                                         ${NC}"
echo -e "${CYAN}====================================================================${NC}"
echo -e "To verify in your terminal:"
echo -e "  ${YELLOW}source /opt/ros/jazzy/setup.bash${NC}"
echo -e "  ${YELLOW}ros2 --help${NC}"
echo -e "  ${YELLOW}gz sim --help${NC}"
echo -e "${CYAN}====================================================================${NC}"
