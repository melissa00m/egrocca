FROM osrf/ros:jazzy-desktop

# Avoid interactive prompts during apt install
ENV DEBIAN_FRONTEND=noninteractive

# Install Gazebo Harmonic bridge and additional dependencies
RUN apt-get update && apt-get install -y \
    ros-jazzy-ros-gz \
    ros-jazzy-teleop-twist-keyboard \
    python3-colcon-common-extensions \
    python3-pip \
    mesa-utils \
    && rm -rf /var/lib/apt/lists/*

# Set up environment
WORKDIR /ros2_ws

# Setup entrypoint to source ROS 2
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc

CMD ["/bin/bash"]
